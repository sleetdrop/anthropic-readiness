"""Capture real HTTP reads without retries, redirects or hidden requests."""

import socket
import time
from dataclasses import replace

import pytest

from anthropic_readiness.config import Limits
from anthropic_readiness.models import CaseContract, RequestSpec, Status
from anthropic_readiness.transport import HttpTransport
from anthropic_readiness.validation.stream import StreamValidator
from tests.integration.conftest import SyntheticServer

pytestmark = pytest.mark.integration


def request(url: str) -> RequestSpec:
    return RequestSpec(
        url,
        (
            ("content-type", "application/json"),
            ("anthropic-version", "2023-06-01"),
            ("anthropic-beta", "synthetic-a,synthetic-b"),
        ),
        {"model": "example-model"},
        True,
    )


@pytest.mark.parametrize(
    ("path", "protocol", "code"),
    [
        ("/valid", "message_stop", 200),
        ("/error", "error_event", 200),
        ("/early", "none", 200),
        ("/http-error", "none", 503),
        ("/redirect", "none", 307),
    ],
)
def test_http_capture_and_no_hidden_requests(
    server: SyntheticServer, path: str, protocol: str, code: int
) -> None:
    capture = HttpTransport().send(request(server.url + path), Limits(), time.monotonic() + 2)
    assert capture.protocol_end == protocol
    assert capture.capture_end == "eof"
    assert capture.status_code == code
    assert len(server.requests) == 1
    headers = server.requests[0][1]
    assert headers["anthropic-version"] == "2023-06-01"
    assert headers["anthropic-beta"] == "synthetic-a,synthetic-b"
    assert "x-api-key" not in headers
    assert "authorization" not in headers
    assert sum(read.length for read in capture.reads) == len(capture.body)


def test_refused_connection_is_environment_blocked() -> None:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    capture = HttpTransport().send(
        request(f"http://127.0.0.1:{port}"), Limits(), time.monotonic() + 1
    )
    assert capture.capture_end == "connection_error"
    assert capture.status_code is None


@pytest.mark.parametrize("compressed", [False, True])
def test_decompressed_body_limit(server: SyntheticServer, compressed: bool) -> None:
    capture = HttpTransport().send(
        request(server.url + ("/gzip" if compressed else "/valid")),
        replace(Limits(), max_response_bytes=32),
        time.monotonic() + 2,
    )
    assert capture.capture_end == "capture_limit"
    assert len(capture.body) == 32
    assert capture.observed_bytes == 33 if compressed else capture.observed_bytes > 32
    assert capture.observed_bytes == sum(read.length for read in capture.reads)
    assert capture.error == "max_response_bytes"


def test_event_limits(server: SyntheticServer) -> None:
    for limits, reason in [
        (replace(Limits(), max_events=1), "max_events"),
        (replace(Limits(), max_event_bytes=20), "max_event_bytes"),
    ]:
        capture = HttpTransport().send(request(server.url + "/valid"), limits, time.monotonic() + 2)
        assert capture.capture_end == "capture_limit"
        assert capture.tail.limit_kind == reason


def test_known_defect_retains_event_evidence(server: SyntheticServer) -> None:
    capture = HttpTransport().send(
        request(server.url + "/duplicate"), Limits(), time.monotonic() + 2
    )
    validator = StreamValidator(CaseContract("synthetic"))
    for frame in capture.frames:
        validator.consume(frame)
    result = validator.finish(capture.protocol_end, capture.capture_end, capture.tail)
    assertion = next(a for a in result.assertions if a.id == "STR-START")
    assert assertion.status == Status.FAIL
    assert assertion.event == 1


def test_reset_preserves_completed_message(server: SyntheticServer) -> None:
    capture = HttpTransport().send(request(server.url + "/reset"), Limits(), time.monotonic() + 2)
    assert capture.protocol_end == "message_stop"
    assert capture.capture_end == "read_error"


def test_observed_size_includes_the_whole_uncompressed_read() -> None:
    import httpx

    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=httpx.ByteStream(b"x" * 1000))

    capture = HttpTransport(transport=httpx.MockTransport(handle)).send(
        request("http://synthetic.invalid"),
        replace(Limits(), max_response_bytes=32),
        time.monotonic() + 1,
    )
    assert capture.observed_bytes == 1000
    assert capture.reads[0].length == 1000
    assert len(capture.body) == 32


def test_environment_proxy_is_not_inherited(
    server: SyntheticServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        monkeypatch.setenv(name, "http://127.0.0.1:1")
    monkeypatch.setenv("NO_PROXY", "")
    capture = HttpTransport().send(request(server.url + "/valid"), Limits(), time.monotonic() + 2)
    assert capture.status_code == 200


def test_offline_guard_rejects_external_addresses() -> None:
    with socket.socket() as sock, pytest.raises(RuntimeError, match="external_network_forbidden"):
        sock.connect(("192.0.2.1", 80))
