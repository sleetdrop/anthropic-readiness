"""Lifecycle defects remain visible even with partial or unfamiliar streams."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from anthropic_readiness.models import (
    CaptureEnd,
    CaseContract,
    JsonObject,
    JsonValue,
    ProtocolEnd,
    Status,
    ValidationResult,
    object_value,
    strict_json,
)
from anthropic_readiness.sse import SSEDecoder
from anthropic_readiness.validation.stream import StreamValidator

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/contracts/core-1.0.0/stream-valid.sse"


def events() -> list[JsonObject]:
    decoder = SSEDecoder(100000, 100)
    return [
        object_value(strict_json(frame.data)) for frame in decoder.feed(FIXTURE.read_bytes(), 0)
    ]


def wire(items: list[JsonObject]) -> bytes:
    return "".join(
        f"event: {item['type']}\ndata: {json.dumps(item)}\n\n" for item in items
    ).encode()


def evaluate(
    items: list[JsonObject],
    end: CaptureEnd = "eof",
    contract: CaseContract | None = None,
    body: bytes | None = None,
    split: int | None = None,
) -> ValidationResult:
    data = wire(items) if body is None else body
    decoder = SSEDecoder(100000, 100)
    validator = StreamValidator(contract or CaseContract("synthetic"))
    chunks = [data] if split is None else [data[:split], data[split:]]
    protocol_end: ProtocolEnd = "none"
    for chunk in chunks:
        for frame in decoder.feed(chunk, 0):
            if frame.event == "message_stop":
                protocol_end = "message_stop"
            elif frame.event == "error":
                protocol_end = "error_event"
            validator.consume(frame)
    return validator.finish(protocol_end, end, decoder.finish())


def status(result: ValidationResult, assertion: str) -> Status:
    return next(a.status for a in result.assertions if a.id == assertion)


def test_duplicate_message_start_hits_expected_assertion() -> None:
    items = events()
    result = evaluate([items[0], *items])
    assert status(result, "STR-START") == Status.FAIL
    assert next(a.event for a in result.assertions if a.id == "STR-START") == 1


@pytest.mark.parametrize("closed", [False, True])
def test_wrong_index_and_closed_block_delta_fail(closed: bool) -> None:
    items = events()
    if closed:
        items.insert(4, items[2])
    else:
        items[2]["index"] = 9
    assert status(evaluate(items), "STR-LIFECYCLE") == Status.FAIL


def test_multiple_message_delta_and_empty_block_pass() -> None:
    items = events()
    items.insert(-1, {"type": "message_delta", "delta": {}, "usage": {"output_tokens": 2}})
    items.pop(2)
    block = object_value(items[1]["content_block"])
    block["text"] = "Hello."
    items[1]["content_block"] = block
    assert evaluate(items).status == Status.PASS


@pytest.mark.parametrize("field", ["stop_reason", "stop_sequence"])
@pytest.mark.parametrize("value", [123, True, {"invalid": True}, []])
def test_invalid_intermediate_stop_field_cannot_be_repaired(field: str, value: JsonValue) -> None:
    items = events()
    items.insert(
        4,
        {"type": "message_delta", "delta": {field: value}, "usage": {"output_tokens": 1}},
    )
    result = evaluate(items)
    assert result.status == Status.FAIL
    failure = next(a for a in result.assertions if a.id == "STR-JSON")
    assert failure.status == Status.FAIL
    assert failure.event == 4
    assert status(result, "MSG-STOP") == Status.PASS
    assert status(result, "MSG-STOP-SEQUENCE") == Status.PASS


@pytest.mark.parametrize(
    "delta",
    [
        {},
        {"stop_reason": None, "stop_sequence": None},
        {"stop_reason": "end_turn", "stop_sequence": None},
        {"future_extension": {"value": 123}},
    ],
)
def test_valid_intermediate_stop_fields_and_extensions_pass(delta: JsonObject) -> None:
    items = events()
    items.insert(4, {"type": "message_delta", "delta": delta, "usage": {"output_tokens": 1}})
    assert evaluate(items).status == Status.PASS


def test_unknown_event_does_not_hide_known_failure() -> None:
    items = events()
    extra: JsonObject = {"type": "future_extension", "value": "unknown"}
    assert evaluate([extra, *items]).status == Status.PASS
    assert status(evaluate([extra, items[0], *items]), "STR-START") == Status.FAIL


def test_unknown_delta_is_indeterminate() -> None:
    items = events()
    items[2]["delta"] = {"type": "future_delta", "value": "unknown"}
    assert evaluate(items).status == Status.INDETERMINATE


def test_error_event_is_task_failure_not_missing_stop() -> None:
    result = evaluate(
        [{"type": "error", "error": {"type": "overloaded_error", "message": "Synthetic overload"}}]
    )
    assert status(result, "STR-ERROR") == Status.FAIL
    assert not any(a.reason_code.startswith("missing_") for a in result.assertions)


def test_valid_stop_with_capture_timeout_is_incomplete() -> None:
    result = evaluate(events(), "timeout")
    assert status(result, "STR-STOP") == Status.PASS
    assert status(result, "TASK-COMPLETE") == Status.PASS
    assert status(result, "CAPTURE-COMPLETE") == Status.INDETERMINATE
    assert result.status == Status.INDETERMINATE


def tool_events(fragment: str = '{"location":"Hanoi"}') -> list[JsonObject]:
    items = events()
    items[1]["content_block"] = {
        "type": "tool_use",
        "id": "synthetic-tool",
        "name": "get_weather",
        "input": {},
    }
    items[2]["delta"] = {"type": "input_json_delta", "partial_json": fragment}
    items[4]["delta"] = {"stop_reason": "tool_use", "stop_sequence": None}
    return items


def test_tool_fragments_and_schema_allowed_empty_input() -> None:
    contract = CaseContract("tool", behavior="tool")
    items = tool_events()
    items[2]["delta"] = {"type": "input_json_delta", "partial_json": '{"location":'}
    items.insert(
        3,
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "input_json_delta", "partial_json": '"Hanoi"}'},
        },
    )
    assert evaluate(items, contract=contract).status == Status.PASS
    empty = replace(contract, input_schema={"type": "object"}, expected_input={})
    assert evaluate(tool_events("{}"), contract=empty).status == Status.PASS


@pytest.mark.parametrize(
    ("fragment", "expected"),
    [("{}", "MSG-TOOL-INPUT"), ("[]", "MSG-TOOL-INPUT"), ('{"x":', "STR-TOOL-JSON")],
)
def test_bad_tool_input(fragment: str, expected: str) -> None:
    assert (
        status(
            evaluate(tool_events(fragment), contract=CaseContract("tool", behavior="tool")),
            expected,
        )
        == Status.FAIL
    )


@pytest.mark.parametrize(
    ("field", "value", "assertion"), [("name", "wrong", "MSG-TOOL-NAME"), ("id", "", "MSG-TOOL-ID")]
)
def test_wrong_tool_names_and_ids(field: str, value: str, assertion: str) -> None:
    items = tool_events()
    block = object_value(items[1]["content_block"])
    block[field] = value
    items[1]["content_block"] = block
    assert (
        status(evaluate(items, contract=CaseContract("tool", behavior="tool")), assertion)
        == Status.FAIL
    )


@pytest.mark.parametrize("index", [-1, True, 2])
def test_invalid_indices(index: int) -> None:
    items = events()
    items[1]["index"] = index
    assert status(evaluate(items), "STR-LIFECYCLE") == Status.FAIL


def test_pre_start_post_stop_and_truncation() -> None:
    items = events()
    assert status(evaluate([items[1], *items]), "STR-LIFECYCLE") == Status.FAIL
    assert status(evaluate([*items, items[1]]), "STR-LIFECYCLE") == Status.FAIL
    assert status(evaluate(items[:-1]), "STR-STOP") == Status.FAIL
    assert status(evaluate(items[:-1], "read_error"), "STR-STOP") == Status.INDETERMINATE
    assert status(evaluate([items[0], *items], "capture_limit"), "STR-START") == Status.FAIL


def test_data_type_strict_json_and_tail() -> None:
    body = wire(events())
    assert evaluate([], body=body + b": harmless comment").status == Status.PASS
    assert status(evaluate([], body=body.rstrip(b"\n")), "SSE-FRAMING") == Status.FAIL
    assert (
        status(
            evaluate([], body=body.replace(b'"type": "message_start"', b'"type": "different"', 1)),
            "STR-TYPE",
        )
        == Status.FAIL
    )
    assert (
        status(evaluate([], body=b"event: message_start\ndata: NaN\n\n"), "STR-JSON") == Status.FAIL
    )


def test_every_split_retains_verdict() -> None:
    items = events()
    expected = [(a.id, a.status) for a in evaluate(items).assertions]
    for split in range(len(wire(items)) + 1):
        assert [(a.id, a.status) for a in evaluate(items, split=split).assertions] == expected


def test_start_core_fields_cannot_be_repaired_by_later_deltas() -> None:
    items = events()
    message = object_value(items[0]["message"])
    message.pop("usage")
    items[0]["message"] = message
    items[4]["usage"] = {"input_tokens": 1, "output_tokens": 2}
    assert status(evaluate(items), "MSG-CORE") == Status.FAIL


def test_unknown_block_does_not_mask_known_tool_input_failure() -> None:
    items = tool_events("{}")
    items.insert(
        4, {"type": "content_block_start", "index": 1, "content_block": {"type": "future_block"}}
    )
    items.insert(5, {"type": "content_block_stop", "index": 1})
    assert (
        status(evaluate(items, contract=CaseContract("tool", behavior="tool")), "MSG-TOOL-INPUT")
        == Status.FAIL
    )


def test_incompatible_initial_input_with_fragments_is_indeterminate() -> None:
    items = tool_events()
    block = object_value(items[1]["content_block"])
    block["input"] = {"location": "Already set"}
    items[1]["content_block"] = block
    assert (
        evaluate(items, contract=CaseContract("tool", behavior="tool")).status
        == Status.INDETERMINATE
    )


def test_unknown_content_does_not_mask_max_tokens_task_failure() -> None:
    items = events()
    items[1]["content_block"] = {"type": "future_block"}
    items.pop(2)
    items[3]["delta"] = {"stop_reason": "max_tokens", "stop_sequence": None}
    assert status(evaluate(items), "TASK-COMPLETE") == Status.FAIL


def test_duplicate_stop_hits_stop_assertion() -> None:
    items = events()
    assert status(evaluate([*items, items[-1]]), "STR-STOP") == Status.FAIL


def test_delta_usage_cannot_reuse_initial_token_counts() -> None:
    items = events()
    items[4]["usage"] = {}
    assert status(evaluate(items), "STR-JSON") == Status.FAIL


@pytest.mark.parametrize(
    "name",
    [
        "stream-valid.sse",
        "stream-duplicate-start.sse",
        "stream-invalid-index.sse",
        "stream-invalid-tail.sse",
    ],
)
def test_versioned_fixture_verdicts_are_split_invariant(name: str) -> None:
    body = FIXTURE.with_name(name).read_bytes()
    expected = {
        "stream-valid.sse": (None, Status.PASS),
        "stream-duplicate-start.sse": ("STR-START", Status.FAIL),
        "stream-invalid-index.sse": ("STR-LIFECYCLE", Status.FAIL),
        "stream-invalid-tail.sse": ("SSE-FRAMING", Status.FAIL),
    }
    assertion_id, verdict = expected[name]
    result = evaluate([], body=body)
    assert result.status == verdict
    if assertion_id is not None:
        assert status(result, assertion_id) == verdict
    signature = [(a.id, a.status) for a in result.assertions]
    for split in range(len(body) + 1):
        assert [
            (a.id, a.status) for a in evaluate([], body=body, split=split).assertions
        ] == signature


def test_tool_json_parser_limit_is_not_invalid_tool_input() -> None:
    contract = CaseContract(
        "tool-depth",
        behavior="tool",
        input_schema={"type": "object", "required": ["nested"]},
        expected_input=None,
    )
    assert evaluate(tool_events('{"nested":[]}'), contract=contract).status == Status.PASS
    fragment = '{"nested":' + "[" * 2000 + "0" + "]" * 2000 + "}"
    result = evaluate(tool_events(fragment), contract=contract)
    assert status(result, "STR-TOOL-JSON") == Status.INDETERMINATE
    assert status(result, "MSG-TOOL-INPUT") == Status.INDETERMINATE
    assert result.status == Status.INDETERMINATE
