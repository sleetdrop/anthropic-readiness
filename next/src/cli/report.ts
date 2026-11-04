import type { Observation, Status } from "../domain.ts";
import type { CaptureRecord, CaseResult, RunResult } from "../runner/assessment.ts";

import {
  escapeHtml as escape,
  reportContents,
  reportDocument,
  type ReportLanguage,
} from "./report-document.ts";
interface Finding {
  readonly label: string;
  readonly entries: { item: CaseResult; observation: Observation }[];
}

const labels: Record<Status, readonly [string, string]> = {
  PASS: ["通过", "Passed"],
  FAIL: ["未通过", "Failed"],
  BLOCKED: ["受阻", "Blocked"],
  INDETERMINATE: ["未能判断", "Inconclusive"],
  SKIP: ["无任务或未执行", "Not applicable or skipped"],
};

function findingKey(observation: Observation): string {
  const { dimension, status, ruleId, reason, expected, location } = observation;
  const missing = location?.missingKey;
  if (missing === "stop_sequence") return JSON.stringify([dimension, status, missing]);
  if (missing === "signature" || reason === "thinking_signature_missing")
    return JSON.stringify([dimension, status, "thinking-signature"]);
  const http =
    ruleId === "HTTP-STATUS" && /^\d{3}$/u.test(observation.actual) ? observation.actual : null;
  return JSON.stringify([dimension, status, ruleId, reason, expected, missing, http]);
}

function findingLabel(observation: Observation, zh: boolean): string {
  const { ruleId, reason, expected, location } = observation;
  const missing = location?.missingKey;
  if (missing === "signature" || reason === "thinking_signature_missing")
    return zh ? "Thinking 缺少签名" : "Missing thinking signature";
  if (missing) return zh ? `缺少字段 ${missing}` : `Missing field ${missing}`;
  if (reason === "invalid_request_accepted")
    return zh ? "端点接受了应被拒绝的请求" : "Endpoint accepted a request that should be rejected";
  if (reason === "unexpected_http_status")
    return /^\d{3}$/u.test(observation.actual)
      ? zh
        ? `HTTP ${observation.actual} 阻止了检查`
        : `HTTP ${observation.actual} prevented the check`
      : zh
        ? "未取得预期的 HTTP 响应"
        : "Expected HTTP response was unavailable";
  if (reason === "model_identity_mismatch")
    return zh
      ? "响应声明的模型名与配置不符"
      : "Response model name differs from the configured name";
  if (reason === "cache_effect_not_observed")
    return zh ? "未观察到缓存写入后命中" : "Cache write followed by a hit was not observed";
  if (reason === "request_constraint_violated" && ruleId === "STRUCTURED-SCHEMA")
    return zh ? "输出不符合所请求的 JSON 结构" : "Output violates the requested JSON shape";
  if (reason === "tool_followup_not_sent")
    return zh
      ? "已观察到工具调用，后续请求未发出"
      : "Tool call received. Follow-up request was not sent";
  if (reason === "not_run") return zh ? "用例未开始" : "Case did not start";
  if (observation.dimension === "behavior")
    return zh ? `任务检查 · ${expected}` : `Task check · ${expected}`;
  return `${ruleId} · ${reason}`;
}

function captureFor(item: CaseResult, observation: Observation): CaptureRecord | undefined {
  const captureId = observation.location?.captureId;
  if (captureId)
    return item.captures.find(
      (capture) => capture.id === captureId || capture.derivedMessageId === captureId,
    );
  return item.captures.length === 1 ? item.captures[0] : undefined;
}

function evidenceLink(capture: CaptureRecord, zh: boolean): string {
  const name = `response-${encodeURIComponent(capture.id)}.json`;
  const label =
    capture.statusCode === null ? (zh ? "捕获记录" : "Capture") : `HTTP ${capture.statusCode}`;
  return `<a href="${escape(name)}.html">${label}</a>`;
}

