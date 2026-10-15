"""Shared final-message checks for nonstream and reconstructed responses."""

from __future__ import annotations

import re

from anthropic_readiness.models import (
    AssertionResult,
    CaseContract,
    Category,
    JsonObject,
    Status,
    ValidationResult,
    object_value,
)
from anthropic_readiness.schema import validate_document


def validate_message(value: object, contract: CaseContract) -> ValidationResult:
    assertions: list[AssertionResult] = []

    def add(
        key: str,
        passed: bool,
        reason: str,
        category: Category = "protocol",
        uncertain: bool = False,
        required: bool = True,
    ) -> None:
        assertions.append(
            AssertionResult(
                key,
                category,
                Status.INDETERMINATE if uncertain else Status.PASS if passed else Status.FAIL,
                "satisfied" if passed and not uncertain else reason,
                required=required,
            )
        )

    if not isinstance(value, dict):
        add("MSG-CORE", False, "message_not_object")
        return ValidationResult(tuple(assertions))
    message = object_value(value)
    core = (
        isinstance(message.get("id"), str)
        and bool(message.get("id"))
        and message.get("type") == "message"
        and message.get("role") == "assistant"
        and isinstance(message.get("model"), str)
        and bool(message.get("model"))
        and isinstance(message.get("content"), list)
        and "stop_reason" in message
        and "stop_sequence" in message
    )
    usage = message.get("usage")
    core = (
        core
        and isinstance(usage, dict)
        and all(
            type(usage.get(k)) is int and int(str(usage[k])) >= 0
            for k in ("input_tokens", "output_tokens")
        )
    )
    blocks = message.get("content")
    unknown = False
    text = ""
    tools: list[JsonObject] = []
    if isinstance(blocks, list):
        for block in blocks:
            if not isinstance(block, dict) or not isinstance(block.get("type"), str):
                core = False
            elif block["type"] == "text":
                if isinstance(block.get("text"), str):
                    text += str(block["text"])
                else:
                    core = False
            elif block["type"] == "tool_use":
                tools.append(block)
                if (
                    not isinstance(block.get("input"), dict)
                    or not isinstance(block.get("name"), str)
                    or not block.get("name")
                ):
                    core = False
            else:
                unknown = True
    add("MSG-CORE", bool(core), "invalid_message_structure")
    if contract.model_policy == "structure_only":
        assertions.append(
            AssertionResult(
                "MSG-MODEL", "protocol", Status.SKIP, "identity_not_checked", required=False
            )
        )
    else:
        add(
            "MSG-MODEL",
            message.get("model") in (contract.model, *contract.aliases),
            "model_identity_mismatch",
        )
    reason = message.get("stop_reason")
    known = {
        "end_turn",
        "max_tokens",
        "stop_sequence",
        "tool_use",
        "pause_turn",
        "refusal",
        "model_context_window_exceeded",
    }
    add(
        "MSG-STOP",
        isinstance(reason, str) and reason in known,
        "unknown_stop_reason" if isinstance(reason, str) else "invalid_stop_reason",
        uncertain=isinstance(reason, str) and reason not in known,
    )
    add(
        "MSG-STOP-SEQUENCE",
        message.get("stop_sequence") is None and reason != "stop_sequence",
        "unexpected_stop_sequence",
    )
    if tools or contract.behavior == "tool":
        add(
            "MSG-TOOL-CALLS",
            len(tools) == 1 if contract.behavior == "tool" else True,
            "wrong_tool_call_count",
            "behavior",
        )
        ids = [tool.get("id") for tool in tools]
        add(
            "MSG-TOOL-ID",
            all(isinstance(i, str) and bool(i) for i in ids)
            and len({str(i) for i in ids}) == len(ids),
            "invalid_or_duplicate_tool_id",
        )
        names_ok = all(
            isinstance(tool.get("name"), str)
            and bool(tool.get("name"))
            and (contract.behavior != "tool" or tool["name"] == contract.tool_name)
            for tool in tools
        )
        add("MSG-TOOL-NAME", names_ok, "wrong_tool_name", "behavior")
        inputs_ok = True
        for tool in tools:
            data = tool.get("input")
            if not isinstance(data, dict):
                inputs_ok = False
                continue
            if contract.behavior == "tool":
                try:
                    validate_document(data, contract.input_schema)
                except ValueError:
                    inputs_ok = False
                if contract.expected_input is not None and data != contract.expected_input:
                    inputs_ok = False
        add("MSG-TOOL-INPUT", inputs_ok, "invalid_tool_input", "behavior")
    if unknown:
        add("MSG-CONTENT", False, "unknown_content_type", uncertain=True)
    task_ok = reason == ("tool_use" if contract.behavior == "tool" else "end_turn")
    if contract.behavior == "tool":
        task_ok = task_ok and len(tools) == 1
    else:
        task_ok = task_ok and bool(text.strip())
        if contract.behavior == "count":
            task_ok = task_ok and re.findall(r"\d+", text) == ["1", "2", "3", "4", "5"]
    add(
        "TASK-COMPLETE",
        task_ok,
        "task_not_completed",
        "behavior",
        uncertain=(isinstance(reason, str) and reason not in known)
        or (unknown and reason == ("tool_use" if contract.behavior == "tool" else "end_turn")),
    )
    sightings = [
        {"tag": tag, "offset": match.start()}
        for tag in ("<analysis>", "<summary>", "<think>", "<thinking>")
        for match in re.finditer(re.escape(tag), text)
    ]
    return ValidationResult(
        tuple(assertions), object_value({"text": text, "tag_sightings": sightings})
    )
