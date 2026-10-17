import assert from "node:assert/strict";
import test from "node:test";
import {
  filterCapabilities,
  selectFinding,
} from "../../src/anthropic_readiness/resources/report-v2.js";

const counts = {
  PASS: 1,
  FAIL: 1,
  INDETERMINATE: 0,
  BLOCKED: 0,
  SKIP: 0,
  pending: 0,
  running: 0,
  not_evaluated: 0,
};
const rows = [
  { key: "mixed", dimensions: { protocol: counts } },
  { key: "passed", dimensions: { protocol: { ...counts, PASS: 2, FAIL: 0 } } },
  { key: "blocked", dimensions: { protocol: { ...counts, PASS: 0, FAIL: 0, BLOCKED: 1 } } },
];

test("filters retain mixed and incomplete states without rewriting counts", () => {
  const before = structuredClone(rows);
  assert.deepEqual(
    filterCapabilities(rows, "attention").map((row) => row.key),
    ["mixed", "blocked"],
  );
  assert.deepEqual(filterCapabilities(rows, "all"), rows);
  assert.deepEqual(rows, before);
});

test("finding lookup follows exact unique IDs and does not select another issue", () => {
  const findings = [
    { id: "finding-1", status: "FAIL" },
    { id: "finding-2", status: "INDETERMINATE" },
  ];
  assert.deepEqual(selectFinding({ findings }, "finding-2"), findings[1]);
  assert.equal(selectFinding({ findings }, "absent"), null);
});
