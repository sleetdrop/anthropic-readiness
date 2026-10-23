"use strict";

// Navigation exercise only. Captures are synthetic, never fetched from an endpoint.
history.scrollRestoration = "manual";
const copy = {
  zh: {
    switchLanguage: "切换到英文（English）", switchDark: "切换到深色主题", switchLight: "切换到浅色主题",
    runFinished: "运行已结束", liveHint: "结果持续更新，可先查看已结束用例。", doneHint: "仍有协议偏差与未能判断项。", casesFinished: "用例已结束", requestsSent: "请求已发出", caseProgress: "用例进度", listLiveTitle: "当前已发现的问题", listFinalTitle: "本次运行结果",
    prototype: "交互流程练习 · 视觉样式未定", client: "Claude Code 未实测", demoState: "样稿状态", running: "运行中", completed: "已结束", light: "浅色", dark: "深色", limits: "全部为模拟数据；仅验证问题、证据和返回路径，不调用模型，不生成正式报告。",
    list: "问题列表", issue: "问题", evidence: "证据", listTitle: "需要查看的结果", listLead: "2 类协议偏差影响 3 个用例；另有 1 个用例未能判断。", filter: "筛选", all: "全部", protocol: "协议偏差", condition: "未能判断", search: "搜索问题", searchHint: "现象、字段或用例名称", phenomenon: "观测现象", kind: "类型", affected: "受影响用例", action: "操作", open: "查看问题", results: "项结果", clear: "清除搜索", noResults: "没有符合条件的结果。", counts: "问题类别数、受影响用例数和失败断言数分别统计；同类现象不代表已确定共同根因。",
    stopTitle: "响应缺少 stop_sequence", streamTitle: "重复发送 message_start", timeoutTitle: "等待流数据超时", stopSub: "两个响应缺少同一个键", streamSub: "文本已生成，事件生命周期有偏差", timeoutSub: "响应未完整结束，不能完成判定", basic: "普通消息", forced: "强制工具选择", streamed: "流式文本", counting: "流式计数",
    backList: "返回问题列表", backIssue: "返回该问题", expected: "期望", actual: "观测到", stopExpected: "响应对象包含 stop_sequence 键", stopActual: "缺少该键，与显式 null 不同", streamExpected: "同一消息只出现一次 message_start", streamActual: "第 58 个事件再次出现 message_start", timeoutExpected: "取得完整响应后判定任务和协议", timeoutActual: "读取等待达到 10 秒上限，捕获不完整", affectedTitle: "选择一处观测", selected: "当前选择", case: "用例", exchange: "交换", location: "位置", inspect: "查看证据", request1: "请求 1", taskPass: "任务已返回预期结果；客户端影响未实测。", inconclusive: "证据不足；不计作协议偏差或通过，不推断链路故障所在层。", scope: "规则与观测标识", snapshot: "API 2023-06-01 · 设计练习，未经真实端点或客户端验证。",
    parentLocation: "定位到父对象 $：这里应包含 stop_sequence；缺失字段没有可高亮的原始字节。", streamLocation: "关联位置：第 58 / 206 个事件；同时保留第 1 个起始事件和附近上下文。", timeoutLocation: "这是超时前已收到的部分数据，未取得消息结束事件。", nearby: "相关上下文", full: "完整序列（206）", eventSearch: "查找事件", eventHint: "例如 message_start", event: "事件", elapsed: "相对时间", observation: "观测", recorded: "已记录", duplicate: "重复起始", omitted: "个事件未展开", expand: "展开完整序列", fields: "结构化字段", raw: "原始数据", capture: "整段 SSE", capturedOnly: "下方仅展示捕获中实际存在的字段；解释不会插入原始数据。", eventSelected: "当前事件", rootObject: "根对象", eventCount: "个事件", noEvents: "没有匹配的事件；当前选中的数据仍保留。", sequenceNote: "长流用于导航结构练习；没有增加正式测试用例或验证渲染性能。", interpretation: "当前问题", frames: "已结束", requests: "请求", restoration: "已恢复上次筛选和阅读位置。"
  },
  en: {
    switchLanguage: "Switch to Chinese (中文)", switchDark: "Switch to dark theme", switchLight: "Switch to light theme",
    runFinished: "Run finished", liveHint: "Results are updating; finished cases are available.", doneHint: "Deviations and inconclusive results remain.", casesFinished: "Cases finished", requestsSent: "Requests sent", caseProgress: "Case progress", listLiveTitle: "Issues found so far", listFinalTitle: "Run results",
    prototype: "Interaction study · Visual style undecided", client: "Claude Code not tested", demoState: "Prototype state", running: "Running", completed: "Completed", light: "Light", dark: "Dark", limits: "Synthetic data only. This demonstrates issue/evidence navigation, without model calls or production reports.",
    list: "Issues", issue: "Issue", evidence: "Evidence", listTitle: "Results to investigate", listLead: "2 protocol deviations affect 3 cases; 1 other case is inconclusive.", filter: "Filter", all: "All", protocol: "Protocol deviation", condition: "Inconclusive", search: "Search issues", searchHint: "Observation, field or case", phenomenon: "Observed phenomenon", kind: "Type", affected: "Affected cases", action: "Action", open: "Inspect issue", results: "results", clear: "Clear search", noResults: "No results match the current selection.", counts: "Issue categories, affected cases and failed assertions are separate counts. Similar observations do not establish a common root cause.",
    stopTitle: "stop_sequence absent from responses", streamTitle: "Duplicate message_start", timeoutTitle: "Timed out waiting for stream data", stopSub: "Two responses omit the same key", streamSub: "Text returned; the event lifecycle deviates", timeoutSub: "Incomplete response; judgment unavailable", basic: "Plain message", forced: "Forced tool choice", streamed: "Streamed text", counting: "Streamed counting",
    backList: "Back to issues", backIssue: "Back to this issue", expected: "Expected", actual: "Observed", stopExpected: "Response object includes stop_sequence", stopActual: "Key absent, distinct from explicit null", streamExpected: "One message_start per message", streamActual: "Another message_start at event 58", timeoutExpected: "Complete response to judge task and protocol", timeoutActual: "10-second read deadline; incomplete capture", affectedTitle: "Select an occurrence", selected: "Selected", case: "Case", exchange: "Exchange", location: "Location", inspect: "Inspect evidence", request1: "Request 1", taskPass: "The task returned its expected result; client impact was not tested.", inconclusive: "Insufficient evidence. Neither a protocol deviation nor a pass; no responsible chain layer is established.", scope: "Rule and observation identifiers", snapshot: "API 2023-06-01 · Design exercise, not verified against an endpoint or client.",
    parentLocation: "Parent object $: stop_sequence should be here. An absent field has no original bytes to highlight.", streamLocation: "Linked location: event 58 of 206, with the first start event and nearby context retained.", timeoutLocation: "Partial data received before the timeout. The message end event was not captured.", nearby: "Related context", full: "Full sequence (206)", eventSearch: "Find events", eventHint: "For example, message_start", event: "Event", elapsed: "Relative time", observation: "Observation", recorded: "Recorded", duplicate: "Duplicate start", omitted: "events collapsed", expand: "Expand full sequence", fields: "Parsed fields", raw: "Raw data", capture: "Full SSE capture", capturedOnly: "Only captured fields appear below. Interpretation is kept out of the original data.", eventSelected: "Selected event", rootObject: "Root object", eventCount: "events", noEvents: "No events match; the selected data remains available.", sequenceNote: "The long stream exercises navigation structure. It adds no formal test or rendering benchmark.", interpretation: "Current issue", frames: "Finished", requests: "Requests", restoration: "Previous filters and reading position restored."
  }
};
const issues = [
  { id: "stop", kind: "protocol", title: "stopTitle", sub: "stopSub", expected: "stopExpected", actual: "stopActual", rule: "MSG-STOP-SEQUENCE", occurrences: [{ label: "basic", id: "ANT-MESSAGE-001", stop: "end_turn" }, { label: "forced", id: "ANT-TOOL-FORCED-001", stop: "tool_use" }] },
  { id: "stream", kind: "protocol", title: "streamTitle", sub: "streamSub", expected: "streamExpected", actual: "streamActual", rule: "STR-LIFECYCLE", occurrences: [{ label: "streamed", id: "ANT-TEXT-SSE-001" }] },
  { id: "timeout", kind: "condition", title: "timeoutTitle", sub: "timeoutSub", expected: "timeoutExpected", actual: "timeoutActual", rule: "CAPTURE-COMPLETE", occurrences: [{ label: "counting", id: "ANT-TEXT-SSE-002" }] }
];
const start = { type: "message_start", message: { id: "msg_flow_stream", type: "message", role: "assistant", model: "diagnostic-model", content: [], stop_reason: null, stop_sequence: null, usage: { input_tokens: 12, output_tokens: 0 } } };
const text = "Hello, this is a synthetic long response used to inspect event ordering and navigate between a protocol observation, the original event payload and its surrounding context without losing the selected issue or the run state. ";
const events = [start, { type: "content_block_start", index: 0, content_block: { type: "text", text: "" } }, ...Array.from({ length: 200 }, (_, i) => ({ type: "content_block_delta", index: 0, delta: { type: "text_delta", text: text[i % text.length] } })), { type: "content_block_stop", index: 0 }, { type: "message_delta", delta: { stop_reason: "end_turn", stop_sequence: null }, usage: { output_tokens: 40 } }, { type: "message_stop" }];
events.splice(57, 0, start);
const params = new URLSearchParams(location.hash.slice(1));
const app = { lang: params.get("lang") === "en" ? "en" : "zh", theme: params.get("theme") === "dark" ? "dark" : "light", runState: params.get("run") === "running" ? "running" : "completed" };
const defaults = { view: "list", issue: "stream", occurrence: 0, filter: "all", search: "", mode: "context", event: 57, eventSearch: "", tab: "fields", scroll: 0, eventScroll: 0, focus: "", depth: 0 };
let state = history.state?.flowStudy === 1 ? { ...defaults, ...history.state.nav } : { ...defaults, view: ["issue", "evidence"].includes(params.get("view")) ? params.get("view") : "list", issue: issues.some(issue => issue.id === params.get("issue")) ? params.get("issue") : "stream", occurrence: params.get("case") === "1" ? 1 : 0, filter: ["protocol", "condition"].includes(params.get("filter")) ? params.get("filter") : "all", search: (params.get("q") || "").slice(0, 128) };
const $ = selector => document.querySelector(selector);
const t = key => copy[app.lang][key];
const esc = value => String(value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const iconLabel = (name, label) => `<span class="icon-label"><span class="icon icon-${name}" aria-hidden="true"></span><span>${esc(label)}</span></span>`;
const searchField = (id, label, hint, value) => `<label class="search-field" for="${id}"><span class="sr-only">${esc(label)}</span><span class="icon icon-search" aria-hidden="true"></span><input id="${id}" type="search" maxlength="128" value="${esc(value)}" placeholder="${esc(hint)}"></label>`;
const currentIssue = () => issues.find(issue => issue.id === state.issue) || issues[0];
const currentOccurrence = () => currentIssue().occurrences[Math.min(state.occurrence, currentIssue().occurrences.length - 1)];
function hash() { return `#${new URLSearchParams({ view: state.view, issue: state.issue, case: String(state.occurrence), filter: state.filter, q: state.search, lang: app.lang, theme: app.theme, run: app.runState })}`; }
function remember() { state.scroll = $("#main").scrollTop; state.eventScroll = $(".event-table")?.scrollTop || 0; history.replaceState({ flowStudy: 1, nav: { ...state } }, "", hash()); }
function navigate(patch) { remember(); state = { ...state, ...patch, depth: state.depth + 1, scroll: 0, eventScroll: 0, focus: "" }; history.pushState({ flowStudy: 1, nav: { ...state } }, "", hash()); render(); }
function back(root = false) {
  if (state.depth > 0) history.go(root ? -state.depth : -1);
  else { state = { ...state, view: root || state.view === "issue" ? "list" : "issue", scroll: 0, focus: "" }; render(); remember(); }
}
function globalContext() {
  document.documentElement.lang = app.lang === "zh" ? "zh-CN" : "en"; document.documentElement.dataset.theme = app.theme;
  document.querySelectorAll("[data-text]").forEach(node => { node.textContent = t(node.dataset.text); });
  const running = app.runState === "running";
  $("#run-status").textContent = t(running ? "running" : "runFinished");
  $("#run-hint").textContent = t(running ? "liveHint" : "doneHint");
  $("#run-counts").textContent = `${t("casesFinished")} ${running ? 4 : 5}/5`;
  $("#request-counts").textContent = `${t("requestsSent")} 6/6`;
  $("#run-progress").setAttribute("value", running ? "4" : "5");
  $("#run-progress").setAttribute("aria-label", t("caseProgress"));
  document.querySelectorAll("[data-run-state]").forEach(button => { button.setAttribute("aria-pressed", String(button.dataset.runState === app.runState)); });
  if ($("#issue-title")) $("#issue-title").textContent = t(running ? "listLiveTitle" : "listFinalTitle");
  $("#language").textContent = app.lang === "zh" ? "EN" : "中";
  $("#language").lang = app.lang === "zh" ? "en" : "zh-CN";
  $("#language").setAttribute("aria-label", t("switchLanguage")); $("#language").title = t("switchLanguage");
  $("#theme").innerHTML = `<span class="icon icon-${app.theme === "light" ? "moon" : "sun"}" aria-hidden="true"></span>`;
  $("#theme").setAttribute("aria-label", t(app.theme === "light" ? "switchDark" : "switchLight")); $("#theme").title = t(app.theme === "light" ? "switchDark" : "switchLight");
}
function filteredIssues() { const query = state.search.trim().toLowerCase(); return issues.filter(issue => (state.filter === "all" || issue.kind === state.filter) && (!query || [t(issue.title), t(issue.sub), ...issue.occurrences.map(item => t(item.label))].join(" ").toLowerCase().includes(query))); }
function listRows() {
  const selected = filteredIssues();
  return selected.length ? selected.map(issue => `<tr><td class="issue-name"><button id="open-${issue.id}" type="button" class="link" data-open-issue="${issue.id}">${t(issue.title)}</button><small>${t(issue.sub)}</small></td><td class="${issue.kind === "protocol" ? "fail" : "unknown"}">${t(issue.kind)}</td><td>${issue.occurrences.map(item => t(item.label)).join(" / ")}</td><td>${issue.occurrences.length}</td></tr>`).join("") : `<tr><td colspan="4" class="empty">${t("noResults")} <button type="button" class="link" data-action="clear">${t("clear")}</button></td></tr>`;
}
function listView() {
  return `<h1 id="issue-title">${t(app.runState === "running" ? "listLiveTitle" : "listFinalTitle")}</h1><p class="lead">${t("listLead")}</p>
    <div class="toolbar"><div id="issue-filter" class="filter-options" role="group" aria-label="${t("filter")}">${[["all", "all"], ["protocol", "protocol"], ["condition", "condition"]].map(([value, label]) => `<button id="filter-${value}" type="button" data-filter="${value}" aria-pressed="${state.filter === value}">${t(label)}</button>`).join("")}</div>
    ${searchField("issue-search", t("search"), t("searchHint"), state.search)}<span class="counter" id="issue-counter">${filteredIssues().length} ${t("results")}</span></div>
    <div class="table-scroll"><table class="issues-table"><thead><tr><th>${t("phenomenon")}</th><th>${t("kind")}</th><th>${t("affected")}</th><th>#</th></tr></thead><tbody id="issue-rows">${listRows()}</tbody></table></div><p class="accounting">${t("counts")}</p>`;
}
function issueView() {
  const issue = currentIssue();
  return `<button type="button" class="link back" data-back="true">${iconLabel("back", t("backList"))}</button><div class="title-line"><h1>${t(issue.title)}</h1><span class="issue-type ${issue.kind === "protocol" ? "fail" : "unknown"}">${t(issue.kind)}</span></div><p class="lead">${t(issue.kind === "protocol" ? "taskPass" : "inconclusive")}</p><dl class="difference"><div><dt>${t("expected")}</dt><dd>${t(issue.expected)}</dd></div><div><dt>${t("actual")}</dt><dd class="${issue.kind === "protocol" ? "fail" : "unknown"}">${t(issue.actual)}</dd></div></dl><h2>${t("affectedTitle")} · ${issue.occurrences.length}</h2><div class="table-scroll"><table class="observation-table"><thead><tr><th>${t("case")}</th><th>${t("exchange")}</th><th>${t("location")}</th><th>${t("action")}</th></tr></thead><tbody>${issue.occurrences.map((item, i) => `<tr class="observation-row ${state.occurrence === i ? "selected" : ""}"><td><label><input id="occurrence-${i}" type="radio" name="occurrence" value="${i}" ${state.occurrence === i ? "checked" : ""}>${t(item.label)}</label></td><td>${t("request1")}</td><td><code>${issue.id === "stop" ? "$.stop_sequence" : issue.id === "stream" ? "event 58 / 206" : "read deadline"}</code></td><td><button id="evidence-${i}" type="button" data-inspect="${i}">${t("inspect")}</button></td></tr>`).join("")}</tbody></table></div><p class="selected-context">${t("selected")}：${t(currentOccurrence().label)} / ${t("request1")}</p><details class="scope-note"><summary>${t("scope")}</summary><p><code>${esc(issue.rule)} · ${esc(currentOccurrence().id)}</code></p><p>${t("snapshot")}</p></details>`;
}
function responseObject() { const item = currentOccurrence(); return { id: `msg_flow_${state.occurrence}`, type: "message", role: "assistant", model: "diagnostic-model", content: item.stop === "tool_use" ? [{ type: "tool_use", id: "tool_flow", name: "get_weather", input: { city: "Hanoi" } }] : [{ type: "text", text: "Hello!" }], stop_reason: item.stop, usage: { input_tokens: 12, output_tokens: 5 } }; }
function streamData() { return currentIssue().id === "timeout" ? [start] : events; }
function frame(event) { return `event: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`; }
function objectTree(value, path = "$") {
  if (value === null || typeof value !== "object") return esc(JSON.stringify(value));
  return `<details open><summary><code>${esc(path)}</code> · ${Array.isArray(value) ? "array" : "object"}</summary><dl>${Object.entries(value).map(([key, child]) => `<dt><code>${esc(key)}</code></dt><dd>${child !== null && typeof child === "object" ? objectTree(child, `${path}.${key}`) : esc(JSON.stringify(child))}</dd>`).join("")}</dl></details>`;
}
function eventRows() {
  const stream = streamData(); const indexes = state.mode === "all" || state.eventSearch || stream.length === 1 ? stream.map((_, index) => index) : [0, 54, 55, 56, 57, 58, 59, 60];
  const selected = indexes.filter(index => !state.eventSearch || stream[index].type.toLowerCase().includes(state.eventSearch.toLowerCase()));
  let last = -1;
  if (!selected.length) return `<tr><td colspan="4" class="empty">${t("noEvents")}</td></tr>`;
  const gapRow = count => `<tr class="gap"><td colspan="4">${count} ${t("omitted")} · <button type="button" class="link" data-mode="all">${t("expand")}</button></td></tr>`;
  const rows = selected.map(index => { const gap = !state.eventSearch && index > last + 1 ? gapRow(index - last - 1) : ""; last = index; return `${gap}<tr data-event="${index}" aria-selected="${state.event === index}" class="${index === 57 ? "violation" : ""}"><td class="event-number">${index + 1}</td><td class="event-number">${(index * .012).toFixed(3)}s</td><td><button type="button" class="link"><code>${esc(stream[index].type)}</code></button></td><td>${t(index === 57 ? "duplicate" : "recorded")}</td></tr>`; }).join("");
  return rows + (!state.eventSearch && last < stream.length - 1 ? gapRow(stream.length - last - 1) : "");
}
function payload() {
  const isStream = currentIssue().id !== "stop"; const value = isStream ? streamData()[state.event] || start : responseObject();
  if (state.tab === "fields") return `<div class="parsed">${objectTree(value)}</div>`;
  return `<pre tabindex="0">${esc(state.tab === "capture" ? streamData().map(frame).join("") : isStream ? frame(value) : JSON.stringify(value, null, 2))}</pre>`;
}
function payloadPanel() { return `<nav class="payload-tabs" aria-label="Payload views">${["fields", "raw", ...(currentIssue().id !== "stop" ? ["capture"] : [])].map(tab => `<button type="button" id="tab-${tab}" data-tab="${tab}" aria-pressed="${state.tab === tab}">${t(tab)}</button>`).join("")}</nav><div class="payload-pane" id="payload-pane">${payload()}</div><p class="context-note">${t("capturedOnly")}</p>`; }
function evidenceView() {
  const issue = currentIssue(); const stream = issue.id !== "stop";
  return `<button type="button" class="link back" data-back="true">${iconLabel("back", t("backIssue"))}</button><h1>${t("evidence")} · ${t(currentOccurrence().label)} / ${t("request1")}</h1><p class="selected-context">${t("interpretation")}：${t(issue.title)}</p><p class="evidence-location ${issue.id === "timeout" ? "condition" : ""}">${t(issue.id === "stop" ? "parentLocation" : issue.id === "stream" ? "streamLocation" : "timeoutLocation")}</p>${stream ? `<div class="event-controls">${issue.id === "stream" ? `<button type="button" id="context-mode" data-mode="context" aria-pressed="${state.mode === "context"}">${t("nearby")}</button><button type="button" id="full-mode" data-mode="all" aria-pressed="${state.mode === "all"}">${t("full")}</button>` : ""}${searchField("event-search", t("eventSearch"), t("eventHint"), state.eventSearch)}</div><div class="event-table"><table><thead><tr><th>#</th><th>${t("elapsed")}</th><th>${t("event")}</th><th>${t("observation")}</th></tr></thead><tbody id="event-rows">${eventRows()}</tbody></table></div><p class="selected-context" id="selected-event">${t("eventSelected")} ${state.event + 1} / ${streamData().length} · <code>${esc((streamData()[state.event] || start).type)}</code></p>` : ""}<div id="payload-section">${payloadPanel()}</div>${issue.id === "stream" ? `<p class="context-note">${t("sequenceNote")}</p>` : ""}`;
}
function render() {
  state.occurrence = Math.min(state.occurrence, currentIssue().occurrences.length - 1); if (currentIssue().id === "timeout") state.event = 0;
  globalContext();
  $("#trail").innerHTML = state.view === "list" ? `<span>run-demo-024 / ${t("list")}</span>` : `<button type="button" class="link" data-root="true">${t("list")}</button><span>/</span>${state.view === "evidence" ? `<button type="button" class="link" data-back="true">${t(currentIssue().title)}</button><span>/</span><span>${t(currentOccurrence().label)} · ${t("request1")}</span>` : `<span>${t(currentIssue().title)}</span>`}`;
  $("#main").innerHTML = state.view === "list" ? listView() : state.view === "issue" ? issueView() : evidenceView();
  $("#main").scrollTop = state.scroll;
  if ($(".event-table")) $(".event-table").scrollTop = state.eventScroll;
  if (state.focus) document.getElementById(state.focus)?.focus({ preventScroll: true });
}
document.addEventListener("click", event => {
  const row = event.target.closest("[data-event]"); const button = event.target.closest("button");
  if (row) { state.event = Number(row.dataset.event); state.eventScroll = $(".event-table").scrollTop; $("#event-rows").innerHTML = eventRows(); $("#selected-event").innerHTML = `${t("eventSelected")} ${state.event + 1} / ${streamData().length} · <code>${esc(streamData()[state.event].type)}</code>`; $("#payload-section").innerHTML = payloadPanel(); remember(); return; }
  if (!button) return;
  if (button.dataset.filter) { remember(); state.filter = button.dataset.filter; state.focus = button.id; render(); remember(); }
  if (button.dataset.runState) { app.runState = button.dataset.runState; globalContext(); remember(); }
  if (button.dataset.openIssue) { state.focus = button.id; navigate({ view: "issue", issue: button.dataset.openIssue, occurrence: 0, mode: "context", event: button.dataset.openIssue === "timeout" ? 0 : 57, tab: "fields", eventSearch: "" }); }
  if (button.dataset.inspect !== undefined) { state.occurrence = Number(button.dataset.inspect); state.focus = button.id; navigate({ view: "evidence" }); }
  if (button.dataset.back) back(); if (button.dataset.root) back(true);
  if (button.dataset.mode) { remember(); state.mode = button.dataset.mode; state.focus = button.id; render(); $(".event-table tr[aria-selected=\"true\"]")?.scrollIntoView({ block: "nearest" }); remember(); }
  if (button.dataset.tab) { remember(); state.tab = button.dataset.tab; state.focus = `tab-${state.tab}`; $("#payload-section").innerHTML = payloadPanel(); document.getElementById(state.focus)?.focus({ preventScroll: true }); remember(); }
  if (button.dataset.action === "clear") { state.search = ""; state.filter = "all"; state.focus = "issue-search"; render(); remember(); }
});
document.addEventListener("input", event => {
  if (event.target.id === "issue-search") { state.search = event.target.value; $("#issue-rows").innerHTML = listRows(); $("#issue-counter").textContent = `${filteredIssues().length} ${t("results")}`; remember(); }
  if (event.target.id === "event-search") { state.eventSearch = event.target.value; $("#event-rows").innerHTML = eventRows(); remember(); }
});
document.addEventListener("change", event => {
  if (event.target.name === "occurrence") { remember(); state.occurrence = Number(event.target.value); state.focus = event.target.id; render(); remember(); }
});
$("#language").addEventListener("click", () => { remember(); app.lang = app.lang === "zh" ? "en" : "zh"; render(); remember(); });
$("#theme").addEventListener("click", () => { remember(); app.theme = app.theme === "light" ? "dark" : "light"; globalContext(); remember(); });
window.addEventListener("popstate", event => { if (event.state?.flowStudy !== 1) return; state = { ...defaults, ...event.state.nav }; render(); history.replaceState({ flowStudy: 1, nav: { ...state } }, "", hash()); $("#announcement").textContent = t("restoration"); });
render(); remember();
