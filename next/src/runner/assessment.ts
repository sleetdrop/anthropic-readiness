/** Shared execution engine. CLI/Web adapters own presentation and persistence. */
import { createHash, randomUUID } from "node:crypto";
import { performance } from "node:perf_hooks";
import { selectCases, type CaseDefinition } from "../catalog.ts";
import { summarize, type Observation, type Status } from "../domain.ts";
import { validateMessage } from "../protocol/messages.ts";
import { validateSse } from "../protocol/sse.ts";
import { captureHttp, type HttpCapture, type HttpLimits } from "./http.ts";

type ObjectValue = Record<string, unknown>;
export interface PlanInput {
  endpoint: string;
  model: string;
  profiles: readonly string[];
  maxRequests?: number;
  runMs?: number;
  attemptMs?: number;
  maxBytes?: number;
  maxTokens?: number;
  readMs?: number;
  connectMs?: number;
  aliases?: readonly string[];
  checkModelIdentity?: boolean;
}
export interface RunPlan {
  readonly endpoint: string;
  readonly model: string;
  readonly aliases: readonly string[];
  readonly checkModelIdentity: boolean;
  readonly apiVersion: "2023-06-01";
  readonly contract: "typescript-messages-2023-06-01-core/0.2.0-dev";
  readonly profiles: readonly string[];
  readonly cases: readonly CaseDefinition[];
  readonly plannedRequests: number;
  readonly maxRequests: number;
  readonly runMs: number;
  readonly maxTokens: number;
  readonly limits: HttpLimits;
}
export interface CaptureRecord {
  id: string;
  statusCode: number | null;
  headers: HttpCapture["headers"];
  end: HttpCapture["end"];
  errorCode: string | null;
  receivedBytes: number;
  retainedBytes: number;
  bodyBase64: string;
  requestBodyBase64: string;
  requestSha256: string;
  sha256: string;
  elapsedMs: number;
  message?: unknown;
  derivedMessageId?: string;
  messageComplete?: boolean;
  events?: ReturnType<typeof validateSse>["events"];
}
export interface CaseResult {
  id: string;
  lifecycle: "finished" | "not_run";
  status: Status;
  protocolStatus: Status;
  behaviorStatus: Status;
  attemptsStarted: number;
  observations: readonly Observation[];
  captures: readonly CaptureRecord[];
}
export interface RunResult {
  schemaVersion: "typescript-run/1";
  plan: RunPlan;
  status: Status;
  clientStatus: "not_tested";
  attemptsStarted: number;
  elapsedMs: number;
  cases: readonly CaseResult[];
  limitations: readonly string[];
}
export interface ExecutionOptions {
  allowLive: boolean;
  token?: string;
  authMode?: "api_key" | "bearer";
  signal?: AbortSignal;
  onCaseComplete?: (result: CaseResult) => void;
  onCapture?: (capture: Readonly<CaptureRecord>) => Promise<void>;
}
const stopReasons = [
  "end_turn",
  "max_tokens",
  "stop_sequence",
  "tool_use",
  "pause_turn",
  "refusal",
  "model_context_window_exceeded",
];
const object = (value: unknown): value is ObjectValue =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const positive = (value: number) => Number.isSafeInteger(value) && value > 0;

