"""Versioned operational values, separate from compatibility judgments and I/O."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Literal

from anthropic_readiness.models import JsonObject

JobState = Literal[
    "queued", "running", "cancelling", "completed", "cancelled", "interrupted", "error"
]
EventKind = Literal[
    "job_transition",
    "case_started",
    "request_started",
    "transport_phase",
    "case_committed",
    "result_committed",
]


def transition_allowed(before: JobState, after: JobState) -> bool:
    transitions: dict[JobState, frozenset[JobState]] = {
        "queued": frozenset({"running", "cancelled", "interrupted", "error"}),
        "running": frozenset({"cancelling", "completed", "interrupted", "error"}),
        "cancelling": frozenset({"cancelled", "interrupted", "error"}),
        "completed": frozenset(),
        "cancelled": frozenset(),
        "interrupted": frozenset(),
        "error": frozenset(),
    }
    if before not in transitions or after not in transitions:
        raise ValueError("unknown_job_state")
    return after in transitions[before]


@dataclass(frozen=True)
class WorkerEvent:
    kind: EventKind
    occurred_at: str
    elapsed_ms: float
    payload: JsonObject

    def to_json(self) -> JsonObject:
        return {
            "kind": self.kind,
            "occurred_at": self.occurred_at,
            "elapsed_ms": self.elapsed_ms,
            "payload": deepcopy(self.payload),
        }


@dataclass(frozen=True)
class ProgressEvent:
    schema_version: str
    run_id: str
    sequence: int
    event: WorkerEvent

    def to_json(self) -> JsonObject:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "sequence": self.sequence,
            **self.event.to_json(),
        }


@dataclass(frozen=True)
class JobRecord:
    id: str
    plan_id: str
    state: JobState
    created_at: str
    updated_at: str
    last_sequence: int
    result_path: str | None

    def to_json(self) -> JsonObject:
        return {
            "schema_version": "1.0",
            "id": self.id,
            "plan_id": self.plan_id,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_sequence": self.last_sequence,
            "result_path": self.result_path,
        }


@dataclass(frozen=True)
class FrozenPlan:
    id: str
    session_id: str
    created_at: str
    expires_at: str
    config_sha256: str
    target: JsonObject
    profiles: tuple[str, ...]
    plan: JsonObject

    def to_json(self) -> JsonObject:
        return {
            "schema_version": "1.0",
            "id": self.id,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "config_sha256": self.config_sha256,
            "target": deepcopy(self.target),
            "profiles": list(self.profiles),
            "plan": deepcopy(self.plan),
        }


@dataclass(frozen=True)
class Admission:
    job: JobRecord
    created: bool
