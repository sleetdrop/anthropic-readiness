/** Bounded execution and evidence capture for endpoint probes. */
import { createHash, randomUUID } from "node:crypto";
import { performance } from "node:perf_hooks";
import { apiVersions, selectCases, type ApiVersion, type CaseDefinition } from "../catalog.ts";
import { summarize, type Observation, type Status } from "../domain.ts";
import { validateAuxiliary } from "../protocol/auxiliary.ts";
import { validateMessage } from "../protocol/messages.ts";
import { validateSse } from "../protocol/sse.ts";
import { captureHttp, type HttpCapture, type HttpLimits } from "./http.ts";

import {
  checkResponseContract,
  checkTask,
  exactReply,
  historyFollowup,
  object,
  parallelFollowup,
  requestBody,
  text,
  weatherFollowup,
  weatherTool,
  type ObjectValue,
  type TaskCheck,
} from "./probes.ts";
export interface PlanInput {
  endpoint: string;
  model: string;
  apiVersion?: ApiVersion;
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
  readonly apiVersion: ApiVersion;
  readonly contract: "typescript-messages-probes/0.3.0-dev";
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
  route?: "count_tokens";
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
  const apiVersion = input.apiVersion ?? "2023-06-01";
  if (!apiVersions.includes(apiVersion)) throw new Error("invalid_api_version");
  const cases = selectCases(input.profiles);
  if (
    apiVersion !== "2026-10-21" &&
    cases.some((item) => item.profile === "anthropic-version-2026")
  )
    throw new Error("profile_requires_api_version");
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
    apiVersion,
    contract: "typescript-messages-probes/0.3.0-dev",
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
  return {
    ruleId,
    ruleVersion: 1,
    dimension,
    status,
    required: true,
    reason,
    expected,
    actual,
  };
}
function finishCase(
  item: CaseDefinition,
  observations: readonly Observation[],
  captures: readonly CaptureRecord[],
): CaseResult {
  return {
    id: item.id,
    lifecycle: captures.length ? "finished" : "not_run",
    status: summarize(observations),
    protocolStatus: summarize(observations.filter((item) => item.dimension === "protocol")),
    behaviorStatus:
      item.expectedStatus || item.route
        ? "SKIP"
        : summarize(observations.filter((observation) => observation.dimension === "behavior")),
    attemptsStarted: captures.length,
    observations,
    captures,
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
  const countUrl = new URL(plan.endpoint);
  countUrl.pathname = countUrl.pathname.replace(/\/$/u, "") + "/count_tokens";
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
      {
        url: item.route === "count_tokens" ? countUrl.href : plan.endpoint,
        body: requestBytes,
        headers,
      },
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
      ...(item.route ? { route: item.route } : {}),
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
    const expectedStatus = item.expectedStatus ?? 200;
    if (captured.statusCode !== expectedStatus) {
      const invalidAccepted =
        item.expectedStatus === 400 &&
        captured.statusCode !== null &&
        captured.statusCode >= 200 &&
        captured.statusCode < 300;
      observations.push(
        observation(
          "HTTP-STATUS",
          invalidAccepted ? "protocol" : "environment",
          invalidAccepted ? "FAIL" : "BLOCKED",
          invalidAccepted ? "invalid_request_accepted" : "unexpected_http_status",
          `HTTP ${expectedStatus}`,
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
    const auxiliary = item.expectedStatus === 400 ? "invalid_request" : item.route;
    if (auxiliary && captured.end !== "eof") {
      observations.push(
        observation(
          "AUX-JSON",
          "protocol",
          "INDETERMINATE",
          "incomplete_capture",
          "complete UTF-8 JSON response",
          captured.end,
        ),
      );
      return null;
    }
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
        observations.push(
          ...(auxiliary
            ? validateAuxiliary(message, id, auxiliary)
            : validateMessage(message, context(id))),
        );
      } catch {
        observations.push(
          observation(
            auxiliary ? "AUX-JSON" : "MESSAGE-JSON",
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
    if (!auxiliary && record.messageComplete && captured.end === "eof")
      observations.push(...checkResponseContract(item.id, message, record.derivedMessageId ?? id));
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
        results.push(finishCase(item, observations, captures));
        continue;
      }
      const nonce = randomUUID();
      const body = requestBody(item, plan.model, plan.maxTokens, nonce);
      const message = await exchange(body, item, observations, captures);
      const addTask = (rule: string, task: TaskCheck, reply: unknown) => {
        observations.push(
          observation(
            rule,
            "behavior",
            task.status === "PASS"
              ? "PASS"
              : reply === null || captures.some((capture) => capture.end !== "eof")
                ? "INDETERMINATE"
                : task.status,
            "selected_task_behavior",
            task.expected,
            task.status === "PASS"
              ? "observed"
              : (task.actual ?? (text(reply).slice(0, 160) || "not observed")),
          ),
        );
      };
      if (item.expectedStatus || item.route) {
        // These probes assert a wire contract without an inference task.
      } else if (item.id === "ANT-TOOL-PARALLEL-001") {
        const tokens = [nonce, randomUUID()];
        const followup = captures[0]?.messageComplete
          ? parallelFollowup(body, message, tokens)
          : null;
        if (followup) {
          const reply = await exchange(followup, item, observations, captures);
          addTask(
            "TASK-TOOL-PARALLEL",
            {
              status: exactReply(reply, tokens.join(" ")),
              expected: "both fresh tool result tokens in city order",
            },
            reply,
          );
        } else {
          addTask(
            "TASK-TOOL-PARALLEL",
            {
              status: "INDETERMINATE",
              expected: "two distinct tool calls in one turn",
              actual: "parallel calls not observed",
            },
            message,
          );
        }
      } else if (
        ["ANT-TOOL-LOOP-001", "ANT-TOOL-SSE-LOOP-001", "ANT-TOOL-RESULT-ERROR-001"].includes(
          item.id,
        )
      ) {
        const legacy = item.id === "ANT-TOOL-LOOP-001";
        const tool = weatherTool(message, !legacy);
        const complete = captures[0]?.messageComplete === true;
        const protocolFault = observations.some(
          (item) => item.dimension === "protocol" && item.status === "FAIL",
        );
        const streamed = item.id === "ANT-TOOL-SSE-LOOP-001";
        const hasInputDelta = captures[0]?.events?.some(
          ({ value }) =>
            object(value) &&
            object(value.delta) &&
            value.delta.type === "input_json_delta" &&
            typeof value.delta.partial_json === "string" &&
            value.delta.partial_json.length > 0,
        );
        if (streamed && complete && tool && !hasInputDelta) {
          observations.push(
            observation(
              "SSE-TOOL-INPUT-DELTA",
              "protocol",
              "FAIL",
              "missing_tool_input_delta",
              "streamed tool arguments",
              "no nonempty input_json_delta",
            ),
          );
        }
        if (tool && (legacy || (complete && !protocolFault && (!streamed || hasInputDelta)))) {
          const followup = weatherFollowup(
            body,
            message,
            tool,
            nonce,
            item.id === "ANT-TOOL-RESULT-ERROR-001",
          );
          const reply = await exchange(followup, item, observations, captures);
          addTask(
            "TASK-TOOL-RESULT",
            {
              status: exactReply(reply, nonce),
              expected: "fresh tool result token",
              actual: "missing token or extra output",
            },
            reply,
          );
        } else if (tool && complete) {
          observations.push(
            observation(
              "TASK-TOOL-RESULT",
              "behavior",
              "INDETERMINATE",
              "tool_followup_not_sent",
              "tool result continuation",
              "first tool call observed; follow-up not sent after a protocol fault",
            ),
          );
        } else {
          addTask(
            "TASK-TOOL-CALL",
            {
              status: "FAIL",
              expected: "get_weather with city Hanoi",
              actual: "expected complete call not observed",
            },
            message,
          );
        }
      } else if (item.id === "ANT-HISTORY-001") {
        const first = exactReply(message, "HELLO");
        addTask("TASK-HISTORY-FIRST", { status: first, expected: "exact text: HELLO" }, message);
        if (first === "PASS" && captures[0]?.messageComplete) {
          const reply = await exchange(
            historyFollowup(body, message),
            item,
            observations,
            captures,
          );
          addTask(
            "TASK-HISTORY-RECALL",
            {
              status: exactReply(reply, nonce),
              expected: "nonce from the first user turn",
              actual: "missing nonce or extra output",
            },
            reply,
          );
        }
      } else if (item.id === "ANT-CACHE-001") {
        const first = exactReply(message, "HELLO");
        addTask("TASK-CACHE-FIRST", { status: first, expected: "exact text: HELLO" }, message);
        if (first === "PASS" && captures[0]?.messageComplete) {
          const reply = await exchange(body, item, observations, captures);
          addTask(
            "TASK-CACHE-REPEAT",
            {
              status: exactReply(reply, "HELLO"),
              expected: "exact text: HELLO",
            },
            reply,
          );
          const created =
            object(message) && object(message.usage)
              ? message.usage.cache_creation_input_tokens
              : undefined;
          const read =
            object(reply) && object(reply.usage) ? reply.usage.cache_read_input_tokens : undefined;
          const valid = (value: unknown) =>
            typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
          const malformed =
            (created !== undefined && !valid(created)) || (read !== undefined && !valid(read));
          const hit =
            typeof created === "number" && typeof read === "number" && created > 0 && read > 0;
          observations.push(
            observation(
              "CACHE-USAGE",
              "protocol",
              malformed ? "FAIL" : hit ? "PASS" : "INDETERMINATE",
              malformed
                ? "invalid_cache_counter"
                : hit
                  ? "cache_write_then_hit"
                  : "cache_effect_not_observed",
              "positive creation then read counters",
              `created=${String(created)}, read=${String(read)}`,
            ),
          );
        }
      } else {
        addTask("TASK-COMPLETE", checkTask(item.id, message), message);
      }
      const result = finishCase(item, observations, captures);
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