export function createPlan(input: PlanInput): RunPlan {
  let url: URL;
  try {
    url = new URL(input.endpoint);
  } catch {
    throw new Error("invalid_url");
  }
  if (
    !["http:", "https:"].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.hash ||
    url.search
  )
    throw new Error("invalid_url");
  if (url.pathname === "/") url.pathname = "/v1/messages";
  else if (url.pathname.replace(/\/$/u, "") === "/v1") url.pathname = "/v1/messages";
  if (typeof input.model !== "string" || !input.model.trim()) throw new Error("invalid_model");
  const cases = selectCases(input.profiles);
  const plannedRequests = cases.reduce((sum, item) => sum + item.maxRequests, 0);
  const maxRequests = input.maxRequests ?? plannedRequests;
  const runMs = input.runMs ?? 300_000;
  const attemptMs = input.attemptMs ?? 30_000;
  const maxBytes = input.maxBytes ?? 2 * 1024 * 1024;
  const maxTokens = input.maxTokens ?? 2048;
  const readMs = input.readMs ?? attemptMs;
  const connectMs = input.connectMs ?? Math.min(attemptMs, 5000);
  if (![maxRequests, runMs, attemptMs, maxBytes, maxTokens, readMs, connectMs].every(positive))
    throw new Error("invalid_limits");
  if (maxRequests < plannedRequests) throw new Error("insufficient_request_budget");
  return {
    endpoint: url.href,
    model: input.model,
    aliases: [...(input.aliases ?? [])],
    checkModelIdentity: input.checkModelIdentity ?? true,
    apiVersion: "2023-06-01",
    contract: "typescript-messages-2023-06-01-core/0.2.0-dev",
    profiles: [...new Set(input.profiles)],
    cases,
    plannedRequests,
    maxRequests,
    runMs,
    maxTokens,
    limits: {
      attemptMs,
      connectMs,
      readMs,
      maxBytes,
    },
  };
}

function observation(
  ruleId: string,
  dimension: Observation["dimension"],
  status: Status,
  reason: string,
  expected: string,
  actual: string,
): Observation {
  return { ruleId, ruleVersion: 1, dimension, status, required: true, reason, expected, actual };
}
function finishCase(
  id: string,
  observations: readonly Observation[],
  captures: readonly CaptureRecord[],
): CaseResult {
  return {
    id,
    lifecycle: captures.length ? "finished" : "not_run",
    status: summarize(observations),
    protocolStatus: summarize(observations.filter((item) => item.dimension === "protocol")),
    behaviorStatus: summarize(observations.filter((item) => item.dimension === "behavior")),
    attemptsStarted: captures.length,
    observations,
    captures,
  };
}
function content(message: unknown): ObjectValue[] {
  return object(message) && Array.isArray(message.content) ? message.content.filter(object) : [];
}
function text(message: unknown): string {
  return content(message)
    .filter((item) => item.type === "text" && typeof item.text === "string")
    .map((item) => String(item.text))
    .join("");
}
function weatherTool(message: unknown): ObjectValue | undefined {
  return content(message).find(
    (item) =>
      item.type === "tool_use" &&
      item.name === "get_weather" &&
      typeof item.id === "string" &&
      item.id.length > 0 &&
      object(item.input) &&
      item.input.city === "Hanoi",
  );
}
function exactReply(message: unknown, expected: string): Status {
  if (text(message).trim() !== expected) return "FAIL";
  const blocks = content(message);
  if (blocks.some((block) => block.type === "tool_use")) return "FAIL";
  return blocks.some(
    (block) => !["text", "thinking", "redacted_thinking"].includes(String(block.type)),
  )
    ? "INDETERMINATE"
    : "PASS";
}
function requestBody(item: CaseDefinition, model: string, maxTokens: number): ObjectValue {
  const tool = item.capabilities.includes("tools");
  const prompt = tool
    ? "Use get_weather to check the weather in Hanoi. After receiving a tool result, reply with only its verification_token."
    : item.id === "ANT-TEXT-SSE-002"
      ? "Count from 1 to 5. Reply with exactly: 1 2 3 4 5"
      : "Reply with exactly HELLO, without punctuation or explanation.";
  return {
    model,
    max_tokens: maxTokens,
    stream: item.response === "sse",
    messages: [{ role: "user", content: prompt }],
    ...(tool
      ? {
          tools: [
            {
              name: "get_weather",
              input_schema: {
                type: "object",
                properties: { city: { type: "string", const: "Hanoi" } },
                required: ["city"],
              },
            },
          ],
          tool_choice: { type: "tool", name: "get_weather" },
        }
      : {}),
  };
}

