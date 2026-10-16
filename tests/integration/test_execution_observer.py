"""Observations add durable progress without changing compatibility judgments."""

import hashlib
import time
from collections.abc import AsyncIterator
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from anthropic_readiness.application import build_plan, run_assessment
from anthropic_readiness.config import Limits, load_target
from anthropic_readiness.credentials import MemoryCredentials
from anthropic_readiness.models import EvidenceRef, JsonObject, RequestSpec
from anthropic_readiness.operations.checkpoints import CheckpointStore
from anthropic_readiness.operations.journal import RunJournal
from anthropic_readiness.operations.models import WorkerEvent
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.operations.ports import CancelToken
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.runner import execute_run
from anthropic_readiness.transport import HttpTransport
from tests.acceptance.test_runner import FixtureTransport
from tests.operation_fixtures import RUN_ID, case_record, context

ROOT = Path(__file__).resolve().parents[2]


def semantics(cases: tuple[JsonObject, ...]) -> list[JsonObject]:
    return [
        {
            "id": case["id"],
            "version": case["version"],
            "required": case["required"],
            "status": case["status"],
            "dimensions": case["dimensions"],
            "assertions": [
                {key: value for key, value in assertion.items() if key != "evidence_refs"}
                for attempt in objects(case["attempts"])
                for assertion in objects(attempt["assertions"])
            ],
        }
        for case in cases
    ]


def test_cli_and_observed_run_keep_identical_assertion_semantics(tmp_path: Path) -> None:
    plan = build_plan(load_target(ROOT / "examples/target.yaml").to_json(), ["anthropic-basic"])
    plain = execute_run(plan, FixtureTransport(fail_second=True), tmp_path / "plain")
    output = tmp_path / "observed"
    observed = execute_run(
        plan,
        FixtureTransport(fail_second=True),
        output,
        observer=DiskExecutionObserver(output / "operations", output),
    )
    assert semantics(plain.cases) == semantics(observed.cases)
    assert plain.plan == observed.plan
    assert [ref.sha256 for ref in plain.evidence if ref.path.endswith("body.bin")] == [
        ref.sha256 for ref in observed.evidence if ref.path.endswith("body.bin")
    ]
    journal = RunJournal(output / "operations", observed.run_id)
    assert journal.snapshot()["state"] == "completed"
    assert (
        len(
            CheckpointStore(
                output / "operations", observed.run_id, evidence_root=output
            ).load_verified()
        )
        == 3
    )


def test_run_id_and_output_ownership_are_consistent(tmp_path: Path) -> None:
    target = replace(
        load_target(ROOT / "examples/target.yaml"),
        auth_mode="api_key",
        credential_env="SYNTHETIC_KEY",
    )
    plan = build_plan(target.to_json(), ["anthropic-basic"])
    job = tmp_path / "job"
    job.mkdir()
    output = job / "assessment"
    operations = job / "operations"
    result = run_assessment(
        plan,
        output,
        credentials=MemoryCredentials(None),
        observer=DiskExecutionObserver(operations, output),
        run_id=RUN_ID,
    )
    assert result.run_id == RUN_ID
    journal = RunJournal(operations, RUN_ID, evidence_root=output)
    snapshot = journal.snapshot()
    assert snapshot["run_id"] == RUN_ID
    assert (
        snapshot["result_sha256"]
        == hashlib.sha256((output / "result.json").read_bytes()).hexdigest()
    )
    assert all(item.run_id == RUN_ID for item in journal.after(0))
    checkpoints = CheckpointStore(operations, RUN_ID, evidence_root=output).load_verified()
    assert len(checkpoints) == 3
    assert all(item["run_id"] == RUN_ID for item in checkpoints)
    with pytest.raises(FileExistsError):
        run_assessment(plan, output, credentials=MemoryCredentials(None), run_id=RUN_ID)


def test_observer_failure_stops_next_request(tmp_path: Path) -> None:
    class FailedObserver(DiskExecutionObserver):
        def commit_case(self, case: JsonObject, refs: tuple[EvidenceRef, ...]) -> JsonObject:
            raise OSError("synthetic_mandatory_write_failure")

    plan = build_plan(load_target(ROOT / "examples/target.yaml").to_json(), ["anthropic-basic"])
    output = tmp_path / "assessment"
    transport = FixtureTransport()
    with pytest.raises(OSError, match="synthetic_mandatory_write_failure"):
        execute_run(plan, transport, output, observer=FailedObserver(output / "operations", output))
    assert transport.calls == 1
    assert not (output / "result.json").exists()
    assert len(list(output.glob("evidence/*/*/body.bin"))) == 1


