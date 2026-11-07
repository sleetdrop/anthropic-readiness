import assert from "node:assert/strict";
import test from "node:test";
import { selectCases } from "../templates/skills/anthropic-readiness/scripts/src/catalog.ts";
import { summarize, type Observation } from "../templates/skills/anthropic-readiness/scripts/src/domain.ts";

const profiles = ["anthropic-basic", "anthropic-tools-smoke", "anthropic-tool-loop"];

test("all selected cases remain explicit and reserve all six requests", () => {
  const cases = selectCases(profiles);
  assert.deepEqual(
    cases.map((item) => item.id),
    [
      "ANT-MESSAGE-001",
      "ANT-TEXT-SSE-001",
      "ANT-TEXT-SSE-002",
      "ANT-TOOL-FORCED-001",
      "ANT-TOOL-LOOP-001",
    ],
  );
  assert.equal(
    cases.reduce((sum, item) => sum + item.maxRequests, 0),
    6,
  );
  assert.deepEqual(cases.at(-1)?.capabilities, ["tools"]);
});

test("duplicate profiles do not create duplicate endpoint work", () => {
  assert.deepEqual(selectCases([...profiles, ...profiles]), selectCases(profiles));
});

test("empty and unknown scopes are rejected instead of silently testing less", () => {
  assert.throws(() => selectCases([]), /empty_scope/);
  assert.throws(() => selectCases(["anthropic-basic", "unknown"]), /unknown_profile/);
});

function observation(status: Observation["status"], required = true): Observation {
  return {
    ruleId: "fixture",
    ruleVersion: 1,
    dimension: "protocol",
    status,
    required,
    reason: "synthetic",
    expected: "fixture",
    actual: "fixture",
  };
}

test("a confirmed defect survives later transport uncertainty", () => {
  assert.equal(summarize([observation("FAIL"), observation("INDETERMINATE")]), "FAIL");
  assert.equal(summarize([observation("BLOCKED"), observation("FAIL")]), "FAIL");
});

test("missing checks and optional observations cannot earn a pass", () => {
  assert.equal(summarize([]), "INDETERMINATE");
  assert.equal(summarize([observation("PASS", false)]), "INDETERMINATE");
  assert.equal(summarize([observation("PASS"), observation("INDETERMINATE")]), "INDETERMINATE");
  assert.equal(summarize([observation("PASS")]), "PASS");
});
