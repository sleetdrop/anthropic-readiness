import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  copyFileSync,
  cpSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test, { type TestContext } from "node:test";

function installSkill(t: TestContext) {
  const root = mkdtempSync(join(tmpdir(), "readiness consumer "));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const skill = join(root, ".agents", "skills", "anthropic-readiness");
  mkdirSync(join(root, ".agents", "skills"), { recursive: true });
  cpSync(new URL("../../scaffold/skills/anthropic-readiness/", import.meta.url), skill, {
    recursive: true,
  });
  writeFileSync(join(root, "package.json"), '{"type":"commonjs"}\n');
  const invoke = (script: string, args: string[]) =>
    spawnSync(process.execPath, [join(skill, "scripts", script), ...args], {
      cwd: root,
      encoding: "utf8",
      timeout: 5000,
    });
  return { root, skill, invoke };
}

test("an installed Skill inspects local evidence and previews a probe from a consumer project", (t) => {
  const { root, skill, invoke } = installSkill(t);
  for (const [fixture, completeness, expected] of [
    ["stream-valid.sse", "complete", "PASS"],
    ["stream-duplicate-start.sse", "complete", "FAIL"],
    ["stream-invalid-tail.sse", "partial", "INDETERMINATE"],
  ] as const) {
    copyFileSync(
      new URL(`../../tests/fixtures/contracts/core-1.0.0/${fixture}`, import.meta.url),
      join(root, "response.sse"),
    );
    const inspected = invoke("src/cli/inspect.ts", [
      "--file", "response.sse", "--format", "sse", "--capture", completeness,
    ]);
    assert.equal(inspected.status, 0, inspected.stderr);
    const result = JSON.parse(inspected.stdout);
    assert.equal(result.status, expected, fixture);
    if (expected === "FAIL") {
      assert.equal(result.findings[0]?.reason, "duplicate_message_start");
      assert.equal(result.findings[0]?.location?.eventIndex, 1);
    }
  }

  symlinkSync(join(skill, "scripts", "src", "cli"), join(skill, "scripts", "linked-cli"), "junction");
  const preview = invoke("linked-cli/main.ts", [
    "plan", "--endpoint", "https://example.invalid/v1", "--model", "synthetic",
    "--profile", "anthropic-tools-smoke", "--max-requests", "1",
  ]);
  assert.equal(preview.status, 0, preview.stderr);
  assert.equal(JSON.parse(preview.stdout).plannedRequests, 1);
});

test("the Skill renders one report from overlapping runs and links the retained evidence", (t) => {
  const { root, skill, invoke } = installSkill(t);
  const source = JSON.parse(
    readFileSync(join(skill, "references", "assessment-example.json"), "utf8"),
  );
  const manifest = join(root, "assessment.json");
  writeFileSync(manifest, JSON.stringify(source));
  for (const [directory, apiVersion, capture] of [
    ["baseline", "2023-06-01", "baseline-capture"],
    ["candidate", "2026-10-21", "candidate-capture"],
  ]) {
    const dir = join(root, directory!);
    mkdirSync(dir);
    writeFileSync(
      join(dir, "result.json"),
      JSON.stringify({
        schemaVersion: "typescript-run/1",
        plan: { model: "example-model", apiVersion, endpoint: "https://private.invalid" },
        clientStatus: "not_tested",
        attemptsStarted: 1,
        cases: [{ id: "ANT-MESSAGE-001", attemptsStarted: 1, captures: [{ id: capture }] }],
      }),
    );
    writeFileSync(join(dir, `response-${capture}.json`), '{"secret":"raw attachment only"}');
  }
  writeFileSync(join(root, "candidate", "response-candidate-capture.json.html"), "<!doctype html>");
  writeFileSync(join(root, "candidate", "report.html"), "<!doctype html>");
  const render = (name: string) =>
    invoke("render-assessment.mts", ["--input", "assessment.json", "--out", name]);

  const output = render("assessment.html");
  assert.equal(output.status, 0, output.stderr);
  const html = readFileSync(join(root, "assessment.html"), "utf8");
  assert.match(html, /<html lang="en">/u);
  assert.match(html, /1 distinct case selected · 2 requests sent/u);
  assert.match(
    html,
    /<p class="report-lead">[^<]+<a class="finding-ref" href="#finding-stop-sequence"/u,
  );
  assert.match(html, /href="candidate\/response-candidate-capture\.json\.html"/u);
  assert.match(html, /href="baseline\/response-baseline-capture\.json"/u);
  assert.match(html, /href="candidate\/report\.html"/u);
  assert.match(html, /<table class="finding-table"/u);
  assert.doesNotMatch(html, /private\.invalid|raw attachment only/u);

  source.findings[0].evidence[0].exchange = 2;
  writeFileSync(manifest, JSON.stringify(source));
  const rejected = render("invalid.html");
  assert.notEqual(rejected.status, 0);
  assert.match(rejected.stderr, /exchange.*2/u);
  assert.equal(existsSync(join(root, "invalid.html")), false);
});
