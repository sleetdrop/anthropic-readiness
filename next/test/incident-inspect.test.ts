import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

const entry = fileURLToPath(new URL("../src/cli/inspect.ts", import.meta.url));
const fixture = (name: string) =>
  fileURLToPath(new URL(`../../tests/fixtures/contracts/core-1.0.0/${name}`, import.meta.url));

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
