"""Packaged operational contract validation; never used by pure value modules."""

import json
from functools import lru_cache

from jsonschema import Draft202012Validator

from anthropic_readiness.json_validation import checked_validator
from anthropic_readiness.models import JsonObject
from anthropic_readiness.schema import load_schema

SCHEMAS = frozenset(
    {
        "plan",
        "job",
        "execution",
        "checkpoint",
        "progress-event",
        "report-view",
        "export-manifest",
        "web-api",
        "web-console-acceptance",
        "web-console-handoff",
    }
)


@lru_cache(maxsize=len(SCHEMAS))
def _validator(schema_name: str) -> Draft202012Validator:
    if schema_name not in SCHEMAS:
        raise ValueError("unknown_operational_schema")
    # Packaged contracts are immutable for the lifetime of a process. Only schema
    # compilation is cached; every incoming document is still validated in full.
    return checked_validator(load_schema(schema_name))


def validate_operational(document: JsonObject, schema_name: str) -> None:
    # JSON Schema numbers alone do not reject Python infinity/NaN.
    json.dumps(document, allow_nan=False)
    errors = sorted(
        _validator(schema_name).iter_errors(document), key=lambda error: str(error.path)
    )
    if errors:
        raise ValueError(
            "schema:" + "; ".join(f"{list(error.path)}:{error.message}" for error in errors)
        )
