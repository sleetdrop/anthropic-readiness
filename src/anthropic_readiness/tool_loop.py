"""Pure bounded client-tool continuation and fresh-result checks."""

from __future__ import annotations

import json
import re
from dataclasses import replace

from anthropic_readiness.models import (
    AssertionResult,
    Capture,
    JsonObject,
    RequestSpec,
    Status,
    ValidationResult,
    object_value,
    strict_json,
)

CASE_ID = "ANT-TOOL-LOOP-001"


def complete_record(record: JsonObject) -> bool:
    raw = record.get("attempts")
    if (
        not isinstance(raw, list)
        or len(raw) != 2
        or not all(isinstance(item, dict) for item in raw)
    ):
        return False
    steps = [object_value(item) for item in raw]
    return (
        [item.get("index") for item in steps] == [1, 2]
        and all(item.get("actual_requests") == 1 for item in steps)
        and [object_value(item.get("observations", {})).get("tool_loop_step") for item in steps]
        == [1, 2]
    )


def tool_message(capture: Capture) -> JsonObject | None:
    if (
        capture.capture_end != "eof"
        or capture.status_code is None
        or not 200 <= capture.status_code < 300
    ):
        return None
    try:
        message = object_value(strict_json(capture.body.decode()))
    except (ValueError, UnicodeError):
        return None
    blocks = message.get("content")
    if (
        message.get("role") != "assistant"
        or message.get("stop_reason") != "tool_use"
        or not isinstance(blocks, list)
    ):
        return None
    tools = [
        block for block in blocks if isinstance(block, dict) and block.get("type") == "tool_use"
    ]
    if len(tools) != 1:
        return None
    tool = tools[0]
    if (
        not isinstance(tool.get("id"), str)
        or not tool["id"]
        or tool.get("name") != "get_weather"
        or tool.get("input") != {"location": "Hanoi"}
    ):
        return None
    return message


def followup_request(first: RequestSpec, message: JsonObject, token: str) -> RequestSpec:
    if re.fullmatch(r"[0-9a-f]{32}", token) is None:
        raise ValueError("invalid_tool_loop_token")
    blocks = message["content"]
    assert isinstance(blocks, list)
    tool = next(
        object_value(block)
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "tool_use"
    )
    messages = first.body["messages"]
    assert isinstance(messages, list)
    body: JsonObject = {
        **first.body,
        "tool_choice": {"type": "none"},
        "messages": [
            *messages,
            {"role": "assistant", "content": blocks},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool["id"],
                        "content": json.dumps(
                            {"temperature_celsius": 23, "verification_token": token},
                            separators=(",", ":"),
                        ),
                    }
                ],
            },
        ],
    }
    return replace(first, body=body)


def validate_step(
    capture: Capture, validated: ValidationResult, step: int, token: str | None
) -> ValidationResult:
    text = str(validated.observations.get("text", ""))
    message = tool_message(capture) if step == 1 else None
    text_only = False
    if step == 2:
        try:
            final = object_value(strict_json(capture.body.decode()))
            blocks = final.get("content")
            text_only = (
                isinstance(blocks, list)
                and bool(blocks)
                and all(isinstance(block, dict) and block.get("type") == "text" for block in blocks)
            )
        except (ValueError, UnicodeError):
            pass
    passed = (
        message is not None
        if step == 1
        else bool(token)
        and text_only
        and capture.capture_end == "eof"
        and text.strip() == token
        and any(a.id == "TASK-COMPLETE" and a.status == Status.PASS for a in validated.assertions)
    )
    complete = (
        capture.capture_end == "eof"
        and capture.status_code is not None
        and 200 <= capture.status_code < 300
    )
    assertion = AssertionResult(
        "LOOP-STEP",
        "behavior",
        Status.PASS if passed else Status.FAIL if complete else Status.INDETERMINATE,
        "satisfied"
        if passed
        else "tool_loop_prerequisite_failed"
        if step == 1
        else "tool_result_not_consumed"
        if complete
        else "tool_loop_incomplete",
        expected="one valid get_weather call for Hanoi" if step == 1 else str(token),
        actual="valid tool call" if message is not None else text,
    )
    return ValidationResult(
        (*validated.assertions, assertion),
        {**validated.observations, "tool_loop_step": step},
    )
