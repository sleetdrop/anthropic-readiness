import assert from "node:assert/strict";
import test from "node:test";
import { legacyLocation } from "../../src/anthropic_readiness/resources/web/workbench-links.js";

const cases = ["ANT-MESSAGE-001", "ANT-TEXT-SSE-001"];
const findings = ["finding-1", "finding-2"];
test("old capability, issue and case fragments select canonical local views", () => {
  for (const [hash, view, key, value] of [
    ["#capabilities", "cases", null, null],
    ["#finding-2", "issues", "issue", "finding-2"],
    ["#case-ANT-TEXT-SSE-001", "cases", "case", "ANT-TEXT-SSE-001"],
  ]) {
    const resolved = legacyLocation(`http://localhost:8766/runs/local${hash}`, cases, findings);
    assert.ok(resolved);
    assert.equal(resolved.origin, "http://localhost:8766");
    assert.equal(resolved.pathname, "/runs/local");
    assert.equal(resolved.searchParams.get("view"), view);
    if (key) assert.equal(resolved.searchParams.get(key), value);
    assert.equal(resolved.hash, "");
  }
});
test("unknown or malformed fragments cannot select an unrecorded case or issue", () => {
  for (const hash of ["#case-UNKNOWN", "#finding-99", "#%E0%A4%A", "#javascript:alert(1)"]) {
    assert.equal(legacyLocation(`http://localhost:8766/runs/local${hash}`, cases, findings), null);
  }
});
