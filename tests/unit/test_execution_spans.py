"""Recorded spans preserve gaps, ordered cursors and actual request accounting."""

from pathlib import Path

import pytest

from anthropic_readiness.operations.checkpoints import CheckpointStore
from anthropic_readiness.operations.journal import RunJournal
from tests.operation_fixtures import ATTEMPT_ID, RUN_ID, case_record, context, event


def test_spans_preserve_real_gaps(tmp_path: Path) -> None:
    operations = tmp_path / "operations"
    journal = RunJournal(operations, RUN_ID)
    journal.begin(context())
    journal.append(event("case_started", 10, {"case_id": "ANT-MESSAGE-001", "case_version": 1}))
    receipt = CheckpointStore(operations, RUN_ID, evidence_root=tmp_path).commit(case_record(), ())
    journal.append(
        event(
            "case_committed", 100, {key: value for key, value in receipt.items() if key != "run_id"}
        )
    )
    journal.append(event("case_started", 1000, {"case_id": "ANT-TEXT-SSE-001", "case_version": 1}))
    spans = journal.snapshot()["spans"]
    assert isinstance(spans, list)
    assert [(span["start_ms"], span["end_ms"]) for span in spans if isinstance(span, dict)] == [
        (10, 100),
        (1000, None),
    ]
    assert [item.sequence for item in journal.after(1)] == [2, 3]


def test_request_events_count_once_and_reject_backwards_time(tmp_path: Path) -> None:
    journal = RunJournal(tmp_path / "operations", RUN_ID)
    journal.begin(context())
    journal.append(event("case_started", 0, {"case_id": "ANT-MESSAGE-001", "case_version": 1}))
    request = event(
        "request_started",
        5,
        {"case_id": "ANT-MESSAGE-001", "attempt_id": ATTEMPT_ID, "request_index": 1},
    )
    journal.append(request)
    assert journal.snapshot()["actual_requests"] == 1
    with pytest.raises(ValueError, match="request_index"):
        journal.append(request)
    with pytest.raises(ValueError, match="elapsed"):
        journal.append(
            event(
                "transport_phase",
                1,
                {"case_id": "ANT-MESSAGE-001", "attempt_id": ATTEMPT_ID, "phase": "receiving"},
            )
        )
    assert journal.snapshot()["actual_requests"] == 1


def test_event_for_unknown_case_is_rejected_without_a_sequence_gap(tmp_path: Path) -> None:
    journal = RunJournal(tmp_path / "operations", RUN_ID)
    journal.begin(context())
    with pytest.raises(ValueError, match="case"):
        journal.append(event("case_started", 0, {"case_id": "other", "case_version": 1}))
    assert journal.after(0) == ()
