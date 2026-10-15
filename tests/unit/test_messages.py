"""Direct message tests distinguish protocol, identity and task semantics."""

from dataclasses import replace
from pathlib import Path

import pytest

from anthropic_readiness.models import (
    CaseContract,
    JsonObject,
    Status,
    as_json,
    object_value,
    strict_json,
)
from anthropic_readiness.validation.messages import validate_message

ROOT = Path(__file__).resolve().parents[1] / "fixtures/contracts/core-1.0.0"


def message(tool: bool = False) -> JsonObject:
    return object_value(
        strict_json(
            (ROOT / ("message-valid-tool.json" if tool else "message-valid.json")).read_text()
        )
    )


def verdict(value: JsonObject, key: str, contract: CaseContract | None = None) -> Status:
    result = validate_message(value, contract or CaseContract("synthetic"))
    return next(a.status for a in result.assertions if a.id == key)


@pytest.mark.parametrize(
    "data", [{}, [], "", {"location": "Paris"}, {"location": "Hanoi", "extra": 1}]
)
def test_tool_input_schema_and_exact_value(data: object) -> None:
    value = message(True)
    blocks = value["content"]
    assert isinstance(blocks, list)
    tool = object_value(blocks[0])
    tool["input"] = as_json(data)
    value["content"] = [tool]
    assert verdict(value, "MSG-TOOL-INPUT", CaseContract("tool", behavior="tool")) == Status.FAIL


@pytest.mark.parametrize(
    ("field", "bad", "expected"), [("name", "wrong", "MSG-TOOL-NAME"), ("id", "", "MSG-TOOL-ID")]
)
def test_wrong_name_and_missing_id(field: str, bad: str, expected: str) -> None:
    value = message(True)
    blocks = value["content"]
    assert isinstance(blocks, list)
    tool = object_value(blocks[0])
    tool[field] = bad
    value["content"] = [tool]
    assert verdict(value, expected, CaseContract("tool", behavior="tool")) == Status.FAIL


def test_duplicate_tool_id_and_wrong_stop() -> None:
    value = message(True)
    blocks = value["content"]
    assert isinstance(blocks, list)
    value["content"] = [*blocks, *blocks]
    assert verdict(value, "MSG-TOOL-ID", CaseContract("tool", behavior="tool")) == Status.FAIL
    value = message(True)
    value["stop_reason"] = "end_turn"
    assert verdict(value, "TASK-COMPLETE", CaseContract("tool", behavior="tool")) == Status.FAIL


def test_empty_tool_input_can_be_allowed_by_schema() -> None:
    value = object_value(strict_json((ROOT / "message-invalid-tool.json").read_text()))
    contract = CaseContract(
        "empty-tool", behavior="tool", input_schema={"type": "object"}, expected_input={}
    )
    assert validate_message(value, contract).status == Status.PASS


def test_model_policy_and_alias() -> None:
    value = message()
    value["model"] = "response-alias"
    contract = CaseContract("model")
    assert verdict(value, "MSG-MODEL", contract) == Status.FAIL
    assert (
        validate_message(value, replace(contract, aliases=("response-alias",))).status
        == Status.PASS
    )
    assert (
        validate_message(value, replace(contract, model_policy="structure_only")).status
        == Status.PASS
    )
    value["model"] = ""
    assert (
        verdict(value, "MSG-CORE", replace(contract, model_policy="structure_only")) == Status.FAIL
    )


def test_unknown_stop_reason_is_indeterminate() -> None:
    value = message()
    value["stop_reason"] = "future_stop"
    assert validate_message(value, CaseContract("unknown")).status == Status.INDETERMINATE


def test_max_tokens_is_protocol_valid_but_task_incomplete() -> None:
    value = message()
    value["stop_reason"] = "max_tokens"
    result = validate_message(value, CaseContract("limited"))
    assert all(a.status == Status.PASS for a in result.assertions if a.category == "protocol")
    assert verdict(value, "TASK-COMPLETE") == Status.FAIL


def test_nonobject_tool_input_is_protocol_structure_failure() -> None:
    value = message(True)
    blocks = value["content"]
    assert isinstance(blocks, list)
    tool = object_value(blocks[0])
    tool["input"] = "not an object"
    value["content"] = [tool]
    assert verdict(value, "MSG-CORE", CaseContract("tool", behavior="tool")) == Status.FAIL


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1, 2, 3, 4, 5", Status.PASS),
        ("1 2 3 4 5 6", Status.FAIL),
        ("1 2 3 4 5 <analysis>marker</analysis>", Status.PASS),
    ],
)
def test_count_and_tag_diagnostics(text: str, expected: Status) -> None:
    value = message()
    value["content"] = [{"type": "text", "text": text}]
    assert verdict(value, "TASK-COMPLETE", CaseContract("count", behavior="count")) == expected
