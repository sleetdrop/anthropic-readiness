import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const entry = fileURLToPath(new URL("../../scaffold/skills/anthropic-readiness/scripts/src/cli/main.ts", import.meta.url));
function cli(args: string[], env: NodeJS.ProcessEnv = process.env) {
  return spawnSync(process.execPath, [entry, ...args], {
    encoding: "utf8",
    timeout: 5000,
    env,
  });
}
const target = ["--endpoint", "http://127.0.0.1:1/v1", "--model", "synthetic"];
test("a configured directory previews without a token and requires bounded consent to run", (t) => {
  const root = mkdtempSync(join(tmpdir(), "readiness target "));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  writeFileSync(join(root, "target.json"), JSON.stringify({
    endpoint: "http://127.0.0.1:1/v1",
    model: "synthetic",
    apiVersion: "2023-06-01",
    authMode: "bearer",
  }));
  const out = join(root, "run");
  const args = ["--target-dir", root, "--profile", "anthropic-tools-smoke"];
  const preview = cli(["plan", ...args]);
  assert.equal(preview.status, 0, preview.stderr);
  assert.equal(JSON.parse(preview.stdout).plannedRequests, 1);
  assert.equal(cli(["plan", ...args, "--endpoint", "https://elsewhere.invalid"]).stderr.trim(), "conflicting_target_options");
  assert.equal(cli(["run", ...args, "--out", out]).stderr.trim(), "live_opt_in_required");
  assert.equal(cli(["run", ...args, "--allow-live", "--out", out]).stderr.trim(), "target_run_limits_required");
  const missingToken = cli([
    "run", ...args, "--allow-live", "--out", out, "--max-requests", "1", "--run-ms", "1000",
  ]);
  assert.equal(missingToken.status, 2);
  assert.equal(missingToken.stderr.trim(), "target_token_unavailable");
  assert.equal(existsSync(out), false);
});

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

test("the AR_DIAG target group is opt-in and explicit arguments override its fields", () => {
  const env = {
    ...process.env,
    AR_DIAG_ENDPOINT_URL: "https://target.example.invalid/v1",
    AR_DIAG_MODEL: "environment-model",
    AR_DIAG_API_VERSION: "2026-10-21",
    AR_DIAG_AUTH_MODE: "none",
    AR_DIAG_AUTH_TOKEN: "synthetic-private-token",
  };
  const preview = cli(["plan", "--use-env"], env);
  assert.equal(preview.status, 0, preview.stderr);
  const plan = JSON.parse(preview.stdout);
  assert.equal(plan.endpoint, "https://target.example.invalid/v1/messages");
  assert.equal(plan.model, "environment-model");
  assert.equal(plan.apiVersion, "2026-10-21");
  assert.doesNotMatch(preview.stdout, /synthetic-private-token/u);
  assert.match(cli(["plan"], env).stderr, /endpoint_and_model_required/u);
  assert.equal(cli(["plan", ...target], { ...env, AR_DIAG_AUTH_MODE: "invalid" }).status, 0);
  assert.equal(
    cli(["plan", "--use-env"], { ...env, AR_DIAG_AUTH_MODE: "invalid" }).stderr.trim(),
    "invalid_auth_mode",
  );
  const override = cli(
    ["plan", "--use-env", ...target, "--api-version", "2023-06-01", "--auth-mode", "none"],
    { ...env, AR_DIAG_AUTH_MODE: "invalid" },
  );
  assert.equal(override.status, 0, override.stderr);
  assert.equal(JSON.parse(override.stdout).model, "synthetic");
  assert.equal(JSON.parse(override.stdout).endpoint, "http://127.0.0.1:1/v1/messages");
  assert.equal(JSON.parse(override.stdout).apiVersion, "2023-06-01");
});

test("an authenticated AR_DIAG run requires the selected credential before creating output", (t) => {
  const root = mkdtempSync(join(tmpdir(), "readiness-config-auth-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const out = join(root, "assessment");
  const result = cli(["run", "--use-env", ...target, "--allow-live", "--out", out], {
    ...process.env,
    AR_DIAG_AUTH_MODE: "bearer",
    AR_DIAG_AUTH_TOKEN: "",
  });
  assert.equal(result.status, 2);
  assert.equal(result.stderr.trim(), "credential_env_unavailable");
  assert.equal(existsSync(out), false);
});
