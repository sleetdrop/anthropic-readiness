import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import test from "node:test";
import { verifyTests } from "../scripts/verification.ts";

function report(tests: number, passed: number, skipped = 0, todo = 0): string {
  return `# tests ${tests}\n# pass ${passed}\n# fail 0\n# cancelled 0\n# skipped ${skipped}\n# todo ${todo}\n`;
}

test("only a complete executed test report can pass the rewrite gate", () => {
  assert.equal(verifyTests(report(2, 2), 0).passed, true);
  for (const [output, code] of [
    [report(0, 0), 0],
    [report(1, 0, 1), 0],
    [report(1, 0, 0, 1), 0],
    [report(1, 1), 1],
    ["", 0],
    [report(2, 1), 0],
  ] as const)
    assert.equal(verifyTests(output, code).passed, false);
});

test("active hooks and CI cannot silently reintroduce the legacy runtime gates", () => {
  const root = new URL("../../", import.meta.url);
  const ci = readFileSync(new URL(".github/workflows/ci.yml", root), "utf8");
  const hook = readFileSync(new URL(".pre-commit-config.yaml", root), "utf8");
  assert.doesNotMatch(ci + hook, /\b(?:uv|python3?|docker|devcontainer)\b/iu);
  assert.match(hook, /npm --prefix next run check/u);
  assert.match(ci, /npm run check/u);
  assert.match(ci, /next\/package-lock\.json/u);
  assert.deepEqual(readdirSync(new URL(".github/workflows/", root)).sort(), ["ci.yml"]);
});
