import assert from "node:assert/strict";
import test from "node:test";
import { createServer } from "node:http";
import { createPlan, executePlan } from "../../skills/anthropic-readiness/scripts/src/runner/assessment.ts";
import { checkResponseContract } from "../../skills/anthropic-readiness/scripts/src/runner/probes.ts";
import { validateSse } from "../../skills/anthropic-readiness/scripts/src/protocol/sse.ts";

test("documented core includes count tokens, negative cases, and a streamed tool round trip", () => {
  const plan = createPlan({
    endpoint: "https://example.invalid/v1",
    model: "example-model",
    profiles: ["anthropic-core"],
  });
  assert.ok(plan.cases.some((item) => item.id === "ANT-COUNT-001"));
  assert.ok(plan.cases.some((item) => item.id === "ANT-ERROR-MISSING-001"));
  assert.equal(plan.cases.find((item) => item.id === "ANT-TOOL-SSE-LOOP-001")?.maxRequests, 2);
  assert.ok(plan.plannedRequests > 6);
});

test("one-token request contract rejects reported output usage above the requested maximum", () => {
  const message = {
    stop_reason: "max_tokens",
    content: [{ type: "text", text: Array.from({ length: 50 }, (_, index) => index + 1).join("\n") }],
    usage: { input_tokens: 2, output_tokens: 100 },
  };
  for (const id of ["ANT-MAX-TOKENS-001", "ANT-MAX-TOKENS-SSE-001"]) {
    const finding = checkResponseContract(id, message, `capture-${id}`, 1).find(
      (item) => item.ruleId === "OUTPUT-TOKEN-LIMIT",
    );
    assert.equal(finding?.status, "FAIL", id);
    assert.equal(finding?.expected, "usage.output_tokens <= requested max_tokens (1)");
    assert.match(finding?.actual ?? "", /requested 1, reported 100/u);
    assert.equal(finding?.location?.pointer, "/usage/output_tokens");
  }
  const control = checkResponseContract("ANT-MAX-TOKENS-001", {
    ...message,
    usage: { input_tokens: 2, output_tokens: 1 },
  }, "normal", 1);
  assert.equal(control.find((item) => item.ruleId === "OUTPUT-TOKEN-LIMIT")?.status, "PASS");
});

test("documented thinking streams retain text and signature in the assembled message", () => {
  const result = validateSse(Buffer.from(thinkingStream()), context, {
    completeCapture: true,
    maxEvents: 100,
    maxEventBytes: 8192,
  });
  assert.deepEqual(result.message?.content, [
    {
      type: "thinking",
      thinking: "fixture reasoning",
      signature: "fixture-signature",
    },
    { type: "text", text: "483" },
  ]);
  assert.ok(result.observations.every((item) => item.status === "PASS"));
  const malformed = validateSse(Buffer.from(thinkingStream(false)), context, {
    completeCapture: true,
    maxEvents: 100,
    maxEventBytes: 8192,
  });
  assert.ok(
    malformed.observations.some(
      (item) => item.ruleId === "SSE-THINKING-SIGNATURE" && item.status === "FAIL",
    ),
  );
});

function thinkingStream(signature = true): string {
  return [
    frame("message_start", { message: { ...message([]), stop_reason: null } }),
    frame("content_block_start", {
      index: 0,
      content_block: { type: "thinking", thinking: "", signature: "" },
    }),
    frame("content_block_delta", {
      index: 0,
      delta: { type: "thinking_delta", thinking: "fixture reasoning" },
    }),
    ...(signature
      ? [
          frame("content_block_delta", {
            index: 0,
            delta: { type: "signature_delta", signature: "fixture-signature" },
          }),
        ]
      : []),
    frame("content_block_stop", { index: 0 }),
    ...textFrames("483", 1),
    ...finishFrames(),
  ].join("");
}

