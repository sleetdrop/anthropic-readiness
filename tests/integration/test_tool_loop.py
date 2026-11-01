"""One tool conversation must consume a fresh result, preserving both exchanges."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from anthropic_readiness.config import Limits, load_target
from anthropic_readiness.contracts import resolve_contract
from anthropic_readiness.diagnostics.identity import installed_identity
from anthropic_readiness.diagnostics.recipes import (
    build_recipe,
    prepare_retest,
    validate_recipe_evidence,
)
from anthropic_readiness.evidence import verify_evidence
from anthropic_readiness.models import Capture, RequestSpec, object_value
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.operations.ports import CancelToken
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.report_sources import load_report_source
from anthropic_readiness.runner import RunPlan, execute_run, plan_run, result_exit_code
from anthropic_readiness.schema import result_from_document
from anthropic_readiness.transport import HttpTransport
from tests.factories import capture
from tests.http_server import SyntheticServer

PROFILE = "anthropic-tool-loop"
CASE_ID = "ANT-TOOL-LOOP-001"


class LoopTransport(HttpTransport):
    def __init__(self, fault: str = "", control: CancelToken | None = None) -> None:
        super().__init__()
        self.requests: list[RequestSpec] = []
        self.fault = fault
        self.cancel_after_first = control

    def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
        self.requests.append(request)
        first = len(self.requests) == 1
        if not first and self.fault == "exception":
            raise RuntimeError("synthetic second exchange failure")
        if not first and self.fault == "timeout":
            return replace(capture(b""), request=request, capture_end="timeout")
        message = json.loads(
            Path("tests/fixtures/contracts/core-1.0.0/message-valid.json").read_text()
        )
        if first:
            message["stop_reason"] = "tool_use"
            message["content"] = [
                {"type": "text", "text": "Checking the weather."},
                {
                    "type": "tool_use",
                    "id": "toolu_loop_1",
                    "name": "get_weather",
                    "input": {"location": "Hanoi"},
                },
            ]
            if self.fault == "bad_id":
                message["content"][1]["id"] = ""
            if self.fault == "missing_metadata":
                del message["stop_sequence"]
            if self.cancel_after_first is not None:
                self.cancel_after_first.cancel("synthetic_between_exchanges")
        else:
            messages = request.body["messages"]
            assert isinstance(messages, list)
            assert len(messages) == 3
            assistant = object_value(messages[1])
            assert assistant["role"] == "assistant"
            content = assistant["content"]
            assert isinstance(content, list)
            assert object_value(content[1])["id"] == "toolu_loop_1"
            user = object_value(messages[2])
            blocks = user["content"]
            assert user["role"] == "user"
            assert isinstance(blocks, list)
            result = object_value(blocks[0])
            assert result["type"] == "tool_result"
            assert result["tool_use_id"] == "toolu_loop_1"
            token = json.loads(str(result["content"]))["verification_token"]
            assert token not in json.dumps(self.requests[0].body)
            message["content"] = [
                {"type": "text", "text": "ignored result" if self.fault == "ignored" else token}
            ]
            if self.fault == "extra_tool":
                message["content"].append(
                    {
                        "type": "tool_use",
                        "id": "toolu_unwanted",
                        "name": "get_weather",
                        "input": {"location": "Hanoi"},
                    }
                )
        return replace(capture(json.dumps(message).encode()), request=request)


def loop_plan() -> RunPlan:
    target = load_target(Path("examples/target.yaml"))
    return plan_run(
        target, resolve_contract(target.contract_id, target.contract_revision), [PROFILE]
    )


def test_plan_reserves_two_requests_for_one_scenario() -> None:
    plan = loop_plan()
    assert [case.id for case in plan.cases] == [CASE_ID]
    assert plan.to_json()["planned_requests"] == 2
    with pytest.raises(ValueError, match="request_budget_insufficient"):
        plan_run(
            replace(plan.target, limits=replace(plan.target.limits, max_requests=1)),
            plan.bundle,
            [PROFILE],
        )


def test_real_result_consumption_retains_two_exchanges_and_progress(tmp_path: Path) -> None:
    tmp_path = tmp_path / "run"
    peer = LoopTransport()
    observer = DiskExecutionObserver(tmp_path / "operations", tmp_path)
    result = execute_run(loop_plan(), peer, tmp_path, observer=observer)
    assert result_exit_code(result) == 0
    assert len(peer.requests) == result.plan["actual_requests"] == 2
    assert len(result.cases) == 1
    assert result.cases[0]["status"] == "PASS"
    assert len(objects(result.cases[0]["attempts"])) == 2
    assert len([ref for ref in result.evidence if ref.path.endswith("/request.json")]) == 2
    assert not verify_evidence(tmp_path, result.evidence)
    assert result_from_document(result.to_json()).cases[0]["status"] == "PASS"


@pytest.mark.parametrize("fault", ["ignored", "bad_id", "missing_metadata", "extra_tool"])
def test_faulty_loop_never_passes(tmp_path: Path, fault: str) -> None:
    tmp_path = tmp_path / "run"
    peer = LoopTransport(fault)
    result = execute_run(loop_plan(), peer, tmp_path)
    assert result.cases[0]["status"] == "FAIL"
    assert result_exit_code(result) == 1
    assert len(peer.requests) == (1 if fault == "bad_id" else 2)
    assert not verify_evidence(tmp_path, result.evidence)


@pytest.mark.parametrize("fault", ["timeout", "exception"])
def test_second_exchange_failure_preserves_first_evidence(tmp_path: Path, fault: str) -> None:
    tmp_path = tmp_path / "run"
    result = execute_run(loop_plan(), LoopTransport(fault), tmp_path)
    assert result.cases[0]["status"] == "INDETERMINATE"
    assert result.plan["actual_requests"] == 2
    assert len(objects(result.cases[0]["attempts"])) == 2
    assert any(ref.path.endswith("/response.json") for ref in result.evidence)
    assert not verify_evidence(tmp_path, result.evidence)


def test_cancellation_between_exchanges_sends_no_followup(tmp_path: Path) -> None:
    tmp_path = tmp_path / "run"
    control = CancelToken()
    peer = LoopTransport(control=control)
    result = execute_run(loop_plan(), peer, tmp_path, control=control)
    assert len(peer.requests) == result.plan["actual_requests"] == 1
    assert result.cases[0]["status"] == "INDETERMINATE"
    assert result_exit_code(result) == 130


def test_truncated_success_record_cannot_claim_complete_loop(tmp_path: Path) -> None:
    tmp_path = tmp_path / "run"
    result = execute_run(loop_plan(), LoopTransport(), tmp_path)
    document = result.to_json()
    cases = document["cases"]
    assert isinstance(cases, list)
    case = object_value(cases[0])
    attempts = case["attempts"]
    assert isinstance(attempts, list)
    case["attempts"] = attempts[:1]
    cases[0] = case
    document["plan"] = {**result.plan, "actual_requests": 1}
    with pytest.raises(ValueError, match="tool_loop"):
        result_from_document(document)


def test_dynamic_followup_has_portable_retest_evidence(tmp_path: Path) -> None:
    output = tmp_path / "run"
    plan = loop_plan()
    identity = installed_identity()
    recipe = build_recipe(plan, identity)
    execute_run(plan, LoopTransport(), output)
    source = load_report_source(output)
    assert source.evidence_verification["status"] == "verified"
    assert validate_recipe_evidence(recipe, source, output) == ()
    retest, changes = prepare_retest(recipe, plan.target.to_json(), identity)
    assert changes["comparable"] is True
    assert retest.planned_requests == 2


def test_single_capture_cannot_be_replayed_as_a_complete_loop(tmp_path: Path) -> None:
    from anthropic_readiness.runner import replay_run

    output = tmp_path / "run"
    plan = loop_plan()
    result = execute_run(plan, LoopTransport(), output)
    capture_path = next(ref.path for ref in result.evidence if ref.path.endswith("/response.json"))
    with pytest.raises(ValueError, match="complete_conversation"):
        replay_run(plan.target, plan.bundle, CASE_ID, output / capture_path, tmp_path / "replay")


@pytest.mark.parametrize(("path", "exit_code"), [("/tool-loop", 0), ("/tool-loop-ignored", 1)])
def test_cli_real_http_loop_writes_independent_report(
    tmp_path: Path, server: SyntheticServer, path: str, exit_code: int
) -> None:
    import subprocess
    import sys

    import yaml

    plan = loop_plan()
    target = replace(plan.target, messages_url=server.url + path)
    config = tmp_path / "target.yaml"
    config.write_text(yaml.safe_dump(target.to_json()))
    output = tmp_path / "cli"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "anthropic_readiness",
            "run",
            "--target",
            str(config),
            "--profile",
            PROFILE,
            "--allow-live",
            "--out",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == exit_code, completed.stderr
    assert len(server.requests) == 2
    assert "Planned requests: 2" in completed.stderr
    assert json.loads(completed.stdout)["actual_requests"] == 2
    result = json.loads((output / "result.json").read_text())
    assert result["cases"][0]["status"] == ("PASS" if exit_code == 0 else "FAIL")
    assert (output / "report.html").is_file()
    assert (output / "report.md").is_file()


def test_deadline_between_exchanges_preserves_incomplete_case(tmp_path: Path) -> None:
    now = [0.0]

    class DeadlineTransport(LoopTransport):
        def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
            result = super().send(request, limits, deadline)
            now[0] = 1000
            return result

    peer = DeadlineTransport()
    result = execute_run(loop_plan(), peer, tmp_path / "run", clock=lambda: now[0])
    assert len(peer.requests) == result.plan["actual_requests"] == 1
    assert result.cases[0]["status"] == "INDETERMINATE"


def test_continuation_does_not_duplicate_or_publish_credentials(tmp_path: Path) -> None:
    plan = loop_plan()
    target = replace(plan.target, auth_mode="api_key", credential_env="SYNTHETIC_LOOP_KEY")
    peer = LoopTransport()
    result = execute_run(
        replace(plan, target=target),
        peer,
        tmp_path / "run",
        environment={"SYNTHETIC_LOOP_KEY": "synthetic-loop-secret"},
    )
    assert result_exit_code(result) == 0
    assert len(peer.requests) == 2
    assert all(
        len([key for key, _ in request.headers if key == "x-api-key"]) == 1
        for request in peer.requests
    )
    assert "synthetic-loop-secret" not in json.dumps(result.to_json())


def test_checkpoint_cannot_publish_a_truncated_successful_loop(tmp_path: Path) -> None:
    from anthropic_readiness.operations.checkpoints import validate_declared_checkpoint

    output = tmp_path / "run"
    execute_run(
        loop_plan(),
        LoopTransport(),
        output,
        observer=DiskExecutionObserver(output / "operations", output),
    )
    checkpoint = object_value(
        json.loads((output / "operations/checkpoints" / (CASE_ID + ".json")).read_text())
    )
    record = object_value(checkpoint["case_record"])
    record["attempts"] = [objects(record["attempts"])[0]]
    checkpoint["case_record"] = record
    context = object_value(json.loads((output / "operations/execution.json").read_text()))
    with pytest.raises(ValueError, match="tool_loop_incomplete"):
        validate_declared_checkpoint(checkpoint, context)


@pytest.mark.parametrize("fault", ["ignored", "missing_metadata"])
def test_repair_comparison_retains_both_exchange_outcomes(tmp_path: Path, fault: str) -> None:
    from anthropic_readiness.application import prepare_assessment
    from anthropic_readiness.diagnostics.context import ContextObserver
    from anthropic_readiness.diagnostics.service import DiagnosticService

    roots = [tmp_path / "before", tmp_path / "after"]
    for root, failure in zip(roots, [fault, ""], strict=True):
        plan, context = prepare_assessment(loop_plan().target.to_json(), [PROFILE])
        observer = ContextObserver(
            root, context.document, DiskExecutionObserver(root / "operations", root)
        )
        try:
            execute_run(plan, LoopTransport(failure), root, observer=observer)
        finally:
            observer.finalize()
    service = DiagnosticService(tmp_path / "workspace")
    before = service.source_facts(roots[0])
    assert object_value(before["eligibility"])["compare"] is True, before["eligibility"]
    checks = objects(before["checks"])
    identifier = "LOOP-STEP" if fault == "ignored" else "MSG-CORE"
    assert next(row for row in checks if row["assertion_id"] == identifier)["status"] == "FAIL"
    comparison = service.compare_sources(*roots).document
    assert comparison["all_previous_failures_passed"] is True
    assert (
        next(row for row in objects(comparison["pairs"]) if row["assertion_id"] == identifier)[
            "transition"
        ]
        == "recovered"
    )
    archive = tmp_path / "handoff.zip"
    service.export(roots[0], archive, include_evidence=True)
    assert archive.is_file()


def test_loop_proof_requires_both_request_and_response(tmp_path: Path) -> None:
    from anthropic_readiness.models import JsonValue
    from anthropic_readiness.report_sources import attempt_evidence_errors

    output = tmp_path / "run"
    result = execute_run(loop_plan(), LoopTransport(), output)
    attempt = objects(result.cases[0]["attempts"])[1]
    checks = objects(attempt["assertions"])
    proof = next(row for row in checks if row["id"] == "LOOP-STEP")
    proof["evidence_refs"] = (
        [
            ref
            for ref in proof["evidence_refs"]
            if isinstance(ref, dict) and str(ref["path"]).endswith("/body.bin")
        ]
        if isinstance(proof["evidence_refs"], list)
        else []
    )
    assertions: list[JsonValue] = []
    assertions.extend(checks)
    attempt["assertions"] = assertions
    errors = attempt_evidence_errors(
        output, CASE_ID, attempt, {(ref.path, ref.sha256) for ref in result.evidence}
    )
    assert "tool_loop_evidence_incomplete" in errors
