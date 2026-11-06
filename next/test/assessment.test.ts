import assert from "node:assert/strict";
import { createServer } from "node:http";
import { existsSync, readFileSync, readdirSync, mkdtempSync, rmSync } from "node:fs";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { createPlan, executePlan } from "../../skills/anthropic-readiness/scripts/src/runner/assessment.ts";

const profiles = ["anthropic-basic", "anthropic-tools-smoke", "anthropic-tool-loop"];
const input = { endpoint: "http://127.0.0.1:1/v1/messages", model: "synthetic", profiles };

test("plan reserves the full scope and rejects insufficient budgets or invalid configuration", () => {
  const plan = createPlan(input);
  assert.equal(plan.plannedRequests, 6);
  assert.equal(plan.cases.length, 5);
  const configured = createPlan({ ...input, maxTokens: 8192, readMs: 60000, attemptMs: 90000 });
  assert.equal(configured.maxTokens, 8192);
  assert.equal(configured.limits.readMs, 60000);
  assert.throws(() => createPlan({ ...input, maxRequests: 5 }), /insufficient_request_budget/);
  assert.throws(() => createPlan({ ...input, model: "" }), /invalid_model/);
  assert.throws(() => createPlan({ ...input, runMs: 0 }), /invalid_limits/);
  assert.equal(
    createPlan({ ...input, endpoint: "http://127.0.0.1:1/v1" }).endpoint,
    input.endpoint,
  );
});

