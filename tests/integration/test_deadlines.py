"""Activity and a protocol stop do not bypass absolute capture deadlines."""

import time
from dataclasses import replace

import pytest

from anthropic_readiness.config import Limits
from anthropic_readiness.models import RequestSpec
from anthropic_readiness.transport import HttpTransport
from tests.http_server import SyntheticServer

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("path", ["/pings", "/stop-open"])
def test_absolute_deadline_with_continuing_reads(server: SyntheticServer, path: str) -> None:
    limits = replace(Limits(), attempt_timeout_s=0.15, read_timeout_s=0.1)
    started = time.monotonic()
    capture = HttpTransport().send(
        RequestSpec(server.url + path, (), {}, True), limits, started + 3
    )
    assert capture.capture_end == "timeout"
    assert time.monotonic() - started < 1
    assert capture.protocol_end == ("message_stop" if path == "/stop-open" else "none")
    assert capture.frames


def test_run_deadline_is_stricter_than_attempt_limit(server: SyntheticServer) -> None:
    started = time.monotonic()
    capture = HttpTransport().send(
        RequestSpec(server.url + "/pings", (), {}, True), Limits(), started + 0.1
    )
    assert capture.capture_end == "timeout"
    assert time.monotonic() - started < 1
