"""Crash boundaries never turn partial writes into completed compatibility checks."""

import hashlib
from pathlib import Path

import pytest

from anthropic_readiness.evidence import atomic_write
from anthropic_readiness.models import EvidenceRef, JsonObject
from anthropic_readiness.operations import checkpoints as checkpoint_module
from anthropic_readiness.operations import journal as journal_module
from anthropic_readiness.operations.checkpoints import CheckpointStore
from anthropic_readiness.operations.journal import RunJournal
from tests.operation_fixtures import RUN_ID, case_record, context, event


def test_committed_checkpoint_round_trip_and_exclusive_publication(tmp_path: Path) -> None:
    operations = tmp_path / "operations"
    journal = RunJournal(operations, RUN_ID)
    journal.begin(context())
    store = CheckpointStore(operations, RUN_ID, evidence_root=tmp_path)
    receipt = store.commit(case_record(), ())
    assert receipt["run_id"] == RUN_ID
    assert store.load_verified()[0]["case_record"] == case_record()
    payload = {key: value for key, value in receipt.items() if key != "run_id"}
    journal.append(event("case_committed", 20, payload))
    assert journal.after(0)[0].event.kind == "case_committed"
    with pytest.raises(FileExistsError):
        store.commit(case_record(), ())


def test_case_is_visible_only_after_evidence_and_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    operations = tmp_path / "operations"
    journal = RunJournal(operations, RUN_ID)
    journal.begin(context())
    evidence = tmp_path / "evidence/body.bin"
    evidence.parent.mkdir()
    atomic_write(evidence, b"retained synthetic bytes")
    ref = EvidenceRef("evidence/body.bin", hashlib.sha256(evidence.read_bytes()).hexdigest())
    store = CheckpointStore(operations, RUN_ID, evidence_root=tmp_path)

    def fail_write(path: Path, data: bytes) -> None:
        raise OSError("synthetic_write_failure")

    monkeypatch.setattr(checkpoint_module, "atomic_write", fail_write)
    with pytest.raises(OSError, match="synthetic_write_failure"):
        store.commit(case_record(), (ref,))
    payload: JsonObject = {
        "case_id": "ANT-MESSAGE-001",
        "checkpoint_path": "checkpoints/ANT-MESSAGE-001.json",
        "sha256": "0" * 64,
        "status": "INDETERMINATE",
        "actual_requests": 0,
    }
    with pytest.raises(FileNotFoundError):
        journal.append(event("case_committed", 20, payload))
    assert not any(item.event.kind == "case_committed" for item in journal.after(0))
    assert evidence.read_bytes() == b"retained synthetic bytes"


def test_restart_retains_committed_prefix(tmp_path: Path) -> None:
    operations = tmp_path / "operations"
    journal = RunJournal(operations, RUN_ID)
    journal.begin(context())
    journal.append(event("case_started", 0, {"case_id": "ANT-MESSAGE-001", "case_version": 1}))
    store = CheckpointStore(operations, RUN_ID, evidence_root=tmp_path)
    receipt = store.commit(case_record(), ())
    journal.append(
        event(
            "case_committed", 20, {key: value for key, value in receipt.items() if key != "run_id"}
        )
    )
    log = operations / "events.jsonl"
    with log.open("ab") as stream:
        stream.write(b'{"sequence":3,"kind":')
    original = log.read_bytes()
    recovered = RunJournal(operations, RUN_ID)
    assert [item.sequence for item in recovered.after(0)] == [1, 2]
    snapshot = recovered.snapshot()
    assert snapshot["state"] == "interrupted"
    warnings = snapshot["warnings"]
    assert isinstance(warnings, list)
    assert "uncommitted_event_tail" in warnings
    assert log.read_bytes() == original
    assert store.load_verified()[0]["case_id"] == "ANT-MESSAGE-001"
    with pytest.raises(ValueError, match="torn_tail"):
        recovered.append(
            event("case_started", 30, {"case_id": "ANT-TEXT-SSE-001", "case_version": 1})
        )


