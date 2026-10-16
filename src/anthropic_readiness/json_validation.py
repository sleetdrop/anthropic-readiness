"""Pure, offline JSON Schema validation without resource loading."""

from __future__ import annotations

from jsonschema import Draft202012Validator

from anthropic_readiness.models import JsonValue


def validate_document(value: object, schema: JsonValue) -> None:
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
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(e.path))
    if errors:
        raise ValueError("schema:" + "; ".join(f"{list(e.path)}:{e.message}" for e in errors))
