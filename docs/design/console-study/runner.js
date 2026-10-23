"use strict";

// Standalone interaction study. All captures are fictional; no network execution.
const labels = {
  zh: {
    skip: "跳至证据", prototype: "设计样稿 · 模拟数据", graphite: "石墨", slate: "冷灰", ink: "墨色", dark: "深色", light: "浅色", scope: "5 个用例 / 最多 6 次请求", completed: "已完成", running: "运行中", stopped: "已停止", rerun: "复测原范围", stop: "停止", export: "导出…", cases: "用例", evidence: "证据", checks: "检查项", show: "显示", all: "全部用例", attention: "仅偏差与未判断", activity: "运行记录", currentOnly: "仅当前用例", synthetic: "以下内容全部为虚构记录", close: "关闭",
    group0: "基础消息", group1: "工具调用", group2: "工具闭环", case0: "普通消息", case1: "流式文本", case2: "流式计数", case3: "强制工具选择", case4: "工具结果往返", pass: "通过", fail: "偏差", unknown: "未判断", pending: "未完成", task: "任务", protocol: "协议", requests: "请求", finished: "已结束", elapsed: "耗时", groupedIssues: "2 类协议偏差 · 1 项未判断", client: "Claude Code 未实测", note: "协议偏差不直接证明客户端不可用。超时保留为未判断。", liveNote: "第 5 个用例 / 第 2 步：等待工具结果响应。已记录的结果保留。", stopNote: "工具闭环未完成，未完成部分不计作通过。",
    response: "响应", request: "请求", events: "流事件", headers: "头信息", request1: "步骤 1 · 产生工具调用", request2: "步骤 2 · 消费工具结果", step: "当前步骤", capture: "捕获内容 · 只读", time: "时间", event: "事件", observation: "观测", valid: "已记录", duplicate: "重复起始", readDeadline: "读取等待达到 10 秒上限，响应未完整结束。", noResponse: "当前步骤尚未取得完整响应。", missingField: "$.stop_sequence：响应中缺少此键", waiting: "等待响应", expected: "期望", actual: "实际", impact: "影响与限制", locate: "定位相关证据", basis: "规则与证据范围", basisText: "API 2023-06-01。此处仅展示当前用例的 6 项示例检查；不是完整断言清单。全部证据均为模拟。",
    validJson: "合法 JSON", parsedJson: "成功解析为对象", validFrames: "合法的 event / data 事件帧", parsedFrames: "已解析事件帧",
    checkHttp: "HTTP 状态", checkJson: "JSON 可解析", checkCapture: "响应完整性", checkStop: "停止字段", checkTask: "任务结果", checkModel: "响应模型", checkFraming: "SSE 格式", checkLifecycle: "事件生命周期", checkTool: "工具选择", checkToken: "工具结果消费", completeResponse: "完整响应", incompleteResponse: "响应未结束", singleStart: "同一消息仅一个起始事件", doubleStart: "message_start 出现两次", stopExpected: "存在 stop_sequence 键", stopMissing: "缺少 stop_sequence；不是显式 null", stopPresent: "stop_sequence: null", taskExpected: "返回该用例预期结果", taskObserved: "已返回预期结果", tokenExpected: "最终响应包含新鲜工具结果标记", tokenObserved: "最终响应包含 token_demo_7b", toolExpected: "调用指定的 echo 工具", toolObserved: "echo · 参数为对象",
    impactMissing: "任务结果已返回。字段缺失会导致严格校验失败；本次未运行 Claude Code，无法据此判断其行为。", impactStream: "文本任务通过。严格的流状态机可能拒绝重复起始事件；实际客户端影响仍需实测。", impactUnknown: "证据不足以完成任务与协议判定。检查读取上限、响应速度与链路等待，不推断故障所在层。", impactPass: "此项通过只证明当前检查满足预期，不代表完整协议或客户端工作流通过。",
    config: "运行配置", configModel: "模型", configEndpoint: "端点", configScope: "范围", configBudget: "上限", budget: "6 次请求 · 总时限 60 秒 · 读取等待 10 秒", demoWarning: "仅演示交互，不发送 API 请求，不改变真实运行记录。", simulateRun: "演示复测", exportTitle: "导出结果", reading: "阅读报告", readingHint: "结论、用例结果、问题与依据；独立 HTML。", bundle: "同事 / Agent 排查包", bundleHint: "摘要、结构化结果、原始交换与规则引用。", previewOnly: "此轮只设计工作台。正式报告和诊断包尚未由此样稿生成。", download: "下载模拟摘要 JSON", recorded: "已记录", archived: "原始结果保留", allSix: "共 6 次请求", log0: "任务完成；stop_sequence 缺失", log1: "文本完成；重复 message_start", log2: "读取超时；协议未判断", log3: "工具已调用；stop_sequence 缺失", log4: "echo 工具调用已返回", log5: "新鲜工具结果已消费"
  },
  en: {
    skip: "Skip to evidence", prototype: "Prototype · Synthetic data", graphite: "Graphite", slate: "Slate", ink: "Ink", dark: "Dark", light: "Light", scope: "5 cases / up to 6 requests", completed: "Completed", running: "Running", stopped: "Stopped", rerun: "Rerun scope", stop: "Stop", export: "Export…", cases: "Cases", evidence: "Evidence", checks: "Checks", show: "Show", all: "All cases", attention: "Deviations & inconclusive", activity: "Run log", currentOnly: "Current case only", synthetic: "All records shown are fictional", close: "Close",
    group0: "Basic messages", group1: "Tool use", group2: "Tool round trip", case0: "Plain message", case1: "Streamed text", case2: "Streamed counting", case3: "Forced tool choice", case4: "Tool-result round trip", pass: "Pass", fail: "Deviation", unknown: "Inconclusive", pending: "Incomplete", task: "Task", protocol: "Protocol", requests: "Requests", finished: "Finished", elapsed: "Elapsed", groupedIssues: "2 protocol deviations · 1 inconclusive", client: "Claude Code not tested", note: "Protocol deviations do not prove client failure. Timeouts remain inconclusive.", liveNote: "Case 5 / step 2: waiting for tool-result response. Recorded outcomes remain available.", stopNote: "The tool round trip is incomplete. Unfinished work does not count as passed.",
    response: "Response", request: "Request", events: "Stream events", headers: "Headers", request1: "Step 1 · Request tool call", request2: "Step 2 · Consume tool result", step: "Current step", capture: "Captured content · Read-only", time: "Time", event: "Event", observation: "Observation", valid: "Recorded", duplicate: "Duplicate start", readDeadline: "The 10-second read deadline was reached before the response completed.", noResponse: "A complete response has not been captured for this step.", missingField: "$.stop_sequence: key absent from response", waiting: "Waiting", expected: "Expected", actual: "Actual", impact: "Impact & limits", locate: "Locate evidence", basis: "Rules & evidence scope", basisText: "API 2023-06-01. These are 6 sample checks for the selected case, not the full assertion list. All captures are synthetic.",
    validJson: "Valid JSON", parsedJson: "Parsed as an object", validFrames: "Valid event / data frames", parsedFrames: "Event frames parsed",
    checkHttp: "HTTP status", checkJson: "JSON parsing", checkCapture: "Complete response", checkStop: "Stop field", checkTask: "Task result", checkModel: "Response model", checkFraming: "SSE framing", checkLifecycle: "Event lifecycle", checkTool: "Tool choice", checkToken: "Tool-result consumption", completeResponse: "Complete response", incompleteResponse: "Response did not finish", singleStart: "One start event per message", doubleStart: "Two message_start events", stopExpected: "stop_sequence key present", stopMissing: "stop_sequence absent, not explicit null", stopPresent: "stop_sequence: null", taskExpected: "Return the expected case result", taskObserved: "Expected result returned", tokenExpected: "Final response includes a fresh tool-result marker", tokenObserved: "Final response contains token_demo_7b", toolExpected: "Invoke the specified echo tool", toolObserved: "echo · object arguments",
    impactMissing: "The task returned its expected result. Strict validation rejects the absent field. Claude Code was not run, so its behavior is not established.", impactStream: "The text task passed. A strict stream state machine may reject duplicate start events; actual client impact needs a separate test.", impactUnknown: "Evidence is insufficient to judge task and protocol. Check read limits, response speed and waiting in the chain; no responsible layer is established.", impactPass: "Passing this check establishes only its specific expectation, not complete protocol compatibility or client readiness.",
    config: "Run configuration", configModel: "Model", configEndpoint: "Endpoint", configScope: "Scope", configBudget: "Limits", budget: "6 requests · 60s total · 10s read wait", demoWarning: "Interaction demo only. No API requests or changes to real run records.", simulateRun: "Simulate rerun", exportTitle: "Export results", reading: "Reading report", readingHint: "Summary, case outcomes, issues and references; standalone HTML.", bundle: "Colleague / Agent diagnostic bundle", bundleHint: "Summary, structured results, exchanges and rule references.", previewOnly: "This iteration designs the workbench. It does not generate a production report or complete diagnostic bundle.", download: "Download synthetic summary JSON", recorded: "Recorded", archived: "Original results retained", allSix: "6 requests total", log0: "Task returned; stop_sequence absent", log1: "Text returned; duplicate message_start", log2: "Read timeout; protocol inconclusive", log3: "Tool invoked; stop_sequence absent", log4: "echo tool call returned", log5: "Fresh tool result consumed"
  }
};
const qs = new URLSearchParams(location.search);
const state = { lang: qs.get("lang") === "en" ? "en" : "zh", theme: qs.get("theme") === "dark" ? "dark" : "light", palette: ["graphite", "slate", "ink"].includes(qs.get("palette")) ? qs.get("palette") : "graphite", scenario: ["running", "stopped"].includes(qs.get("state")) ? qs.get("state") : "completed", index: 1, tab: "events", event: 1, step: 1, check: 3, filter: "all", logs: true, currentOnly: false };
const cases = [
  { id: "ANT-MESSAGE-001", group: 0, task: "pass", protocol: "fail", time: "1.1s", stream: false },
  { id: "ANT-TEXT-SSE-001", group: 0, task: "pass", protocol: "fail", time: "2.6s", stream: true },
  { id: "ANT-TEXT-SSE-002", group: 0, task: "unknown", protocol: "unknown", time: "10.0s", stream: true },
  { id: "ANT-TOOL-FORCED-001", group: 1, task: "pass", protocol: "fail", time: "0.9s", stream: false },
  { id: "ANT-TOOL-LOOP-001", group: 2, task: "pass", protocol: "pass", time: "4.2s", stream: false }
];
const $ = selector => document.querySelector(selector);
const t = key => labels[state.lang][key];
const esc = value => String(value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const pending = () => state.index === 4 && state.step === 1 && state.scenario !== "completed";
const caseStatus = index => index === 4 && state.scenario !== "completed" ? state.scenario === "running" ? "running" : "pending" : cases[index].protocol;
function syncUrl() { history.replaceState(null, "", `?${new URLSearchParams({ lang: state.lang, theme: state.theme, palette: state.palette, state: state.scenario })}`); }
function selectCase(index, step = 1) {
  state.index = index; state.step = step; state.check = index === 2 ? 2 : 3; state.event = index === 2 ? 0 : 1; state.tab = cases[index].stream ? "events" : "response";
  document.body.dataset.mobile = "evidence"; document.body.dataset.checks = "closed"; render();
}
function responseObject() {
  const tool = state.index === 3 || (state.index === 4 && state.step === 0);
  return { id: `msg_demo_${state.index + 1}`, type: "message", role: "assistant", model: "diagnostic-model", content: tool ? [{ type: "tool_use", id: "tool_demo", name: "echo", input: { value: "sample" } }] : [{ type: "text", text: state.index === 4 ? "Result received: token_demo_7b" : "Hello" }], stop_reason: tool ? "tool_use" : "end_turn", ...(state.index === 0 || state.index === 3 ? {} : { stop_sequence: null }), usage: { input_tokens: 12, output_tokens: 5 } };
}
function requestObject() {
  const tool = state.index === 3 || state.index === 4;
  const messages = [{ role: "user", content: tool ? "Use echo to return the value sample." : state.index === 2 ? "Count from one to five." : "Say hello." }];
  if (state.index === 4 && state.step === 1) messages.push({ role: "assistant", content: [{ type: "tool_use", id: "tool_demo", name: "echo", input: { value: "sample" } }] }, { role: "user", content: [{ type: "tool_result", tool_use_id: "tool_demo", content: "token_demo_7b" }] });
  return { model: "diagnostic-model", max_tokens: 64, stream: cases[state.index].stream, messages, ...(tool ? { tools: [{ name: "echo", input_schema: { type: "object", properties: { value: { type: "string" } }, required: ["value"] } }], ...(state.index === 3 || state.step === 0 ? { tool_choice: { type: "tool", name: "echo" } } : {}) } : {}) };
}
function streamEvents() {
  const start = { type: "message_start", message: { id: "msg_demo_stream", type: "message", role: "assistant", model: "diagnostic-model", content: [], stop_reason: null, stop_sequence: null, usage: { input_tokens: 12, output_tokens: 0 } } };
  if (state.index === 2) return [{ time: "0.00s", data: start }];
  return [start, start, { type: "content_block_start", index: 0, content_block: { type: "text", text: "" } }, { type: "content_block_delta", index: 0, delta: { type: "text_delta", text: "Hello" } }, { type: "content_block_stop", index: 0 }, { type: "message_delta", delta: { stop_reason: "end_turn", stop_sequence: null }, usage: { output_tokens: 5 } }, { type: "message_stop" }].map((data, i) => ({ time: ["0.00s", "0.04s", "0.10s", "0.80s", "2.40s", "2.50s", "2.60s"][i], data }));
}
function checks() {
  const check = (id, key, status, expected, actual) => ({ id, key, status, expected, actual });
  const unknown = state.index === 2 || pending();
  const result = [check("HTTP-STATUS", "checkHttp", pending() ? "unknown" : "pass", "200", pending() ? t("waiting") : "200"), check(cases[state.index].stream ? "SSE-FRAMING" : "MSG-JSON", cases[state.index].stream ? "checkFraming" : "checkJson", pending() ? "unknown" : "pass", t(cases[state.index].stream ? "validFrames" : "validJson"), pending() ? t("waiting") : t(cases[state.index].stream ? "parsedFrames" : "parsedJson")), check("CAPTURE-COMPLETE", "checkCapture", unknown ? "unknown" : "pass", t("completeResponse"), unknown ? t("incompleteResponse") : t("completeResponse"))];
  result.push(cases[state.index].stream ? check("STR-LIFECYCLE", "checkLifecycle", state.index === 2 ? "unknown" : "fail", t("singleStart"), state.index === 2 ? t("incompleteResponse") : t("doubleStart")) : check("MSG-STOP-SEQUENCE", "checkStop", unknown ? "unknown" : state.index === 0 || state.index === 3 ? "fail" : "pass", t("stopExpected"), unknown ? t("waiting") : state.index === 0 || state.index === 3 ? t("stopMissing") : t("stopPresent")));
  result.push(check("TASK-COMPLETE", "checkTask", unknown ? "unknown" : "pass", t("taskExpected"), unknown ? t("incompleteResponse") : t("taskObserved")));
  result.push(state.index === 4 && state.step === 1 ? check("TASK-COMPLETE", "checkToken", pending() ? "unknown" : "pass", t("tokenExpected"), pending() ? t("waiting") : t("tokenObserved")) : state.index === 3 || (state.index === 4 && state.step === 0) ? check("MSG-TOOL-NAME", "checkTool", "pass", t("toolExpected"), t("toolObserved")) : check("MSG-MODEL", "checkModel", "pass", "diagnostic-model", "diagnostic-model"));
  return result;
}
function tree() {
  return [0, 1, 2].map(group => {
    const members = cases.map((item, index) => ({ item, index })).filter(({ item, index }) => item.group === group && (state.filter === "all" || caseStatus(index) !== "pass"));
    if (!members.length) return "";
    return `<details class="case-group" open><summary>${t(`group${group}`)}<span>${members.length}</span></summary>${members.map(({ index }) => { const status = caseStatus(index); return `<button type="button" class="case-row" data-case="${index}" aria-current="${index === state.index}"><span>${t(`case${index}`)}</span><small class="${status}-text">${t(status)}</small></button>`; }).join("")}</details>`;
  }).join("");
}
function codeView(value, focusType = false) {
  const source = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return `<ol class="code-view" aria-label="${t("capture")}" tabindex="0">${source.split("\n").map(line => { const match = line.match(/^(\s*)("[^"]+")(:.*)$/); const content = match ? `${esc(match[1])}<span class="code-key">${esc(match[2])}</span>${esc(match[3])}` : esc(line); return `<li${focusType && line.includes('"type": "message_start"') ? ' class="focus-line"' : ""}><code>${content || " "}</code></li>`; }).join("")}</ol>`;
}
function evidence() {
  const meta = `<div class="capture-meta"><span>${state.tab === "request" ? "POST /v1/messages" : cases[state.index].stream ? "HTTP 200 · text/event-stream" : "HTTP 200 · application/json"}</span><span>${t("capture")}</span></div>`;
  if (state.tab === "request") return meta + codeView(requestObject());
  if (state.tab === "headers") return `<div class="capture-meta">${t("capture")}</div>` + codeView(`Request headers (synthetic)\nanthropic-version: 2023-06-01\ncontent-type: application/json\n\nResponse headers (synthetic)\n${pending() ? t("noResponse") : `HTTP 200\ncontent-type: ${cases[state.index].stream ? "text/event-stream" : "application/json"}`}`);
  if (pending()) return `<div class="notice">${t("noResponse")}</div>${codeView(t(state.scenario === "running" ? "waiting" : "pending"))}`;
  if (cases[state.index].stream) {
    const events = streamEvents();
    if (state.tab === "response") return meta + (state.index === 2 ? `<div class="notice">${t("readDeadline")}</div>` : "") + codeView(events.map(item => `event: ${item.data.type}\ndata: ${JSON.stringify(item.data)}\n`).join("\n"));
    const event = events[Math.min(state.event, events.length - 1)];
    return `${state.index === 2 ? `<div class="notice">${t("readDeadline")}</div>` : ""}<div class="event-list"><table><thead><tr><th>#</th><th>${t("time")}</th><th>${t("event")}</th><th>${t("observation")}</th></tr></thead><tbody>${events.map((item, index) => `<tr data-event="${index}" class="${index === 1 ? "invalid" : ""}" aria-selected="${index === state.event}"><td class="numeric">${index + 1}</td><td class="numeric">${item.time}</td><td class="event-name"><button class="event-button" type="button">${esc(item.data.type)}</button></td><td>${t(index === 1 ? "duplicate" : "valid")}</td></tr>`).join("")}</tbody></table></div><div class="payload-heading"><span>#${state.event + 1} · ${esc(event.data.type)}</span><span>data</span></div>${codeView(event.data, state.index === 1 && state.event === 1)}`;
  }
  return meta + (state.index === 0 || state.index === 3 ? `<div class="notice protocol-notice">${t("missingField")}</div>` : "") + codeView(responseObject());
}
function renderChecks() {
  const list = checks(); const selected = list[state.check];
  $("#check-count").textContent = list.length;
  $("#check-list").innerHTML = list.map((item, index) => `<button type="button" class="check-row" data-check="${index}" aria-current="${index === state.check}"><span>${t(item.key)}</span><span class="${item.status}-text">${t(item.status)}</span></button>`).join("");
  const impact = selected.status === "pass" ? "impactPass" : selected.status === "unknown" ? "impactUnknown" : cases[state.index].stream ? "impactStream" : "impactMissing";
  $("#check-detail").innerHTML = `<section class="check-detail"><h2>${t(selected.key)}</h2><div class="rule-id">${esc(selected.id)} · ${esc(cases[state.index].id)}</div><dl><dt>${t("expected")}</dt><dd>${esc(selected.expected)}</dd><dt>${t("actual")}</dt><dd class="${selected.status === "fail" ? "observation-fail" : ""}">${esc(selected.actual)}</dd></dl><button class="locate" type="button" data-locate="true">${t("locate")}</button><h3>${t("impact")}</h3><p>${t(impact)}</p><details><summary>${t("basis")}</summary><p>${t("basisText")}</p></details></section>`;
}
function logs() {
  const rows = [[0, 0, "00:00.0", "1.1s", "fail", 0], [1, 0, "00:01.1", "2.6s", "fail", 1], [2, 0, "00:03.7", "10.0s", "unknown", 2], [3, 0, "00:13.7", "0.9s", "fail", 3], [4, 0, "00:14.6", "1.2s", "pass", 4], [4, 1, "00:15.8", state.scenario === "completed" ? "3.0s" : "—", state.scenario === "completed" ? "pass" : state.scenario === "running" ? "running" : "pending", 5]];
  return rows.filter(row => !state.currentOnly || row[0] === state.index).map(([index, step, time, duration, status, description]) => `<button type="button" class="log-row" data-log-case="${index}" data-log-step="${step}" aria-current="${index === state.index && (index !== 4 || step === state.step)}"><span class="numeric">${time}</span><span class="${status}-text">${t(status)}</span><span>${t(`case${index}`)}${index === 4 ? ` / ${step + 1}` : ""}</span><span class="log-description">${t(index === 4 && step === 1 && state.scenario !== "completed" ? state.scenario === "running" ? "waiting" : "pending" : `log${description}`)}</span><span class="numeric">${duration}</span></button>`).join("");
}
function render() {
  document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en"; document.documentElement.dataset.theme = state.theme; document.documentElement.dataset.palette = state.palette;
  document.querySelectorAll("[data-text]").forEach(node => { node.textContent = t(node.dataset.text); });
  $("#language").textContent = state.lang === "zh" ? "English" : "中文"; $("#theme").textContent = t(state.theme === "light" ? "dark" : "light"); $("#palette").value = state.palette; $("#scenario").value = state.scenario; $("#filter").value = state.filter;
  $("#stop").disabled = state.scenario !== "running"; $("#rerun").disabled = state.scenario === "running";
  $("#case-tree").innerHTML = tree(); $("#run-note").innerHTML = `<strong>${t("groupedIssues")}</strong>${t(state.scenario === "running" ? "liveNote" : state.scenario === "stopped" ? "stopNote" : "note")}`;
  const item = cases[state.index]; const incomplete = state.index === 4 && state.scenario !== "completed"; const status = incomplete ? "unknown" : item.protocol;
  $("#case-heading").innerHTML = `<h1>${t(`case${state.index}`)}<span>${esc(item.id)}</span></h1><div class="case-facts"><span class="${incomplete ? "unknown" : item.task}-text">${t("task")} · ${t(incomplete ? "unknown" : item.task)}</span><span class="${status}-text">${t("protocol")} · ${t(status)}</span><span>${incomplete ? t(state.scenario) : item.time}</span></div>`;
  $("#exchange-selector").innerHTML = state.index === 4 ? [0, 1].map(step => `<button type="button" data-step="${step}" aria-pressed="${state.step === step}">${t(step === 0 ? "request1" : "request2")}</button>`).join("") : "";
  $("#evidence-tabs").innerHTML = ["response", "request", ...(item.stream ? ["events"] : []), "headers"].map(tab => `<button type="button" data-tab="${tab}" aria-current="${state.tab === tab ? "page" : "false"}">${t(tab)}</button>`).join("");
  $("#evidence-body").innerHTML = evidence(); renderChecks();
  $("#activity-toggle").setAttribute("aria-expanded", String(state.logs)); $("#current-only").checked = state.currentOnly; $("#activity-body").innerHTML = state.logs ? logs() : "";
  $("#statusbar").innerHTML = `<strong>${t(state.scenario)}</strong><span>${t("finished")} ${state.scenario === "completed" ? 5 : 4}/5</span><span>${t("requests")} 6/6</span><span>${t("elapsed")} ${state.scenario === "completed" ? "18.8" : "16.2"}s</span><span>${t("groupedIssues")}</span><span class="client-note">${t("client")}</span>`;
  syncUrl();
}
function openDialog(content) { $("#dialog-content").innerHTML = content; $("#dialog").showModal(); }
function config(rerun = false) { openDialog(`<h2>${t("config")}</h2><dl class="config-grid"><dt>${t("configModel")}</dt><dd>diagnostic-model</dd><dt>${t("configEndpoint")}</dt><dd>http://inference.example.test:3456</dd><dt>${t("configScope")}</dt><dd>${t("scope")}</dd><dt>${t("configBudget")}</dt><dd>${t("budget")}</dd></dl><p>${t("demoWarning")}</p>${rerun ? `<div class="dialog-actions"><button class="primary" type="button" data-action="run">${t("simulateRun")}</button></div>` : ""}`); }
function download() {
  const url = URL.createObjectURL(new Blob([JSON.stringify({ synthetic: true, prototype_only: true, selected_case: cases[state.index].id, cases, notice: "Fictional design sample, not a compatibility report." }, null, 2)], { type: "application/json" }));
  const link = document.createElement("a"); link.href = url; link.download = "synthetic-runner-summary.json"; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
document.addEventListener("click", event => {
  const button = event.target.closest("button"); const eventRow = event.target.closest("[data-event]");
  if (eventRow) { state.event = Number(eventRow.dataset.event); $("#evidence-body").innerHTML = evidence(); return; }
  if (!button) return;
  if (button.dataset.case !== undefined) selectCase(Number(button.dataset.case));
  if (button.dataset.logCase !== undefined) selectCase(Number(button.dataset.logCase), Number(button.dataset.logStep));
  if (button.dataset.tab) { state.tab = button.dataset.tab; render(); }
  if (button.dataset.step !== undefined) { state.step = Number(button.dataset.step); render(); }
  if (button.dataset.check !== undefined) { state.check = Number(button.dataset.check); renderChecks(); }
  if (button.dataset.locate) {
    const id = checks()[state.check].id;
    state.tab = id === "HTTP-STATUS" ? "headers" : id === "STR-LIFECYCLE" || (id === "MSG-MODEL" && cases[state.index].stream) || (id === "TASK-COMPLETE" && cases[state.index].stream) ? "events" : "response";
    state.event = id === "MSG-MODEL" || state.index === 2 ? 0 : id === "TASK-COMPLETE" ? 3 : 1;
    render(); document.body.dataset.checks = "closed";
  }
  if (button.dataset.action === "run") { $("#dialog").close(); state.scenario = "running"; selectCase(4); }
  if (button.dataset.action === "reading" || button.dataset.action === "bundle") openDialog(`<h2>${t(button.dataset.action)}</h2><p>${t("previewOnly")}</p><p>${t("demoWarning")}</p><div class="dialog-actions"><button type="button" data-action="download">${t("download")}</button></div>`);
  if (button.dataset.action === "download") download();
});
$("#language").addEventListener("click", () => { state.lang = state.lang === "zh" ? "en" : "zh"; render(); });
$("#theme").addEventListener("click", () => { state.theme = state.theme === "light" ? "dark" : "light"; render(); });
$("#palette").addEventListener("change", event => { state.palette = event.target.value; render(); });
$("#scenario").addEventListener("change", event => { state.scenario = event.target.value; render(); });
$("#filter").addEventListener("change", event => { state.filter = event.target.value; render(); });
$("#current-only").addEventListener("change", event => { state.currentOnly = event.target.checked; render(); });
$("#activity-toggle").addEventListener("click", () => { state.logs = !state.logs; render(); });
$("#target").addEventListener("click", () => config()); $("#scope").addEventListener("click", () => config()); $("#rerun").addEventListener("click", () => config(true));
$("#stop").addEventListener("click", () => { state.scenario = "stopped"; render(); });
$("#export").addEventListener("click", () => openDialog(`<h2>${t("exportTitle")}</h2><button type="button" class="export-option" data-action="reading">${t("reading")}<small>${t("readingHint")}</small></button><button type="button" class="export-option" data-action="bundle">${t("bundle")}<small>${t("bundleHint")}</small></button><p>${t("previewOnly")}</p>`));
$("#show-cases").addEventListener("click", () => { document.body.dataset.mobile = "cases"; document.body.dataset.checks = "closed"; });
$("#show-evidence").addEventListener("click", () => { document.body.dataset.mobile = "evidence"; document.body.dataset.checks = "closed"; });
$("#show-checks").addEventListener("click", () => { document.body.dataset.checks = document.body.dataset.checks === "open" ? "closed" : "open"; });
for (const [id, variable, direction] of [["left-splitter", "--case-width", 1], ["right-splitter", "--check-width", -1]]) {
  const splitter = $(`#${id}`);
  const resize = value => { const minimum = direction === 1 ? 180 : 260; const other = parseFloat(getComputedStyle(document.documentElement).getPropertyValue(direction === 1 ? "--check-width" : "--case-width")); const maximum = Math.max(minimum, Math.min(direction === 1 ? 360 : 420, innerWidth - other - 290)); document.documentElement.style.setProperty(variable, `${Math.max(minimum, Math.min(maximum, value))}px`); };
  splitter.addEventListener("keydown", event => { if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return; event.preventDefault(); resize(parseFloat(getComputedStyle(document.documentElement).getPropertyValue(variable)) + (event.key === "ArrowRight" ? 20 : -20) * direction); });
  splitter.addEventListener("pointerdown", event => { event.preventDefault(); const start = event.clientX; const size = parseFloat(getComputedStyle(document.documentElement).getPropertyValue(variable)); const move = update => resize(size + (update.clientX - start) * direction); const end = () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", end); }; window.addEventListener("pointermove", move); window.addEventListener("pointerup", end); });
}
render();
