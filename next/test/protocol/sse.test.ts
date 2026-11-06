import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { summarize, type MessageValidationContext, type Observation } from "../../../scaffold/skills/anthropic-readiness/scripts/src/domain.ts";
import { validateSse } from "../../../scaffold/skills/anthropic-readiness/scripts/src/protocol/sse.ts";

const context: MessageValidationContext = {
  captureId: "sse-capture",
  requestedModel: "model-a",
  modelAliases: [],
  checkModelIdentity: true,
  stopReasons: ["end_turn", "stop_sequence", "tool_use", "max_tokens"],
};
const defaults = { completeCapture: true, maxEvents: 100, maxEventBytes: 16_384 };

function wireEvent(event: string, value: unknown, ending = "\n"): string {
  return `event: ${event}${ending}data: ${JSON.stringify(value)}${ending}${ending}`;
}

function start(id = "msg-1"): Record<string, unknown> {
  return {
    type: "message_start",
    message: {
      id,
      type: "message",
      role: "assistant",
      model: "model-a",
      content: [],
      stop_reason: null,
      stop_sequence: null,
      usage: { input_tokens: 3, output_tokens: 0 },
    },
  };
}

function textEvents(text: string): string {
  return (
    wireEvent("message_start", start()) +
    wireEvent("content_block_start", {
      type: "content_block_start",
      index: 0,
      content_block: { type: "text", text: "" },
    }) +
    wireEvent("content_block_delta", {
      type: "content_block_delta",
      index: 0,
      delta: { type: "text_delta", text },
    }) +
    wireEvent("content_block_stop", { type: "content_block_stop", index: 0 }) +
    wireEvent("message_delta", {
      type: "message_delta",
      delta: { stop_reason: "end_turn", stop_sequence: null },
      usage: { output_tokens: 1 },
    }) +
    wireEvent("message_stop", { type: "message_stop" })
  );
}

function run(body: string | Uint8Array, options: Partial<typeof defaults> = {}) {
  return validateSse(typeof body === "string" ? new TextEncoder().encode(body) : body, context, {
    ...defaults,
    ...options,
  });
}

function observation(
  result: { observations: readonly Observation[] },
  ruleId: string,
): Observation {
  const found = result.observations.find((item) => item.ruleId === ruleId);
  assert.ok(found, `expected ${ruleId} observation`);
  return found;
}

function fixture(name: string): Uint8Array {
  return readFileSync(
    new URL(`../../../tests/fixtures/contracts/core-1.0.0/${name}`, import.meta.url),
  );
}

test("valid reference stream dispatches events and assembles its message", () => {
  const result = validateSse(fixture("stream-valid.sse"), context, defaults);
  assert.equal(summarize(result.observations), "PASS");
  assert.equal(result.events.length, 6);
  assert.deepEqual(
    result.events.map((item) => item.index),
    [0, 1, 2, 3, 4, 5],
  );
  assert.deepEqual(result.message?.content, [{ type: "text", text: "Hello." }]);
  assert.equal(result.message?.stop_reason, "end_turn");
});

test("reference duplicate start and invalid index remain proven faults", () => {
  const duplicate = new TextDecoder().decode(fixture("stream-duplicate-start.sse"));
  const changedSecond = duplicate
    .replace('"id":"synthetic-message"', '"id":"first-message"')
    .replace('"id":"synthetic-message"', '"id":"second-message"');
  const duplicateResult = run(changedSecond, { completeCapture: false });
  assert.equal(summarize(duplicateResult.observations), "FAIL");
  assert.equal(duplicateResult.message?.id, "first-message");
  assert.ok(observation(duplicateResult, "SSE-LIFECYCLE").status === "FAIL");

  const indexResult = validateSse(fixture("stream-invalid-index.sse"), context, defaults);
  assert.equal(summarize(indexResult.observations), "FAIL");
  assert.ok(
    indexResult.observations.some((item) => item.reason === "content_index_not_sequential"),
  );
});