def test_no_auth_mode_does_not_resolve_or_send_a_credential(tmp_path: Path) -> None:
    class UnusedCredentials:
        def resolve(self) -> str | None:
            raise AssertionError("no_auth_must_not_resolve")

    plan = build_plan(load_target(ROOT / "examples/target.yaml").to_json(), ["anthropic-basic"])
    transport = FixtureTransport()
    result = execute_run(plan, transport, tmp_path / "no-auth", credentials=UnusedCredentials())
    assert result.plan["actual_requests"] == 3
    assert [case["status"] for case in result.cases] == ["PASS"] * 3


def test_event_write_failure_cannot_become_a_response_error(tmp_path: Path) -> None:
    class FailedObserver(DiskExecutionObserver):
        def emit(self, event: WorkerEvent) -> None:
            if event.kind == "transport_phase" and event.payload["phase"] == "awaiting_headers":
                raise ValueError("synthetic_observer_failure")
            super().emit(event)

    plan = build_plan(load_target(ROOT / "examples/target.yaml").to_json(), ["anthropic-basic"])
    output = tmp_path / "assessment"
    with pytest.raises(RuntimeError, match="observation_failed"):
        run_assessment(
            plan,
            output,
            credentials=MemoryCredentials(None),
            observer=FailedObserver(output / "operations", output),
        )
    assert not (output / "result.json").exists()


def test_checkpoint_cannot_certify_an_unexecuted_case(tmp_path: Path) -> None:
    operations = tmp_path / "operations"
    RunJournal(operations, RUN_ID).begin(context())
    record = case_record()
    record["status"] = "PASS"
    preconditions = objects(record["preconditions"])
    preconditions[0]["status"] = "PASS"
    record["preconditions"] = list(preconditions)
    with pytest.raises(ValueError, match="unexecuted_case_pass"):
        CheckpointStore(operations, RUN_ID, evidence_root=tmp_path).commit(record, ())


def test_checkpoint_rejects_missing_required_success_assertion(tmp_path: Path) -> None:
    plan = build_plan(load_target(ROOT / "examples/target.yaml").to_json(), ["anthropic-basic"])
    output = tmp_path / "source"
    result = execute_run(plan, FixtureTransport(), output)
    operations = tmp_path / "operations"
    RunJournal(operations, RUN_ID, evidence_root=output).begin(context())
    record = result.to_json()["cases"]
    case = objects(record)[0]
    attempt = objects(case["attempts"])[0]
    attempt["assertions"] = [
        item for item in objects(attempt["assertions"]) if item["id"] != "TASK-COMPLETE"
    ]
    case["attempts"] = [attempt]
    with pytest.raises(ValueError, match="missing_assertion"):
        CheckpointStore(operations, RUN_ID, evidence_root=output).commit(case, result.evidence)


def test_case_completion_timestamp_follows_durable_commit(tmp_path: Path) -> None:
    now = [0.0]

    class DelayedObserver(DiskExecutionObserver):
        def commit_case(self, case: JsonObject, refs: tuple[EvidenceRef, ...]) -> JsonObject:
            receipt = super().commit_case(case, refs)
            now[0] += 1
            return receipt

    output = tmp_path / "assessment"
    plan = build_plan(load_target(ROOT / "examples/target.yaml").to_json(), ["anthropic-basic"])
    result = execute_run(
        plan,
        FixtureTransport(),
        output,
        clock=lambda: now[0],
        observer=DelayedObserver(output / "operations", output),
    )
    spans = objects(RunJournal(output / "operations", result.run_id).snapshot()["spans"])
    assert [span["end_ms"] for span in spans if span["phase"] == "case"] == [1000, 2000, 3000]


def test_transport_phases_are_observed_safe_and_content_activity_is_coalesced() -> None:
    events: list[WorkerEvent] = []

    class RecordingObserver:
        def begin(self, context: JsonObject) -> None:
            raise AssertionError("transport_must_not_own_run_initialization")

        def emit(self, event: WorkerEvent) -> None:
            events.append(event)

        def commit_case(self, case: JsonObject, refs: tuple[EvidenceRef, ...]) -> JsonObject:
            raise AssertionError("transport_must_not_own_checkpoints")

    class Chunks(httpx.AsyncByteStream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            for _ in range(100):
                yield b"synthetic-private-model-text"

    started = time.monotonic()
    token = CancelToken()
    observer = RecordingObserver()
    transport = HttpTransport(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=Chunks()))
    )
    transport.bind_execution(
        "ANT-MESSAGE-001",
        RUN_ID,
        observer=observer,
        control=token,
        elapsed_ms=lambda: (time.monotonic() - started) * 1000,
    )
    captured = transport.send(
        RequestSpec("http://synthetic.invalid", (), {}, False), Limits(), started + 5
    )
    assert captured.capture_end == "eof"
    assert len(captured.reads) == 100
    assert [item.payload["phase"] for item in events] == [
        "awaiting_headers",
        "headers_received",
        "receiving",
    ]
    assert all("synthetic-private-model-text" not in str(item.to_json()) for item in events)
    assert all(item.kind == "transport_phase" for item in events)