test("literal JSON null is a structural fault, while a legal SSE error is not a protocol fault", async (t) => {
  let mode = "null";
  const valid = JSON.parse(
    readFileSync(
      new URL("../../tests/fixtures/contracts/core-1.0.0/message-valid.json", import.meta.url),
      "utf8",
    ),
  );
  const stream = readFileSync(
    new URL("../../tests/fixtures/contracts/core-1.0.0/stream-valid.sse", import.meta.url),
    "utf8",
  );
  const server = createServer(async (req, res) => {
    let raw = "";
    for await (const chunk of req) raw += String(chunk);
    const body = JSON.parse(raw);
    if (body.stream) {
      res.setHeader("content-type", "text/event-stream");
      res.end(
        mode === "error"
          ? 'event: error\ndata: {"type":"error","error":{"type":"overloaded_error","message":"busy"}}\n\n'
          : stream,
      );
    } else {
      res.setHeader("content-type", "application/json");
      res.end(mode === "null" ? "null" : JSON.stringify(valid));
    }
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  t.after(async () => {
    server.closeAllConnections();
    await new Promise<void>((resolve) => server.close(() => resolve()));
  });
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("fixture_address");
  const plan = createPlan({
    ...input,
    endpoint: `http://127.0.0.1:${address.port}/v1/messages`,
    model: "example-model",
    profiles: ["anthropic-basic"],
  });
  const nullResult = await executePlan(plan, { allowLive: true });
  assert.equal(nullResult.cases[0]?.protocolStatus, "FAIL");
  mode = "error";
  const errorResult = await executePlan(plan, { allowLive: true });
  for (const item of errorResult.cases.slice(1)) {
    assert.equal(item.behaviorStatus, "FAIL");
    assert.ok(
      !item.observations.some((obs) => obs.dimension === "protocol" && obs.status === "FAIL"),
    );
  }
});

test("execution requires explicit live admission before any connection", async () => {
  await assert.rejects(
    executePlan(createPlan(input), { allowLive: false }),
    /live_opt_in_required/,
  );
});

test("an exact-output response prefix cannot pass while its stream is unfinished", async (t) => {
  const event = (type: string, value: object) =>
    `event: ${type}\ndata: ${JSON.stringify({ type, ...value })}\n\n`;
  const server = createServer(async (_request, response) => {
    response.setHeader("content-type", "text/event-stream");
    response.write(
      event("message_start", {
        message: {
          id: "msg-partial",
          type: "message",
          role: "assistant",
          model: "example-model",
          content: [],
          stop_reason: null,
          stop_sequence: null,
          usage: { input_tokens: 2, output_tokens: 0 },
        },
      }) +
        event("content_block_start", {
          index: 0,
          content_block: { type: "text", text: "" },
        }) +
        event("content_block_delta", { index: 0, delta: { type: "text_delta", text: "HELLO" } }) +
        event("content_block_stop", { index: 0 }),
    );
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  t.after(async () => {
    server.closeAllConnections();
    await new Promise<void>((resolve) => server.close(() => resolve()));
  });
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("fixture_address");
  const plan = createPlan({
    endpoint: `http://127.0.0.1:${address.port}/v1/messages`,
    model: "example-model",
    profiles: ["anthropic-basic"],
    readMs: 50,
    attemptMs: 250,
  });
  const selected = plan.cases.find((item) => item.id === "ANT-TEXT-SSE-001");
  assert.ok(selected);
  const result = await executePlan(
    { ...plan, cases: [selected], plannedRequests: 1, maxRequests: 1 },
    { allowLive: true, authMode: "none" },
  );
  const item = result.cases[0];
  assert.equal(item?.captures[0]?.messageComplete, false);
  assert.equal(item?.behaviorStatus, "INDETERMINATE");
  assert.equal(item?.observations.find((value) => value.ruleId === "TASK-COMPLETE")?.status, "INDETERMINATE");
});

test("cancellation retains every selected case without admitting any request", async () => {
  const controller = new AbortController();
  controller.abort();
  const result = await executePlan(createPlan(input), {
    allowLive: true,
    signal: controller.signal,
  });
  assert.equal(result.attemptsStarted, 0);
  assert.equal(result.cases.length, 5);
  assert.equal(result.status, "INDETERMINATE");
  assert.ok(
    result.cases.every((item) => item.lifecycle === "not_run" && item.status === "INDETERMINATE"),
  );
});

test("five selected scenarios run six requests and consume a fresh tool result", async (t) => {
  const requests: Record<string, unknown>[] = [];
  let expectedAuth: "api_key" | "bearer" | "none" = "api_key";
  const server = createServer(async (req, res) => {
    let text = "";
    for await (const chunk of req) text += String(chunk);
    const body = JSON.parse(text) as Record<string, unknown>;
    requests.push(body);
    assert.equal(req.headers["anthropic-version"], "2023-06-01");
    assert.equal(
      req.headers["x-api-key"],
      expectedAuth === "api_key" ? "synthetic-key" : undefined,
    );
    assert.equal(
      req.headers.authorization,
      expectedAuth === "bearer" ? "Bearer synthetic-key" : undefined,
    );
    assert.equal(body.max_tokens, 2048);
    const messages = body.messages as { role: string; content: unknown }[];
    const last = messages.at(-1)?.content;
    const toolResult = Array.isArray(last) ? (last[0] as Record<string, unknown>) : null;
    const token = toolResult
      ? (JSON.parse(String(toolResult.content)).verification_token as string)
      : null;
    const forced = (body.tool_choice as Record<string, unknown> | undefined)?.type === "tool";
    const count = JSON.stringify(messages).includes("1 to 5");
    const content = forced
      ? [{ type: "tool_use", id: "call-1", name: "get_weather", input: { city: "Hanoi" } }]
      : [{ type: "text", text: token ?? (count ? "1 2 3 4 5" : "HELLO") }];
    const message = {
      id: "msg-fixture",
      type: "message",
      role: "assistant",
      model: "synthetic",
      content,
      stop_reason: forced ? "tool_use" : "end_turn",
      stop_sequence: null,
      usage: { input_tokens: 2, output_tokens: 3 },
    };
    if (body.stream) {
      const event = (type: string, value: object) =>
        `event: ${type}\ndata: ${JSON.stringify({ type, ...value })}\n\n`;
      res.setHeader("content-type", "text/event-stream");
      res.end(
        event("message_start", { message: { ...message, content: [], stop_reason: null } }) +
          event("content_block_start", { index: 0, content_block: { type: "text", text: "" } }) +
          event("content_block_delta", {
            index: 0,
            delta: { type: "text_delta", text: (content[0] as { text: string }).text },
          }) +
          event("content_block_stop", { index: 0 }) +
          event("message_delta", {
            delta: { stop_reason: "end_turn", stop_sequence: null },
            usage: { output_tokens: 3 },
          }) +
          event("message_stop", {}),
      );
    } else {
      res.setHeader("content-type", "application/json");
      res.end(JSON.stringify(message));
    }
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  t.after(async () => {
    server.closeAllConnections();
    await new Promise<void>((resolve) => server.close(() => resolve()));
  });
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("fixture_address");
  const plan = createPlan({ ...input, endpoint: `http://127.0.0.1:${address.port}/v1/messages` });
  const report = await executePlan(plan, { allowLive: true, token: "synthetic-key" });
  assert.equal(report.status, "PASS");
  assert.equal(report.attemptsStarted, 6);
  assert.equal(report.cases.length, 5);
  assert.equal(requests.length, 6);
  assert.equal(report.clientStatus, "not_tested");
  assert.ok(
    report.cases.every((item) => item.behaviorStatus === "PASS" && item.protocolStatus === "PASS"),
  );
  function verificationToken(request: Record<string, unknown> | undefined): string {
    const messages = request?.messages as { content: unknown }[];
    const result = messages.at(-1)?.content as { content: string }[];
    return JSON.parse(result[0]!.content).verification_token as string;
  }
  const nonce = verificationToken(requests[5]);
  assert.ok(nonce.length > 10);
  assert.ok(!JSON.stringify(requests[4]).includes(nonce));
  assert.ok(!JSON.stringify(report).includes("synthetic-key"));
  for (const item of report.cases)
    for (const capture of item.captures) {
      assert.match(capture.sha256, /^[a-f0-9]{64}$/u);
      assert.equal(Buffer.from(capture.bodyBase64, "base64").length, capture.retainedBytes);
      assert.equal(typeof capture.headersMs, "number");
      assert.equal(typeof capture.firstByteMs, "number");
    }
  expectedAuth = "none";
  const repeated = await executePlan(plan, {
    allowLive: true,
    authMode: "none",
    token: "synthetic-key",
  });
  assert.equal(repeated.status, "PASS");
  assert.notEqual(verificationToken(requests[11]), nonce);
  const directory = mkdtempSync(join(tmpdir(), "readiness-cli-positive-"));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const output = join(directory, "assessment");
  const cli = fileURLToPath(new URL("../../skills/anthropic-readiness/scripts/src/cli/main.ts", import.meta.url));
  const args = [
    cli,
    "run",
    "--endpoint",
    plan.endpoint,
    "--model",
    "synthetic",
    ...profiles.flatMap((profile) => ["--profile", profile]),
    "--out",
    output,
    "--allow-live",
    "--auth-env",
    "SYNTHETIC_READINESS_KEY",
  ];
  const exec = promisify(execFile);
  expectedAuth = "api_key";
  const child = await exec(process.execPath, args, {
    env: { ...process.env, SYNTHETIC_READINESS_KEY: "synthetic-key" },
    timeout: 5000,
  });
  assert.match(child.stdout, /PASS/u);
  const serialized = readFileSync(join(output, "result.json"), "utf8");
  assert.equal(JSON.parse(serialized).attemptsStarted, 6);
  for (const item of JSON.parse(serialized).cases)
    for (const capture of item.captures) {
      const raw = JSON.parse(readFileSync(join(output, `response-${capture.id}.json`), "utf8"));
      assert.equal(raw.sha256, capture.sha256);
      assert.equal(raw.message, undefined);
      const view = readFileSync(join(output, `response-${capture.id}.json.html`), "utf8");
      assert.match(view, /class="json-key">[^<]*statusCode/u);
      assert.match(view, /href="response-[^"]+\.json"/u);
      assert.equal(raw.bodyBase64, capture.bodyBase64);
    }
  assert.ok(!serialized.includes("synthetic-key"));
  const resultView = readFileSync(join(output, "result.json.html"), "utf8");
  assert.match(resultView, /<html lang="en">/u);
  assert.match(resultView, /href="result\.json"/u);
  const html = readFileSync(join(output, "report.html"), "utf8");
  assert.match(html, /^<!doctype html>/u);
  assert.match(html, /<html lang="en">/u);
  assert.match(html, /ANT-TOOL-LOOP-001/u);
  assert.equal(existsSync(join(output, "report.md")), false);
  const bearerOutput = join(directory, "bearer-assessment");
  expectedAuth = "bearer";
  const bearer = await exec(
    process.execPath,
    [...args.map((value) => (value === output ? bearerOutput : value)), "--auth-mode", "bearer"],
    {
      env: { ...process.env, SYNTHETIC_READINESS_KEY: "synthetic-key" },
      timeout: 5000,
    },
  );
  assert.match(bearer.stdout, /PASS/u);
  for (const filename of readdirSync(bearerOutput)) {
    assert.ok(!readFileSync(join(bearerOutput, filename), "utf8").includes("synthetic-key"));
  }
  for (const mode of ["api_key", "bearer", "none"] as const) {
    expectedAuth = mode;
    const envOutput = join(directory, `environment-${mode}`);
    const envArgs = [
      cli,
      "run",
      "--use-env",
      "--profile",
      "anthropic-basic",
      "--allow-live",
      "--max-requests",
      "3",
      "--out",
      envOutput,
    ];
    if (mode === "none") envArgs.push("--auth-env", "SYNTHETIC_MISSING_TOKEN");
    const result = await exec(process.execPath, envArgs, {
      env: {
        ...process.env,
        AR_DIAG_ENDPOINT_URL: plan.endpoint,
        AR_DIAG_MODEL: "synthetic",
        AR_DIAG_API_VERSION: "2023-06-01",
        AR_DIAG_AUTH_MODE: mode,
        AR_DIAG_AUTH_TOKEN: "synthetic-key",
      },
      timeout: 5000,
    });
    assert.match(result.stdout, /PASS/u);
    for (const filename of readdirSync(envOutput))
      assert.ok(!readFileSync(join(envOutput, filename), "utf8").includes("synthetic-key"));
  }
  const overrideOutput = join(directory, "environment-credential-override");
  expectedAuth = "bearer";
  const override = await exec(
    process.execPath,
    [
      cli,
      "run",
      "--use-env",
      "--profile",
      "anthropic-basic",
      "--allow-live",
      "--max-requests",
      "3",
      "--out",
      overrideOutput,
      "--auth-env",
      "SYNTHETIC_READINESS_KEY",
      "--auth-mode",
      "bearer",
    ],
    {
      env: {
        ...process.env,
        AR_DIAG_ENDPOINT_URL: plan.endpoint,
        AR_DIAG_MODEL: "synthetic",
        AR_DIAG_API_VERSION: "2023-06-01",
        AR_DIAG_AUTH_MODE: "api_key",
        AR_DIAG_AUTH_TOKEN: "synthetic-unused-key",
        SYNTHETIC_READINESS_KEY: "synthetic-key",
      },
      timeout: 5000,
    },
  );
  assert.match(override.stdout, /PASS/u);
  const count = requests.length;
  await assert.rejects(
    exec(process.execPath, args, {
      env: { ...process.env, SYNTHETIC_READINESS_KEY: "synthetic-key" },
      timeout: 5000,
    }),
    /output_directory_must_be_new/u,
  );
  assert.equal(requests.length, count);
});

test("controlled tasks reject incidental digits, non-greetings and extra tool calls", async (t) => {
  const server = createServer(async (req, res) => {
    let raw = "";
    for await (const chunk of req) raw += String(chunk);
    const body = JSON.parse(raw);
    const messages = body.messages;
    const tail = messages.at(-1).content;
    const followup = Array.isArray(tail) ? JSON.parse(tail[0].content) : null;
    const forced = body.tool_choice?.type === "tool";
    const bad = JSON.stringify(messages).includes("1 to 5")
      ? "Answer: 1,2,3,4,5"
      : "I cannot help with that.";
    const tool = { type: "tool_use", id: "tool-1", name: "get_weather", input: { city: "Hanoi" } };
    const content = forced
      ? [tool]
      : followup
        ? [{ type: "text", text: followup.verification_token }, tool]
        : [{ type: "text", text: bad }];
    res.setHeader("content-type", body.stream ? "text/event-stream" : "application/json");
    if (body.stream) {
      const fixture = readFileSync(
        new URL("../../tests/fixtures/contracts/core-1.0.0/stream-valid.sse", import.meta.url),
        "utf8",
      );
      res.end(fixture.replaceAll("example-model", "synthetic").replaceAll("Hello.", bad));
    } else
      res.end(
        JSON.stringify({
          id: "msg",
          type: "message",
          role: "assistant",
          model: "synthetic",
          content,
          stop_reason: forced || followup ? "tool_use" : "end_turn",
          stop_sequence: null,
          usage: { input_tokens: 1, output_tokens: 1 },
        }),
      );
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  t.after(async () => {
    server.closeAllConnections();
    await new Promise<void>((resolve) => server.close(() => resolve()));
  });
  const addr = server.address();
  if (!addr || typeof addr === "string") throw new Error("fixture_address");
  const report = await executePlan(
    createPlan({ ...input, endpoint: `http://127.0.0.1:${addr.port}/v1/messages` }),
    { allowLive: true },
  );
  for (const item of report.cases.filter((item) => item.id !== "ANT-TOOL-FORCED-001"))
    assert.equal(item.behaviorStatus, "FAIL", item.id);
});
