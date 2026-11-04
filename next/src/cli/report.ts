import type { Observation, Status } from "../domain.ts";
import type { CaptureRecord, CaseResult, RunResult } from "../runner/assessment.ts";

type Language = "zh" | "en";
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

function escape(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replace(/[\\`*_\[\]|]/gu, "\\$&")
    .replace(/[\r\n]+/gu, " ");
}

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
    return zh ? "响应声明的模型名与配置不符" : "Reported model differs from configured identity";
  if (reason === "cache_effect_not_observed")
    return zh ? "未观察到缓存写入后命中" : "Cache write followed by a hit was not observed";
  if (reason === "request_constraint_violated" && ruleId === "STRUCTURED-SCHEMA")
    return zh ? "输出不符合所请求的 JSON 结构" : "Output violates the requested JSON shape";
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

function evidenceLink(capture: CaptureRecord): string {
  const name = `response-${encodeURIComponent(capture.id)}.json`;
  return `[${capture.statusCode === null ? "Capture" : `HTTP ${capture.statusCode}`}](${name})`;
}

export function markdown(report: RunResult, language: Language): string {
  const zh = language === "zh";
  const status = (value: Status) => labels[value][zh ? 0 : 1];
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
  const link = (id: string) => `[${id}](#${id.toLowerCase()})`;
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
    return `| ${escape(item.id)} | ${status(item.status)} | ${status(item.protocolStatus)} | ${behavior} | ${item.attemptsStarted} / ${max} | ${issueLinks || "—"} |`;
  });
  return [
    zh ? "# Anthropic 端点检查记录" : "# Anthropic endpoint check record",
    "",
    `**${status(report.status)}** · ${escape(report.plan.model)} · API ${escape(report.plan.apiVersion)}`,
    "",
    zh
      ? `${deviations} 个用例发现协议偏差。任务行为通过 ${tasksPassed} 项、未通过 ${tasksFailed} 项。受阻 ${blocked} 项、未开始 ${notStarted} 项。协议与任务计数可能涉及同一用例。`
      : `${deviations} cases with protocol deviations. ${tasksPassed} tasks passed and ${tasksFailed} failed. ${blocked} blocked, ${notStarted} ${notStarted === 1 ? "case" : "cases"} not started. Protocol and task counts may overlap.`,
    "",
    zh
      ? `**范围**　${report.cases.length} 个用例 · 发起 ${report.attemptsStarted} / ${report.plan.plannedRequests} 次请求 · SDK / Claude Code 未实测`
      : `**Scope**  ${report.cases.length} cases · ${report.attemptsStarted} / ${report.plan.plannedRequests} requests started · SDK / Claude Code not tested`,
    `**${zh ? "响应声明的模型" : "Reported model"}**　${[...models].map(escape).join(", ") || "—"}`,
    "",
    zh ? "## 主要观测" : "## Findings at a glance",
    "",
    ...findings
      .slice(0, 4)
      .map((finding) =>
        zh
          ? `- ${link(finding.id)} ${escape(finding.label)}（涉及 ${affected(finding)} 个用例）`
          : `- ${link(finding.id)} ${escape(finding.label)} (${affected(finding)} affected cases)`,
      ),
    ...(findings.length
      ? []
      : [zh ? "没有需要汇总的异常观测。" : "No exception observations to summarize."]),
    "",
    zh ? "## 发现与证据" : "## Findings and evidence",
    "",
    zh
      ? "同组表示观测现象相近。用例数去重，观测数可能包含原始事件及其派生消息。证据仅列代表项。"
      : "Groups describe similar observations. Case counts are distinct. Observation counts may include an original event and its derived message. Evidence links show representative exchanges.",
    "",
    ...findings.flatMap((finding) => {
      const entries = [...finding.entries].sort(
        (a, b) =>
          Number(b.observation.location?.eventIndex !== undefined) -
          Number(a.observation.location?.eventIndex !== undefined),
      );
      const sample = entries[0];
      if (!sample) return [];
      const { observation } = sample;
      const location = observation.location;
      const capture = captureFor(sample.item, observation);
      const pointer = location?.pointer;
      const place = [
        location?.eventIndex === undefined ? "" : `SSE #${location.eventIndex}`,
        pointer === undefined ? "" : escape(pointer || (zh ? "根对象" : "root object")),
      ]
        .filter(Boolean)
        .join(" · ");
      const observed = location?.missingKey
        ? zh
          ? "对应字段不存在"
          : "Field absent"
        : observation.reason === "thinking_signature_missing"
          ? zh
            ? "结束前未收到签名事件"
            : "No signature event before block close"
          : observation.ruleId === "HTTP-STATUS" && capture?.statusCode
            ? `HTTP ${capture.statusCode}`
            : "";
      const rules = [...new Set(entries.map((entry) => entry.observation.ruleId))]
        .map(escape)
        .join(", ");
      return [
        `### ${finding.id}`,
        "",
        `**${escape(finding.label)}** · ${status(observation.status)} · ${affected(finding)} ${zh ? "个用例" : "cases"} · ${entries.length} ${zh ? "条观测" : "observations"}`,
        "",
        `- **${zh ? "预期" : "Expected"}**　${escape(observation.expected)}`,
        ...(observed ? [`- **${zh ? "观测" : "Observed"}**　${observed}`] : []),
        `- **${zh ? "代表性证据" : "Representative evidence"}**　${escape(sample.item.id)}${capture ? ` · ${evidenceLink(capture)}` : ""}${place ? ` · ${place}` : ""}`,
        `- **${zh ? "规则" : "Rules"}**　${rules}`,
        "",
      ];
    }),
    zh ? "## 用例矩阵" : "## Case matrix",
    "",
    zh
      ? "| 用例 | 综合状态 | 协议 | 任务 | 请求 | 发现 |"
      : "| Case | Outcome | Protocol | Task | Requests | Findings |",
    "| --- | --- | --- | --- | ---: | --- |",
    ...rows,
    "",
    zh
      ? "任务列的「—」表示该项无需推理任务。请求列保留已发起次数与计划上限，便于识别只执行了首轮的用例。"
      : "A dash in the task column indicates no inference task. Request counts show started and planned exchanges, including cases that stopped after their first exchange.",
    "",
    zh ? "## 范围与原始资料" : "## Scope and original records",
    "",
    `- **${zh ? "规则快照" : "Rule snapshot"}**　${escape(report.plan.contract)}`,
    zh
      ? "- [result.json](result.json) 保存逐用例判断与原始证据。SSE 事件从 0 编号，派生消息与原始事件分别记录。分享前审阅捕获内容。"
      : "- [result.json](result.json) retains per-case judgments and evidence. SSE event indices start at zero. Derived messages are recorded separately from original events. Review captures before sharing.",
    ...report.limitations.map((item) => `- ${escape(item)}`),
    "",
    "[Messages API](https://platform.claude.com/docs/en/api/messages/create) · [Streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)",
    "",
  ].join("\n");
}
