"""Persisted operational contracts cannot imply execution or leak extra fields."""

import itertools
from typing import cast

import pytest

from anthropic_readiness.models import JsonObject, JsonValue
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.operations.models import (
    FrozenPlan,
    JobRecord,
    JobState,
    ProgressEvent,
    WorkerEvent,
    transition_allowed,
)
from anthropic_readiness.operations.ports import CancelToken

RUN_ID = "11111111-1111-4111-8111-111111111111"
PLAN_ID = "22222222-2222-4222-8222-222222222222"
NOW = "2026-10-17T00:00:00+00:00"


def job_document() -> JsonObject:
    return {
        "schema_version": "1.0",
        "id": RUN_ID,
        "plan_id": PLAN_ID,
        "state": "queued",
        "created_at": NOW,
        "updated_at": NOW,
        "last_sequence": 0,
        "result_path": None,
    }


def event_document() -> JsonObject:
    return {
        "schema_version": "1.0",
        "run_id": RUN_ID,
        "sequence": 1,
        "kind": "case_started",
        "occurred_at": NOW,
        "elapsed_ms": 0,
        "payload": {"case_id": "ANT-MESSAGE-001", "case_version": 1},
    }


def test_job_record_serializes_the_versioned_identity() -> None:
    value = JobRecord(RUN_ID, PLAN_ID, "queued", NOW, NOW, 0, None)
    assert value.to_json() == job_document()


def test_event_serialization_is_flat_and_sequenced() -> None:
    value = ProgressEvent(
        "1.0",
        RUN_ID,
        1,
        WorkerEvent("case_started", NOW, 0, {"case_id": "ANT-MESSAGE-001", "case_version": 1}),
    )
    assert value.to_json() == event_document()


def test_frozen_plan_serialization_cannot_share_mutable_output() -> None:
    value = FrozenPlan(
        PLAN_ID,
        "a" * 64,
        NOW,
        "2026-10-17T00:15:00+00:00",
        "b" * 64,
        {"model": "synthetic"},
        ("anthropic-basic",),
        {"cases": []},
    )
    document = value.to_json()
    assert document["profiles"] == ["anthropic-basic"]
    assert document["session_id"] == "a" * 64
    target = document["target"]
    assert isinstance(target, dict)
    target["model"] = "edited"
    assert value.target == {"model": "synthetic"}


def test_valid_operational_records_are_accepted() -> None:
    validate_operational(job_document(), "job")
    validate_operational(event_document(), "progress-event")


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("credential", "synthetic-secret"),
        ("state", "done"),
        ("last_sequence", -1),
        ("last_sequence", True),
        ("result_path", "../../outside.json"),
    ],
)
def test_operational_job_rejects_unsafe_fields(key: str, value: JsonValue) -> None:
    document = job_document()
    document[key] = value
    with pytest.raises(ValueError, match="schema:"):
        validate_operational(document, "job")


@pytest.mark.parametrize(
    "change",
    [
        {"sequence": 0},
        {"sequence": True},
        {"elapsed_ms": -1},
        {"kind": "text_delta"},
        {"credential": "synthetic-secret"},
        {"payload": {"case_id": "ANT-MESSAGE-001", "case_version": 1, "raw_text": "private"}},
    ],
)
def test_progress_event_rejects_unbounded_or_unknown_payload(change: JsonObject) -> None:
    with pytest.raises(ValueError, match="schema:"):
        validate_operational({**event_document(), **change}, "progress-event")


STATES: tuple[JobState, ...] = (
    "queued",
    "running",
    "cancelling",
    "completed",
    "cancelled",
    "interrupted",
    "error",
)
ALLOWED = {
    ("queued", "running"),
    ("queued", "cancelled"),
    ("queued", "interrupted"),
    ("queued", "error"),
    ("running", "cancelling"),
    ("running", "completed"),
    ("running", "interrupted"),
    ("running", "error"),
    ("cancelling", "cancelled"),
    ("cancelling", "interrupted"),
    ("cancelling", "error"),
}


@pytest.mark.parametrize(("before", "after"), list(itertools.product(STATES, repeat=2)))
def test_job_lifecycle_matches_the_declared_transition_table(
    before: JobState,
    after: JobState,
) -> None:
    assert transition_allowed(before, after) is ((before, after) in ALLOWED)


def test_cancellation_is_sticky_and_retains_the_first_reason() -> None:
    token = CancelToken()
    assert token.requested is False
    token.cancel("user_cancelled")
    token.cancel("parent_lost")
    assert token.requested is True
    assert token.reason_code == "user_cancelled"


def test_unknown_schema_and_nonfinite_numbers_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown_operational_schema"):
        validate_operational({}, "../target")
    document = event_document()
    document["elapsed_ms"] = float("inf")
    with pytest.raises(ValueError, match="Out of range"):
        validate_operational(document, "progress-event")
    with pytest.raises(ValueError, match="unknown_job_state"):
        transition_allowed(cast(JobState, "unknown"), "running")