def test_corrupt_interior_event_is_not_discarded(tmp_path: Path) -> None:
    operations = tmp_path / "operations"
    journal = RunJournal(operations, RUN_ID)
    journal.begin(context())
    journal.append(event("case_started", 0, {"case_id": "ANT-MESSAGE-001", "case_version": 1}))
    log = operations / "events.jsonl"
    log.write_bytes(b"not-json\n" + log.read_bytes())
    original = log.read_bytes()
    with pytest.raises(ValueError, match="journal"):
        RunJournal(operations, RUN_ID).snapshot()
    assert log.read_bytes() == original


def test_snapshot_write_failure_recovers_durable_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    operations = tmp_path / "operations"
    journal = RunJournal(operations, RUN_ID)
    journal.begin(context())

    def fail_snapshot(root: Path, document: JsonObject) -> None:
        raise OSError("synthetic_snapshot_failure")

    monkeypatch.setattr(journal_module, "replace_snapshot", fail_snapshot)
    with pytest.raises(OSError, match="synthetic_snapshot_failure"):
        journal.append(event("case_started", 10, {"case_id": "ANT-MESSAGE-001", "case_version": 1}))
    recovered = RunJournal(operations, RUN_ID)
    assert recovered.snapshot()["sequence"] == 1
    assert recovered.after(0)[0].event.kind == "case_started"


def test_missing_published_checkpoint_cannot_disappear_from_verified_load(tmp_path: Path) -> None:
    operations = tmp_path / "operations"
    journal = RunJournal(operations, RUN_ID)
    journal.begin(context())
    store = CheckpointStore(operations, RUN_ID, evidence_root=tmp_path)
    receipt = store.commit(case_record(), ())
    journal.append(
        event(
            "case_committed", 10, {key: value for key, value in receipt.items() if key != "run_id"}
        )
    )
    (operations / str(receipt["checkpoint_path"])).unlink()
    with pytest.raises(ValueError, match="missing_checkpoint"):
        store.load_verified()


def test_checkpoint_rejects_missing_or_changed_evidence(tmp_path: Path) -> None:
    operations = tmp_path / "operations"
    RunJournal(operations, RUN_ID).begin(context())
    store = CheckpointStore(operations, RUN_ID, evidence_root=tmp_path)
    with pytest.raises(ValueError, match="evidence"):
        store.commit(case_record(), (EvidenceRef("missing.bin", "0" * 64),))
    evidence = tmp_path / "body.bin"
    evidence.write_bytes(b"before")
    store.commit(case_record(), (EvidenceRef("body.bin", hashlib.sha256(b"before").hexdigest()),))
    evidence.write_bytes(b"after")
    with pytest.raises(ValueError, match="evidence"):
        store.load_verified()


def test_begin_cannot_reset_existing_sequence_or_change_identity(tmp_path: Path) -> None:
    journal = RunJournal(tmp_path / "operations", RUN_ID)
    journal.begin(context())
    journal.append(event("case_started", 0, {"case_id": "ANT-MESSAGE-001", "case_version": 1}))
    journal.begin(context())
    assert journal.snapshot()["sequence"] == 1
    changed = context()
    changed["run_id"] = "44444444-4444-4444-8444-444444444444"
    with pytest.raises(ValueError, match="identity"):
        journal.begin(changed)


def test_case_completion_cannot_reference_a_symlink(tmp_path: Path) -> None:
    operations = tmp_path / "operations"
    journal = RunJournal(operations, RUN_ID)
    journal.begin(context())
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    (operations / "checkpoints").mkdir(exist_ok=True)
    (operations / "checkpoints/ANT-MESSAGE-001.json").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        journal.append(
            event(
                "case_committed",
                5,
                {
                    "case_id": "ANT-MESSAGE-001",
                    "checkpoint_path": "checkpoints/ANT-MESSAGE-001.json",
                    "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                    "status": "INDETERMINATE",
                    "actual_requests": 0,
                },
            )
        )