test("complete streams require a dispatched blank-line boundary at EOF", () => {
  const valid = new TextDecoder().decode(fixture("stream-valid.sse"));
  const unterminated = valid.trimEnd();
  const complete = run(unterminated, { completeCapture: true });
  assert.equal(summarize(complete.observations), "FAIL");
  assert.equal(observation(complete, "SSE-FRAMING").status, "FAIL");

  const interrupted = run(unterminated, { completeCapture: false });
  assert.equal(summarize(interrupted.observations), "INDETERMINATE");
  assert.equal(observation(interrupted, "SSE-FRAMING").status, "INDETERMINATE");

  const legacyTail = validateSse(fixture("stream-invalid-tail.sse"), context, defaults);
  assert.equal(summarize(legacyTail.observations), "FAIL");
});

test("preserves whitespace while assembling text split across events", () => {
  const result = run(
    textEvents("  first\n")
      .replace('"text":"  first\\n"', '"text":"  first"')
      .replace(
        wireEvent("content_block_stop", { type: "content_block_stop", index: 0 }),
        wireEvent("content_block_delta", {
          type: "content_block_delta",
          index: 0,
          delta: { type: "text_delta", text: " second " },
        }) + wireEvent("content_block_stop", { type: "content_block_stop", index: 0 }),
      ),
  );
  assert.equal(summarize(result.observations), "PASS");
  assert.deepEqual(result.message?.content, [{ type: "text", text: "  first second " }]);
});

test("assembles fragmented tool JSON only at block completion", () => {
  const body =
    wireEvent("message_start", start()) +
    wireEvent("content_block_start", {
      type: "content_block_start",
      index: 0,
      content_block: { type: "tool_use", id: "tool-1", name: "lookup", input: {} },
    }) +
    wireEvent("content_block_delta", {
      type: "content_block_delta",
      index: 0,
      delta: { type: "input_json_delta", partial_json: '{"city":' },
    }) +
    wireEvent("content_block_delta", {
      type: "content_block_delta",
      index: 0,
      delta: { type: "input_json_delta", partial_json: '"Oslo"}' },
    }) +
    wireEvent("content_block_stop", { type: "content_block_stop", index: 0 }) +
    wireEvent("message_delta", {
      type: "message_delta",
      delta: { stop_reason: "tool_use", stop_sequence: null },
      usage: { output_tokens: 2 },
    }) +
    wireEvent("message_stop", { type: "message_stop" });
  const result = run(body);
  assert.equal(summarize(result.observations), "PASS");
  assert.deepEqual(result.message?.content, [
    { type: "tool_use", id: "tool-1", name: "lookup", input: { city: "Oslo" } },
  ]);
});

test("keeps assembled usage separate from the captured message_start event", () => {
  const body = textEvents("Hello.").replace('"output_tokens":1', '"output_tokens":17');
  const result = run(body);
  assert.equal(summarize(result.observations), "PASS");
  assert.equal(
    (result.events[0]?.value as { message: { usage: { output_tokens: number } } }).message.usage
      .output_tokens,
    0,
  );
  assert.equal((result.message?.usage as { output_tokens: number }).output_tokens, 17);
});

test("an incomplete capture remains inconclusive even when message_stop was observed", () => {
  const result = run(textEvents("Hello."), { completeCapture: false });
  assert.equal(observation(result, "SSE-CAPTURE").status, "INDETERMINATE");
  assert.equal(summarize(result.observations), "INDETERMINATE");

  const knownFault = run(
    wireEvent("message_start", start()) + wireEvent("message_start", start()),
    { completeCapture: false },
  );
  assert.equal(summarize(knownFault.observations), "FAIL");
});

