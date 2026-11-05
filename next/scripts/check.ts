/** Small shared check entry point for local use, hooks and CI. */
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { verifyTests } from "./verification.ts";

const root = new URL("../", import.meta.url);
const output = new URL("artifacts/checks/", root);
mkdirSync(output, { recursive: true });
const startedAt = new Date().toISOString();
writeFileSync(
  new URL("result.json", output),
  JSON.stringify({
    schemaVersion: 1,
    scope: "incident-diagnosis",
    startedAt,
    status: "running",
  }),
);
const require = createRequire(import.meta.url);
function run(name: string, args: string[], timeout: number) {
  const child = spawnSync(process.execPath, args, {
    cwd: fileURLToPath(root),
    encoding: "utf8",
    timeout,
    maxBuffer: 16 * 1024 * 1024,
  });
  const log = (child.stdout ?? "") + (child.stderr ?? "") + (child.error?.message ?? "");
  writeFileSync(new URL(`${name}.log`, output), log);
  process.stdout.write(log);
  return { exitCode: child.status, log };
}
const types = run("types", [require.resolve("typescript/bin/tsc"), "--noEmit"], 60_000);
const tests =
  types.exitCode === 0 ? run("tests", ["--test", "--test-reporter=tap"], 120_000) : null;
const judged = tests ? verifyTests(tests.log, tests.exitCode) : null;
const passed = types.exitCode === 0 && judged?.passed === true;
writeFileSync(
  new URL("result.json", output),
  JSON.stringify(
    {
      schemaVersion: 1,
      scope: "incident-diagnosis",
      node: process.version,
      startedAt,
      status: passed ? "passed" : "failed",
      types: types.exitCode === 0 ? "passed" : "failed",
      tests: judged ?? { passed: false, reason: "not_run", counts: null },
    },
    null,
    2,
  ) + "\n",
);
console.log(`Skill checks: ${passed ? "passed" : "failed"}; endpoint coverage is separate.`);
process.exitCode = passed ? 0 : 1;
