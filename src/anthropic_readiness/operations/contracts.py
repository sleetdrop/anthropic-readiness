"""Packaged operational contract validation; never used by pure value modules."""

import json

from anthropic_readiness.models import JsonObject
from anthropic_readiness.schema import load_schema, validate_document

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


def validate_operational(document: JsonObject, schema_name: str) -> None:
    if schema_name not in SCHEMAS:
        raise ValueError("unknown_operational_schema")
    # JSON Schema numbers alone do not reject Python infinity/NaN.
    json.dumps(document, allow_nan=False)
    validate_document(document, load_schema(schema_name))
