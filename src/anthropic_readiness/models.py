"""Pure, versioned domain records shared by adapters and validators."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal, TypeAlias

JsonValue: TypeAlias = "bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None"
JsonObject: TypeAlias = dict[str, JsonValue]
Category: TypeAlias = Literal["protocol", "behavior", "client", "environment"]
CaptureEnd: TypeAlias = Literal[
    "eof", "timeout", "read_error", "capture_limit", "cancelled", "connection_error"
]
ProtocolEnd: TypeAlias = Literal["message_stop", "error_event", "none"]


class Status(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    BLOCKED = "BLOCKED"
    INDETERMINATE = "INDETERMINATE"


def aggregate_required(statuses: Sequence[Status]) -> Status:
    if not statuses:
        return Status.INDETERMINATE
    order = (Status.FAIL, Status.BLOCKED, Status.INDETERMINATE, Status.SKIP, Status.PASS)
    return next(s for s in order if s in statuses)


def readiness(status: Status) -> str:
    return (
        "passed"
        if status == Status.PASS
        else "not_ready"
        if status == Status.FAIL
        else "incomplete"
    )


def as_json(value: object) -> JsonValue:
    """Narrow untrusted values recursively; never use casts to certify input."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, list):
        return [as_json(v) for v in value]
    if isinstance(value, dict) and all(isinstance(k, str) for k in value):
        return {str(k): as_json(v) for k, v in value.items()}
    raise ValueError("not_json")


def object_value(value: object) -> JsonObject:
    parsed = as_json(value)
    if not isinstance(parsed, dict):
        raise ValueError("expected_object")
    return parsed


class JsonDepthError(ValueError):
    """The parser cannot certify input at this nesting depth."""


def strict_json(text: str) -> JsonValue:
    def reject_constant(value: str) -> None:
        raise ValueError(f"invalid_json_constant:{value}")

    def pairs(items: list[tuple[str, object]]) -> JsonObject:
        result: JsonObject = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate_json_key:{key}")
            result[key] = as_json(value)
        return result

    try:
        return as_json(json.loads(text, parse_constant=reject_constant, object_pairs_hook=pairs))
    except RecursionError as exc:
        raise JsonDepthError("json_depth_limit") from exc


@dataclass(frozen=True)
class EvidenceRef:
    path: str
    sha256: str
    event: int | None = None
    pointer: str | None = None

    def to_json(self) -> JsonObject:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "event": self.event,
            "pointer": self.pointer,
        }


@dataclass(frozen=True)
class AssertionResult:
    id: str
    category: Category
    status: Status
    reason_code: str
    expected: str = ""
    actual: str = ""
    required: bool = True
    version: int = 1
    evidence_refs: tuple[EvidenceRef, ...] = ()
    event: int | None = None
    pointer: str | None = None

    def to_json(self) -> JsonObject:
        return {
            "id": self.id,
            "version": self.version,
            "category": self.category,
            "required": self.required,
            "status": self.status.value,
            "reason_code": self.reason_code,
            "expected": self.expected,
            "actual": self.actual,
            "evidence_refs": [r.to_json() for r in self.evidence_refs],
        }


@dataclass(frozen=True)
class ValidationResult:
    assertions: tuple[AssertionResult, ...]
    observations: JsonObject = field(default_factory=dict)

    @property
    def status(self) -> Status:
        return aggregate_required([a.status for a in self.assertions if a.required])


@dataclass(frozen=True)
class ContractSpec:
    id: str
    revision: str
    api_version: str
    beta_headers: tuple[str, ...] = ()
    validator_version: str = "1.0.0"


def _weather_input() -> JsonObject:
    return {"location": "Hanoi"}


@dataclass(frozen=True)
class CaseContract:
    case_id: str
    model: str = "example-model"
    model_policy: str = "request_or_alias"
    aliases: tuple[str, ...] = ()
    behavior: str = "greeting"
    tool_name: str = "get_weather"
    input_schema: JsonObject = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
            "additionalProperties": False,
        }
    )
    expected_input: JsonObject | None = field(default_factory=_weather_input)
    spec: ContractSpec | None = None


@dataclass(frozen=True)
class RequestSpec:
    url: str
    headers: tuple[tuple[str, str], ...]
    body: JsonObject
    streaming: bool


@dataclass(frozen=True)
class ReadRecord:
    length: int
    received_ms: float


@dataclass(frozen=True)
class SSEFrame:
    sequence: int
    event: str
    data: str
    received_ms: float
    id: str = ""
    retry: int | None = None


@dataclass(frozen=True)
class DecodeTail:
    pending_data: bool = False
    encoding_errors: int = 0
    limit_kind: str | None = None


@dataclass(frozen=True)
class Capture:
    request: RequestSpec
    status_code: int | None = None
    headers: tuple[tuple[str, str], ...] = ()
    body: bytes = b""
    reads: tuple[ReadRecord, ...] = ()
    frames: tuple[SSEFrame, ...] = ()
    protocol_end: ProtocolEnd = "none"
    capture_end: CaptureEnd = "eof"
    tail: DecodeTail = field(default_factory=DecodeTail)
    observed_bytes: int = 0
    duration_ms: float = 0
    headers_ms: float | None = None
    error: str | None = None


@dataclass(frozen=True)
class RunResult:
    run_id: str
    assessment_id: str
    mode: Literal["live", "replay"]
    started_at: str
    finished_at: str
    tool: JsonObject
    execution_environment: JsonObject
    contract: JsonObject
    target: JsonObject
    plan: JsonObject
    profiles: tuple[JsonObject, ...]
    cases: tuple[JsonObject, ...]
    evidence: tuple[EvidenceRef, ...]
    report_context: JsonObject
    limitations: tuple[str, ...]
    source_run_id: str | None = None
    schema_version: str = "1.0"

    def to_json(self) -> JsonObject:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "assessment_id": self.assessment_id,
            "source_run_id": self.source_run_id,
            "mode": self.mode,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "tool": self.tool,
            "execution_environment": self.execution_environment,
            "contract": self.contract,
            "target": self.target,
            "plan": self.plan,
            "profiles": list(self.profiles),
            "cases": list(self.cases),
            "evidence": [r.to_json() for r in self.evidence],
            "report_context": self.report_context,
            "limitations": list(self.limitations),
        }
