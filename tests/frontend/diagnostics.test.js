import assert from "node:assert/strict";
import test from "node:test";
import { readEvidence } from "../../src/anthropic_readiness/resources/web/diagnostics.js";

test("evidence display bounds bytes, preserves UTF-8 prefix and cancels the remaining stream", async () => {
  let cancelled = false;
  const body = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode("ABC€remaining evidence"));
    },
    cancel() {
      cancelled = true;
    },
  });
  const value = await readEvidence(new Response(body), 6);
  assert.deepEqual(value, { text: "ABC€", truncated: true });
  assert.equal(cancelled, true);
});
test("complete evidence at the byte limit is not falsely labeled truncated", async () => {
  assert.deepEqual(await readEvidence(new Response("ABC€"), 6), { text: "ABC€", truncated: false });
  assert.deepEqual(await readEvidence(new Response(null), 6), { text: "", truncated: false });
});
