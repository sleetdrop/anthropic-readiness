import assert from "node:assert/strict";
import test from "node:test";
import {
  readingTarget,
  jsonRows,
} from "../../src/anthropic_readiness/resources/web/evidence-json.js";

test("only supported checked reasons or explicit pointers supply a reading target", () => {
  const value =
    /** @type {import('../../src/anthropic_readiness/resources/web/contracts.js').JsonObject} */ ({
      type: "message",
      model: "alias",
      stop_reason: "end_turn",
      usage: { input_tokens: 1, output_tokens: "8" },
    });
  assert.deepEqual(readingTarget(value, null, "invalid_message_structure"), {
    pointer: "",
    missing: true,
  });
  value.stop_sequence = null;
  assert.deepEqual(readingTarget(value, null, "invalid_message_structure"), {
    pointer: "/usage/output_tokens",
    missing: false,
  });
  assert.equal(readingTarget(value, null, "unsupported_reason"), null);
  assert.deepEqual(readingTarget(value, "/model", "unsupported_reason"), {
    pointer: "/model",
    missing: false,
  });
  assert.equal(readingTarget(value, "/model/no-child", "unsupported_reason"), null);
  assert.equal(readingTarget(value, "/bad~2key", "unsupported_reason"), null);
  assert.deepEqual(
    readingTarget({ type: "message_start", message: value }, null, "model_identity_mismatch"),
    { pointer: "/message/model", missing: false },
  );
  assert.deepEqual(readingTarget({ type: "message_start" }, null, "duplicate_message_start"), {
    pointer: "/type",
    missing: false,
  });
});

test("tree projections preserve punctuation, escaped pointers and bounded rows", () => {
  const value = { "a/b": { "~key": "<img>" }, list: [null, 8] };
  const result = jsonRows(value, new Set(["", "/a~1b", "/list"]), 50);
  assert.equal(result.limited, false);
  assert.equal(result.rows.find((r) => r.pointer === "/a~1b/~0key")?.text, '    "~key": "<img>"');
  assert.equal(result.rows.find((r) => r.pointer === "/list/0")?.text, "    null,");
  assert.equal(result.rows.filter((r) => !r.closing).length, 6);
  const limited = jsonRows({ a: 1, b: 2, c: 3 }, new Set([""]), 2);
  assert.equal(limited.limited, true);
  assert.equal(limited.rows.length, 2);
});

test("a bounded reading window includes late targets without rendering their earlier siblings", () => {
  const value = {
    ...Object.fromEntries(Array.from({ length: 600 }, (_, i) => ["field" + i, i])),
    usage: { output_tokens: "8" },
  };
  const projection = jsonRows(value, new Set(["", "/usage"]), 500, "/usage/output_tokens");
  assert.ok(projection.start > 0);
  assert.ok(projection.rows.some((row) => row.pointer === "/usage/output_tokens" && !row.closing));
  assert.ok(projection.rows.length <= 500);
});