test("wrong envelope types and known delta kinds fail at event locations", () => {
  const wrongType = run(wireEvent("message_start", { ...start(), type: "ping" }));
  const mismatch = wrongType.observations.find(
    (item) => item.reason === "event_data_type_mismatch",
  );
  assert.equal(mismatch?.status, "FAIL");
  assert.equal(mismatch?.location?.eventIndex, 0);
  assert.equal(mismatch?.location?.captureId, context.captureId);

  const nullEnvelope = run(wireEvent("ping", null));
  const nullObservation = nullEnvelope.observations.find(
    (item) => item.reason === "event_data_not_object",
  );
  assert.equal(nullObservation?.status, "FAIL");
  assert.equal(nullObservation?.location?.pointer, "");

  const wrongKind = run(
    wireEvent("message_start", start()) +
      wireEvent("content_block_start", {
        type: "content_block_start",
        index: 0,
        content_block: { type: "text", text: "" },
      }) +
      wireEvent("content_block_delta", {
        type: "content_block_delta",
        index: 0,
        delta: { type: "input_json_delta", partial_json: "{}" },
      }),
  );
  assert.ok(
    wrongKind.observations.some(
      (item) => item.reason === "delta_wrong_block_kind" && item.status === "FAIL",
    ),
  );

  const missingDeltaField = run(
    wireEvent("message_start", start()) +
      wireEvent("content_block_start", {
        type: "content_block_start",
        index: 0,
        content_block: { type: "text", text: "" },
      }) +
      wireEvent("content_block_delta", {
        type: "content_block_delta",
        index: 0,
        delta: { type: "text_delta" },
      }),
  );
  const missingText = missingDeltaField.observations.find(
    (item) => item.reason === "missing_field" && item.location?.missingKey === "text",
  );
  assert.equal(missingText?.status, "FAIL");
  assert.equal(missingText?.location?.eventIndex, 2);
});

test("unknown events, blocks, and deltas remain inconclusive", () => {
  const unknownEvent = wireEvent("future_event", { type: "future_event", value: 1 });
  const result = run(unknownEvent, { completeCapture: false });
  assert.equal(observation(result, "SSE-EXTENSION").status, "INDETERMINATE");
  assert.equal(summarize(result.observations), "INDETERMINATE");

  const unknownBlock = run(
    wireEvent("message_start", start()) +
      wireEvent("content_block_start", {
        type: "content_block_start",
        index: 0,
        content_block: { type: "future_block", payload: 1 },
      }) +
      wireEvent("content_block_stop", { type: "content_block_stop", index: 0 }) +
      wireEvent("message_delta", {
        type: "message_delta",
        delta: { stop_reason: "end_turn", stop_sequence: null },
        usage: { output_tokens: 1 },
      }) +
      wireEvent("message_stop", { type: "message_stop" }),
  );
  assert.ok(
    unknownBlock.observations.some(
      (item) => item.reason === "unknown_block_type" && item.status === "INDETERMINATE",
    ),
  );
  assert.equal(summarize(unknownBlock.observations), "INDETERMINATE");

  const unknownDelta = run(
    wireEvent("message_start", start()) +
      wireEvent("content_block_start", {
        type: "content_block_start",
        index: 0,
        content_block: { type: "text", text: "" },
      }) +
      wireEvent("content_block_delta", {
        type: "content_block_delta",
        index: 0,
        delta: { type: "future_delta", data: "x" },
      }) +
      wireEvent("content_block_stop", { type: "content_block_stop", index: 0 }) +
      wireEvent("message_delta", {
        type: "message_delta",
        delta: { stop_reason: "end_turn", stop_sequence: null },
        usage: { output_tokens: 1 },
      }) +
      wireEvent("message_stop", { type: "message_stop" }),
  );
  assert.ok(
    unknownDelta.observations.some(
      (item) => item.reason === "unknown_delta_type" && item.status === "INDETERMINATE",
    ),
  );
  assert.equal(summarize(unknownDelta.observations), "INDETERMINATE");
});

test("ping is recognized without changing message assembly", () => {
  const result = run(wireEvent("ping", { type: "ping" }) + textEvents("Hello."));
  assert.equal(summarize(result.observations), "PASS");
  assert.equal(result.events[0]?.event, "ping");
  assert.deepEqual(result.message?.content, [{ type: "text", text: "Hello." }]);
});

