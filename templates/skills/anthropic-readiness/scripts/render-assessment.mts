import { readFile, stat, writeFile } from "node:fs/promises";
import { basename, dirname, relative, resolve, sep } from "node:path";
import { parseArgs } from "node:util";
import {
  escapeHtml as escape,
  reportContents,
  reportDocument,
  reportHeading,
} from "./report-document.mts";

const statuses = {
  passed: "Passed",
  partial: "Partially tested",
  deviation: "Protocol deviation",
  rejected: "Explicitly rejected",
  blocked: "Blocked",
  inconclusive: "Inconclusive",
  untested: "Not tested",
} as const;

interface Run {
  id: string;
  label: string;
  model: string;
  version: string;
  resultPath: string;
  requests: number;
  cases: Map<string, string[]>;
}

function record(value: unknown, label: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value))
    throw new Error(`${label} must be an object`);
  return value as Record<string, unknown>;
}

function list(value: unknown, label: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`${label} must be an array`);
  return value;
}

function text(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${label} must be text`);
  return value.trim();
}

function id(value: unknown, label: string): string {
  const result = text(value, label);
  if (!/^[a-zA-Z0-9_-]+$/u.test(result)) throw new Error(`${label} contains invalid characters`);
  return result;
}

async function readJson(path: string): Promise<unknown> {
  return JSON.parse(await readFile(path, "utf8")) as unknown;
}

async function isFile(path: string): Promise<boolean> {
  try {
    return (await stat(path)).isFile();
  } catch (error) {
    if (error && typeof error === "object" && "code" in error && error.code === "ENOENT")
      return false;
    throw error;
  }
}

function link(path: string, output: string, label: string): string {
  const href = relative(dirname(output), path).split(sep).map(encodeURIComponent).join("/");
  return `<a href="${escape(href)}">${escape(label)}</a>`;
}

async function jsonLink(path: string, output: string, label: string): Promise<string> {
  if (!(await isFile(path))) throw new Error(`Missing evidence file ${basename(path)}`);
  const viewer = path + ".html";
  return link((await isFile(viewer)) ? viewer : path, output, label);
}

async function readRun(value: unknown, input: string): Promise<Run> {
  const spec = record(value, "Run");
  const runId = id(spec.id, "Run ID");
  const resultPath = resolve(dirname(input), text(spec.result, "Result path"));
  const result = record(await readJson(resultPath), "Result");
  if (result.schemaVersion !== "typescript-run/1")
    throw new Error(`Unknown result schema for ${runId}`);
  const plan = record(result.plan, "Run plan");
  const cases = new Map<string, string[]>();
  let requests = 0;
  for (const value of list(result.cases, "Run cases")) {
    const entry = record(value, "Case");
    const caseId = id(entry.id, "Case ID");
    if (cases.has(caseId)) throw new Error(`Duplicate case ${caseId} in ${runId}`);
    const captures = list(entry.captures, "Captures").map((value) =>
      id(record(value, "Capture").id, "Capture ID"),
    );
    if (entry.attemptsStarted !== captures.length)
      throw new Error(`Request count does not match captures for ${caseId}`);
    requests += captures.length;
    cases.set(caseId, captures);
  }
  if (result.attemptsStarted !== requests)
    throw new Error(`Request count does not match captures for ${runId}`);
  return {
    id: runId,
    label: text(spec.label, "Run label"),
    model: text(plan.model, "Model"),
    version: text(plan.apiVersion, "API version"),
    resultPath,
    requests,
    cases,
  };
}

function comparison(value: unknown): string {
  if (value === undefined) return "";
  const table = record(value, "Comparison");
  const columns = list(table.columns, "Comparison columns").map((value) =>
    text(value, "Column name"),
  );
  const rows = list(table.rows, "Comparison rows").map((row) => list(row, "Comparison row"));
  if (columns.length < 2 || !rows.length || rows.some((row) => row.length !== columns.length))
    throw new Error("Comparison must have at least two columns and equally sized rows");
  const numeric = columns.map(
    (_, index) => index > 0 && rows.every((row) => typeof row[index] === "number"),
  );
  return `<div class="table-scroll" tabindex="0" role="region" aria-label="Comparison"><table class="finding-table">
<caption>${escape(text(table.caption, "Comparison caption"))}</caption>
<thead><tr>${columns.map((column, index) => `<th scope="col"${numeric[index] ? ' class="number"' : ""}>${escape(column)}</th>`).join("")}</tr></thead>
<tbody>${rows
    .map(
      (row) =>
        `<tr>${row
          .map((value, index) => {
            const cell = escape(
              typeof value === "number" ? String(value) : text(value, "Comparison cell"),
            );
            return index === 0
              ? `<th scope="row">${cell}</th>`
              : `<td${numeric[index] ? ' class="number"' : ""}>${cell}</td>`;
          })
          .join("")}</tr>`,
    )
    .join("")}</tbody>
</table></div>`;
}

async function evidenceLink(
  value: unknown,
  runs: Map<string, Run>,
  output: string,
): Promise<string> {
  const item = record(value, "Evidence");
  const runId = id(item.run, "Evidence run");
  const run = runs.get(runId);
  if (!run) throw new Error(`Unknown evidence run ${runId}`);
  const caseId = id(item.case, "Evidence case");
  const captures = run.cases.get(caseId);
  if (!captures) throw new Error(`Unknown case ${caseId} in ${runId}`);
  const exchange = item.exchange;
  if (typeof exchange !== "number" || !Number.isSafeInteger(exchange) || exchange < 1)
    throw new Error("Evidence exchange must be a positive integer");
  const capture = captures[exchange - 1];
  if (!capture) throw new Error(`No exchange ${exchange} for ${caseId} in ${runId}`);
  const href = await jsonLink(
    resolve(dirname(run.resultPath), `response-${capture}.json`),
    output,
    `Exchange ${exchange}`,
  );
  const location =
    item.location === undefined ? "" : ` · ${escape(text(item.location, "Evidence location"))}`;
  return `<li>${escape(run.label)} · <code>${escape(caseId)}</code> · ${href}${location}</li>`;
}

function referenceLink(value: unknown): string {
  const source = record(value, "Reference");
  const url = new URL(text(source.url, "Reference URL"));
  if (url.protocol !== "https:" || url.username || url.password)
    throw new Error("References must use HTTPS without credentials");
  return `<a href="${escape(url.href)}">${escape(text(source.title, "Reference title"))}</a>`;
}

async function renderAssessment(input: string, output: string): Promise<string> {
  const spec = record(await readJson(input), "Assessment");
  const summary = record(spec.summary, "Summary");
  const date = text(spec.date, "Test date");
  const timestamp = new Date(date);
  if (
    !/^\d{4}-\d{2}-\d{2}$/u.test(date) ||
    !Number.isFinite(+timestamp) ||
    timestamp.toISOString().slice(0, 10) !== date
  )
    throw new Error("Test date must use YYYY-MM-DD");
  const dateLabel = new Intl.DateTimeFormat("en-GB", { dateStyle: "long", timeZone: "UTC" }).format(
    timestamp,
  );
  const runs = new Map<string, Run>();
  const paths = new Set<string>();
  for (const value of list(spec.runs, "Runs")) {
    const run = await readRun(value, input);
    if (runs.has(run.id)) throw new Error(`Duplicate run ${run.id}`);
    if (paths.has(run.resultPath)) throw new Error(`Result file repeated in ${run.id}`);
    paths.add(run.resultPath);
    runs.set(run.id, run);
  }
  const models = new Set([...runs.values()].map((run) => run.model));
  const model = models.values().next().value;
  if (!model || models.size !== 1)
    throw new Error("Use at least one run and one requested model per report");
  const versions = new Set([...runs.values()].map((run) => run.version));
  const distinctCases = new Set([...runs.values()].flatMap((run) => [...run.cases.keys()])).size;
  const requests = [...runs.values()].reduce((sum, run) => sum + run.requests, 0);

  const findingNumbers = new Map<string, number>();
  const findings: string[] = [];
  for (const value of list(spec.findings, "Findings")) {
    const finding = record(value, "Finding");
    const key = id(finding.id, "Finding ID");
    if (findingNumbers.has(key)) throw new Error(`Duplicate finding ${key}`);
    const number = findingNumbers.size + 1;
    findingNumbers.set(key, number);
    const evidence = await Promise.all(
      list(finding.evidence, "Finding evidence").map((item) => evidenceLink(item, runs, output)),
    );
    if (!evidence.length) throw new Error(`Finding ${key} requires an evidence link`);
    const references = list(finding.references ?? [], "References").map(referenceLink);
    findings.push(`<article id="finding-${key}">
<h3>${number}. ${escape(text(finding.title, "Finding title"))}</h3>
<dl class="comparison"><div><dt>Expected</dt><dd>${escape(text(finding.expected, "Expected"))}</dd></div>
<div><dt>Observed</dt><dd>${escape(text(finding.observed, "Observed"))}</dd></div></dl>
${comparison(finding.comparison)}
${finding.nextCheck === undefined ? "" : `<p>${escape(text(finding.nextCheck, "Next check"))}</p>`}
<ul class="meta">${evidence.join("")}</ul>
${references.length ? `<p class="meta">${references.join(" · ")}</p>` : ""}
</article>`);
  }
  const findingRef = (value: unknown) => {
    const key = id(value, "Finding reference");
    const number = findingNumbers.get(key);
    if (!number) throw new Error(`Unknown finding ${key}`);
    return `<a class="finding-ref" href="#finding-${key}" aria-label="Finding ${number}">[${number}]</a>`;
  };
  const capabilities = list(spec.capabilities, "Capabilities").map((value) => {
    const item = record(value, "Capability");
    const name = text(item.name, "Capability name");
    const status = text(item.status, "Capability status");
    if (!Object.hasOwn(statuses, status)) throw new Error(`Unknown capability status for ${name}`);
    const refs = list(item.findings ?? [], "Finding references").map(findingRef);
    return `<tr role="row"><th role="rowheader" scope="row">${escape(name)}</th>
<td role="cell"${status === "deviation" ? ' class="status-fail"' : ""}>${statuses[status as keyof typeof statuses]}</td>
<td role="cell">${escape(text(item.observation, "Capability observation"))}${refs.length ? " " + refs.join(" ") : ""}</td></tr>`;
  });
  if (!capabilities.length) throw new Error("At least one capability is required");

  const runRows = await Promise.all(
    [...runs.values()].map(async (run) => {
      const check = resolve(dirname(run.resultPath), "report.html");
      const checks = (await isFile(check)) ? link(check, output, "Check record") + " · " : "";
      const evidence = await jsonLink(run.resultPath, output, "Result JSON");
      return `<tr><th scope="row">${escape(run.label)}</th><td><code>${escape(run.version)}</code></td>
<td class="number">${run.cases.size}</td><td class="number">${run.requests}</td><td>${checks}${evidence}</td></tr>`;
    }),
  );
  const contents = [
    ["results", "Results by capability"],
    ["findings", "Findings"],
    ["records", "Test records"],
  ] as const;

  return reportDocument(
    `${model} compatibility with Anthropic Messages`,
    "en",
    `<header class="report-header">
<p class="report-type">Anthropic Messages compatibility report</p><h1 id="report-top">${escape(model)}</h1>
<dl class="report-meta"><div><dt>Test date</dt><dd><time datetime="${date}">${escape(dateLabel)}</time></dd></div>
<div><dt>API versions sent</dt><dd>${[...versions].map((version) => `<code>${escape(version)}</code>`).join(", ")}</dd></div>
<div><dt>Test scope</dt><dd>${distinctCases} distinct ${distinctCases === 1 ? "case" : "cases"} selected · ${requests} ${requests === 1 ? "request" : "requests"} sent</dd></div></dl>
</header>
<main>
<section class="report-overview" aria-labelledby="summary"><div>
${reportHeading("summary", "Summary", 1)}
<p class="report-lead">${escape(text(summary.lead, "Summary lead"))}${summary.finding === undefined ? "" : " " + findingRef(summary.finding)}</p>
<p>${escape(text(summary.detail, "Summary detail"))}</p>
<p class="scope-note">${escape(text(summary.scope, "Summary scope"))}</p>
</div>${reportContents(contents, "en")}</section>
<section aria-labelledby="results">${reportHeading("results", "Results by capability", 2)}
<table class="capability-table" role="table"><thead role="rowgroup"><tr role="row">
<th role="columnheader" scope="col">Capability</th><th role="columnheader" scope="col">Result</th><th role="columnheader" scope="col">Observation</th>
</tr></thead><tbody role="rowgroup">${capabilities.join("\n")}</tbody></table></section>
<section aria-labelledby="findings">${reportHeading("findings", "Findings", 3)}
${findings.join("\n") || "<p>No findings were selected for this summary. See the test records for individual results.</p>"}</section>
<section aria-labelledby="records">${reportHeading("records", "Test records", 4)}
<div class="table-scroll" tabindex="0" role="region" aria-labelledby="records"><table>
<caption>Each row describes one run. A case may appear in more than one run.</caption>
<thead><tr><th scope="col">Run</th><th scope="col">API version</th><th scope="col" class="number">Cases</th><th scope="col" class="number">Requests sent</th><th scope="col">Files</th></tr></thead>
<tbody>${runRows.join("\n")}</tbody></table></div></section>
</main>`,
    { interactiveContents: true },
  );
}

try {
  const { values } = parseArgs({ options: { input: { type: "string" }, out: { type: "string" } } });
  if (!values.input || !values.out?.endsWith(".html"))
    throw new Error(
      "Usage: node render-assessment.mts --input assessment.json --out NEW_REPORT.html",
    );
  const output = resolve(values.out);
  const html = await renderAssessment(resolve(values.input), output);
  await writeFile(output, html, { flag: "wx", mode: 0o600 });
} catch (error) {
  process.stderr.write(
    `${error instanceof Error ? error.message : "Could not render assessment"}\n`,
  );
  process.exitCode = 1;
}