export async function executePlan(plan: RunPlan, options: ExecutionOptions): Promise<RunResult> {
  if (options.allowLive !== true) throw new Error("live_opt_in_required");
  const started = performance.now();
  const abort = new AbortController();
  const stop = () => abort.abort();
  if (options.signal?.aborted) abort.abort();
  options.signal?.addEventListener("abort", stop, { once: true });
  const deadline = setTimeout(stop, plan.runMs);
  const results: CaseResult[] = [];
  let attemptsStarted = 0;
  const context = (captureId: string) => ({
    captureId,
    requestedModel: plan.model,
    modelAliases: plan.aliases,
    checkModelIdentity: plan.checkModelIdentity,
    stopReasons,
  });
  async function exchange(
    body: ObjectValue,
    item: CaseDefinition,
    observations: Observation[],
    captures: CaptureRecord[],
  ): Promise<unknown> {
    if (abort.signal.aborted || attemptsStarted >= plan.maxRequests) return null;
    attemptsStarted++;
    const id = randomUUID();
    const headers: [string, string][] = [
      ["content-type", "application/json"],
      ["anthropic-version", plan.apiVersion],
      ["accept", item.response === "sse" ? "text/event-stream" : "application/json"],
    ];
    if (options.token)
      headers.push(
        options.authMode === "bearer"
          ? ["authorization", `Bearer ${options.token}`]
          : ["x-api-key", options.token],
      );
    const requestBytes = Buffer.from(JSON.stringify(body));
    const captured = await captureHttp(
      { url: plan.endpoint, body: requestBytes, headers },
      {
        ...plan.limits,
        attemptMs: Math.max(
          1,
          Math.min(plan.limits.attemptMs, Math.ceil(plan.runMs - (performance.now() - started))),
        ),
      },
      { signal: abort.signal },
    );
    const record: CaptureRecord = {
      id,
      statusCode: captured.statusCode,
      headers: captured.headers,
      end: captured.end,
      errorCode: captured.errorCode,
      receivedBytes: captured.receivedBytes,
      retainedBytes: captured.body.length,
      bodyBase64: captured.body.toString("base64"),
      requestBodyBase64: requestBytes.toString("base64"),
      requestSha256: createHash("sha256").update(requestBytes).digest("hex"),
      sha256: createHash("sha256").update(captured.body).digest("hex"),
      elapsedMs: captured.elapsedMs,
    };
    captures.push(record);
    await options.onCapture?.(record);
    if (captured.end !== "eof")
      observations.push(
        observation(
          "CAPTURE-COMPLETE",
          "environment",
          "INDETERMINATE",
          captured.end,
          "complete response",
          captured.end,
        ),
      );
    if (captured.statusCode !== 200) {
      observations.push(
        observation(
          "HTTP-STATUS",
          "environment",
          "BLOCKED",
          "unexpected_http_status",
          "HTTP 200",
          String(captured.statusCode ?? captured.errorCode ?? captured.end),
        ),
      );
      return null;
    }
    const header = (name: string) =>
      captured.headers
        .filter(([key]) => key.toLowerCase() === name)
        .map(([, value]) => value)
        .join(",");
    const encoding = header("content-encoding").toLowerCase().trim();
    if (encoding && encoding !== "identity") {
      observations.push(
        observation(
          "HTTP-ENCODING",
          "environment",
          "BLOCKED",
          "encoding_not_yet_supported",
          "identity encoding",
          encoding,
        ),
      );
      return null;
    }
    const mime = header("content-type").split(";")[0]?.trim().toLowerCase();
    const expected = item.response === "sse" ? "text/event-stream" : "application/json";
    observations.push(
      observation(
        "HTTP-CONTENT-TYPE",
        "protocol",
        mime === expected ? "PASS" : "FAIL",
        "response_media_type",
        expected,
        mime ?? "missing",
      ),
    );
    let message: unknown;
    if (item.response === "sse") {
      const parsed = validateSse(captured.body, context(id), {
        completeCapture: captured.end === "eof",
        maxEvents: 10000,
        maxEventBytes: plan.limits.maxBytes,
      });
      observations.push(...parsed.observations);
      record.events = parsed.events;
      message = parsed.message;
      record.derivedMessageId = id + ":assembled";
      record.message = message;
      record.messageComplete = parsed.events.some(
        (event) =>
          event.event === "message_stop" &&
          object(event.value) &&
          event.value.type === "message_stop",
      );
      if (record.messageComplete && message !== null)
        observations.push(...validateMessage(message, context(record.derivedMessageId)));
    } else {
      try {
        message = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(captured.body));
        record.message = message;
        record.messageComplete = captured.end === "eof";
        observations.push(...validateMessage(message, context(id)));
      } catch {
        observations.push(
          observation(
            "MESSAGE-JSON",
            "protocol",
            captured.end === "eof" ? "FAIL" : "INDETERMINATE",
            "invalid_or_incomplete_json",
            "complete UTF-8 JSON response",
            "could not decode complete JSON",
          ),
        );
        return null;
      }
    }
    return message;
  }
  try {
    for (const item of plan.cases) {
      const observations: Observation[] = [],
        captures: CaptureRecord[] = [];
      if (abort.signal.aborted) {
        observations.push(
          observation(
            "CASE-EXECUTION",
            "environment",
            "INDETERMINATE",
            "not_run",
            "selected case executed",
            "cancelled or run deadline reached",
          ),
        );
        results.push(finishCase(item.id, observations, captures));
        continue;
      }
      const body = requestBody(item, plan.model, plan.maxTokens);
      let message = await exchange(body, item, observations, captures);
      if (item.id === "ANT-TOOL-LOOP-001") {
        const tool = weatherTool(message);
        if (tool) {
          const nonce = randomUUID();
          const messages = body.messages as unknown[];
          const followup = {
            ...body,
            tool_choice: { type: "auto" },
            messages: [
              ...messages,
              { role: "assistant", content: object(message) ? message.content : [] },
              {
                role: "user",
                content: [
                  {
                    type: "tool_result",
                    tool_use_id: tool.id,
                    content: JSON.stringify({
                      temperature_c: 20,
                      condition: "clear",
                      verification_token: nonce,
                    }),
                  },
                ],
              },
            ],
          };
          message = await exchange(followup, item, observations, captures);
          const taskStatus = exactReply(message, nonce);
          observations.push(
            observation(
              "TASK-TOOL-RESULT",
              "behavior",
              message === null || (taskStatus !== "PASS" && captures.some((c) => c.end !== "eof"))
                ? "INDETERMINATE"
                : taskStatus,
              "tool_result_consumption",
              "fresh tool result token",
              taskStatus === "PASS" ? "only token returned" : "missing token or extra output",
            ),
          );
        } else
          observations.push(
            observation(
              "TASK-TOOL-CALL",
              "behavior",
              message === null || captures.some((c) => c.end !== "eof") ? "INDETERMINATE" : "FAIL",
              "expected_tool_missing",
              "get_weather with city Hanoi",
              "expected call not observed",
            ),
          );
      } else {
        const taskStatus: Status =
          item.id === "ANT-TOOL-FORCED-001"
            ? weatherTool(message)
              ? "PASS"
              : "FAIL"
            : exactReply(message, item.id === "ANT-TEXT-SSE-002" ? "1 2 3 4 5" : "HELLO");
        observations.push(
          observation(
            "TASK-COMPLETE",
            "behavior",
            taskStatus === "PASS"
              ? "PASS"
              : message === null || captures.some((c) => c.end !== "eof")
                ? "INDETERMINATE"
                : taskStatus,
            "selected_task_behavior",
            item.id === "ANT-TOOL-FORCED-001"
              ? "get_weather with city Hanoi"
              : item.id === "ANT-TEXT-SSE-002"
                ? "exact text: 1 2 3 4 5"
                : "exact text: HELLO",
            taskStatus === "PASS" ? "observed" : text(message).slice(0, 160) || "not observed",
          ),
        );
      }
      const result = finishCase(item.id, observations, captures);
      results.push(result);
      options.onCaseComplete?.(result);
    }
  } finally {
    clearTimeout(deadline);
    options.signal?.removeEventListener("abort", stop);
  }
  return {
    schemaVersion: "typescript-run/1",
    plan,
    status: summarize(results.flatMap((item) => item.observations)),
    clientStatus: "not_tested",
    attemptsStarted,
    elapsedMs: performance.now() - started,
    cases: results,
    limitations: [
      "Selected structural/task checks only; not a full compatibility certificate.",
      "SDK and Claude Code workflows are not tested.",
      "Compressed response decoding and duplicate JSON-key detection are not implemented.",
      "SSE assembled-message locations refer to derived data, not original event nodes.",
    ],
  };
}