test("known lifecycle order, duplicate starts, late events, and partial faults are retained", () => {
  const base = textEvents("Hello.");
  const duplicateStart = run(
    base.replace(
      wireEvent("message_start", start()),
      wireEvent("message_start", start()) + wireEvent("message_start", start()),
    ),
    { completeCapture: false },
  );
  assert.equal(summarize(duplicateStart.observations), "FAIL");
  assert.equal(duplicateStart.message?.id, "msg-1");

  const afterStop = run(base + wireEvent("ping", { type: "ping" }));
  assert.ok(
    afterStop.observations.some(
      (item) => item.reason === "event_after_message_stop" && item.status === "FAIL",
    ),
  );

  const partialWithDuplicate = run(
    wireEvent("message_start", start()) + wireEvent("message_start", start()),
    { completeCapture: false },
  );
  assert.equal(summarize(partialWithDuplicate.observations), "FAIL");
});

test("supports BOM, comments, CR/CRLF and multiline data fields", () => {
  const message = JSON.stringify(start()).replace(',"message":', ',\n"message":');
  const split = message.indexOf("\n");
  const body = `\uFEFF: keepalive\r\nevent: message_start\rdata: ${message.slice(0, split)}\ndata: ${message.slice(split + 1)}\r\n\r\n`;
  const result = run(body, { completeCapture: false });
  assert.equal(result.events[0]?.event, "message_start");
  assert.equal(result.events[0]?.data, message);
  assert.equal(observation(result, "SSE-LIFECYCLE").status, "INDETERMINATE");

  const leadingBom = run(`\uFEFF${wireEvent("ping", { type: "ping" })}`, {
    completeCapture: false,
  });
  assert.equal(leadingBom.events[0]?.event, "ping");
});

test("only consumes a BOM at absolute input offset zero", () => {
  const result = run(`\n\uFEFFevent: ping\ndata: {"type":"ping"}\n\n`, { completeCapture: false });
  assert.ok(
    result.observations.some(
      (item) => item.reason === "unknown_event" && item.status === "INDETERMINATE",
    ),
  );
});

test("rejects malformed JSON and invalid UTF-8 without producing a passing message", () => {
  const malformed = run("event: message_start\ndata: {bad json}\n\n");
  assert.equal(observation(malformed, "SSE-JSON").status, "FAIL");
  assert.equal(observation(malformed, "SSE-JSON").location, undefined);
  assert.equal(malformed.events[0]?.value, null);

  const invalidPrefix = new Uint8Array([
    ...new TextEncoder().encode("event: message_start\ndata: "),
    0xe2,
    0x28,
    0xa1,
    ...new TextEncoder().encode("\n\n"),
  ]);
  const invalid = run(invalidPrefix, { completeCapture: false });
  const invalidUtf8 = invalid.observations.find((item) => item.reason === "invalid_utf8");
  assert.equal(invalidUtf8?.status, "FAIL");
  assert.equal(invalidUtf8?.location, undefined);

  const incomplete = new Uint8Array([
    ...new TextEncoder().encode('event: message_start\ndata: {"type":"message_start","message":"'),
    0xe2,
  ]);
  const truncated = run(incomplete, { completeCapture: false });
  assert.ok(
    truncated.observations.some(
      (item) => item.reason === "incomplete_utf8_tail" && item.status === "INDETERMINATE",
    ),
  );

  const malformedCompletedLine = new Uint8Array([
    ...new TextEncoder().encode('event: ping\ndata: {"type":"ping"}\n'),
    0xff,
    ...new TextEncoder().encode("\n"),
  ]);
  const malformedTail = run(malformedCompletedLine, { completeCapture: false });
  assert.ok(
    malformedTail.observations.some(
      (item) => item.reason === "invalid_utf8" && item.status === "FAIL",
    ),
  );
});

