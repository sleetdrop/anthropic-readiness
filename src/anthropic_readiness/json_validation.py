"""Pure, offline JSON Schema validation without resource loading."""

from __future__ import annotations

import json
from functools import lru_cache

from jsonschema import Draft202012Validator

from anthropic_readiness.models import JsonValue, strict_json


def checked_validator(schema: JsonValue) -> Draft202012Validator:
    def check_refs(node: JsonValue) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if (
                    key in {"$ref", "$dynamicRef"}
                    and isinstance(child, str)
                    and not child.startswith("#")
                ):
                    raise ValueError("external_schema_reference")
                check_refs(child)
        elif isinstance(node, list):
            for child in node:
                check_refs(child)

    check_refs(schema)
    if not isinstance(schema, (dict, bool)):
        raise ValueError("invalid_schema")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@lru_cache(maxsize=64)
def _compiled_validator(serialized: str) -> Draft202012Validator:
    # Own the schema snapshot; callers cannot mutate a cached validator's rules.
    return checked_validator(strict_json(serialized))


def validate_document(value: object, schema: JsonValue) -> None:
    # Retain declaration order so equal-path diagnostics keep their original order.
    serialized = json.dumps(schema, separators=(",", ":"), allow_nan=False)
    # Cache schema compilation only. Every document still receives the full check.
    errors = sorted(_compiled_validator(serialized).iter_errors(value), key=lambda e: str(e.path))
    if errors:
        raise ValueError("schema:" + "; ".join(f"{list(e.path)}:{e.message}" for e in errors))