const context = {
  captureId: "synthetic",
  requestedModel: "example-model",
  modelAliases: [],
  checkModelIdentity: true,
  stopReasons: ["end_turn", "tool_use"],
};
function message(content: object[], stop = "end_turn", sequence: string | null = null, usage = {}) {
  return {
    id: "msg_fixture",
    type: "message",
    role: "assistant",
    model: "example-model",
    content,
    stop_reason: stop,
    stop_sequence: sequence,
    usage: { input_tokens: 2, output_tokens: 3, ...usage },
  };
}
function frame(type: string, fields: object = {}): string {
  return `event: ${type}\ndata: ${JSON.stringify({ type, ...fields })}\n\n`;
}
function textFrames(text: string, index = 0): string[] {
  return [
    frame("content_block_start", {
      index,
      content_block: { type: "text", text: "" },
    }),
    frame("content_block_delta", {
      index,
      delta: { type: "text_delta", text },
    }),
    frame("content_block_stop", { index }),
  ];
}
function finishFrames(stop = "end_turn", sequence: string | null = null, outputTokens = 3): string[] {
  return [
    frame("message_delta", {
      delta: { stop_reason: stop, stop_sequence: sequence },
      usage: { output_tokens: outputTokens },
    }),
    frame("message_stop"),
  ];
}

const expandedProfiles = [
  "anthropic-core",
  "anthropic-version-2026",
  "anthropic-prefill",
  "anthropic-structured",
  "anthropic-thinking",
  "anthropic-vision",
  "anthropic-pdf",
  "anthropic-citations",
  "anthropic-cache",
];
const validError = {
  type: "error",
  error: { type: "invalid_request_error", message: "invalid fixture request" },
};
const weather = (city = "Hanoi") => ({
  type: "tool_use",
  id: `toolu_${city}`,
  name: "get_weather",
  input: { city },
});

