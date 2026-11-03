/** Offline inspection of one successful Messages response body. */
import { createHash } from "node:crypto";
import { constants } from "node:fs";
import { open } from "node:fs/promises";
import { parseArgs } from "node:util";
import { summarize, type MessageValidationContext, type Observation } from "../domain.ts";
import { validateMessage } from "../protocol/messages.ts";
import { validateSse } from "../protocol/sse.ts";

const maxBytes = 2 * 1024 * 1024;
const stopReasons = [
  "end_turn",
  "max_tokens",
  "stop_sequence",
  "tool_use",
  "pause_turn",
  "refusal",
  "model_context_window_exceeded",
];

async function readBody(file: string): Promise<Buffer> {
  const handle = await open(file, constants.O_RDONLY | constants.O_NONBLOCK);
  try {
    const stat = await handle.stat();
    if (!stat.isFile() || stat.size > maxBytes) throw new Error("unreadable_or_oversize_capture");
    const buffer = Buffer.alloc(maxBytes + 1);
    let size = 0;
    while (size < buffer.length) {
      const { bytesRead } = await handle.read(buffer, size, buffer.length - size, size);
      if (!bytesRead) break;
      size += bytesRead;
    }
    if (size > maxBytes) throw new Error("unreadable_or_oversize_capture");
    return buffer.subarray(0, size);
  } finally {
    await handle.close();
  }
}

function inspectMessage(
  body: Buffer,
  context: MessageValidationContext,
  complete: boolean,
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
  return validateMessage(message, context);
}

async function main(): Promise<void> {
  try {
    const { values } = parseArgs({
      options: {
        file: { type: "string" },
        format: { type: "string" },
        capture: { type: "string" },
      },
    });
    const { file, format, capture } = values;
    if (
      !file ||
      (format !== "message" && format !== "sse") ||
      (capture !== "complete" && capture !== "partial")
    ) {
      throw new Error("invalid_arguments");
    }
    const complete = capture === "complete";
    const body = await readBody(file);
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
      "Could not inspect capture. Use --file FILE (regular file, at most 2 MiB) " +
        "--format message|sse --capture complete|partial.\n",
    );
    process.exitCode = 2;
  }
}

await main();
