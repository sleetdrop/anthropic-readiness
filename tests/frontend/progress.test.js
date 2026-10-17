import assert from "node:assert/strict";
import test from "node:test";
import { reduceSnapshot } from "../../src/anthropic_readiness/resources/web/progress.js";

/** @type {import("../../src/anthropic_readiness/resources/web/progress.js").Execution} */
const execution = {
  schema_version: "1.0",
  run_id: "one",
  config_sha256: "hash",
  target: {},
  contract: {},
  plan: {},
  sequence: 0,
  state: "running",
  case_states: [
    { case_id: "first", state: "pending", checkpoint_path: null, checkpoint_sha256: null },
    { case_id: "second", state: "pending", checkpoint_path: null, checkpoint_sha256: null },
  ],
  actual_requests: 0,
  elapsed_ms: 0,
  started_at: "2026-10-17T00:00:00Z",
  updated_at: "2026-10-17T00:00:00Z",
  finished_at: null,
  spans: [],
  warnings: [],
  result_sha256: null,
  terminal_reason: null,
};

/** @param {number} sequence @param {string} kind @param {import("../../src/anthropic_readiness/resources/web/forms.js").JsonObject} payload */
function event(sequence, kind, payload) {
  return {
    type: "progress",
    value: {
      schema_version: "1.0",
      run_id: "one",
      sequence,
      occurred_at: "2026-10-17T00:00:01Z",
      elapsed_ms: 1000,
      kind,
      payload,
    },
  };
}

test("test_reducer_deduplicates_and_recovers_ahead_cursor", () => {
  const initial = { execution: structuredClone(execution), needsSnapshot: false };
  const first = reduceSnapshot(initial, event(1, "case_started", { case_id: "first" }));
  assert.equal(first.execution?.sequence, 1);
  assert.equal(first.execution?.case_states[0].state, "running");
  assert.equal(first.execution?.case_states[1].state, "pending");
  assert.deepEqual(reduceSnapshot(first, event(1, "case_started", { case_id: "first" })), first);
  const gap = reduceSnapshot(
    first,
    event(3, "request_started", { case_id: "first", request_index: 1 }),
  );
  assert.equal(gap.execution?.sequence, 1);
  assert.equal(gap.execution?.actual_requests, 0);
  assert.equal(gap.needsSnapshot, true);
  const reset = reduceSnapshot(gap, { type: "reset", value: structuredClone(execution) });
  assert.equal(reset.execution?.sequence, 0);
  assert.equal(reset.needsSnapshot, false);
  assert.equal(initial.execution.case_states[0].state, "pending");
});

test("case completion preserves original FAIL and requests never double count", () => {
  const state = {
    execution: { ...structuredClone(execution), sequence: 4, actual_requests: 1 },
    needsSnapshot: false,
  };
  const committed = event(5, "case_committed", {
    case_id: "first",
    status: "FAIL",
    checkpoint_path: "checkpoints/first.json",
    sha256: "abc",
    actual_requests: 1,
  });
  const result = reduceSnapshot(state, committed);
  assert.equal(result.execution?.case_states[0].state, "FAIL");
  assert.equal(result.execution?.actual_requests, 1);
  assert.equal(result.execution?.case_states[1].state, "pending");
});

test("request-start uses the packaged request_index without repeated increments", () => {
  const state = { execution: structuredClone(execution), needsSnapshot: false };
  const started = event(1, "request_started", {
    case_id: "first",
    attempt_id: "attempt",
    request_index: 1,
  });
  const next = reduceSnapshot(state, started);
  assert.equal(next.needsSnapshot, false);
  assert.equal(next.execution?.actual_requests, 1);
  assert.equal(reduceSnapshot(next, started).execution?.actual_requests, 1);
});
