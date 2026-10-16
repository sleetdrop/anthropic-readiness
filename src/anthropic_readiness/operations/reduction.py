"""Pure execution-observation reduction; never recalculates compatibility verdicts."""

from __future__ import annotations

from copy import deepcopy
from typing import cast

from anthropic_readiness.models import JsonObject, JsonValue, object_value
from anthropic_readiness.operations.models import JobState, ProgressEvent, transition_allowed

TERMINAL = frozenset({"completed", "cancelled", "interrupted", "error"})


def objects(value: JsonValue) -> list[JsonObject]:
    if not isinstance(value, list):
        raise ValueError("expected_operational_array")
    return [object_value(item) for item in value]


def reduce_snapshot(snapshot: JsonObject, entry: ProgressEvent) -> JsonObject:
    result = deepcopy(snapshot)
    if result["run_id"] != entry.run_id:
        raise ValueError("event_run_identity")
    if entry.sequence != int(str(result["sequence"])) + 1:
        raise ValueError("journal_sequence_gap")
    event = entry.event
    if event.elapsed_ms < float(str(result["elapsed_ms"])):
        raise ValueError("event_elapsed_backwards")
    if result["state"] in TERMINAL:
        raise ValueError("terminal_execution")
    payload = event.payload
    cases = objects(result["case_states"])
    spans = objects(result["spans"])
    case_id = payload.get("case_id")
    case = next((item for item in cases if item["case_id"] == case_id), None)
    if case_id is not None and case is None:
        raise ValueError("event_unknown_case")
    if event.kind == "job_transition":
        before, after = payload["from"], payload["to"]
        initial = before is None and result["sequence"] == 0 and after == result["state"]
        if not initial and (
            before != result["state"]
            or not transition_allowed(cast(JobState, before), cast(JobState, after))
        ):
            raise ValueError("illegal_job_transition")
        result["state"] = after
        if after in TERMINAL:
            result["finished_at"] = event.occurred_at
            result["terminal_reason"] = payload.get("reason_code")
    elif event.kind == "case_started":
        if case is None or case["state"] != "pending":
            raise ValueError("case_already_started")
        if any(item["state"] == "running" for item in cases):
            raise ValueError("case_concurrency_limit")
        planned = objects(object_value(result["plan"])["cases"])
        definition = next(item for item in planned if item["id"] == case_id)
        if payload["case_version"] != definition["version"]:
            raise ValueError("case_version_mismatch")
        case["state"] = "running"
        spans.append(
            {
                "case_id": case_id,
                "attempt_id": None,
                "phase": "case",
                "started_at": event.occurred_at,
                "ended_at": None,
                "start_ms": event.elapsed_ms,
                "end_ms": None,
            }
        )
    elif event.kind == "request_started":
        if case is None or case["state"] != "running":
            raise ValueError("request_case_not_running")
        expected = int(str(result["actual_requests"])) + 1
        limit = object_value(object_value(result["plan"])["limits"])["max_requests"]
        if payload["request_index"] != expected or expected > int(str(limit)):
            raise ValueError("request_index_or_limit")
        result["actual_requests"] = expected
    elif event.kind == "transport_phase":
        if case is None or case["state"] != "running":
            raise ValueError("phase_case_not_running")
        active = next(
            (
                span
                for span in reversed(spans)
                if span["case_id"] == case_id and span["phase"] != "case" and span["end_ms"] is None
            ),
            None,
        )
        if (
            active is None
            or active["phase"] != payload["phase"]
            or active["attempt_id"] != payload["attempt_id"]
        ):
            if active is not None:
                active.update({"end_ms": event.elapsed_ms, "ended_at": event.occurred_at})
            spans.append(
                {
                    "case_id": case_id,
                    "attempt_id": payload["attempt_id"],
                    "phase": payload["phase"],
                    "started_at": event.occurred_at,
                    "ended_at": None,
                    "start_ms": event.elapsed_ms,
                    "end_ms": None,
                }
            )
    elif event.kind == "case_committed":
        if case is None or case["state"] not in {"pending", "running"}:
            raise ValueError("case_already_committed")
        case.update(
            {
                "state": payload["status"],
                "checkpoint_path": payload["checkpoint_path"],
                "checkpoint_sha256": payload["sha256"],
            }
        )
        for span in spans:
            if span["case_id"] == case_id and span["end_ms"] is None:
                span.update({"end_ms": event.elapsed_ms, "ended_at": event.occurred_at})
    elif event.kind == "result_committed":
        if any(item["state"] in {"pending", "running"} for item in cases):
            raise ValueError("result_missing_case_completion")
        result["result_sha256"] = payload["sha256"]
    result.update(
        {
            "sequence": entry.sequence,
            "updated_at": event.occurred_at,
            "elapsed_ms": event.elapsed_ms,
            "case_states": list(cases),
            "spans": list(spans),
        }
    )
    return result