test("all documented presets execute their bounded synthetic exchanges", async (t) => {
  const requestCounts = new Map<string, number>();
  const sequence = [
    "ANT-MESSAGE-001",
    "ANT-TEXT-SSE-001",
    "ANT-TEXT-SSE-002",
    "ANT-TOOL-FORCED-001",
    "ANT-TOOL-LOOP-001",
    "ANT-TOOL-LOOP-001",
    "ANT-SYSTEM-BLOCKS-001",
    "ANT-HISTORY-001",
    "ANT-HISTORY-001",
    "ANT-STOP-SEQUENCE-001",
    "ANT-STOP-SEQUENCE-SSE-001",
    "ANT-MAX-TOKENS-001",
    "ANT-MAX-TOKENS-SSE-001",
    "ANT-TOOL-NONE-001",
    "ANT-TOOL-ANY-001",
    "ANT-TOOL-SSE-LOOP-001",
    "ANT-TOOL-SSE-LOOP-001",
    "ANT-TOOL-PARALLEL-001",
    "ANT-TOOL-PARALLEL-001",
    "ANT-TOOL-RESULT-ERROR-001",
    "ANT-TOOL-RESULT-ERROR-001",
    "ANT-COUNT-001",
    "ANT-COUNT-TOOLS-001",
    "ANT-ERROR-MISSING-001",
    "ANT-ERROR-ROLE-001",
    "ANT-ERROR-TOOL-ID-001",
    "ANT-COUNT-ERROR-001",
    "ANT-ERROR-SAMPLING-001",
    "ANT-ERROR-ASSISTANT-DOCUMENT-001",
    "ANT-ERROR-USER-CITATION-001",
    "ANT-PREFILL-001",
    "ANT-TOOL-STRICT-001",
    "ANT-STRUCTURED-001",
    "ANT-STRUCTURED-SSE-001",
    "ANT-THINKING-001",
    "ANT-THINKING-SSE-001",
    "ANT-VISION-001",
    "ANT-PDF-001",
    "ANT-DOCUMENT-CITATION-001",
    "ANT-CACHE-001",
    "ANT-CACHE-001",
  ];
  let requests = 0;
  let cachedRequest: unknown;
  const endpoint = await listen(t, async (request, response) => {
    const id = sequence[requests++];
    assert.ok(id, "unexpected request");
    const attempt = (requestCounts.get(id) ?? 0) + 1;
    requestCounts.set(id, attempt);
    assert.equal(request.headers["anthropic-version"], "2026-10-21");
    const body = await readBody(request);
    const isCount = id.startsWith("ANT-COUNT-");
    const isStream = id.includes("-SSE-");
    assert.equal(request.url, isCount ? "/proxy/v1/messages/count_tokens" : "/proxy/v1/messages");
    assert.equal(body.stream === true, isStream, id);
    response.setHeader("content-type", isStream ? "text/event-stream" : "application/json");

    if (id.includes("-ERROR-") && id !== "ANT-TOOL-RESULT-ERROR-001") {
      if (id === "ANT-COUNT-ERROR-001") assert.equal(body.messages, undefined);
      if (id === "ANT-ERROR-MISSING-001") assert.equal(body.max_tokens, undefined);
      if (id === "ANT-ERROR-ROLE-001") assert.equal(body.messages[0].role, "system");
      if (id === "ANT-ERROR-TOOL-ID-001")
        assert.equal(body.messages[2].content[0].tool_use_id, "toolu_wrong");
      if (id === "ANT-ERROR-SAMPLING-001") assert.equal(body.temperature, 1);
      if (id === "ANT-ERROR-ASSISTANT-DOCUMENT-001")
        assert.equal(body.messages[1].content[0].type, "document");
      if (id === "ANT-ERROR-USER-CITATION-001")
        assert.equal(body.messages[0].content[1].citations.length, 1);
      response.statusCode = 400;
      response.end(JSON.stringify(validError));
      return;
    }
    if (isCount) {
      assert.equal(body.max_tokens, undefined);
      assert.equal(body.stream, undefined);
      if (id === "ANT-COUNT-TOOLS-001") assert.equal(body.tools[0].name, "get_weather");
      response.end('{"input_tokens":42}');
      return;
    }

    let reply = "HELLO";
    let stop = "end_turn";
    let stopSequence: string | null = null;
    let toolCalls: ReturnType<typeof weather>[] = [];
    let usage = {};
    if (id === "ANT-TEXT-SSE-002") reply = "1 2 3 4 5";
    if (id === "ANT-SYSTEM-BLOCKS-001") {
      assert.equal(body.system[0].type, "text");
      assert.equal(body.messages[0].content.length, 2);
    }
    if (id === "ANT-HISTORY-001" && attempt === 2) {
      const nonce = String(body.messages[0].content).match(/[\da-f]{8}(?:-[\da-f-]+){4}/u)?.[0];
      assert.ok(nonce);
      assert.equal(body.messages[1].role, "assistant");
      assert.equal(body.messages[1].content[0].text, "HELLO");
      assert.ok(!String(body.messages[2].content).includes(nonce));
      reply = nonce;
    }
    if (id.includes("-STOP-SEQUENCE-")) {
      stop = "stop_sequence";
      stopSequence = "ZEBRASTOP";
      assert.deepEqual(body.stop_sequences, [stopSequence]);
    }
    if (id.includes("-MAX-TOKENS-")) {
      assert.equal(body.max_tokens, 1);
      stop = "max_tokens";
      reply = "1";
      usage = { output_tokens: 1 };
    }
    if (id === "ANT-TOOL-NONE-001") assert.equal(body.tool_choice.type, "none");
    if (id === "ANT-TOOL-ANY-001") {
      assert.deepEqual(body.tool_choice, {
        type: "any",
        disable_parallel_tool_use: true,
      });
    }
    if (id === "ANT-TOOL-STRICT-001") {
      assert.equal(body.tools[0].strict, true);
      assert.equal(body.tools[0].input_schema.additionalProperties, false);
    }
    if (id.startsWith("ANT-TOOL-") && id !== "ANT-TOOL-NONE-001") {
      if (attempt === 1) {
        stop = "tool_use";
        toolCalls = id === "ANT-TOOL-PARALLEL-001" ? [weather("Oslo"), weather()] : [weather()];
      } else {
        const history = body.messages[1].content;
        const results = body.messages[2].content;
        assert.equal(history.length, results.length);
        assert.deepEqual(
          new Set(results.map((item: { tool_use_id: string }) => item.tool_use_id)),
          new Set(history.map((item: { id: string }) => item.id)),
        );
        if (id === "ANT-TOOL-RESULT-ERROR-001") assert.equal(results[0].is_error, true);
        reply = results
          .map((item: { content: string }) => {
            const value = JSON.parse(item.content);
            return value.verification_token ?? value.recovery_token;
          })
          .join(" ");
      }
    }
    if (id === "ANT-PREFILL-001") {
      assert.equal(body.messages.at(-1).role, "assistant");
      reply = "WORLD";
    }
    if (id.startsWith("ANT-STRUCTURED-")) {
      assert.equal(body.output_config.format.type, "json_schema");
      reply = '{"greeting":"HELLO"}';
    }
    if (id.startsWith("ANT-THINKING-")) {
      assert.equal(body.thinking.type, "adaptive");
      response.end(
        isStream
          ? thinkingStream()
          : JSON.stringify(
              message([
                {
                  type: "thinking",
                  thinking: "",
                  signature: "fixture-signature",
                },
                { type: "text", text: "483" },
              ]),
            ),
      );
      return;
    }
    if (id === "ANT-VISION-001" || id === "ANT-PDF-001") {
      const source = body.messages[0].content[0].source;
      assert.equal(source.type, "base64");
      const bytes = Buffer.from(source.data, "base64");
      if (id === "ANT-VISION-001") {
        assert.equal(bytes.subarray(1, 4).toString(), "PNG");
        reply = "RED";
      } else {
        assert.match(bytes.toString(), /^%PDF-1\.4[\s\S]*\(ORCHID\)/u);
        reply = "ORCHID";
      }
    }
    if (id === "ANT-DOCUMENT-CITATION-001") {
      const document = body.messages[0].content[0];
      assert.equal(document.citations.enabled, true);
      const cited = "purple bridge";
      const start = String(document.source.data).indexOf(cited);
      response.end(
        JSON.stringify(
          message([
            {
              type: "text",
              text: "It is purple.",
              citations: [
                {
                  type: "char_location",
                  document_index: 0,
                  cited_text: cited,
                  start_char_index: start,
                  end_char_index: start + cited.length,
                },
              ],
            },
          ]),
        ),
      );
      return;
    }
    if (id === "ANT-CACHE-001") {
      assert.equal(body.system[1].cache_control.type, "ephemeral");
      if (attempt === 1) cachedRequest = body;
      else assert.deepEqual(body, cachedRequest);
      usage =
        attempt === 1 ? { cache_creation_input_tokens: 5200 } : { cache_read_input_tokens: 5200 };
    }
    if (isStream) {
      response.end(
        [
          frame("message_start", {
            message: { ...message([]), stop_reason: null },
          }),
          ...(toolCalls.length ? toolFrames() : textFrames(reply)),
          ...finishFrames(stop, stopSequence, id.includes("-MAX-TOKENS-") ? 1 : 3),
        ].join(""),
      );
    } else {
      response.end(
        JSON.stringify(
          message(
            toolCalls.length ? toolCalls : [{ type: "text", text: reply }],
            stop,
            stopSequence,
            usage,
          ),
        ),
      );
    }
  });
  const plan = createPlan({
    endpoint,
    model: "example-model",
    profiles: expandedProfiles,
    apiVersion: "2026-10-21",
  });
  const result = await executePlan(plan, { allowLive: true });
  assert.deepEqual(
    result.cases
      .filter((item) => item.status !== "PASS")
      .map(({ id, observations }) => [id, observations.filter((item) => item.status !== "PASS")]),
    [],
  );
  assert.equal(result.status, "PASS");
  assert.equal(result.attemptsStarted, sequence.length);
  assert.equal(plan.plannedRequests, sequence.length);
  assert.equal(result.cases.length, new Set(sequence).size);
});

