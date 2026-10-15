"""Every selected case remains represented after skips, failures and interruption."""

import json
from dataclasses import replace
from pathlib import Path

from anthropic_readiness.config import Limits, load_target
from anthropic_readiness.contracts import resolve_contract
from anthropic_readiness.models import Capture, RequestSpec
from anthropic_readiness.runner import execute_run, plan_run, result_exit_code
from anthropic_readiness.transport import HttpTransport
from tests.factories import capture

ROOT = Path(__file__).resolve().parents[2]


class FixtureTransport(HttpTransport):
    def __init__(self, fail_second: bool = False, internal_second: bool = False):
        super().__init__()
        self.calls = 0
        self.fail_second = fail_second
        self.internal_second = internal_second

    def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
        self.calls += 1
        if self.internal_second and self.calls == 2:
            raise RuntimeError("synthetic internal fault")
        if request.streaming:
            name = (
                "stream-duplicate-start.sse"
                if self.fail_second and self.calls == 2
                else "stream-valid.sse"
            )
            body = (ROOT / "tests/fixtures/contracts/core-1.0.0" / name).read_bytes()
            if self.calls == 3:
                body = body.replace(b"Hello.", b"1 2 3 4 5")
            result = capture(body, True)
        else:
            result = capture()
        return replace(result, request=request)


def test_failure_after_success_and_internal_exit_precedence(tmp_path: Path) -> None:
    target = load_target(ROOT / "examples/target.yaml")
    plan = plan_run(
        target, resolve_contract(target.contract_id, target.contract_revision), ["anthropic-basic"]
    )
    result = execute_run(plan, FixtureTransport(fail_second=True), tmp_path / "failure")
    assert [c["status"] for c in result.cases] == ["PASS", "FAIL", "PASS"]
    assert result_exit_code(result) == 1
    internal = execute_run(plan, FixtureTransport(internal_second=True), tmp_path / "internal")
    assert result_exit_code(internal) == 4
    assert len(internal.cases) == 3
    assert internal.cases[0]["status"] == "PASS"


def test_missing_credentials_and_capability_exclusion(tmp_path: Path) -> None:
    target = load_target(ROOT / "examples/target.yaml")
    target = replace(
        target,
        auth_mode="api_key",
        credential_env="SYNTHETIC_MISSING_KEY",
        capabilities=(("streaming", False), ("tools", False)),
    )
    transport = FixtureTransport()
    result = execute_run(
        plan_run(
            target,
            resolve_contract(target.contract_id, target.contract_revision),
            ["anthropic-basic", "anthropic-tools-smoke"],
        ),
        transport,
        tmp_path / "run",
        environment={},
    )
    assert [c["status"] for c in result.cases] == ["BLOCKED", "SKIP", "SKIP", "SKIP"]
    assert transport.calls == 0
    assert result_exit_code(result) == 3


def test_run_deadline_preserves_unexecuted_cases(tmp_path: Path) -> None:
    target = load_target(ROOT / "examples/target.yaml")
    now = [0.0]

    class DelayedTransport(FixtureTransport):
        def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
            result = super().send(request, limits, deadline)
            now[0] = 1000
            return result

    result = execute_run(
        plan_run(
            target,
            resolve_contract(target.contract_id, target.contract_revision),
            ["anthropic-basic"],
        ),
        DelayedTransport(),
        tmp_path / "run",
        clock=lambda: now[0],
    )
    assert [c["status"] for c in result.cases] == ["PASS", "INDETERMINATE", "INDETERMINATE"]
    assert result.plan["actual_requests"] == 1
    assert result_exit_code(result) == 3


def test_secret_is_absent_from_complete_output(tmp_path: Path) -> None:
    target = load_target(ROOT / "examples/target.yaml")
    secret = "synthetic-runner-credential"
    target = replace(target, auth_mode="api_key", credential_env="SYNTHETIC_KEY")

    class EchoTransport(FixtureTransport):
        def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
            assert dict(request.headers)["x-api-key"] == secret
            value = json.loads(capture().body)
            value["content"][0]["text"] = secret
            return replace(capture(json.dumps(value).encode()), request=request)

    out = tmp_path / "run"
    result = execute_run(
        plan_run(
            target,
            resolve_contract(target.contract_id, target.contract_revision),
            ["anthropic-basic"],
        ),
        EchoTransport(),
        out,
        environment={"SYNTHETIC_KEY": secret},
    )
    assert result.plan["actual_requests"] == 3
    assert all(
        secret.encode() not in path.read_bytes() for path in out.rglob("*") if path.is_file()
    )


