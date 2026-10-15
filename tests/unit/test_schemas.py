"""Untrusted documents cannot bypass structural and relational checks."""

import pytest

from anthropic_readiness.models import JsonObject
from anthropic_readiness.schema import load_schema, validate_document


def test_boolean_count_is_rejected() -> None:
    schema: JsonObject = {
        "type": "object",
        "properties": {"count": {"type": "integer", "minimum": 0}},
    }
    with pytest.raises(ValueError, match="schema"):
        validate_document({"count": True}, schema)


def test_unknown_status_is_rejected() -> None:
    schema = load_schema("result")
    assertion_schema = schema["$defs"]
    assert isinstance(assertion_schema, dict)
    with pytest.raises(ValueError, match="schema"):
        validate_document({"status": "SUCCESS"}, assertion_schema["assertion"])


def test_external_schema_reference_is_rejected() -> None:
    with pytest.raises(ValueError, match="external"):
        validate_document({}, {"$ref": "https://example.invalid/evil.json"})