test("bad errors and counts fail without masking blocked or partial responses", async (t) => {
  let status = 400;
  let payload = validError as unknown;
  const endpoint = await listen(t, async (_request, response) => {
    response.statusCode = status;
    response.setHeader("content-type", "application/json");
    response.end(JSON.stringify(payload));
  });
  const plan = createPlan({
    endpoint,
    model: "example-model",
    profiles: ["anthropic-errors"],
  });
  const run = () => executePlan(plan, { allowLive: true });
  assert.equal((await run()).status, "PASS");
  const partial = await executePlan(
    createPlan({
      endpoint,
      model: "example-model",
      profiles: ["anthropic-errors"],
      maxBytes: 10,
    }),
    { allowLive: true },
  );
  assert.equal(partial.status, "INDETERMINATE");
  assert.ok(partial.cases.every((item) => item.protocolStatus === "INDETERMINATE"));
  payload = { type: "error", error: { type: "invalid_request_error" } };
  const malformed = await run();
  assert.equal(malformed.status, "FAIL");
  assert.deepEqual(
    malformed.cases[0]?.observations.find((item) => item.ruleId === "ERROR-MESSAGE")?.location,
    {
      captureId: malformed.cases[0]?.captures[0]?.id,
      pointer: "/error",
      missingKey: "message",
    },
  );
  status = 200;
  assert.equal((await run()).cases[0]?.observations[0]?.reason, "invalid_request_accepted");
  status = 401;
  assert.equal((await run()).status, "BLOCKED");
  status = 200;
  payload = { input_tokens: "42" };
  const count = await executePlan(
    createPlan({
      endpoint,
      model: "example-model",
      profiles: ["anthropic-count"],
    }),
    { allowLive: true },
  );
  assert.equal(count.status, "FAIL");
  assert.equal(
    count.cases[0]?.observations.find((item) => item.ruleId === "COUNT-INPUT")?.location?.pointer,
    "/input_tokens",
  );
});