export function renderReport(report: RunResult, language: ReportLanguage): string {
  const zh = language === "zh";
  const status = (value: Status) =>
    `<span class="status-${value.toLowerCase()}">${labels[value][zh ? 0 : 1]}</span>`;
  const groups = new Map<string, Finding>();
  for (const item of report.cases) {
    for (const observation of item.observations) {
      if (!observation.required || observation.status === "PASS" || observation.status === "SKIP")
        continue;
      const key = findingKey(observation);
      const finding = groups.get(key);
      if (finding) finding.entries.push({ item, observation });
      else
        groups.set(key, { label: findingLabel(observation, zh), entries: [{ item, observation }] });
    }
  }
  const affected = (finding: Finding) => new Set(finding.entries.map(({ item }) => item.id)).size;
  const priority = (finding: Finding) =>
    finding.entries[0]?.observation.dimension === "protocol" &&
    finding.entries[0]?.observation.status === "FAIL"
      ? 0
      : 1;
  const findings = [...groups.values()]
    .sort((a, b) => priority(a) - priority(b) || affected(b) - affected(a))
    .map((finding, index) => ({ ...finding, id: `F${String(index + 1).padStart(2, "0")}` }));
  const link = (id: string) => `<a href="#${id.toLowerCase()}">${id}</a>`;
  const count = (predicate: (item: CaseResult) => boolean) => report.cases.filter(predicate).length;
  const deviations = count((item) => item.protocolStatus === "FAIL");
  const tasksPassed = count((item) => item.behaviorStatus === "PASS");
  const tasksFailed = count((item) => item.behaviorStatus === "FAIL");
  const blocked = count((item) => item.status === "BLOCKED");
  const notStarted = count((item) => item.lifecycle === "not_run");
  const models = new Set<string>();
  for (const item of report.cases) {
    for (const { message } of item.captures) {
      if (
        message &&
        typeof message === "object" &&
        "model" in message &&
        typeof message.model === "string"
      )
        models.add(message.model);
    }
  }
  const rows = report.cases.map((item) => {
    const max = report.plan.cases.find((candidate) => candidate.id === item.id)?.maxRequests ?? "?";
    const issueLinks = findings
      .filter((finding) => finding.entries.some((entry) => entry.item === item))
      .map((finding) => link(finding.id))
      .join(", ");
    const behavior = item.behaviorStatus === "SKIP" ? "—" : status(item.behaviorStatus);
    return `<tr><th scope="row"><code>${escape(item.id)}</code></th><td>${status(item.status)}</td><td>${status(item.protocolStatus)}</td><td>${behavior}</td><td class="number">${item.attemptsStarted} / ${max}</td><td>${issueLinks || "—"}</td></tr>`;
  });
  const titles = zh
    ? { overview: "结果概览", findings: "发现与证据", cases: "用例矩阵", scope: "范围与附件" }
    : {
        overview: "Overview",
        findings: "Findings and evidence",
        cases: "Case matrix",
        scope: "Scope and attachments",
      };
  const title = zh ? "Anthropic 端点检查记录" : "Anthropic endpoint check record";
  const caseCount = (value: number) =>
    zh ? `${value} 个用例` : `${value} ${value === 1 ? "case" : "cases"}`;
  const observationCount = (value: number) =>
    zh ? `${value} 条观测` : `${value} ${value === 1 ? "observation" : "observations"}`;
  const dimensions: Record<Observation["dimension"], string> = zh
    ? { protocol: "协议", behavior: "任务", environment: "执行环境", client: "客户端" }
    : { protocol: "Protocol", behavior: "Task", environment: "Execution", client: "Client" };

  const articles = findings.map((finding) => {
    const entries = [...finding.entries].sort(
      (a, b) =>
        Number(b.observation.location?.eventIndex !== undefined) -
        Number(a.observation.location?.eventIndex !== undefined),
    );
    const observation = entries[0]!.observation;
    const capture = captureFor(entries[0]!.item, observation);
    let observed: string;
    if (observation.location?.missingKey) {
      observed = zh ? "对应字段不存在" : "Field absent";
    } else if (observation.reason === "thinking_signature_missing") {
      observed = zh ? "区块关闭前未收到签名事件" : "No signature event before block close";
    } else if (observation.ruleId === "HTTP-STATUS" && capture?.statusCode) {
      observed = `HTTP ${capture.statusCode}`;
    } else if (observation.reason === "tool_followup_not_sent") {
      observed = zh
        ? "首轮调用已观察到，后续请求未发送"
        : "The endpoint returned a tool call. The runner did not send a tool result.";
    } else {
      observed = zh ? "详见捕获或原始检查记录" : "See the captured response or the JSON record.";
    }
    const evidence = new Set(
      entries.map(({ item, observation }) => {
        const location = observation.location;
        const capture = captureFor(item, observation);
        const step = capture ? item.captures.indexOf(capture) + 1 : undefined;
        const position = [
          step === undefined ? "" : zh ? `交换 ${step}` : `Exchange ${step}`,
          location?.eventIndex === undefined ? "" : `SSE #${location.eventIndex}`,
          capture && location && location.captureId === capture.derivedMessageId
            ? zh
              ? "派生消息"
              : "Derived message"
            : "",
          location
            ? `<code>${escape(location.pointer || (zh ? "根对象" : "root object"))}</code>`
            : "",
          location?.missingKey ? `<code>${escape(location.missingKey)}</code>` : "",
        ].filter(Boolean);
        return `<li><span><code>${escape(item.id)}</code></span><span class="occurrence-location"><code>${escape(observation.ruleId)}</code>${position.length ? ` · ${position.join(" · ")}` : ""}</span><span>${capture ? evidenceLink(capture, zh) : "—"}</span></li>`;
      }),
    );
    return `<article id="${finding.id.toLowerCase()}">
<h3><span class="finding-id">${finding.id}</span> ${escape(finding.label)}</h3>
<p class="meta">${dimensions[observation.dimension]} · ${status(observation.status)} · ${caseCount(affected(finding))} · ${observationCount(entries.length)}</p>
<dl class="comparison"><div><dt>${zh ? "预期" : "Expected"}</dt><dd>${escape(observation.expected)}</dd></div><div><dt>${zh ? "代表性观测" : "Observed"}</dt><dd>${observed}</dd></div></dl>
${capture ? `<p class="meta">${zh ? "代表性捕获" : "Example response"} · <code>${escape(entries[0]!.item.id)}</code> · ${evidenceLink(capture, zh)}</p>` : ""}
<details><summary>${zh ? "全部证据位置" : "All occurrences"}</summary><ul class="occurrences">${[...evidence].join("\n")}</ul></details>
</article>`;
  });

  return reportDocument(
    title,
    language,
    `<header class="report-header">
<p class="report-type">${title}</p>
<h1>${escape(report.plan.model)}</h1>
<dl class="report-meta">
<div><dt>${zh ? "结果" : "Result"}</dt><dd>${status(report.status)}</dd></div>
<div><dt>${zh ? "请求 API 版本" : "API version sent"}</dt><dd><code>${escape(report.plan.apiVersion)}</code></dd></div>
<div><dt>${zh ? "用例 · 已发请求" : "Cases · Requests sent"}</dt><dd>${report.cases.length} · ${report.attemptsStarted}</dd></div>
</dl>
</header>
<main>
<section class="report-overview" aria-labelledby="overview">
<div><h2 id="overview">${titles.overview}</h2>
<p>${
      zh
        ? `${deviations} 个用例发现协议偏差。任务行为通过 ${tasksPassed} 项、未通过 ${tasksFailed} 项。受阻 ${blocked} 项、未开始 ${notStarted} 项。`
        : `${deviations} cases with protocol deviations. ${tasksPassed} tasks passed and ${tasksFailed} failed. ${blocked} blocked, ${caseCount(notStarted)} not started.`
    }</p>
<p class="muted">${
      zh
        ? `${caseCount(report.cases.length)} · 发起 ${report.attemptsStarted} / ${report.plan.plannedRequests} 次请求 · SDK / Claude Code 未实测。协议与任务计数可能涉及同一用例。`
        : `${caseCount(report.cases.length)} · ${report.attemptsStarted} / ${report.plan.plannedRequests} requests started · SDK / Claude Code not tested. Protocol and task counts may overlap.`
    }</p>
<p>${zh ? "响应声明的模型" : "Reported model"} <code>${[...models].map(escape).join(", ") || "—"}</code></p>
${
  findings.length
    ? `<ul>${findings
        .slice(0, 4)
        .map(
          (finding) =>
            `<li>${link(finding.id)} ${escape(finding.label)} <span class="muted">· ${caseCount(affected(finding))}</span></li>`,
        )
        .join("")}</ul>`
    : ""
}
</div>
${reportContents(
  Object.entries(titles).filter(([id]) => id !== "overview"),
  language,
)}
</section>
<section aria-labelledby="findings"><h2 id="findings">${titles.findings}</h2>
<p class="muted">${zh ? "按现象归并。观测可来自原始事件及其派生消息，用例数已去重。" : "Each finding lists the number of distinct cases. The observation count may include both raw SSE events and the assembled message."}</p>
${articles.join("\n") || `<p>${zh ? "没有需要汇总的异常观测。" : "No findings in the selected checks."}</p>`}
</section>
<section aria-labelledby="cases"><h2 id="cases">${titles.cases}</h2>
<div class="table-scroll" tabindex="0" role="region" aria-labelledby="cases"><table class="matrix">
<caption>${zh ? "请求列显示已发起次数与计划上限。「—」表示无需推理任务。" : "Requests are shown as started / planned. A dash means the case has no inference task."}</caption>
<thead><tr>${(zh ? ["用例", "综合状态", "协议", "任务", "请求", "发现"] : ["Case", "Outcome", "Protocol", "Task", "Requests", "Findings"]).map((label) => `<th scope="col">${label}</th>`).join("")}</tr></thead>
<tbody>${rows.join("\n")}</tbody>
</table></div></section>
<section aria-labelledby="scope"><h2 id="scope">${titles.scope}</h2>
<ul><li>${zh ? "规则快照" : "Rule snapshot"} <code>${escape(report.plan.contract)}</code></li>
<li><a href="result.json.html">result.json</a> · ${zh ? "逐用例判断及原始证据。SSE 事件从 0 编号。分享附件前请审阅。" : "Case results and captured data. SSE event indices start at zero. Review attachments before sharing."}</li>
${report.limitations.map((item) => `<li>${escape(item)}</li>`).join("")}</ul>
<p><a href="https://platform.claude.com/docs/en/api/messages/create">Messages API</a> · <a href="https://platform.claude.com/docs/en/build-with-claude/streaming">Streaming</a></p>
</section>
</main>`,
  );
}
