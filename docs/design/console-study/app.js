"use strict";

// All observations are fictional. This prototype has no network execution path.
const messages = {
  zh: {
    skip: "跳至内容", workspace: "本机工作区", prototype: "交互样稿 · 模拟数据", records: "测试记录", assessment: "端点兼容性检查",
    export: "导出…", retest: "按原配置复测", scope: "5 个用例 · 3 个测试集", configuration: "查看运行配置", scenario: "演示状态", completed: "已完成", running: "运行中",
    overview: "概览", issues: "问题", close: "关闭", dark: "深色", light: "浅色",
    disclaimer: "设计预览 · 所有结果均为虚构，不会访问模型端点。", coverageNote: "当前目录：5 个正式用例。界面样稿不增加测试覆盖。",
    headline: "发现 2 类协议偏差，另有 1 项未能判断", outcome: "4 个任务行为通过，1 个未能判断。协议检查有偏差；Claude Code 工作流尚未实测。",
    needsAttention: "需要排查", liveHeadline: "正在检查工具结果往返", liveOutcome: "前 4 个用例已有结果。当前等待第 2 步响应，已发现的问题可立即查看。",
    finalizing: "第 5 / 5 个用例 · 等待工具结果响应", finishedCases: "已结束用例", startedRequests: "已发出请求 / 上限", elapsed: "耗时", client: "Claude Code", notTested: "未实测", noVerdict: "不能据此判断客户端可用性",
    coverage: "用例结果", twoDimensions: "任务行为与协议分别判定", case: "用例 / 请求数", behavior: "任务", protocol: "协议", duration: "耗时", requests: "次请求", requestOne: "1 次请求", requestTwo: "2 次请求",
    pass: "通过", fail: "偏差", unknown: "未判断", active: "运行中", observed: "实际观测", all: "全部", deviations: "协议偏差", conditions: "未能判断",
    matrixNote: "协议偏差不等于客户端不可用；超时不直接判定为协议错误。", issueSummary: "待排查问题", grouped: "按原因归并", allIssues: "查看全部问题", affectedTwo: "影响 2 个用例", affectedOne: "影响 1 个用例",
    issue0: "响应缺少停止字段", issue1: "重复发送流起始事件", issue2: "等待流数据超时",
    blurb0: "任务已返回结果，但 stop_sequence 字段缺失。", blurb1: "文本已生成，事件序列中出现两个 message_start。", blurb2: "10 秒内未收到后续数据，证据不足以完成判定。",
    case0: "普通消息", case1: "流式文本", case2: "流式计数", case3: "强制工具选择", case4: "工具结果往返",
    inspectorHint: "选择问题查看原因、影响与原始证据", issueLabel: "问题", observation: "字段差异", sequence: "事件顺序", timing: "等待记录", response: "响应原文", request: "请求", references: "依据与范围",
    description0: "响应应包含 stop_sequence；两个响应均未提供该键。缺失与显式 null 是不同的观测结果。",
    description1: "同一条 SSE 消息中观测到两次 message_start。后续文本可以拼接，但事件生命周期存在偏差。",
    description2: "流式计数在读取期间触发 10 秒等待上限。未取得完整响应，任务与协议检查均保留为未能判断。",
    expected: "期望", actual: "实际", missing: "缺少该键", present: "键存在，值为 null", excerpt: "相关字段节选 · 完整内容见“响应原文”", pointer: "响应位置：$.stop_sequence",
    impact: "已知影响", nextStep: "建议排查", impact0: "两个用例都返回了任务预期结果。严格检查会拒绝缺失字段；本次没有运行 Claude Code，不能断言它会受影响。",
    next0: "核对端点输出与各层转换后的响应，定位字段在哪一层丢失；修复后按原配置复测。当前证据无法确定具体责任环节。",
    impact1: "本样例中的文本任务通过。依赖合法事件状态转换的客户端可能拒绝此流，具体客户端行为需要另行实测。",
    next1: "沿链路检查是否重复包装 SSE 消息起始事件；保留完整事件序列，再复测流式文本用例。",
    impact2: "尚不能区分模型响应慢、链路等待或其他执行条件。此结果不会计作协议偏差，也不会被视为通过。",
    next2: "先核对读取等待上限与代理超时配置，检查是否持续返回数据；条件明确后复测，保留此次未完成的观测。",
    technical: "技术标识与证据位置", synthetic: "以下内容均为样稿生成的虚构证据。", sourceNote: "正式实现应链接本次运行锁定的规则快照及其官方引用。这里展示的是信息组织方式。",
    ref0: "Messages 响应结构：区分字段缺失与显式空值。", ref1: "Streaming 生命周期：同一消息的起始事件与结束事件应按约定出现。", ref2: "本次读取超时来自演示配置，不是 Anthropic 协议要求。",
    step: "顺序", event: "事件", result: "判定", valid: "正常", duplicate: "重复起始", partial: "已收到部分数据", deadline: "读取等待达到上限", notCompared: "未完成协议判定",
    planTitle: "原配置复测", planIntro: "复用端点、模型和测试范围。旧记录作为对照保留。", target: "端点", model: "模型", planScope: "测试范围", planBudget: "执行上限", budgetValue: "6 次请求 · 总时限 60 秒 · 读取等待 10 秒",
    mockStart: "演示复测过程", mockNote: "这是交互演示。点击后切换到模拟运行状态，不会发送 API 请求。", configured: "运行配置", scopeValue: "基础消息、工具选择、工具结果往返", restartNote: "此样稿未实现自动推进；可用“演示状态”切回已完成。",
    exportTitle: "你想如何使用结果？", exportIntro: "先选择用途，文件格式与内容随后确认。", readable: "阅读与留档", readableNote: "独立 HTML · 结论、用例矩阵、问题与依据，可离线阅读。", bundle: "交给同事与 Agent 排查", bundleNote: "建议的诊断包 · 摘要、结构化结果、请求响应与规则引用。", sampleDownload: "下载模拟摘要 JSON", sampleDownloadNote: "样稿仅导出带有模拟标记的摘要，不生成正式报告或完整诊断包。", previewTitle: "诊断包内容预览", fileSummary: "建议包含 4 类内容；真实文件数与大小应在导出时计算。", readingSummary: "阅读报告应独立说明结论、范围、证据和限制。此轮仅预览控制台的交互设计。",
    stop: "演示停止", stoppedTitle: "运行已停止", stoppedBody: "已结束用例的结果保留，工具结果往返尚未完成。未完成部分不会计作通过。", stopped: "已停止", pending: "未完成", noIssues: "当前筛选下没有问题", cancelled: "工具结果往返未完成，未计入已结束用例。", exportManifest: "查看建议的文件组织", selectedCase: "当前用例", syntheticTime: "演示时间", completedNote: "运行已结束；仍需区分协议偏差与实际客户端影响。"
  },
  en: {
    skip: "Skip to content", workspace: "Local workspace", prototype: "Prototype · Synthetic data", records: "Test runs", assessment: "Endpoint compatibility assessment",
    export: "Export…", retest: "Rerun configuration", scope: "5 cases · 3 profiles", configuration: "Run configuration", scenario: "Demo state", completed: "Completed", running: "Running",
    overview: "Overview", issues: "Issues", close: "Close", dark: "Dark", light: "Light",
    disclaimer: "Design preview · Fictional results. No model endpoint is contacted.", coverageNote: "Current catalog: 5 formal cases. This prototype adds no coverage.",
    headline: "2 protocol deviations; 1 inconclusive result", outcome: "4 tasks passed; 1 is inconclusive. Protocol deviations were observed. Claude Code was not tested.",
    needsAttention: "Needs investigation", liveHeadline: "Checking the tool-result round trip", liveOutcome: "The first 4 cases have results. Waiting for the second exchange; observed issues are available now.",
    finalizing: "Case 5 / 5 · Waiting for tool-result response", finishedCases: "Cases finished", startedRequests: "Requests started / limit", elapsed: "Elapsed", client: "Claude Code", notTested: "Not tested", noVerdict: "Client readiness is not established",
    coverage: "Case results", twoDimensions: "Task and protocol judged separately", case: "Case / requests", behavior: "Task", protocol: "Protocol", duration: "Duration", requests: "requests", requestOne: "1 request", requestTwo: "2 requests",
    pass: "Pass", fail: "Deviation", unknown: "Inconclusive", active: "Running", observed: "Observed", all: "All", deviations: "Protocol", conditions: "Inconclusive",
    matrixNote: "Protocol deviations do not prove client failure. Timeouts are not protocol violations.", issueSummary: "Investigate", grouped: "Grouped by cause", allIssues: "View all issues", affectedTwo: "Affects 2 cases", affectedOne: "Affects 1 case",
    issue0: "Stop field absent from responses", issue1: "Duplicate stream start event", issue2: "Timed out waiting for stream data",
    blurb0: "Tasks returned results, but stop_sequence is missing.", blurb1: "Text was generated; two message_start events were received.", blurb2: "No further data within 10 seconds; incomplete evidence.",
    case0: "Plain message", case1: "Streamed text", case2: "Streamed counting", case3: "Forced tool choice", case4: "Tool-result round trip",
    inspectorHint: "Select an issue to inspect its impact and evidence", issueLabel: "Issue", observation: "Field difference", sequence: "Event sequence", timing: "Wait record", response: "Raw response", request: "Request", references: "Basis & scope",
    description0: "The response should include stop_sequence. Two responses omit the key. An absent key and an explicit null are different observations.",
    description1: "Two message_start events occurred within one SSE message. Text can be assembled, but the event lifecycle deviates from expectations.",
    description2: "Streamed counting reached the 10-second read deadline. Without a complete response, both task and protocol remain inconclusive.",
    expected: "Expected", actual: "Actual", missing: "Key absent", present: "Key present; value null", excerpt: "Relevant fields only · Full payload under Raw response", pointer: "Response location: $.stop_sequence",
    impact: "Observed impact", nextStep: "Investigate next", impact0: "Both cases returned the expected task results. Strict validation rejects the absent field. Claude Code was not run, so its behavior is not established.",
    next0: "Compare the endpoint output and responses after each conversion layer. Find where the field is lost, then rerun this configuration. These observations do not identify the responsible layer.",
    impact1: "The sample text task passed. A client enforcing valid event transitions may reject the stream; actual client behavior needs a separate test.",
    next1: "Check whether any layer emits the SSE start event twice. Preserve the full event sequence and rerun streamed text.",
    impact2: "Slow inference, waiting in the chain, or other execution conditions remain possible. This observation counts as neither a protocol deviation nor a pass.",
    next2: "Check read deadlines and proxy timeouts, and whether data continues to arrive. Rerun under explicit conditions while preserving this incomplete observation.",
    technical: "Technical identifiers & evidence location", synthetic: "The following evidence is fictional and generated for this prototype.", sourceNote: "Production should link the run's pinned rule snapshot and official references. This sample demonstrates the information structure.",
    ref0: "Messages response structure: absent keys and explicit null values are distinct.", ref1: "Streaming lifecycle: message start and end events must follow the expected sequence.", ref2: "The read deadline comes from demo configuration, not the Anthropic protocol.",
    step: "Order", event: "Event", result: "Check", valid: "Valid", duplicate: "Duplicate start", partial: "Partial data received", deadline: "Read deadline reached", notCompared: "Protocol check incomplete",
    planTitle: "Rerun the configuration", planIntro: "Reuse the target, model and test scope. Keep the original run as the baseline.", target: "Endpoint", model: "Model", planScope: "Scope", planBudget: "Limits", budgetValue: "6 requests · 60s total · 10s read wait",
    mockStart: "Simulate rerun", mockNote: "Interactive demonstration only. This switches to a simulated running state without sending API requests.", configured: "Run configuration", scopeValue: "Basic messages, tool choice, tool-result round trip", restartNote: "This sample does not advance automatically. Use Demo state to return to Completed.",
    exportTitle: "How will you use these results?", exportIntro: "Choose a purpose before selecting formats and contents.", readable: "Read & archive", readableNote: "Standalone HTML · Summary, case matrix, issues and references for offline reading.", bundle: "Investigate with a colleague & Agent", bundleNote: "Proposed diagnostic bundle · Summary, structured results, exchanges and rule references.", sampleDownload: "Download synthetic summary JSON", sampleDownloadNote: "This prototype exports a labeled synthetic summary, not a production report or complete diagnostic bundle.", previewTitle: "Diagnostic bundle preview", fileSummary: "4 proposed content groups; compute actual file counts and sizes when exporting.", readingSummary: "The reading report should explain conclusions, scope, evidence and limitations independently. This iteration previews console interactions only.",
    stop: "Simulate stop", stoppedTitle: "Run stopped", stoppedBody: "Finished case results are retained. The tool-result round trip is incomplete and does not count as passed.", stopped: "Stopped", pending: "Incomplete", noIssues: "No issues match this filter", cancelled: "Tool-result round trip remains incomplete; excluded from finished cases.", exportManifest: "View proposed file organization", selectedCase: "Selected case", syntheticTime: "Demo timing", completedNote: "Execution finished; protocol deviations and demonstrated client impact remain distinct."
  }
};
const initial = new URLSearchParams(location.search);
const state = { lang: initial.get("lang") === "en" ? "en" : "zh", theme: initial.get("theme") === "dark" ? "dark" : "light", view: initial.get("view") === "issues" ? "issues" : "overview", scenario: ["running", "stopped"].includes(initial.get("state")) ? initial.get("state") : "completed", issue: 0, filter: "all", evidence: "observation", caseIndex: 0 };
const cases = [
  { id: "ANT-MESSAGE-001", requests: 1, duration: "1.1s", task: "pass", protocol: "fail", issue: 0 },
  { id: "ANT-TEXT-SSE-001", requests: 1, duration: "2.6s", task: "pass", protocol: "fail", issue: 1 },
  { id: "ANT-TEXT-SSE-002", requests: 1, duration: "10.0s", task: "unknown", protocol: "unknown", issue: 2 },
  { id: "ANT-TOOL-FORCED-001", requests: 1, duration: "0.9s", task: "pass", protocol: "fail", issue: 0 },
  { id: "ANT-TOOL-LOOP-001", requests: 2, duration: "4.2s", task: "pass", protocol: "pass", issue: null }
];
const affected = [[0, 3], [1], [2]];
const $ = (selector) => document.querySelector(selector);
const t = (key) => messages[state.lang][key];
const esc = (value) => String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const badge = (status, label = status) => `<span class="badge ${status}">${t(label)}</span>`;
const issueTone = (index) => index === 2 ? "unknown" : "fail";
function syncUrl() {
  const query = new URLSearchParams({ lang: state.lang, theme: state.theme, view: state.view, state: state.scenario });
  history.replaceState(null, "", `?${query}`);
}
function render() {
  document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
  document.documentElement.dataset.theme = state.theme;
  document.querySelectorAll("[data-text]").forEach((node) => { node.textContent = t(node.dataset.text); });
  $("#language").textContent = state.lang === "zh" ? "English" : "中文";
  $("#theme").textContent = t(state.theme === "light" ? "dark" : "light");
  $("#theme").setAttribute("aria-label", state.lang === "zh" ? `切换到${$("#theme").textContent}主题` : `Switch to ${$("#theme").textContent.toLowerCase()} theme`);
  $("#run-status").textContent = t(state.scenario);
  $("#run-status").classList.toggle("active", state.scenario === "running");
  $("#scenario").value = state.scenario;
  $("#retest").textContent = t(state.scenario === "running" ? "stop" : "retest");
  document.querySelectorAll("[data-view]").forEach((node) => {
    if (node.dataset.view === state.view) node.setAttribute("aria-current", "page"); else node.removeAttribute("aria-current");
  });
  $("#view-root").innerHTML = state.view === "overview" ? overview() : inspector();
  syncUrl();
}
function overview() {
  const running = state.scenario === "running";
  const stopped = state.scenario === "stopped";
  const rows = cases.map((item, index) => {
    const status = index === 4 && (running || stopped) ? (running ? "active" : "pending") : null;
    const task = status ? `<span class="badge ${running ? "live" : "neutral"}">${t(status)}</span>` : badge(item.task);
    const protocol = status ? `<span class="badge neutral">${t(status)}</span>` : badge(item.protocol);
    return `<tr><td><button type="button" class="text-button case-name" data-case="${index}">${t(`case${index}`)}</button><span class="case-id">${t(item.requests === 1 ? "requestOne" : "requestTwo")}</span></td><td>${task}</td><td>${protocol}</td><td class="numeric duration">${status ? "—" : item.duration}</td></tr>`;
  }).join("");
  const issues = [0, 1, 2].map((index) => `<button class="issue-row" type="button" data-issue="${index}"><span class="issue-line"><strong>${t(`issue${index}`)}</strong>${badge(issueTone(index), index === 2 ? "conditions" : "deviations")}</span><p>${t(index === 0 ? "affectedTwo" : "affectedOne")} · ${t(`blurb${index}`)}</p></button>`).join("");
  return `<section class="outcome"><div><h2>${t(running ? "liveHeadline" : stopped ? "stoppedTitle" : "headline")}</h2><p>${t(running ? "liveOutcome" : stopped ? "stoppedBody" : "outcome")}</p>${running ? `<div class="progress-area"><progress value="4" max="5" aria-label="${t("finishedCases")}"></progress><span class="progress-caption">${t("finalizing")}</span></div>` : ""}</div>${badge(running ? "live" : stopped ? "neutral" : "fail", running ? "running" : stopped ? "stopped" : "needsAttention")}</section>
    <section class="metrics" aria-label="${t("overview")}"><div class="metric"><span class="metric-label">${t("finishedCases")}</span><span class="metric-value">${running || stopped ? 4 : 5}<small>/ 5</small></span></div><div class="metric"><span class="metric-label">${t("startedRequests")}</span><span class="metric-value">6<small>/ 6</small></span></div><div class="metric"><span class="metric-label">${t("elapsed")}</span><span class="metric-value">${running || stopped ? "16.2" : "18.8"}<small>s</small></span></div><div class="metric"><span class="metric-label">${t("client")}</span><span class="metric-value">${t("notTested")}</span></div></section>
    <div class="overview-grid"><section class="panel"><div class="panel-heading"><h3>${t("coverage")}</h3><small>${t("twoDimensions")}</small></div><table class="case-table"><thead><tr><th scope="col">${t("case")}</th><th scope="col">${t("behavior")}</th><th scope="col">${t("protocol")}</th><th scope="col" class="duration">${t("duration")}</th></tr></thead><tbody>${rows}</tbody></table><p class="panel-note">${t("matrixNote")}</p></section>
    <section class="panel"><div class="panel-heading"><h3>${t("issueSummary")} <span class="count">3</span></h3><small>${t("grouped")}</small></div>${issues}<button type="button" class="text-button panel-link" data-view="issues">${t("allIssues")}</button></section></div>`;
}
function inspector() {
  const visible = [0, 1, 2].filter((index) => state.filter === "all" || (state.filter === "fail" ? index < 2 : index === 2));
  if (!visible.includes(state.issue)) { state.issue = visible[0]; state.caseIndex = affected[state.issue][0]; state.evidence = "observation"; }
  const filters = [["all", "all"], ["fail", "deviations"], ["unknown", "conditions"]].map(([key, label]) => `<button type="button" data-filter="${key}" aria-pressed="${state.filter === key}">${t(label)} <span class="numeric">${key === "all" ? 3 : key === "fail" ? 2 : 1}</span></button>`).join("");
  const choices = visible.map((index) => `<button type="button" class="issue-choice" data-issue="${index}" aria-current="${index === state.issue}">${badge(issueTone(index), index === 2 ? "conditions" : "deviations")}<strong>${t(`issue${index}`)}</strong><small>${index === 0 ? "P-01" : index === 1 ? "P-02" : "E-01"} · ${t(index === 0 ? "affectedTwo" : "affectedOne")}</small></button>`).join("");
  return `<div class="inspector-toolbar"><div class="filter-group" aria-label="${t("issues")}">${filters}</div><span class="inspector-hint">${t("inspectorHint")}</span></div><div class="inspector-grid"><section class="panel" aria-label="${t("issues")}">${choices}</section><section class="panel detail">${detail()}</section></div>`;
}
function detail() {
  const i = state.issue;
  const chips = affected[i].map((index) => `<button type="button" data-observation-case="${index}" aria-pressed="${state.caseIndex === index}">${t(`case${index}`)}</button>`).join("");
  const tabs = ["observation", "response", "request", "references"].map((key) => `<button type="button" data-evidence="${key}" aria-pressed="${state.evidence === key}">${t(key === "observation" && i > 0 ? i === 1 ? "sequence" : "timing" : key)}</button>`).join("");
  return `<div class="detail-heading"><span class="issue-number">${t("issueLabel")} ${i === 0 ? "P-01" : i === 1 ? "P-02" : "E-01"}</span>${badge(issueTone(i), i === 2 ? "conditions" : "deviations")}</div><h2>${t(`issue${i}`)}</h2><p class="detail-description">${t(`description${i}`)}</p><div class="case-chips" aria-label="${t("selectedCase")}">${chips}</div><nav class="evidence-tabs" aria-label="${t("observed")}">${tabs}</nav><div class="evidence">${evidence()}</div><div class="interpretation"><section><h3>${t("impact")}</h3><p>${t(`impact${i}`)}</p></section><section><h3>${t("nextStep")}</h3><p>${t(`next${i}`)}</p></section></div><details><summary>${t("technical")}</summary><p><code>${esc(cases[state.caseIndex].id)} · ${["MSG-STOP-SEQUENCE", "STR-LIFECYCLE", "READ-DEADLINE (demo)"][i]}</code></p><p><code>synthetic/case-${state.caseIndex + 1}/${i === 1 ? "events.sse" : "response.json"}</code></p><p>${t("synthetic")}</p></details>`;
}
function payload() {
  if (state.issue === 1) {
    const start = { type: "message_start", message: { id: "msg_demo", type: "message", role: "assistant", model: "diagnostic-model", content: [], stop_reason: null, stop_sequence: null, usage: { input_tokens: 12, output_tokens: 0 } } };
    const events = [start, start, { type: "content_block_start", index: 0, content_block: { type: "text", text: "" } }, { type: "content_block_delta", index: 0, delta: { type: "text_delta", text: "Hello" } }, { type: "content_block_stop", index: 0 }, { type: "message_delta", delta: { stop_reason: "end_turn", stop_sequence: null }, usage: { output_tokens: 5 } }, { type: "message_stop" }];
    return events.map(event => `event: ${event.type}\ndata: ${JSON.stringify(event)}\n`).join("\n");
  }
  if (state.issue === 2) return 'event: message_start\ndata: {"type":"message_start","message":{"id":"msg_demo"}}\n\n[synthetic capture ends at read deadline]';
  return JSON.stringify({ id: "msg_demo", type: "message", role: "assistant", model: "diagnostic-model", content: state.caseIndex === 3 ? [{ type: "tool_use", id: "tool_demo", name: "echo", input: { value: "sample" } }] : [{ type: "text", text: "Hello" }], stop_reason: state.caseIndex === 3 ? "tool_use" : "end_turn", usage: { input_tokens: 12, output_tokens: 5 } }, null, 2);
}
function evidence() {
  if (state.evidence === "response") return `<pre tabindex="0">${esc(payload())}</pre><p class="evidence-caption">${t("synthetic")}</p>`;
  if (state.evidence === "request") return `<pre tabindex="0">${esc(JSON.stringify({ model: "diagnostic-model", max_tokens: 64, stream: state.issue > 0, messages: [{ role: "user", content: state.issue === 2 ? "Count from one to five." : state.caseIndex === 3 ? "Call the echo tool with sample." : "Say hello." }], ...(state.caseIndex === 3 ? { tools: [{ name: "echo", input_schema: { type: "object", properties: { value: { type: "string" } }, required: ["value"] } }], tool_choice: { type: "tool", name: "echo" } } : {}) }, null, 2))}</pre><p class="evidence-caption">${t("synthetic")}</p>`;
  if (state.evidence === "references") return `<div class="reference-copy"><p>${t(`ref${state.issue}`)}</p><p>${t("sourceNote")}</p><p>API: <code>2023-06-01</code> · ${esc(cases[state.caseIndex].id)}</p></div>`;
  if (state.issue === 1) return `<table class="event-table"><thead><tr><th>${t("step")}</th><th>${t("event")}</th><th>${t("result")}</th></tr></thead><tbody><tr><td>01</td><td><code>message_start</code></td><td>${t("valid")}</td></tr><tr class="invalid"><td>02</td><td><code>message_start</code></td><td>${t("duplicate")}</td></tr><tr><td>03–05</td><td><code>content_block_*</code></td><td>${t("valid")}</td></tr><tr><td>06–07</td><td><code>message_delta / stop</code></td><td>${t("valid")}</td></tr></tbody></table><p class="evidence-caption">${t("synthetic")}</p>`;
  if (state.issue === 2) return `<table class="event-table"><tbody><tr><th>0.0s</th><td>${t("partial")}</td></tr><tr><th>10.0s</th><td>${t("deadline")}</td></tr><tr><th>${t("result")}</th><td>${t("notCompared")}</td></tr></tbody></table>`;
  const reason = state.caseIndex === 3 ? "tool_use" : "end_turn";
  return `<div class="diff-grid"><div class="diff-column"><div class="diff-label"><span>${t("expected")}</span><span>${t("present")}</span></div><pre>{
  "stop_reason": "${reason}",
<span class="good-line">  "stop_sequence": null</span>}</pre></div><div class="diff-column"><div class="diff-label"><span>${t("actual")}</span><span class="missing-key">${t("missing")}</span></div><pre>{
  "stop_reason": "${reason}"
}</pre></div></div><p class="evidence-caption">${t("excerpt")} · <code>$.stop_sequence</code></p>`;
}
function showDialog(content) { $("#dialog-content").innerHTML = content; $("#dialog").showModal(); }
function plan(retest) {
  showDialog(`<h2>${t(retest ? "planTitle" : "configured")}</h2><p>${t(retest ? "planIntro" : "completedNote")}</p><dl class="plan-list"><dt>${t("target")}</dt><dd>http://inference.example.test:3456</dd><dt>${t("model")}</dt><dd>diagnostic-model</dd><dt>${t("planScope")}</dt><dd>${t("scopeValue")} · 5</dd><dt>${t("planBudget")}</dt><dd>${t("budgetValue")}</dd></dl>${retest ? `<p class="modal-note">${t("mockNote")}</p><button type="button" class="button primary" data-action="simulate">${t("mockStart")}</button>` : ""}`);
}
function exportChoice() {
  showDialog(`<h2>${t("exportTitle")}</h2><p>${t("exportIntro")}</p><div class="dialog-options"><button type="button" class="export-choice" data-action="reading"><strong>${t("readable")}</strong><small>${t("readableNote")}</small></button><button type="button" class="export-choice" data-action="bundle"><strong>${t("bundle")}</strong><small>${t("bundleNote")}</small></button></div><p>${t("sampleDownloadNote")}</p>`);
}
function downloadSample() {
  const document = { synthetic: true, prototype_only: true, endpoint: "http://inference.example.test:3456", model: "diagnostic-model", state: state.scenario, client_tested: false, cases: cases.map((item, index) => ({ ...item, task: index === 4 && state.scenario !== "completed" ? "unassessed" : item.task, protocol: index === 4 && state.scenario !== "completed" ? "unassessed" : item.protocol })), notice: "Fictional design sample. Not a production report, capture or compatibility assessment." };
  const url = URL.createObjectURL(new Blob([JSON.stringify(document, null, 2)], { type: "application/json" }));
  const link = window.document.createElement("a"); link.href = url; link.download = "synthetic-console-summary.json"; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
document.addEventListener("click", (event) => {
  const button = event.target.closest("button"); if (!button) return;
  if (button.dataset.view) { state.view = button.dataset.view; render(); }
  if (button.dataset.issue !== undefined) { state.issue = Number(button.dataset.issue); state.caseIndex = affected[state.issue][0]; state.view = "issues"; state.filter = "all"; state.evidence = "observation"; render(); }
  if (button.dataset.filter) { state.filter = button.dataset.filter; render(); }
  if (button.dataset.evidence) { state.evidence = button.dataset.evidence; render(); }
  if (button.dataset.observationCase !== undefined) { state.caseIndex = Number(button.dataset.observationCase); render(); }
  if (button.dataset.case !== undefined) {
    const index = Number(button.dataset.case);
    if (cases[index].issue !== null) { state.issue = cases[index].issue; state.caseIndex = index; state.view = "issues"; state.filter = "all"; state.evidence = "observation"; render(); }
    else showDialog(`<h2>${t(`case${index}`)}</h2><p>${t(state.scenario === "completed" ? "pass" : state.scenario === "running" ? "running" : "pending")} · ${esc(cases[index].id)}</p><p>${state.scenario === "completed" ? t("completedNote") : t("cancelled")}</p><p>${t("synthetic")}</p>`);
  }
  if (button.dataset.action === "simulate") { $("#dialog").close(); state.scenario = "running"; state.view = "overview"; render(); $("#announcement").textContent = t("restartNote"); }
  if (button.dataset.action === "reading") showDialog(`<h2>${t("readable")}</h2><p>${t("readingSummary")}</p><p class="modal-note">${t("sampleDownloadNote")}</p><button class="button primary" type="button" data-action="download">${t("sampleDownload")}</button>`);
  if (button.dataset.action === "bundle") showDialog(`<h2>${t("previewTitle")}</h2><p>${t("fileSummary")}</p><dl class="plan-list"><dt>01</dt><dd>README.md · ${t("readable")}</dd><dt>02</dt><dd>results.json · ${t("coverage")}</dd><dt>03</dt><dd>evidence/ · ${t("request")} / ${t("response")}</dd><dt>04</dt><dd>references/ · ${t("references")}</dd></dl><p class="modal-note">${t("sampleDownloadNote")}</p><button class="button primary" type="button" data-action="download">${t("sampleDownload")}</button>`);
  if (button.dataset.action === "download") downloadSample();
});
$("#language").addEventListener("click", () => { if ($("#dialog").open) $("#dialog").close(); state.lang = state.lang === "zh" ? "en" : "zh"; render(); });
$("#theme").addEventListener("click", () => { state.theme = state.theme === "light" ? "dark" : "light"; render(); });
$("#scenario").addEventListener("change", (event) => { state.scenario = event.target.value; render(); });
$("#configuration").addEventListener("click", () => plan(false));
$("#retest").addEventListener("click", () => { if (state.scenario === "running") { state.scenario = "stopped"; render(); } else plan(true); });
$("#export").addEventListener("click", exportChoice);
render();
