import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { summarize } from "../templates/skills/anthropic-readiness/scripts/src/domain.ts";
import { validateSse } from "../templates/skills/anthropic-readiness/scripts/src/protocol/sse.ts";

const entry = fileURLToPath(new URL("../templates/skills/anthropic-readiness/scripts/src/cli/inspect.ts", import.meta.url));
const fixture = (name: string) =>
  fileURLToPath(new URL(`./fixtures/contracts/core-1.0.0/${name}`, import.meta.url));

function inspect(name: string, format: string, capture: string) {
  const child = spawnSync(
    process.execPath,
    [entry, "--file", fixture(name), "--format", format, "--capture", capture],
    { encoding: "utf8", timeout: 5000 },
  );
  assert.equal(child.status, 0, child.stderr);
  return JSON.parse(child.stdout);
}

test("incident inspector distinguishes normal SSE from a located duplicate start", () => {
  const normal = inspect("stream-valid.sse", "sse", "complete");
  const fault = inspect("stream-duplicate-start.sse", "sse", "complete");
  assert.equal(normal.status, "PASS");
  assert.equal(fault.status, "FAIL");
  assert.ok(
    fault.findings.some(
      (item: { reason: string; location?: { eventIndex: number } }) =>
        item.reason === "duplicate_message_start" && item.location?.eventIndex === 1,
    ),
  );
  assert.notEqual(fault.capture.sha256, normal.capture.sha256);
});

test("a truncated stream is inconclusive and does not claim an absent terminal event is a fault", () => {
  const partial = inspect("stream-invalid-tail.sse", "sse", "partial");
  assert.equal(partial.status, "INDETERMINATE");
  assert.ok(
    partial.findings.some((item: { reason: string }) => item.reason === "capture_incomplete"),
  );
});

test("JSON evidence checks structure without treating a model alias as a protocol defect", () => {
  const result = inspect("message-valid.json", "message", "complete");
  assert.equal(result.status, "PASS");
  assert.equal(result.modelIdentity, "not_checked");
});

test("offline and online SSE validation agree on a null final stop reason", () => {
  const normal = readFileSync(fixture("stream-valid.sse"), "utf8");
  const faulty = normal.replace('"stop_reason":"end_turn"', '"stop_reason":null');
  assert.notEqual(faulty, normal);
  const directory = mkdtempSync(join(tmpdir(), "readiness-inspect-parity-"));
  try {
    const path = join(directory, "faulty.sse");
    writeFileSync(path, faulty);
    const offline = inspectPath(path, "sse", "complete");
    const context = {
      captureId: "parity-capture",
      requestedModel: "model-a",
      modelAliases: [],
      checkModelIdentity: false,
      stopReasons: ["end_turn", "max_tokens", "stop_sequence", "tool_use"],
    };
    const online = validateSse(Buffer.from(faulty), context, {
      completeCapture: true,
      maxEvents: 100,
      maxEventBytes: 16_384,
    });
    assert.equal(offline.status, "FAIL");
    assert.equal(summarize(online.observations), "FAIL");
    assert.ok(offline.findings.some((item: { reason: string }) => item.reason === "final_stop_reason_missing"));
    assert.ok(online.observations.some((item) => item.reason === "final_stop_reason_missing"));
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("inspector verifies and decodes a saved response record in one command", () => {
  const body = readFileSync(fixture("stream-valid.sse"));
  const directory = mkdtempSync(join(tmpdir(), "readiness-record-inspect-"));
  try {
    const path = join(directory, "response-record.json");
    writeFileSync(
      path,
      JSON.stringify({
        statusCode: 200,
        headers: [
          ["content-type", "text/event-stream; charset=utf-8"],
          ["content-encoding", "identity"],
        ],
        end: "eof",
        bodyBase64: body.toString("base64"),
        sha256: createHash("sha256").update(body).digest("hex"),
      }),
    );
    const result = inspectRecord(path);
    assert.equal(result.format, "sse");
    assert.equal(result.capture.complete, true);
    assert.equal(result.status, "PASS");

    writeFileSync(path, JSON.stringify({ statusCode: 200, headers: [], end: "eof", bodyBase64: body.toString("base64"), sha256: "0".repeat(64) }));
    const mismatch = spawnSync(process.execPath, [entry, "--record", path], {
      encoding: "utf8",
      timeout: 5000,
    });
    assert.equal(mismatch.status, 2);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("record inspection preserves count-token route and capture completeness", () => {
  const directory = mkdtempSync(join(tmpdir(), "readiness-count-record-"));
  const writeRecord = (name: string, body: string, end = "eof") => {
    const bytes = Buffer.from(body);
    const path = join(directory, name);
    writeFileSync(
      path,
      JSON.stringify({
        statusCode: 200,
        route: "count_tokens",
        headers: [["content-type", "application/json"]],
        end,
        bodyBase64: bytes.toString("base64"),
        sha256: createHash("sha256").update(bytes).digest("hex"),
      }),
    );
    return path;
  };
  try {
    const normal = inspectRecord(writeRecord("count-normal.json", '{"input_tokens":42}'));
    assert.equal(normal.status, "PASS");
    assert.equal(normal.route, "count_tokens");
    assert.deepEqual(normal.findings, []);

    const malformed = inspectRecord(
      writeRecord("count-malformed.json", '{"input_tokens":"42"}'),
    );
    assert.equal(malformed.status, "FAIL");
    assert.ok(
      malformed.findings.some(
        (item: { reason: string; location?: { pointer: string } }) =>
          item.reason === "invalid_field" && item.location?.pointer === "/input_tokens",
      ),
    );

    const partial = inspectRecord(
      writeRecord("count-partial.json", '{"input_tokens":42}', "read_timeout"),
    );
    assert.equal(partial.status, "INDETERMINATE");
    assert.equal(partial.capture.complete, false);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

function inspectPath(path: string, format: string, capture: string) {
  const child = spawnSync(
    process.execPath,
    [entry, "--file", path, "--format", format, "--capture", capture],
    { encoding: "utf8", timeout: 5000 },
  );
  assert.equal(child.status, 0, child.stderr);
  return JSON.parse(child.stdout);
}

function inspectRecord(path: string) {
  const child = spawnSync(process.execPath, [entry, "--record", path], {
    encoding: "utf8",
    timeout: 5000,
  });
  assert.equal(child.status, 0, child.stderr);
  return JSON.parse(child.stdout);
}
