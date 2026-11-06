/** Offline inspection of one successful Messages response body. */
import { createHash } from "node:crypto";
import { parseArgs } from "node:util";
import { summarize, type MessageValidationContext, type Observation } from "../domain.ts";
import { validateAuxiliary } from "../protocol/auxiliary.ts";
import { validateMessage } from "../protocol/messages.ts";
import { validateSse } from "../protocol/sse.ts";
import { readBoundedFile } from "./local-file.ts";

const maxBytes = 2 * 1024 * 1024;
const maxRecordBytes = 3 * 1024 * 1024;
const stopReasons = [
  "end_turn",
  "max_tokens",
  "stop_sequence",
  "tool_use",
  "pause_turn",
  "refusal",
  "model_context_window_exceeded",
];

async function readRecord(file: string): Promise<{
  body: Buffer;
  format: "message" | "sse";
  complete: boolean;
  route?: "count_tokens";
}> {
  const bytes = await readBoundedFile(file, maxRecordBytes);
  const value: unknown = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  if (typeof value !== "object" || value === null || Array.isArray(value))
    throw new Error("invalid_capture_record");
  const record = value as Record<string, unknown>;
  if (record.route !== undefined && record.route !== "count_tokens")
    throw new Error("unsupported_capture_route");
  if (
    typeof record.statusCode !== "number" ||
    !Number.isInteger(record.statusCode) ||
    record.statusCode < 200 || record.statusCode >= 300 ||
    !["eof", "connect_timeout", "read_timeout", "attempt_timeout", "response_limit", "cancelled", "network_error", "observer_error"].includes(String(record.end)) ||
    !Array.isArray(record.headers) ||
    typeof record.bodyBase64 !== "string" ||
    !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/u.test(record.bodyBase64) ||
    typeof record.sha256 !== "string" ||
    !/^[a-f0-9]{64}$/u.test(record.sha256)
  ) throw new Error("invalid_capture_record");
  const body = Buffer.from(record.bodyBase64, "base64");
  if (body.length > maxBytes || body.toString("base64") !== record.bodyBase64)
    throw new Error("invalid_capture_record");
  if (createHash("sha256").update(body).digest("hex") !== record.sha256)
    throw new Error("capture_hash_mismatch");
  const headers = record.headers.filter(
    (header): header is [string, string] =>
      Array.isArray(header) && header.length === 2 &&
      typeof header[0] === "string" && typeof header[1] === "string",
  );
  if (headers.length !== record.headers.length) throw new Error("invalid_capture_record");
  const header = (name: string) =>
    headers
      .filter(([key]) => key.toLowerCase() === name)
      .map(([, content]) => content)
      .join(",");
  const encoding = header("content-encoding").trim().toLowerCase();
  if (encoding && encoding !== "identity") throw new Error("unsupported_capture_encoding");
  const mediaType = header("content-type").split(";")[0]?.trim().toLowerCase();
  const format = mediaType === "text/event-stream"
    ? "sse"
    : mediaType === "application/json" ? "message" : undefined;
  if (!format) throw new Error("unsupported_capture_content_type");
  if (record.route === "count_tokens" && format !== "message")
    throw new Error("unsupported_capture_route_format");
  return {
    body,
    format,
    complete: record.end === "eof",
    ...(record.route === "count_tokens" ? { route: "count_tokens" as const } : {}),
  };
}

function inspectMessage(
  body: Buffer,
  context: MessageValidationContext,
  complete: boolean,
  route?: "count_tokens",
): readonly Observation[] {
  if (!complete) {
    return [
      {
        ruleId: "INSPECT-CAPTURE",
        ruleVersion: 1,
        dimension: "environment",
        required: true,
        status: "INDETERMINATE",
        reason: "capture_incomplete",
        expected: "complete JSON body",
        actual: "capture may be partial",
      },
    ];
  }
  let message: unknown;
  try {
    message = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(body));
  } catch {
    return [
      {
        ruleId: "INSPECT-JSON",
        ruleVersion: 1,
        dimension: "protocol",
        required: true,
        status: "FAIL",
        reason: "invalid_json_body",
        expected: "one UTF-8 JSON message",
        actual: "body cannot be decoded and parsed as JSON",
      },
    ];
  }
  return route === "count_tokens"
    ? validateAuxiliary(message, context.captureId, route)
    : validateMessage(message, context);
}

async function main(): Promise<void> {
  try {
    const { values } = parseArgs({
      options: {
        file: { type: "string" },
        record: { type: "string" },
        format: { type: "string" },
        capture: { type: "string" },
      },
    });
    const { file, record, format, capture } = values;
    if (record) {
      if (file || format || capture) throw new Error("invalid_arguments");
      const inspected = await readRecord(record);
      const body = inspected.body;
      const sha256 = createHash("sha256").update(body).digest("hex");
      const context: MessageValidationContext = {
        captureId: sha256,
        requestedModel: "",
        modelAliases: [],
        checkModelIdentity: false,
        stopReasons,
      };
      const stream = inspected.format === "sse"
        ? validateSse(body, context, {
            completeCapture: inspected.complete,
            maxEvents: 10_000,
            maxEventBytes: maxBytes,
          })
        : undefined;
      const observations = stream?.observations ??
        inspectMessage(body, context, inspected.complete, inspected.route);
      const findings = observations.filter((item) => item.status !== "PASS");
      process.stdout.write(JSON.stringify({
        schemaVersion: "incident-inspect/1",
        scope: "local-core-rules",
        format: inspected.format,
        ...(inspected.route ? { route: inspected.route } : {}),
        capture: { file: record, complete: inspected.complete, sha256, bytes: body.length },
        ...(stream ? { events: stream.events.length } : {}),
        modelIdentity: "not_checked",
        status: summarize(observations),
        findings,
      }, null, 2) + "\n");
      return;
    }
    if (
      !file ||
      (format !== "message" && format !== "sse") ||
      (capture !== "complete" && capture !== "partial")
    ) {
      throw new Error("invalid_arguments");
    }
    const complete = capture === "complete";
    const body = await readBoundedFile(file, maxBytes);
    const sha256 = createHash("sha256").update(body).digest("hex");
    const context: MessageValidationContext = {
      captureId: sha256,
      requestedModel: "",
      modelAliases: [],
      checkModelIdentity: false,
      stopReasons,
    };
    const stream =
      format === "sse"
        ? validateSse(body, context, {
            completeCapture: complete,
            maxEvents: 10_000,
            maxEventBytes: maxBytes,
          })
        : undefined;
    const observations = stream?.observations ?? inspectMessage(body, context, complete);
    const findings = observations.filter((item) => item.status !== "PASS");
    process.stdout.write(
      JSON.stringify(
        {
          schemaVersion: "incident-inspect/1",
          scope: "local-core-rules",
          format,
          capture: { file, complete, sha256, bytes: body.length },
          ...(stream ? { events: stream.events.length } : {}),
          modelIdentity: "not_checked",
          status: summarize(observations),
          findings,
        },
        null,
        2,
      ) + "\n",
    );
  } catch {
    process.stderr.write(
      "Could not inspect capture. Use --file FILE --format message|sse --capture complete|partial, " +
      "or --record RESPONSE_RECORD (successful record, at most 2 MiB decoded body).\n",
    );
    process.exitCode = 2;
  }
}

await main();
