"""Ordered message and per-index content states; retain proven defects."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from anthropic_readiness.models import (
    AssertionResult,
    CaptureEnd,
    CaseContract,
    DecodeTail,
    JsonDepthError,
    JsonObject,
    ProtocolEnd,
    SSEFrame,
    Status,
    ValidationResult,
    aggregate_required,
    object_value,
    strict_json,
)
from anthropic_readiness.validation.messages import validate_message

KNOWN = {
    "message_start",
    "content_block_start",
    "content_block_delta",
    "content_block_stop",
    "message_delta",
    "message_stop",
    "error",
    "ping",
}


@dataclass
class Block:
    value: JsonObject
    event: int
    closed: bool = False
    fragments: list[str] = field(default_factory=list)
    unknown: bool = False


class StreamValidator:
    def __init__(self, contract: CaseContract):
        self.contract = contract
        self._checks: dict[str, AssertionResult] = {}
        self._message: JsonObject | None = None
        self._blocks: dict[int, Block] = {}
        self._starts = 0
        self._deltas = 0
        self._stops = 0
        self._phase = "before_start"
        self._error = False
        self._unknown = False
        self._extensions: list[str] = []

    def _record(
        self, key: str, reason: str, event: int | None = None, status: Status = Status.FAIL
    ) -> None:
        item = AssertionResult(
            key, "behavior" if key == "STR-ERROR" else "protocol", status, reason, event=event
        )
        previous = self._checks.get(key)
        if previous is None or aggregate_required([previous.status, status]) != previous.status:
            self._checks[key] = item

    def consume(self, frame: SSEFrame) -> None:
        event = frame.event
        seq = frame.sequence
        try:
            data = object_value(strict_json(frame.data))
        except JsonDepthError:
            self._record("STR-JSON", "json_depth_limit", seq, Status.INDETERMINATE)
            return
        except (ValueError, UnicodeError):
            self._record("STR-JSON", "invalid_event_json", seq)
            return
        if data.get("type") != event:
            self._record("STR-TYPE", "event_type_mismatch", seq)
        if event not in KNOWN:
            self._extensions.append(event)
            return
        if event == "ping":
            return
        if event == "error":
            detail = data.get("error")
            if (
                not isinstance(detail, dict)
                or not isinstance(detail.get("type"), str)
                or not isinstance(detail.get("message"), str)
            ):
                self._record("STR-JSON", "invalid_error_event", seq)
            self._record("STR-ERROR", "service_error", seq)
            self._error = True
            return
        if self._phase == "stopped" or self._error:
            self._record("STR-LIFECYCLE", "event_after_termination", seq)
        if event == "message_start":
            self._starts += 1
            if self._starts != 1:
                self._record("STR-START", "duplicate_message_start", seq)
                return
            if self._phase != "before_start":
                self._record("STR-LIFECYCLE", "late_message_start", seq)
            message = data.get("message")
            if not isinstance(message, dict):
                self._record("MSG-CORE", "invalid_initial_message", seq)
            else:
                self._message = dict(message)
                initial = validate_message({**message, "stop_reason": "end_turn"}, self.contract)
                for item in initial.assertions:
                    if (
                        item.id in {"MSG-CORE", "MSG-MODEL", "MSG-STOP-SEQUENCE"}
                        and item.status == Status.FAIL
                    ):
                        self._checks[item.id] = replace(item, event=seq)
                if (
                    message.get("content") != []
                    or "stop_reason" not in message
                    or message.get("stop_reason") is not None
                ):
                    self._record("MSG-CORE", "invalid_initial_message", seq)
            self._phase = "content"
        elif event == "message_delta":
            if self._phase not in {"content", "message_delta"} or any(
                not b.closed for b in self._blocks.values()
            ):
                self._record("STR-LIFECYCLE", "message_delta_out_of_order", seq)
            self._deltas += 1
            delta = data.get("delta")
            usage = data.get("usage")
            if not isinstance(delta, dict) or not isinstance(usage, dict):
                self._record("STR-JSON", "invalid_message_delta", seq)
            elif self._message is not None:
                if (
                    type(usage.get("output_tokens")) is not int
                    or int(str(usage.get("output_tokens", -1))) < 0
                ):
                    self._record("STR-JSON", "invalid_delta_usage", seq)
                for key in ("stop_reason", "stop_sequence"):
                    if key in delta:
                        if delta[key] is not None and not isinstance(delta[key], str):
                            self._record("STR-JSON", "invalid_delta_stop_fields", seq)
                        self._message[key] = delta[key]
                old_usage = self._message.get("usage")
                self._message["usage"] = {
                    **(old_usage if isinstance(old_usage, dict) else {}),
                    **usage,
                }
            self._phase = "message_delta"
        elif event == "message_stop":
            self._stops += 1
            if self._stops != 1:
                self._record("STR-STOP", "duplicate_message_stop", seq)
            if (
                self._stops != 1
                or self._phase != "message_delta"
                or any(not b.closed for b in self._blocks.values())
            ):
                self._record("STR-LIFECYCLE", "message_stop_out_of_order", seq)
            self._phase = "stopped"
        else:
            self._content(event, data, seq)

    def _content(self, event: str, data: JsonObject, seq: int) -> None:
        index = data.get("index")
        if type(index) is not int or index < 0:
            self._record("STR-LIFECYCLE", "invalid_index", seq)
            return
        if self._phase != "content":
            self._record("STR-LIFECYCLE", "content_out_of_order", seq)
        if event == "content_block_start":
            if index in self._blocks or index != len(self._blocks):
                self._record("STR-LIFECYCLE", "duplicate_or_noncontiguous_index", seq)
                return
            block = data.get("content_block")
            if not isinstance(block, dict) or not isinstance(block.get("type"), str):
                self._record("STR-JSON", "invalid_content_block", seq)
                return
            self._blocks[index] = Block(dict(block), seq)
            if block["type"] not in {"text", "tool_use"}:
                self._blocks[index].unknown = True
                self._unknown = True
            return
        block_state = self._blocks.get(index)
        if block_state is None or block_state.closed:
            self._record("STR-LIFECYCLE", "delta_or_stop_for_nonopen_block", seq)
            return
        if event == "content_block_stop":
            block_state.closed = True
            if block_state.fragments:
                if block_state.value.get("input") != {}:
                    block_state.unknown = True
                    self._unknown = True
                    self._record(
                        "STR-RECONSTRUCTION",
                        "initial_input_with_fragments",
                        seq,
                        Status.INDETERMINATE,
                    )
                else:
                    try:
                        block_state.value["input"] = strict_json("".join(block_state.fragments))
                    except JsonDepthError:
                        block_state.unknown = True
                        self._unknown = True
                        self._record("STR-TOOL-JSON", "json_depth_limit", seq, Status.INDETERMINATE)
                    except ValueError:
                        self._record("STR-TOOL-JSON", "invalid_tool_json", seq)
            return
        delta = data.get("delta")
        if not isinstance(delta, dict) or not isinstance(delta.get("type"), str):
            self._record("STR-JSON", "invalid_content_delta", seq)
            return
        kind = delta["type"]
        if kind not in {"text_delta", "input_json_delta"}:
            block_state.unknown = True
            self._unknown = True
            self._record("STR-RECONSTRUCTION", "unknown_delta", seq, Status.INDETERMINATE)
        elif kind == "text_delta":
            text = delta.get("text")
            initial = block_state.value.get("text")
            if (
                block_state.value.get("type") != "text"
                or not isinstance(text, str)
                or not isinstance(initial, str)
            ):
                self._record("STR-JSON", "delta_block_type_mismatch", seq)
            else:
                block_state.value["text"] = initial + text
        elif block_state.value.get("type") != "tool_use" or not isinstance(
            delta.get("partial_json"), str
        ):
            self._record("STR-JSON", "delta_block_type_mismatch", seq)
        else:
            block_state.fragments.append(str(delta["partial_json"]))

    def finish(
        self, protocol_end: ProtocolEnd, capture_end: CaptureEnd, tail: DecodeTail
    ) -> ValidationResult:
        incomplete = capture_end != "eof"
        for key in ("STR-JSON", "STR-TYPE", "STR-LIFECYCLE"):
            if key not in self._checks:
                self._record(key, "satisfied", status=Status.PASS)
        self._checks["CAPTURE-COMPLETE"] = AssertionResult(
            "CAPTURE-COMPLETE",
            "environment",
            Status.INDETERMINATE if incomplete else Status.PASS,
            capture_end,
        )
        if tail.encoding_errors:
            self._record("SSE-FRAMING", "invalid_utf8")
        elif tail.pending_data:
            self._record(
                "SSE-FRAMING",
                "undispatched_data_tail",
                status=Status.INDETERMINATE if incomplete else Status.FAIL,
            )
        else:
            self._record("SSE-FRAMING", "satisfied", status=Status.PASS)
        if not self._error:
            missing_status = Status.INDETERMINATE if incomplete else Status.FAIL
            for key, count, name in [
                ("STR-START", self._starts, "message_start"),
                ("STR-DELTA", self._deltas, "message_delta"),
                ("STR-STOP", self._stops, "message_stop"),
            ]:
                self._record(
                    key,
                    "satisfied" if count else f"missing_{name}",
                    status=Status.PASS if count else missing_status,
                )
            if any(not b.closed for b in self._blocks.values()):
                self._record("STR-LIFECYCLE", "unclosed_blocks", status=missing_status)
            if self._message is not None and self._stops:
                self._message["content"] = [self._blocks[i].value for i in sorted(self._blocks)]
                validated = validate_message(self._message, self.contract)
                known = validate_message(
                    {
                        **self._message,
                        "content": [b.value for b in self._blocks.values() if not b.unknown],
                    },
                    self.contract,
                )
                known_input_failure = any(
                    a.id == "MSG-TOOL-INPUT" and a.status == Status.FAIL for a in known.assertions
                )
                uncertain_input = any(
                    b.unknown and b.value.get("type") == "tool_use" for b in self._blocks.values()
                )
                for item in validated.assertions:
                    if (
                        uncertain_input and not known_input_failure and item.id == "MSG-TOOL-INPUT"
                    ) or (
                        self._unknown
                        and item.id == "TASK-COMPLETE"
                        and self.contract.behavior != "tool"
                        and self._message.get("stop_reason") == "end_turn"
                    ):
                        item = replace(
                            item, status=Status.INDETERMINATE, reason_code="unknown_reconstruction"
                        )
                    existing = self._checks.get(item.id)
                    if (
                        existing is None
                        or aggregate_required([existing.status, item.status]) != existing.status
                    ):
                        self._checks[item.id] = item
                observations = validated.observations
            else:
                observations = {}
        else:
            observations = {"failure_domain": "service_error"}
        observations["unknown_events"] = list(self._extensions)
        observations["protocol_end"] = protocol_end
        return ValidationResult(tuple(self._checks.values()), observations)
