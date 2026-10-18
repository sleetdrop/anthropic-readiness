"""Closed, packaged diagnostic schemas; archives never select schema resources."""

import json
from functools import lru_cache
from importlib.resources import files

from jsonschema import Draft202012Validator

from anthropic_readiness.json_validation import checked_validator
from anthropic_readiness.models import JsonObject, object_value, strict_json

SCHEMAS = frozenset(
    {
        "implementation-identity",
        "retest-recipe",
        "assessment-context",
        "diagnostic-package",
        "imported-baseline",
        "comparison",
        "workbench-view",
        "document-view",
        "export-manifest-v2",
    }
)


@lru_cache(maxsize=len(SCHEMAS))
def _validator(name: str) -> Draft202012Validator:
    if name not in SCHEMAS:
        raise ValueError("unknown_diagnostic_schema")
    schema = object_value(
        strict_json(
            files("anthropic_readiness")
            .joinpath(f"resources/schemas/{name}.schema.json")
            .read_text()
        )
    )
    return checked_validator(schema)


def validate_diagnostic(document: JsonObject, name: str) -> None:
    """Check structure here; services own cross-file/evidence relationship checks."""
    validator = _validator(name)
    json.dumps(document, allow_nan=False)
    errors = sorted(validator.iter_errors(document), key=lambda error: str(error.path))
    if errors:
        raise ValueError("schema:" + "; ".join(f"{list(e.path)}:{e.message}" for e in errors))
