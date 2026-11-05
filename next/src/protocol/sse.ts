import type { MessageValidationContext, Observation } from "../domain.ts";

type JsonObject = Record<string, unknown>;
type BlockKind = "text" | "tool_use" | "thinking" | "redacted_thinking" | "unknown";

export interface SseEvent {
  /** Zero-based index among dispatched SSE events, including invalid/oversized ones. */
  readonly index: number;
  readonly event: string;
  readonly data: string;
  readonly value: unknown;
}

export interface SseResult {
  readonly events: readonly SseEvent[];
  readonly observations: readonly Observation[];
  readonly message: Readonly<Record<string, unknown>> | null;
}

interface ActiveBlock {
  readonly index: number;
  readonly kind: BlockKind;
  readonly value: JsonObject;
  text: string;
  partialJson: string;
  signatureSeen: boolean;
}

const knownEvents = new Set([
  "message_start",
  "content_block_start",
  "content_block_delta",
  "content_block_stop",
  "message_delta",
  "message_stop",
  "ping",
  "error",
]);

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function pointerPart(value: string): string {
  return value.replaceAll("~", "~0").replaceAll("/", "~1");
}

function describe(value: unknown): string {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  if (typeof value === "number") return Number.isInteger(value) ? "integer" : "number";
  return typeof value;
}

function isNonnegativeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

function incompleteUtf8(bytes: Uint8Array): "valid" | "incomplete" | "invalid" {
  const decoder = new TextDecoder("utf-8", { fatal: true });
  try {
    decoder.decode(bytes, { stream: true });
  } catch {
    return "invalid";
  }
  try {
    decoder.decode();
    return "valid";
  } catch {
    return "incomplete";
  }
}

