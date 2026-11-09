import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const entry = fileURLToPath(new URL("../bin/anthropic-readiness.mjs", import.meta.url));

test("the initializer does not impose an upper Node version limit", (t) => {
  const root = mkdtempSync(join(tmpdir(), "readiness future node "));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  // Override only the version guard; real runtime coverage uses the packed scaffold test.
  const preload = "data:text/javascript," + encodeURIComponent(
    'Object.defineProperty(process.versions, "node", { value: "28.0.0" });',
  );
  const project = join(root, "workbench");
  const result = spawnSync(process.execPath, ["--import", preload, entry, "init", project], {
    encoding: "utf8", timeout: 5000,
  });
  assert.equal(result.status, 0, result.stderr);
  assert.ok(existsSync(join(project, ".agents", "skills", "anthropic-readiness", "SKILL.md")));
});

test("unsupported Node releases fail clearly before creating a workbench", (t) => {
  const root = mkdtempSync(join(tmpdir(), "readiness unsupported node "));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const version of ["20.20.2", "23.11.0", "27.0.0-alpha.1"]) {
    const preload = "data:text/javascript," + encodeURIComponent(
      `Object.defineProperty(process.versions, "node", { value: ${JSON.stringify(version)} });`,
    );
    const project = join(root, version);
    const result = spawnSync(process.execPath, ["--import", preload, entry, "init", project], {
      encoding: "utf8", timeout: 5000,
    });
    assert.equal(result.status, 1, version);
    assert.match(result.stderr, /Node\.js 22\.18\+ \(22\.x\) or 24\.2\+/u);
    assert.ok(result.stderr.includes(version));
    assert.equal(existsSync(project), false);
  }
});
