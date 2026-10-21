"""Untrusted documents cannot bypass structural and relational checks."""

import pytest
from jsonschema import Draft202012Validator

from anthropic_readiness import json_validation
from anthropic_readiness.models import JsonObject, JsonValue
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


def test_reused_schema_avoids_recompilation_but_validates_each_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    compiled: list[JsonValue] = []
    real = json_validation.checked_validator

    def observed(schema: JsonValue) -> Draft202012Validator:
        compiled.append(schema)
        return real(schema)

    monkeypatch.setattr(json_validation, "checked_validator", observed)
    schema: JsonObject = {"title": "Repeated document validation regression", "type": "integer"}
    validate_document(7, schema)
    with pytest.raises(ValueError, match="schema"):
        validate_document("invalid", schema)
    validate_document(8, dict(schema))
    assert len(compiled) == 1


def test_changed_schema_cannot_reuse_an_old_validation_rule() -> None:
    schema: JsonObject = {"type": "object", "properties": {"value": {"type": "integer"}}}
    validate_document({"value": 7}, schema)
    properties = schema["properties"]
    assert isinstance(properties, dict)
    properties["value"] = {"type": "string"}
    with pytest.raises(ValueError, match="schema"):
        validate_document({"value": 7}, schema)
    validate_document({"value": "valid"}, schema)
    validate_document(7, {"type": "integer"})


@pytest.mark.parametrize("keyword", ["$ref", "$dynamicRef"])
def test_warmed_schema_still_rejects_new_external_references(keyword: str) -> None:
    schema: JsonObject = {"$defs": {"item": {"type": "integer"}}, keyword: "#/$defs/item"}
    validate_document(7, schema)
    schema[keyword] = "https://example.invalid/never-fetch.json"
    with pytest.raises(ValueError, match="external_schema_reference"):
        validate_document(7, schema)


def test_compiled_schema_is_not_exposed_through_the_callers_dictionary() -> None:
    schema: JsonObject = {"type": "integer", "title": "Isolated schema snapshot regression"}
    validate_document(7, schema)
    schema["type"] = "string"
    with pytest.raises(ValueError, match="schema"):
        validate_document("invalid", {"type": "integer", "title": schema["title"]})
    validate_document(7, {"type": "integer", "title": schema["title"]})


def test_compiled_schema_preserves_declared_error_order() -> None:
    schema: JsonObject = {"type": "number", "minimum": 5, "maximum": 3}
    for _ in range(2):
        with pytest.raises(ValueError, match=r"minimum.*maximum"):
            validate_document(4, schema)