def test_returned_result_and_saved_result_are_both_sanitized(tmp_path: Path) -> None:
    target = load_target(ROOT / "examples/target.yaml")
    target = replace(target, auth_mode="api_key", credential_env="SYNTHETIC_KEY")
    secret = "synthetic-header-credential"

    class HeaderEchoTransport(FixtureTransport):
        def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
            return replace(
                super().send(request, limits, deadline), headers=(("content-type", secret),)
            )

    result = execute_run(
        plan_run(
            target,
            resolve_contract(target.contract_id, target.contract_revision),
            ["anthropic-basic"],
        ),
        HeaderEchoTransport(),
        tmp_path / "run",
        environment={"SYNTHETIC_KEY": secret},
    )
    assert secret not in json.dumps(result.to_json())


def test_missing_required_assertion_and_profile_member_are_rejected(tmp_path: Path) -> None:
    from anthropic_readiness.models import object_value
    from anthropic_readiness.schema import validate_result_semantics

    target = load_target(ROOT / "examples/target.yaml")
    result = execute_run(
        plan_run(
            target,
            resolve_contract(target.contract_id, target.contract_revision),
            ["anthropic-basic"],
        ),
        FixtureTransport(),
        tmp_path / "run",
    )
    document = object_value(json.loads(json.dumps(result.to_json())))
    cases = document["cases"]
    assert isinstance(cases, list)
    first = object_value(cases[0])
    attempts = first["attempts"]
    assert isinstance(attempts, list)
    attempt = object_value(attempts[0])
    assertions = attempt["assertions"]
    assert isinstance(assertions, list)
    attempt["assertions"] = [
        a for a in assertions if not isinstance(a, dict) or a.get("id") != "TASK-COMPLETE"
    ]
    first["attempts"] = [attempt]
    cases[0] = first
    assert any("missing_assertion" in error for error in validate_result_semantics(document))
    document = result.to_json()
    document["profiles"] = [
        {"id": "anthropic-basic", "version": 1, "cases": ["ANT-MESSAGE-001"], "readiness": "passed"}
    ]
    assert any("profile_cases" in error for error in validate_result_semantics(document))


def test_replay_mode_requires_capture_before_execution(tmp_path: Path) -> None:
    import pytest

    target = load_target(ROOT / "examples/target.yaml")
    plan = plan_run(
        target, resolve_contract(target.contract_id, target.contract_revision), ["anthropic-basic"]
    )
    transport = FixtureTransport()
    with pytest.raises(ValueError, match="run_mode_capture_mismatch"):
        execute_run(replace(plan, mode="replay"), transport, tmp_path / "run")
    assert transport.calls == 0
    assert not (tmp_path / "run").exists()


def test_invalid_assertion_event_reference_blocks_final_result(tmp_path: Path) -> None:
    import pytest

    class BadEvidenceTransport(FixtureTransport):
        def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
            result = super().send(request, limits, deadline)
            return replace(
                result,
                frames=tuple(
                    replace(frame, sequence=frame.sequence + 999) for frame in result.frames
                ),
            )

    target = load_target(ROOT / "examples/target.yaml")
    out = tmp_path / "run"
    with pytest.raises(RuntimeError, match="evidence_integrity"):
        execute_run(
            plan_run(
                target,
                resolve_contract(target.contract_id, target.contract_revision),
                ["anthropic-basic"],
            ),
            BadEvidenceTransport(fail_second=True),
            out,
        )
    assert not (out / "result.json").exists()


def test_interrupt_exit_precedes_known_failure(tmp_path: Path) -> None:
    import signal

    target = load_target(ROOT / "examples/target.yaml")
    result = execute_run(
        plan_run(
            target,
            resolve_contract(target.contract_id, target.contract_revision),
            ["anthropic-basic"],
        ),
        FixtureTransport(fail_second=True),
        tmp_path / "run",
    )
    assert (
        result_exit_code(replace(result, execution_environment={"interruption": signal.SIGINT}))
        == 130
    )
    assert (
        result_exit_code(
            replace(
                result, execution_environment={"interruption": None, "internal_error": "synthetic"}
            )
        )
        == 4
    )