/** Parse and validate one bounded, content-decoded server-sent-event stream. */
export function validateSse(
  body: Uint8Array,
  context: MessageValidationContext,
  options: { completeCapture: boolean; maxEvents: number; maxEventBytes: number },
): SseResult {
  const events: SseEvent[] = [];
  const observations: Observation[] = [];
  let assembled: JsonObject | null = null;
  let started = false;
  let deltaSeen = false;
  let stopped = false;
  let errorTerminated = false;
  let active: ActiveBlock | null = null;
  let nextBlockIndex = 0;
  let dispatchedCount = 0;

  const add = (
    ruleId: string,
    status: Observation["status"],
    reason: string,
    expected: string,
    actual: string,
    eventIndex?: number,
    pointer = "",
    missingKey?: string,
    dimension: Observation["dimension"] = "protocol",
  ): void => {
    observations.push({
      ruleId,
      ruleVersion: 1,
      dimension,
      status,
      required: true,
      reason,
      expected,
      actual,
      ...(eventIndex === undefined
        ? {}
        : {
            location: {
              captureId: context.captureId,
              pointer,
              eventIndex,
              ...(missingKey === undefined ? {} : { missingKey }),
            },
          }),
    });
  };

  const checkField = (
    object: JsonObject,
    key: string,
    parent: string,
    valid: (value: unknown) => boolean,
    expected: string,
    eventIndex: number,
    ruleId: string,
  ): { present: boolean; value: unknown; valid: boolean } => {
    const present = Object.hasOwn(object, key);
    const value = object[key];
    const passes = present && valid(value);
    add(
      ruleId,
      passes ? "PASS" : "FAIL",
      passes ? "field_valid" : present ? "invalid_field" : "missing_field",
      expected,
      present ? describe(value) : "missing",
      eventIndex,
      present ? `${parent}/${pointerPart(key)}` : parent,
      present ? undefined : key,
    );
    return { present, value, valid: passes };
  };

  const eventObject = (event: SseEvent, expectedType: string): JsonObject | null => {
    if (!isObject(event.value)) {
      add("SSE-ENVELOPE", "FAIL", "event_data_not_object", "JSON object", describe(event.value), event.index);
      return null;
    }
    const type = checkField(event.value, "type", "", (value) => value === expectedType,
      `string ${JSON.stringify(expectedType)}`, event.index, "SSE-ENVELOPE-TYPE");
    if (!type.valid) {
      if (type.present && type.value !== expectedType) {
        add("SSE-ENVELOPE", "FAIL", "event_data_type_mismatch", `type ${expectedType}`, describe(type.value), event.index, "/type");
      }
      return null;
    }
    return event.value;
  };

  const failLifecycle = (event: SseEvent, reason: string, expected: string, actual: string): void => {
    add("SSE-LIFECYCLE", "FAIL", reason, expected, actual, event.index);
  };

  const processEvent = (event: SseEvent): void => {
    if (stopped) {
      failLifecycle(event, "event_after_message_stop", "no events after message_stop", event.event);
      return;
    }
    if (errorTerminated) {
      if (knownEvents.has(event.event)) {
        failLifecycle(event, "event_after_error_termination", "no events after error termination", event.event);
      } else {
        add("SSE-EXTENSION", "INDETERMINATE", "unknown_event", "recognized SSE event", "unrecognized event", event.index);
      }
      return;
    }
    if (!knownEvents.has(event.event)) {
      add("SSE-EXTENSION", "INDETERMINATE", "unknown_event", "recognized SSE event", "unrecognized event", event.index);
      return;
    }

    if (event.event === "message_start") {
      const data = eventObject(event, "message_start");
      if (started) {
        failLifecycle(event, "duplicate_message_start", "one message_start", "duplicate message_start");
        return;
      }
      started = true;
      if (deltaSeen) failLifecycle(event, "message_start_out_of_order", "message_start before message_delta", "message_start after message_delta");
      if (data === null) return;

      const messageField = checkField(data, "message", "", isObject, "JSON object", event.index, "SSE-MESSAGE-START");
      if (!messageField.valid || !isObject(messageField.value)) return;
      const initial = messageField.value;
      assembled = {
        ...initial,
        content: Array.isArray(initial.content) ? [...initial.content] : [],
        ...(isObject(initial.usage) ? { usage: { ...initial.usage } } : {}),
      };
      checkField(initial, "id", "/message", (value) => typeof value === "string" && value.length > 0, "nonempty string", event.index, "SSE-MESSAGE-START");
      checkField(initial, "type", "/message", (value) => value === "message", 'string "message"', event.index, "SSE-MESSAGE-START");
      checkField(initial, "role", "/message", (value) => value === "assistant", 'string "assistant"', event.index, "SSE-MESSAGE-START");
      checkField(initial, "model", "/message", (value) => typeof value === "string" && value.length > 0, "nonempty string", event.index, "SSE-MESSAGE-START");
      const content = checkField(initial, "content", "/message", Array.isArray, "empty array", event.index, "SSE-MESSAGE-START");
      if (content.valid && Array.isArray(content.value) && content.value.length > 0) {
        add("SSE-MESSAGE-START", "FAIL", "initial_message_content_not_empty", "empty array", "nonempty array", event.index, "/message/content");
      }
      checkField(initial, "stop_reason", "/message", (value) => value === null, "null before message_delta", event.index, "SSE-MESSAGE-START");
      checkField(initial, "stop_sequence", "/message", (value) => value === null, "null before message_delta", event.index, "SSE-MESSAGE-START");
      const usageField = checkField(initial, "usage", "/message", isObject, "JSON object", event.index, "SSE-MESSAGE-START");
      if (usageField.valid && isObject(usageField.value)) {
        checkField(usageField.value, "input_tokens", "/message/usage", isNonnegativeInteger, "nonnegative integer", event.index, "SSE-MESSAGE-START");
        checkField(usageField.value, "output_tokens", "/message/usage", isNonnegativeInteger, "nonnegative integer", event.index, "SSE-MESSAGE-START");
      }
      return;
    }

    if (event.event === "ping") {
      eventObject(event, "ping");
      return;
    }

    if (event.event === "error") {
      const data = eventObject(event, "error");
      if (data !== null) {
        errorTerminated = true;
        add("SSE-ERROR", "INDETERMINATE", "error_detail_not_validated", "service-specific error details", "error details retained without taxonomy", event.index);
      }
      add("SSE-ERROR", "FAIL", "error_event_received", "successful message stream", "server error event received", event.index, "", undefined, "behavior");
      return;
    }

    if (event.event === "message_stop") {
      const data = eventObject(event, "message_stop");
      if (!started) failLifecycle(event, "message_stop_before_start", "message_start before message_stop", "message_stop before start");
      if (active !== null) failLifecycle(event, "message_stop_with_open_block", "all blocks stopped before message_stop", "content block still open");
      if (!deltaSeen) failLifecycle(event, "message_stop_before_delta", "message_delta before message_stop", "message_delta missing");
      if (data !== null) stopped = true;
      return;
    }

    const expectedType = event.event;
    const data = eventObject(event, expectedType);
    if (data === null) return;
    if (!started) {
      failLifecycle(event, "event_before_message_start", "message_start before content and message events", event.event);
      return;
    }

    if (event.event === "content_block_start") {
      if (deltaSeen) {
        failLifecycle(event, "block_start_after_message_delta", "all blocks before message_delta", "content_block_start after message_delta");
        return;
      }
      if (active !== null) {
        failLifecycle(event, "nested_content_block_start", "previous content block stopped first", "new block started while another is open");
        return;
      }
      const index = checkField(data, "index", "", isNonnegativeInteger, "nonnegative sequential integer", event.index, "SSE-BLOCK-INDEX");
      let blockIndex = -1;
      if (index.valid && typeof index.value === "number") {
        blockIndex = index.value;
        if (blockIndex !== nextBlockIndex) {
          add("SSE-BLOCK-INDEX", "FAIL", "content_index_not_sequential", `index ${nextBlockIndex}`, `index ${blockIndex}`, event.index, "/index");
        }
        nextBlockIndex += 1;
      }
      const blockField = checkField(data, "content_block", "", isObject, "JSON object", event.index, "SSE-BLOCK");
      if (!blockField.valid || !isObject(blockField.value)) return;
      const block = blockField.value;
      const blockType = checkField(block, "type", "/content_block", (value) => typeof value === "string", "string block type", event.index, "SSE-BLOCK");
      if (!blockType.valid || typeof blockType.value !== "string") return;
      let kind: BlockKind;
      let text = "";
      if (blockType.value === "text") {
        kind = "text";
        const initialText = checkField(block, "text", "/content_block", (value) => typeof value === "string", "string", event.index, "SSE-BLOCK");
        if (initialText.valid && typeof initialText.value === "string") text = initialText.value;
      } else if (blockType.value === "tool_use") {
        kind = "tool_use";
        checkField(block, "id", "/content_block", (value) => typeof value === "string" && value.length > 0, "nonempty string", event.index, "SSE-BLOCK");
        checkField(block, "name", "/content_block", (value) => typeof value === "string" && value.length > 0, "nonempty string", event.index, "SSE-BLOCK");
        checkField(block, "input", "/content_block", isObject, "JSON object", event.index, "SSE-BLOCK");
      } else if (blockType.value === "thinking") {
        kind = "thinking";
        const initial = checkField(block, "thinking", "/content_block", (value) => typeof value === "string", "string", event.index, "SSE-THINKING");
        if (typeof initial.value === "string") text = initial.value;
        checkField(block, "signature", "/content_block", (value) => value === "", "empty string before signature_delta", event.index, "SSE-THINKING");
      } else if (blockType.value === "redacted_thinking") {
        kind = "redacted_thinking";
        checkField(block, "data", "/content_block", (value) => typeof value === "string" && value.length > 0, "nonempty string", event.index, "SSE-THINKING");
      } else {
        kind = "unknown";
        add("SSE-EXTENSION", "INDETERMINATE", "unknown_block_type", "recognized content block", "unrecognized content block", event.index, "/content_block/type");
      }
      if (blockIndex >= 0) {
        const blockValue = { ...block };
        if (kind === "tool_use" && isObject(block.input)) blockValue.input = { ...block.input };
        active = { index: blockIndex, kind, value: blockValue, text, partialJson: "", signatureSeen: false };
      }
      return;
    }

    if (event.event === "content_block_delta") {
      if (deltaSeen) {
        failLifecycle(event, "delta_after_message_delta", "content deltas before message_delta", "content delta after message_delta");
        return;
      }
      const index = checkField(data, "index", "", isNonnegativeInteger, "nonnegative integer", event.index, "SSE-BLOCK-INDEX");
      if (!index.valid || typeof index.value !== "number") return;
      if (active === null) {
        failLifecycle(event, "delta_without_open_block", "an open content block", "delta without an open block");
        return;
      }
      if (index.value !== active.index) {
        failLifecycle(event, "delta_index_mismatch", `active block index ${active.index}`, `delta index ${index.value}`);
        return;
      }
      const deltaField = checkField(data, "delta", "", isObject, "JSON object", event.index, "SSE-DELTA");
      if (!deltaField.valid || !isObject(deltaField.value)) return;
      const delta = deltaField.value;
      const type = checkField(delta, "type", "/delta", (value) => typeof value === "string", "string delta type", event.index, "SSE-DELTA");
      if (!type.valid || typeof type.value !== "string") return;
      if (type.value === "text_delta") {
        if (active.kind !== "text") {
          failLifecycle(event, "delta_wrong_block_kind", "text block for text_delta", `${active.kind} block`);
          return;
        }
        const text = checkField(delta, "text", "/delta", (value) => typeof value === "string", "string", event.index, "SSE-DELTA");
        if (text.valid && typeof text.value === "string") active.text += text.value;
      } else if (type.value === "input_json_delta") {
        if (active.kind !== "tool_use") {
          failLifecycle(event, "delta_wrong_block_kind", "tool_use block for input_json_delta", `${active.kind} block`);
          return;
        }
        const fragment = checkField(delta, "partial_json", "/delta", (value) => typeof value === "string", "string", event.index, "SSE-DELTA");
        if (fragment.valid && typeof fragment.value === "string") active.partialJson += fragment.value;
      } else if (type.value === "thinking_delta" || type.value === "signature_delta") {
        if (active.kind !== "thinking" || active.signatureSeen) {
          failLifecycle(event, "unexpected_thinking_delta", "an open thinking block before its signature", `${active.kind} block or a delta after signature`);
          return;
        }
        if (type.value === "thinking_delta") {
          const thinking = checkField(delta, "thinking", "/delta", (value) => typeof value === "string", "string", event.index, "SSE-THINKING");
          if (typeof thinking.value === "string") active.text += thinking.value;
        } else {
          const signature = checkField(delta, "signature", "/delta", (value) => typeof value === "string" && value.length > 0, "nonempty string", event.index, "SSE-THINKING-SIGNATURE");
          if (signature.valid) {
            active.value.signature = signature.value;
            active.signatureSeen = true;
          }
        }
      } else {
        add("SSE-EXTENSION", "INDETERMINATE", "unknown_delta_type", "recognized delta type", "unrecognized delta type", event.index, "/delta/type");
      }
      return;
    }

    if (event.event === "content_block_stop") {
      if (deltaSeen) {
        failLifecycle(event, "block_stop_after_message_delta", "all blocks before message_delta", "content_block_stop after message_delta");
        return;
      }
      const index = checkField(data, "index", "", isNonnegativeInteger, "nonnegative integer", event.index, "SSE-BLOCK-INDEX");
      if (!index.valid || typeof index.value !== "number") return;
      if (active === null) {
        failLifecycle(event, "block_stop_without_open_block", "an open content block", "block stop without an open block");
        return;
      }
      if (index.value !== active.index) {
        failLifecycle(event, "block_stop_index_mismatch", `active block index ${active.index}`, `stop index ${index.value}`);
        return;
      }
      if (active.kind === "text") {
        active.value.text = active.text;
      } else if (active.kind === "thinking") {
        active.value.thinking = active.text;
        add("SSE-THINKING-SIGNATURE", active.signatureSeen ? "PASS" : "FAIL",
          active.signatureSeen ? "thinking_signature_seen" : "thinking_signature_missing",
          "signature_delta before content_block_stop", active.signatureSeen ? "seen" : "missing", event.index, "");
      } else if (active.kind === "tool_use") {
        if (active.partialJson.length > 0) {
          try {
            const parsed: unknown = JSON.parse(active.partialJson);
            if (!isObject(parsed)) {
              add("SSE-TOOL-JSON", "FAIL", "tool_input_not_object", "JSON object", describe(parsed));
            } else {
              active.value.input = parsed;
            }
          } catch {
            add("SSE-TOOL-JSON", "FAIL", "tool_input_json_invalid", "complete JSON object", "invalid or incomplete JSON");
          }
        }
      }
      if (assembled !== null && Array.isArray(assembled.content)) assembled.content.push(active.value);
      active = null;
      return;
    }

    if (event.event === "message_delta") {
      if (active !== null) failLifecycle(event, "message_delta_with_open_block", "all content blocks stopped before message_delta", "content block still open");
      deltaSeen = true;
      const deltaField = checkField(data, "delta", "", isObject, "JSON object", event.index, "SSE-MESSAGE-DELTA");
      if (!deltaField.valid || !isObject(deltaField.value)) return;
      const delta = deltaField.value;
      const stopReason = checkField(delta, "stop_reason", "/delta", (value) => value === null || typeof value === "string" && value.length > 0, "string stop reason or intermediate null", event.index, "SSE-MESSAGE-DELTA");
      const stopSequence = checkField(delta, "stop_sequence", "/delta", (value) => value === null || typeof value === "string", "string or null", event.index, "SSE-MESSAGE-DELTA");
      if (assembled !== null) {
        if (stopReason.valid) assembled.stop_reason = stopReason.value;
        if (stopSequence.valid) assembled.stop_sequence = stopSequence.value;
      }
      if (stopReason.valid && typeof stopReason.value === "string") {
        const known = context.stopReasons.includes(stopReason.value);
        add("SSE-STOP", known ? "PASS" : "INDETERMINATE", known ? "stop_reason_known" : "unknown_stop_reason", "reason in selected protocol snapshot", known ? "known stop reason" : "unrecognized stop reason", event.index, "/delta/stop_reason");
        if (known && stopSequence.valid) {
          const valid = stopReason.value === "stop_sequence"
            ? typeof stopSequence.value === "string"
            : stopSequence.value === null;
          add("SSE-STOP-SEQUENCE", valid ? "PASS" : "FAIL", valid ? "stop_sequence_valid" : "unexpected_stop_sequence", "string for stop_sequence; otherwise null", describe(stopSequence.value), event.index, "/delta/stop_sequence");
        } else if (!known) {
          add("SSE-STOP-SEQUENCE", "INDETERMINATE", "stop_sequence_relation_unknown", "string when reason is stop_sequence; otherwise null", stopSequence.present ? describe(stopSequence.value) : "missing", event.index, stopSequence.present ? "/delta/stop_sequence" : "/delta", stopSequence.present ? undefined : "stop_sequence");
        }
      }
      const usageField = checkField(data, "usage", "", isObject, "JSON object", event.index, "SSE-USAGE");
      if (!usageField.valid || !isObject(usageField.value)) return;
      const outputTokens = checkField(usageField.value, "output_tokens", "/usage", isNonnegativeInteger, "nonnegative integer", event.index, "SSE-USAGE");
      if (assembled !== null) {
        if (isObject(assembled.usage) && outputTokens.valid) assembled.usage.output_tokens = outputTokens.value;
      }
      return;
    }
  };

  if (!Number.isSafeInteger(options.maxEvents) || options.maxEvents < 1 ||
      !Number.isSafeInteger(options.maxEventBytes) || options.maxEventBytes < 1 ||
      typeof options.completeCapture !== "boolean" || !(body instanceof Uint8Array)) {
    add("SSE-LIMIT", "BLOCKED", "invalid_sse_options", "positive safe integer limits and byte body", "invalid options or body", undefined, "", undefined, "environment");
    return { events, observations, message: null };
  }

  const hasInitialBom = body[0] === 0xef && body[1] === 0xbb && body[2] === 0xbf;
  const input = hasInitialBom ? body.subarray(3) : body;

  let lines: Uint8Array[] = [];
  let line: number[] = [];
  let lineLength = 0;
  let frameBytes = hasInitialBom ? 3 : 0;
  let frameOverflow = false;
  let halted = false;

  const dispatchFrame = (): void => {
    if (frameOverflow) {
      if (dispatchedCount >= options.maxEvents) {
        add("SSE-LIMIT", "BLOCKED", "event_count_limit_exceeded", `at most ${options.maxEvents} events`, "additional dispatched event", undefined, "", undefined, "environment");
        halted = true;
        return;
      }
      const index = dispatchedCount++;
      // The frame's JSON cannot be retained within the configured bound, so its event location is unavailable.
      add("SSE-LIMIT", "BLOCKED", "event_byte_limit_exceeded", `at most ${options.maxEventBytes} bytes per frame`, `oversized frame at dispatched index ${index} omitted from storage`, undefined, "", undefined, "environment");
      return;
    }
    if (lines.length === 0) return;
    const rawLines = lines;
    const decodedLines: string[] = [];
    let invalidUtf8 = false;
    for (const bytes of rawLines) {
      try {
        decodedLines.push(new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes));
      } catch {
        invalidUtf8 = true;
        decodedLines.push(new TextDecoder("utf-8", { ignoreBOM: true }).decode(bytes));
      }
    }
    let eventName = "message";
    const dataLines: string[] = [];
    for (const decodedLine of decodedLines) {
      if (decodedLine.startsWith(":")) continue;
      const separator = decodedLine.indexOf(":");
      const fieldName = separator < 0 ? decodedLine : decodedLine.slice(0, separator);
      let fieldValue = separator < 0 ? "" : decodedLine.slice(separator + 1);
      if (fieldValue.startsWith(" ")) fieldValue = fieldValue.slice(1);
      if (fieldName === "event") eventName = fieldValue;
      else if (fieldName === "data") dataLines.push(fieldValue);
    }
    if (dataLines.length === 0) return;
    if (dispatchedCount >= options.maxEvents) {
      add("SSE-LIMIT", "BLOCKED", "event_count_limit_exceeded", `at most ${options.maxEvents} events`, "additional dispatched event", undefined, "", undefined, "environment");
      halted = true;
      return;
    }
    const index = dispatchedCount++;
    const data = dataLines.join("\n");
    let value: unknown = null;
    let parsedJson = false;
    if (!invalidUtf8) {
      try {
        value = JSON.parse(data);
        parsedJson = true;
      } catch {
        add("SSE-JSON", "FAIL", "event_json_invalid", "valid JSON data", "malformed JSON");
      }
    } else {
      add("SSE-FRAMING", "FAIL", "invalid_utf8", "valid UTF-8 event fields", "malformed UTF-8 bytes");
    }
    const event: SseEvent = { index, event: eventName, data, value };
    events.push(event);
    if (invalidUtf8 || !parsedJson) {
      if (eventName === "error") {
        add("SSE-ERROR", "FAIL", "error_event_received", "successful message stream", "server error event received", undefined, "", undefined, "behavior");
      }
      return;
    }
    processEvent(event);
  };

  const finishLine = (terminatorBytes: number): void => {
    const blank = lineLength === 0;
    if (!frameOverflow && frameBytes + lineLength + terminatorBytes > options.maxEventBytes) {
      frameOverflow = true;
      lines = [];
      line = [];
    }
    frameBytes += lineLength + terminatorBytes;
    if (!frameOverflow && !blank) lines.push(Uint8Array.from(line));
    line = [];
    lineLength = 0;
    if (blank) {
      dispatchFrame();
      lines = [];
      frameBytes = 0;
      frameOverflow = false;
    }
  };

  for (let offset = 0; offset < input.byteLength && !halted; offset += 1) {
    const byte = input[offset]!;
    if (byte === 0x0a) {
      finishLine(1);
    } else if (byte === 0x0d) {
      const crlf = input[offset + 1] === 0x0a;
      finishLine(crlf ? 2 : 1);
      if (crlf) offset += 1;
    } else {
      lineLength += 1;
      if (!frameOverflow && frameBytes + lineLength <= options.maxEventBytes) line.push(byte);
      else {
        frameOverflow = true;
        lines = [];
        line = [];
      }
    }
  }

  if (!halted && (lineLength > 0 || lines.length > 0 || frameOverflow)) {
    const invalidCompletedLine = lines.some((completedLine) => {
      try {
        new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(completedLine);
        return false;
      } catch {
        return true;
      }
    });
    const tailState = incompleteUtf8(Uint8Array.from(line));
    if (invalidCompletedLine || tailState === "invalid") {
      add("SSE-FRAMING", "FAIL", "invalid_utf8", "valid UTF-8 trailing bytes", "malformed UTF-8 prefix", undefined);
    } else if (tailState === "incomplete") {
      add("SSE-FRAMING", options.completeCapture ? "FAIL" : "INDETERMINATE", "incomplete_utf8_tail", "complete UTF-8 sequence", options.completeCapture ? "truncated UTF-8 in complete capture" : "capture ended mid-codepoint", undefined);
    }
    add("SSE-FRAMING", options.completeCapture ? "FAIL" : "INDETERMINATE", "incomplete_trailing_frame", "blank-line event boundary", "unterminated event frame", undefined);
  }

  if (!halted && !errorTerminated) {
    if (!started) add("SSE-LIFECYCLE", options.completeCapture ? "FAIL" : "INDETERMINATE", "message_start_missing", "message_start event", "not observed");
    if (!deltaSeen) add("SSE-LIFECYCLE", options.completeCapture ? "FAIL" : "INDETERMINATE", "message_delta_missing", "message_delta event", "not observed");
    if (!stopped) add("SSE-LIFECYCLE", options.completeCapture ? "FAIL" : "INDETERMINATE", "message_stop_missing", "message_stop event", "not observed");
    if (active !== null) add("SSE-LIFECYCLE", options.completeCapture ? "FAIL" : "INDETERMINATE", "content_block_unfinished", "content_block_stop event", "content block remains open");
  }
  if (!options.completeCapture) {
    add("SSE-CAPTURE", "INDETERMINATE", "capture_incomplete", "complete capture", "capture may be partial", undefined, "", undefined, "environment");
  }
  return { events, observations, message: assembled };
}