test("bounds event count and event bytes and validates option limits", () => {
  const invalidOptions = validateSse(new Uint8Array(), context, {
    completeCapture: true,
    maxEvents: 0,
    maxEventBytes: 100,
  });
  assert.equal(summarize(invalidOptions.observations), "BLOCKED");
  assert.equal(observation(invalidOptions, "SSE-LIMIT").dimension, "environment");

  const overlong = run(wireEvent("ping", { type: "ping", padding: "x".repeat(100) }), {
    maxEventBytes: 32,
  });
  assert.ok(
    overlong.observations.some(
      (item) => item.reason === "event_byte_limit_exceeded" && item.status === "BLOCKED",
    ),
  );
  assert.equal(observation(overlong, "SSE-LIMIT").dimension, "environment");
  assert.equal(overlong.events.length, 0);

  const tooMany = run(wireEvent("ping", { type: "ping" }) + wireEvent("ping", { type: "ping" }), {
    maxEvents: 1,
  });
  assert.ok(
    tooMany.observations.some(
      (item) => item.reason === "event_count_limit_exceeded" && item.status === "BLOCKED",
    ),
  );
  assert.equal(tooMany.events.length, 1);
  assert.equal(summarize(tooMany.observations), "BLOCKED");
});

test("validates message_start shape and error events without fabricating a message", () => {
  const badStart = start();
  (badStart.message as Record<string, unknown>).content = [{ type: "text", text: "unexpected" }];
  const invalid = run(wireEvent("message_start", badStart), { completeCapture: false });
  assert.ok(
    invalid.observations.some(
      (item) => item.reason === "initial_message_content_not_empty" && item.status === "FAIL",
    ),
  );

  const error = run(
    wireEvent("error", { type: "error", error: { type: "overloaded_error", message: "Busy" } }),
  );
  assert.equal(error.message, null);
  assert.ok(error.events.length === 1);
  assert.ok(
    error.observations.some((item) => item.dimension === "behavior" && item.status === "FAIL"),
  );

  const malformedError = run("event: error\ndata: {not-json}\n\n", { completeCapture: false });
  assert.ok(
    malformedError.observations.some(
      (item) => item.dimension === "behavior" && item.status === "FAIL",
    ),
  );
});

test("a valid error event terminates success-path expectations without a protocol failure", () => {
  const beforeStart = run(
    wireEvent("error", { type: "error", error: { custom: "service detail" } }),
  );
  assert.equal(observation(beforeStart, "SSE-ERROR").status, "INDETERMINATE");
  assert.ok(
    beforeStart.observations.some(
      (item) => item.dimension === "behavior" && item.status === "FAIL",
    ),
  );
  assert.ok(
    !beforeStart.observations.some(
      (item) => item.dimension === "protocol" && item.status === "FAIL",
    ),
  );

  const duringMessage = run(
    wireEvent("message_start", start()) +
      wireEvent("content_block_start", {
        type: "content_block_start",
        index: 0,
        content_block: { type: "text", text: "" },
      }) +
      wireEvent("error", { type: "error", error: { custom: "service detail" } }),
  );
  assert.ok(
    duringMessage.observations.some(
      (item) => item.dimension === "behavior" && item.status === "FAIL",
    ),
  );
  assert.ok(
    !duringMessage.observations.some(
      (item) => item.dimension === "protocol" && item.status === "FAIL",
    ),
  );

  const contentAfterError = run(
    wireEvent("error", { type: "error", error: {} }) + wireEvent("message_start", start()),
  );
  assert.ok(
    contentAfterError.observations.some(
      (item) => item.reason === "event_after_error_termination" && item.status === "FAIL",
    ),
  );
});

test("empty tool JSON assembly preserves the initial object input", () => {
  const body =
    wireEvent("message_start", start()) +
    wireEvent("content_block_start", {
      type: "content_block_start",
      index: 0,
      content_block: { type: "tool_use", id: "tool-1", name: "lookup", input: {} },
    }) +
    wireEvent("content_block_stop", { type: "content_block_stop", index: 0 }) +
    wireEvent("message_delta", {
      type: "message_delta",
      delta: { stop_reason: "tool_use", stop_sequence: null },
      usage: { output_tokens: 1 },
    }) +
    wireEvent("message_stop", { type: "message_stop" });
  const result = run(body);
  assert.equal(summarize(result.observations), "PASS");
  assert.deepEqual(result.message?.content, [
    { type: "tool_use", id: "tool-1", name: "lookup", input: {} },
  ]);
});