test("new-version breaking probes require explicit selection of the matching version", () => {
  assert.throws(
    () =>
      createPlan({
        endpoint: "https://example.invalid",
        model: "example-model",
        profiles: ["anthropic-version-2026"],
      }),
    /profile_requires_api_version/u,
  );
});

function toolFrames(): string[] {
  const { input: _, ...block } = weather();
  return [
    frame("content_block_start", {
      index: 0,
      content_block: { ...block, input: {} },
    }),
    frame("content_block_delta", {
      index: 0,
      delta: { type: "input_json_delta", partial_json: '{"city":' },
    }),
    frame("content_block_delta", {
      index: 0,
      delta: { type: "input_json_delta", partial_json: '"Hanoi"}' },
    }),
    frame("content_block_stop", { index: 0 }),
  ];
}

async function readBody(request: import("node:http").IncomingMessage) {
  let raw = "";
  for await (const chunk of request) raw += String(chunk);
  return JSON.parse(raw);
}

async function listen(
  t: import("node:test").TestContext,
  handler: Parameters<typeof createServer>[1],
) {
  const server = createServer(handler);
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  t.after(async () => {
    server.closeAllConnections();
    await new Promise<void>((resolve) => server.close(() => resolve()));
  });
  const address = server.address();
  assert.ok(address && typeof address !== "string");
  return `http://127.0.0.1:${address.port}/proxy/v1/messages`;
}

test("request-specific wire violations stay separate from task failures", async (t) => {
  const endpoint = await listen(t, async (request, response) => {
    const body = await readBody(request);
    if (body.stream) {
      response.setHeader("content-type", "text/event-stream");
      response.end(
        [
          frame("message_start", {
            message: {
              ...message([]),
              stop_reason: null,
              ...(body.tools ? { stop_sequence: undefined } : {}),
            },
          }),
          ...(body.tools ? toolFrames() : textFrames('{"greeting":"HELLO","extra":true}')),
          ...finishFrames(body.tools ? "tool_use" : "end_turn"),
        ].join(""),
      );
      return;
    }
    response.setHeader("content-type", "application/json");
    response.end(
      JSON.stringify(
        body.output_config
          ? message([{ type: "text", text: '{"greeting":"WRONG"}' }])
          : message([weather()], "tool_use"),
      ),
    );
  });
  const result = await executePlan(
    createPlan({
      endpoint,
      model: "example-model",
      profiles: ["anthropic-tools", "anthropic-structured"],
    }),
    { allowLive: true },
  );
  const find = (id: string) => result.cases.find((item) => item.id === id);
  assert.equal(find("ANT-TOOL-NONE-001")?.protocolStatus, "FAIL");
  assert.equal(find("ANT-STRUCTURED-001")?.protocolStatus, "PASS");
  assert.equal(find("ANT-STRUCTURED-001")?.behaviorStatus, "FAIL");
  assert.equal(find("ANT-STRUCTURED-SSE-001")?.protocolStatus, "FAIL");
  const loop = find("ANT-TOOL-SSE-LOOP-001");
  assert.equal(loop?.attemptsStarted, 1);
  assert.equal(loop?.protocolStatus, "FAIL");
  assert.equal(loop?.behaviorStatus, "INDETERMINATE");
  assert.ok(loop?.observations.some((item) => item.reason === "tool_followup_not_sent"));
});
