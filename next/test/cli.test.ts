import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const entry = fileURLToPath(new URL("../src/cli/main.ts", import.meta.url));
function cli(args: string[]) {
  return spawnSync(process.execPath, [entry, ...args], {
    encoding: "utf8",
    timeout: 5000,
  });
}
const target = ["--endpoint", "http://127.0.0.1:1/v1", "--model", "synthetic"];
test("CLI preview is usable without live consent and preserves full case/request scope", () => {
  const child = cli(["plan", ...target]);
  assert.equal(child.status, 0, child.stderr);
  const plan = JSON.parse(child.stdout);
  assert.equal(plan.plannedRequests, 27);
  assert.equal(plan.cases.length, 22);
  assert.deepEqual(plan.profiles, ["anthropic-core"]);
});
test("CLI run refuses admission before creating output without explicit opt-in", (t) => {
  const root = mkdtempSync(join(tmpdir(), "readiness-cli-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const out = join(root, "assessment");
  const child = cli(["run", ...target, "--out", out]);
  assert.equal(child.status, 2);
  assert.match(child.stderr, /live_opt_in_required/u);
  assert.equal(existsSync(out), false);
});
test("CLI rejects insufficient budgets instead of silently executing less", () => {
  const child = cli(["plan", ...target, "--max-requests", "4"]);
  assert.equal(child.status, 2);
  assert.match(child.stderr, /insufficient_request_budget/u);
});

test("a named credential must be available before any output or request", (t) => {
  const root = mkdtempSync(join(tmpdir(), "readiness-cli-auth-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const out = join(root, "assessment");
  const child = spawnSync(
    process.execPath,
    [entry, "run", ...target, "--allow-live", "--out", out, "--auth-env", "SYNTHETIC_EMPTY_TOKEN"],
    {
      encoding: "utf8",
      timeout: 5000,
      env: { ...process.env, SYNTHETIC_EMPTY_TOKEN: "" },
    },
  );
  assert.equal(child.status, 2);
  assert.equal(child.stderr.trim(), "credential_env_unavailable");
  assert.equal(existsSync(out), false);
});