test("unknown frame tail cannot erase an observed lifecycle fault", () => {
  const valid = textEvents("Hello.");
  const duplicateStart = valid.replace(
    wireEvent("message_start", start()),
    wireEvent("message_start", start()) + wireEvent("message_start", start()),
  );
  const partial = run(duplicateStart.slice(0, duplicateStart.lastIndexOf("\n\n")), {
    completeCapture: false,
  });
  assert.equal(summarize(partial.observations), "FAIL");
  assert.ok(
    partial.observations.some(
      (item) => item.reason === "duplicate_message_start" && item.status === "FAIL",
    ),
  );
});

test("multiple message_delta updates are allowed and preserve original cumulative usage", () => {
  const end = wireEvent("message_stop", { type: "message_stop" });
  const extra = wireEvent("message_delta", {
    type: "message_delta",
    delta: { stop_reason: "end_turn", stop_sequence: null },
    usage: { output_tokens: 7 },
  });
  const result = run(textEvents("Hello").replace(end, extra + end));
  assert.equal(summarize(result.observations), "PASS");
  assert.equal((result.message?.usage as Record<string, unknown>).output_tokens, 7);
  const deltas = result.events.filter((event) => event.event === "message_delta");
  assert.equal(deltas.length, 2);
  assert.equal((deltas[0]!.value as { usage: { output_tokens: number } }).usage.output_tokens, 1);
});

test("intermediate null stop reasons can precede the final message_delta", () => {
  const before = wireEvent("message_delta", {
    type: "message_delta",
    delta: { stop_reason: null, stop_sequence: null },
    usage: { output_tokens: 0 },
  });
  const marker = wireEvent("message_delta", {
    type: "message_delta",
    delta: { stop_reason: "end_turn", stop_sequence: null },
    usage: { output_tokens: 1 },
  });
  const result = run(textEvents("Hello").replace(marker, before + marker));
  assert.equal(summarize(result.observations), "PASS");
  assert.equal(result.message?.stop_reason, "end_turn");
});

test("message_stop requires the final message_delta to carry a stop reason", () => {
  const valid = textEvents("Hello.");
  const invalid = valid.replace('"stop_reason":"end_turn"', '"stop_reason":null');
  const result = run(invalid);
  const finding = result.observations.find((item) => item.reason === "final_stop_reason_missing");
  assert.equal(finding?.status, "FAIL");
  assert.equal(finding?.location?.eventIndex, 4);
  assert.equal(finding?.location?.pointer, "/delta/stop_reason");

  const partial = run(invalid.slice(0, invalid.lastIndexOf("event: message_stop")), {
    completeCapture: false,
  });
  assert.equal(summarize(partial.observations), "INDETERMINATE");
});

test("final usage updates overwrite supplied counters without mutating raw events", () => {
  const body = textEvents("Hello.").replace(
    '"usage":{"output_tokens":1}',
    '"usage":{"input_tokens":9,"output_tokens":1,"cache_creation_input_tokens":4,"cache_read_input_tokens":7}',
  );
  const result = run(body);
  assert.equal(summarize(result.observations), "PASS");
  assert.deepEqual(result.message?.usage, {
    input_tokens: 9,
    output_tokens: 1,
    cache_creation_input_tokens: 4,
    cache_read_input_tokens: 7,
  });
  assert.deepEqual(
    (result.events.at(-2)?.value as { usage: Record<string, unknown> }).usage,
    { input_tokens: 9, output_tokens: 1, cache_creation_input_tokens: 4, cache_read_input_tokens: 7 },
  );
  assert.deepEqual(
    (result.events[0]?.value as { message: { usage: Record<string, unknown> } }).message.usage,
    { input_tokens: 3, output_tokens: 0 },
  );
});

test("whitespace around JSON null still exposes a proven known-event envelope fault", () => {
  const stop = wireEvent("message_stop", { type: "message_stop" });
  const result = run(textEvents("Hello").replace(stop, "event: ping\ndata:  null  \n\n" + stop));
  assert.equal(summarize(result.observations), "FAIL");
  assert.ok(result.observations.some((item) => item.reason === "event_data_not_object"));
});
