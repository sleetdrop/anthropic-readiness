import assert from "node:assert/strict";
import test from "node:test";
import {
  deriveActivity,
  reduceWorkbench,
} from "../../src/anthropic_readiness/resources/web/workbench.js";
/** @typedef {import("../../src/anthropic_readiness/resources/web/contracts.js").JsonObject} JsonObject */
/** @returns {JsonObject} */
function frame() {
  return {
    generation: "one",
    job: { state: "running" },
    worker: { state: "running", observed_at: "2026-10-19T00:01:00Z" },
    facts: {
      run_id: "run-one",
      execution: {
        sequence: 10,
        elapsed_ms: 5000,
        updated_at: "2026-10-19T00:00:05Z",
        spans: [{ phase: "awaiting_headers", case_id: "case-one", start_ms: 2000, end_ms: null }],
      },
    },
  };
}
/** @returns {import("../../src/anthropic_readiness/resources/web/contracts.js").WorkbenchState} */
function state() {
  return {
    snapshot: frame(),
    readOrder: 1,
    selectedIssue: "stable-issue",
    selectedCase: "case-one",
    connection: "connected",
  };
}
test("activity age, recorded duration and open phase use separate clocks", () => {
  const execution =
    /** @type {import("../../src/anthropic_readiness/resources/web/progress.js").Execution} */ (
      /** @type {unknown} */ (frame().facts && /** @type {JsonObject} */ (frame().facts).execution)
    );
  const view = deriveActivity(execution, Date.parse("2026-10-19T00:01:05Z"));
  assert.equal(view.ageMs, 60000);
  assert.equal(view.recordedElapsedMs, 5000);
  assert.equal(view.phase, "awaiting_headers");
  assert.equal(view.phaseElapsedMs, 3000);
  assert.equal(view.caseId, "case-one");
});
test("no execution and clock disagreement never invent activity", () => {
  assert.deepEqual(deriveActivity(null, Date.now()), {
    updatedAt: null,
    ageMs: null,
    clockDifference: false,
    recordedElapsedMs: null,
    phase: null,
    phaseElapsedMs: null,
    caseId: null,
  });
  const execution =
    /** @type {import("../../src/anthropic_readiness/resources/web/progress.js").Execution} */ (
      /** @type {unknown} */ (/** @type {JsonObject} */ (frame().facts).execution)
    );
  const view = deriveActivity(execution, Date.parse("2026-10-18T00:00:00Z"));
  assert.equal(view.ageMs, null);
  assert.equal(view.clockDifference, true);
});
test("out-of-order reads and stale execution cannot roll back facts", () => {
  const current = state();
  assert.equal(reduceWorkbench(current, { type: "snapshot", value: frame(), order: 0 }), current);
  const stale = frame();
  /** @type {JsonObject} */ (/** @type {JsonObject} */ (stale.facts).execution).sequence = 9;
  assert.equal(reduceWorkbench(current, { type: "snapshot", value: stale, order: 2 }), current);
});
test("a same-generation snapshot updates only real worker observations and retains selection", () => {
  const current = state();
  const incoming = frame();
  incoming.worker = { state: "not_running", observed_at: "2026-10-19T00:02:00Z" };
  const result = reduceWorkbench(current, { type: "snapshot", value: incoming, order: 2 });
  assert.equal(result.snapshot?.worker, incoming.worker);
  assert.equal(result.selectedIssue, "stable-issue");
  assert.equal(result.selectedCase, "case-one");
  assert.equal(
    current.snapshot?.worker && /** @type {JsonObject} */ (current.snapshot.worker).state,
    "running",
  );
});
test("different runs and terminal-to-active snapshots cannot replace a completed source", () => {
  const current = state();
  if (current.snapshot) current.snapshot.job = { state: "completed" };
  assert.equal(reduceWorkbench(current, { type: "snapshot", value: frame(), order: 2 }), current);
  const foreign = frame();
  /** @type {JsonObject} */ (foreign.facts).run_id = "another-run";
  const active = state();
  assert.equal(reduceWorkbench(active, { type: "snapshot", value: foreign, order: 2 }), active);
});
test("connection and explicit selection events do not mutate evidence facts", () => {
  const current = state();
  const reconnect = reduceWorkbench(current, { type: "connection", value: "reconnecting" });
  assert.equal(reconnect.snapshot, current.snapshot);
  const selected = reduceWorkbench(reconnect, { type: "selection", issue: "chosen", caseId: null });
  assert.equal(selected.selectedIssue, "chosen");
  assert.equal(selected.snapshot, current.snapshot);
});
