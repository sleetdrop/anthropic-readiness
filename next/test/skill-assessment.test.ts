import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const entry = fileURLToPath(
  new URL(
    "../../skills/anthropic-incident-diagnosis/scripts/render-assessment.mts",
    import.meta.url,
  ),
);

test("the Skill renders one report from overlapping runs and links the retained evidence", (t) => {
  const root = mkdtempSync(join(tmpdir(), "skill-assessment-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const source = JSON.parse(
    readFileSync(
      new URL(
        "../../skills/anthropic-incident-diagnosis/references/assessment-example.json",
        import.meta.url,
      ),
      "utf8",
    ),
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
    spawnSync(process.execPath, [entry, "--input", manifest, "--out", join(root, name)], {
      encoding: "utf8",
      timeout: 5000,
    });

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
