import assert from "node:assert/strict";
import test from "node:test";
import { renderReport } from "../src/cli/report.ts";
import { renderJsonView } from "../src/cli/json-view.ts";
import type { Observation } from "../src/domain.ts";
import { createPlan, type RunResult } from "../src/runner/assessment.ts";

test("report groups repeated faults, keeps evidence navigable and separates task outcomes", () => {
  const plan = createPlan({
    endpoint: "https://private.invalid",
    model: "example <script>unsafe</script>",
    profiles: ["anthropic-basic"],
  });
  const result: RunResult = {
    schemaVersion: "typescript-run/1",
    plan,
    status: "FAIL",
    clientStatus: "not_tested",
    attemptsStarted: 2,
    elapsedMs: 250,
    limitations: [],
    cases: plan.cases.map((item, index) => {
      const sent = index < 2;
      const id = `capture-${index}`;
      const observation: Observation = {
        ruleId: "MSG-STOP-SEQUENCE-FIELD",
        ruleVersion: 1,
        dimension: "protocol",
        status: "FAIL",
        required: true,
        reason: "missing_field",
        expected: "string or null",
        actual: "missing",
        location: { captureId: id, pointer: "", missingKey: "stop_sequence" },
      };
      return {
        id: item.id,
        lifecycle: sent ? "finished" : "not_run",
        status: sent ? "FAIL" : "INDETERMINATE",
        protocolStatus: sent ? "FAIL" : "INDETERMINATE",
        behaviorStatus: sent ? "PASS" : "INDETERMINATE",
        attemptsStarted: sent ? 1 : 0,
        observations: sent
          ? [observation, { ...observation, required: false, actual: "untrusted response text" }]
          : [],
        captures: sent
          ? [
              {
                id,
                statusCode: 200,
                headers: [],
                end: "eof",
                errorCode: null,
                receivedBytes: 0,
                retainedBytes: 0,
                bodyBase64: "",
                requestBodyBase64: "",
                requestSha256: "",
                sha256: "",
                elapsedMs: 125,
              },
            ]
          : [],
      };
    }),
  };
  const en = renderReport(result, "en");
  assert.match(en, /^<!doctype html>/u);
  assert.match(en, /<html lang="en">/u);
  assert.match(en, /2 cases with protocol deviations/u);
  assert.match(en, /2 tasks passed/u);
  assert.match(en, /1 case not started/u);
  assert.equal([...en.matchAll(/<article id="f\d+"/gu)].length, 1);
  assert.match(en, /2 cases · 2 observations/u);
  assert.match(en, /href="#f01"/u);
  assert.match(en, /<details>/u);
  assert.match(en, /href="response-capture-0\.json\.html"/u);
  assert.match(en, /href="response-capture-1\.json\.html"/u);
  assert.match(en, /href="result\.json\.html"/u);
  assert.match(en, /example &lt;script&gt;unsafe&lt;\/script&gt;/u);
  assert.doesNotMatch(en, /<script|private\.invalid|untrusted response text/u);
  assert.match(renderReport(result, "zh"), /2 个用例发现协议偏差/u);
});

test("JSON viewer highlights tokens while keeping untrusted values inert", () => {
  const json =
    JSON.stringify(
      {
        tag: "</code><script>unsafe</script>",
        number: -2.5,
        list: [true, false, null],
        quoted: 'Escaped "quote": value',
      },
      null,
      2,
    ) + "\n";
  const html = renderJsonView(json, "result.json", "zh");
  assert.match(html, /class="json-key">&quot;tag&quot;<\/span>:/u);
  assert.match(html, /class="json-string">&quot;&lt;\/code&gt;&lt;script&gt;/u);
  assert.match(html, /class="json-number">-2\.5<\/span>/u);
  assert.match(html, /class="json-literal">null<\/span>/u);
  assert.match(html, /href="result\.json"/u);
  assert.doesNotMatch(html, /<script/u);
});
