"""Values passed from verified I/O loading to deterministic report projection."""

import json
from dataclasses import dataclass

from anthropic_readiness.json_validation import checked_validator
from anthropic_readiness.models import JsonObject, RunResult
from anthropic_readiness.schema import load_schema

# Resolve the immutable packaged boundary once, before any pure projection runs.
_VIEW_VALIDATOR = checked_validator(load_schema("report-view"))


@dataclass(frozen=True)
class ReportSource:
    result: RunResult | None
    result_sha256: str | None
    case_records: tuple[JsonObject, ...]
    execution: JsonObject | None
    evidence_verification: JsonObject
    diagnostics: tuple[JsonObject, ...]
    plan: JsonObject


@dataclass(frozen=True)
class ReportView:
    document: JsonObject

    def __post_init__(self) -> None:
        json.dumps(self.document, allow_nan=False)
        errors = sorted(_VIEW_VALIDATOR.iter_errors(self.document), key=lambda item: str(item.path))
        if errors:
            raise ValueError("schema:" + "; ".join(error.message for error in errors))
