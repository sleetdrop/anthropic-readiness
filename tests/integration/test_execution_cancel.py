"""Cancellation is sticky before registration and stops subsequent dispatch."""

import threading
import time
from pathlib import Path

import httpx

from anthropic_readiness.application import build_plan
from anthropic_readiness.config import Limits, load_target
from anthropic_readiness.models import RequestSpec
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.operations.ports import CancelToken
from anthropic_readiness.runner import execute_run, result_exit_code
from anthropic_readiness.transport import HttpTransport
from tests.acceptance.test_runner import FixtureTransport
from tests.http_server import SyntheticServer

ROOT = Path(__file__).resolve().parents[2]


def test_cancel_before_transport_callback_registration() -> None:
    calls: list[str] = []
    token = CancelToken()
    token.cancel("user_cancelled")

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200)

    transport = HttpTransport(
        transport=httpx.MockTransport(handle),
        control=token,
    )
    captured = transport.send(
        RequestSpec("http://synthetic.invalid", (), {}, False), Limits(), time.monotonic() + 1
    )
    assert captured.capture_end == "cancelled"
    assert not calls


def test_late_callback_registration_observes_cancellation_once() -> None:
    token = CancelToken()
    callbacks: list[str] = []
    token.cancel("first")
    unsubscribe = token.register(lambda: callbacks.append("called"))
    token.cancel("second")
    unsubscribe()
    assert callbacks == ["called"]
    assert token.reason_code == "first"


def test_cancelled_run_checkpoints_all_required_cases_without_dispatch(tmp_path: Path) -> None:
    token = CancelToken()
    token.cancel("user_cancelled")
    output = tmp_path / "assessment"
    plan = build_plan(load_target(ROOT / "examples/target.yaml").to_json(), ["anthropic-basic"])
    transport = FixtureTransport()
    result = execute_run(
        plan,
        transport,
        output,
        control=token,
        observer=DiskExecutionObserver(output / "operations", output),
    )
    assert transport.calls == 0
    assert result.plan["actual_requests"] == 0
    assert [case["status"] for case in result.cases] == ["INDETERMINATE"] * 3
    assert len(list((output / "operations/checkpoints").glob("*.json"))) == 3
    assert result_exit_code(result) == 130


def test_cancel_during_transport_stops_without_waiting_for_read_timeout(
    server: SyntheticServer,
) -> None:
    token = CancelToken()
    timer = threading.Timer(0.1, lambda: token.cancel("user_cancelled"))
    started = time.monotonic()
    timer.start()
    try:
        captured = HttpTransport(control=token).send(
            RequestSpec(server.url + "/pings", (), {}, True), Limits(), started + 10
        )
    finally:
        timer.cancel()
        timer.join()
    assert captured.capture_end == "cancelled"
    assert time.monotonic() - started < 1
    assert len(server.requests) == 1
