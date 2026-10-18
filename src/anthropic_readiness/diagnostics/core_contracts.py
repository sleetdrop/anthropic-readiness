"""Core metadata validation without presentation schema dependencies."""

import json
from functools import lru_cache
from importlib.resources import files

from jsonschema import Draft202012Validator

from anthropic_readiness.json_validation import checked_validator
from anthropic_readiness.models import JsonObject, object_value, strict_json

CORE_SCHEMAS = frozenset(
    {
        "implementation-identity",
        "retest-recipe",
        "assessment-context",
        "diagnostic-identity-manifest",
        "assessment-context-verification",
    }
)


@lru_cache(maxsize=len(CORE_SCHEMAS))
def _validator(name: str) -> Draft202012Validator:
    if name not in CORE_SCHEMAS:
        raise ValueError("unknown_core_diagnostic_schema")
    schema = object_value(
        strict_json(
            files("anthropic_readiness")
            .joinpath(f"resources/schemas/{name}.schema.json")
            .read_text()
        )
    )
    return checked_validator(schema)


def validate_core(document: JsonObject, name: str) -> None:
    json.dumps(document, allow_nan=False)
    errors = sorted(_validator(name).iter_errors(document), key=lambda error: str(error.path))
    if errors:
        raise ValueError("schema:" + "; ".join(f"{list(e.path)}:{e.message}" for e in errors))
