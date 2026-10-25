"use strict";

// Synthetic reading samples only. No protocol engine or endpoint is invoked.
const words = {
  study: ["证据定位 · 交互样稿", "Evidence location · interaction study"],
  title: ["响应证据", "Response evidence"],
  back: ["返回问题", "Back to issue"],
  download: ["下载完整样例", "Download sample capture"],
  case: ["用例", "Case"],
  phenomenon: ["观测现象", "Observation"],
  action: ["操作", "Action"],
  sample_case: ["合成示例", "Synthetic example"],
  open: ["查看证据", "View evidence"],
  events: ["相关事件", "Related events"],
  event: ["事件", "Event"],
  context: ["定位关系", "Relationship"],
  parsed: ["解析视图", "Parsed view"],
  raw: ["源记录", "Source record"],
  notes: ["显示标注", "Show annotations"],
  previous: ["上一位置", "Previous"],
  next: ["下一位置", "Next"],
  locate: ["回到定位", "Locate target"],
  location: ["位置", "Location"],
  copy_location: ["复制路径", "Copy path"],
  copy_source: ["复制原始数据", "Copy original data"],
  limits: [
    "全部为合成数据；仅讨论证据交互，不运行模型、不生成测试结论。",
    "Synthetic data only; no model calls or compatibility verdicts.",
  ],
  scenario: ["样稿情形", "Study scenario"],
  missing_case: ["缺少字段", "Missing field"],
  type_case: ["值类型错误", "Wrong value type"],
  sse_case: ["重复 SSE 事件", "Repeated SSE event"],
  missing_title: ["响应缺少 stop_sequence", "Response is missing stop_sequence"],
  type_title: ["output_tokens 的类型不符", "Incorrect output_tokens type"],
  sse_title: ["重复发送 message_start", "Repeated message_start"],
  missing_note: [
    "此对象应包含 stop_sequence。字段未提供，与值为 null 不同。",
    "This object requires stop_sequence. An absent field differs from an explicit null.",
  ],
  type_note: [
    "output_tokens 应为整数，实际记录的是字符串。",
    "output_tokens must be an integer; the recorded value is a string.",
  ],
  sse_note: [
    "同一消息在事件 #0 开始后，事件 #5 再次发送 message_start。",
    "After this message starts at event #0, event #5 sends message_start again.",
  ],
  context_note: [
    "这是首次开始事件，用于与事件 #5 对照；此处没有被标为异常。",
    "This first start event is related context for event #5, not a marked fault.",
  ],
  annotation: ["诊断说明 · 不属于响应内容", "Diagnostic note · not response content"],
  parent: ["父对象定位", "Parent object"],
  exact: ["字段定位", "Field location"],
  related: ["相关证据", "Related context"],
  expected: ["期望", "Expected"],
  observed: ["观测到", "Observed"],
  details: ["展开说明", "Show details"],
  collapse_note: ["收起说明", "Hide details"],
  missing_expected: [
    "存在 stop_sequence 键；允许显式 null",
    "stop_sequence key is present; explicit null is allowed",
  ],
  missing_actual: ["对象中没有该键", "The key is absent from this object"],
  type_expected: ["整数（integer）", "Integer"],
  type_actual: ['字符串（string）："8"', 'String: "8"'],
  sse_expected: ["同一消息只有一个开始事件", "One start event for the message"],
  sse_actual: ["事件 #0 与 #5 都发送了 message_start", "Events #0 and #5 both send message_start"],
  related_event: ["查看首次事件 #0", "Inspect first event #0"],
  fault_event: ["回到异常事件 #5", "Return to event #5"],
  first: ["首次开始 · 对照", "First start · context"],
  repeated: ["再次开始 · 示例偏差", "Repeated start · sample deviation"],
  surrounding: ["上下文", "Context"],
  all_events: ["显示全部 7 个事件", "Show all 7 events"],
  relevant_events: ["仅相关上下文", "Related context only"],
  parsed_note: [
    "标注与数据分开呈现；复制与下载不会包含诊断说明。",
    "Annotations are separate from data and excluded from copy/download.",
  ],
  raw_note: [
    "源记录保留原文；切换解析视图查看节点标注。",
    "Original text is preserved; use Parsed view for node annotations.",
  ],
  capture: ["合成响应 · 请求 1 · response.json", "Synthetic response · request 1 · response.json"],
  stream_capture: [
    "合成捕获 · 请求 1 · events.jsonl · 事件从 0 编号",
    "Synthetic capture · request 1 · events.jsonl · zero-based event numbers",
  ],
  copied: ["已复制", "Copied"],
  copy_failed: [
    "剪贴板不可用，可在源记录中选择复制。",
    "Clipboard unavailable; select and copy text in Source record.",
  ],
  fold: ["折叠", "Collapse"],
  unfold: ["展开", "Expand"],
  contains: ["对象内含一处定位", "Contains a target location"],
  free_context: ["自由查看上下文", "Browsing context"],
  root: ["响应根对象", "Response root"],
  navigation: ["调查位置", "Investigation location"],
  data_view: ["数据视图", "Data view"],
  evidence_data: ["证据数据", "Evidence data"],
};
const sampleRaw = {
  missing:
    '{\n  "id": "msg_sample",\n  "type": "message",\n  "role": "assistant",\n  "model": "example-model",\n  "content": [{ "type": "text", "text": "Ready." }],\n  "stop_reason": "end_turn",\n  "usage": { "input_tokens": 24, "output_tokens": 8 }\n}',
  type: '{\n  "id": "msg_sample",\n  "type": "message",\n  "role": "assistant",\n  "model": "example-model",\n  "content": [{ "type": "text", "text": "Ready." }],\n  "stop_reason": "end_turn",\n  "stop_sequence": null,\n  "usage": {\n    "input_tokens": 24,\n    "output_tokens": "8"\n  }\n}',
};
const eventValues = [
  {
    type: "message_start",
    message: {
      id: "msg_sample",
      type: "message",
      role: "assistant",
      model: "example-model",
      content: [],
      stop_reason: null,
      stop_sequence: null,
      usage: { input_tokens: 24, output_tokens: 0 },
    },
  },
  { type: "content_block_start", index: 0, content_block: { type: "text", text: "" } },
  { type: "content_block_delta", index: 0, delta: { type: "text_delta", text: "Ready." } },
  { type: "content_block_stop", index: 0 },
  {
    type: "message_delta",
    delta: { stop_reason: "end_turn", stop_sequence: null },
    usage: { output_tokens: 8 },
  },
  {
    type: "message_start",
    message: {
      id: "msg_sample",
      type: "message",
      role: "assistant",
      model: "example-model",
      content: [],
      stop_reason: null,
      stop_sequence: null,
      usage: { input_tokens: 24, output_tokens: 0 },
    },
  },
  { type: "message_stop" },
];
const records = eventValues.map(
  (value, sequence) =>
    JSON.stringify({ sequence, event: value.type, data: JSON.stringify(value) }) + "\n",
);
const params = new URLSearchParams(location.hash.slice(1));
const app = {
  scenario: ["missing", "type", "sse"].includes(params.get("scenario"))
    ? params.get("scenario")
    : "missing",
  lang: params.get("lang") === "en" ? "en" : "zh",
  theme: params.get("theme") === "dark" ? "dark" : "light",
  view: "evidence",
};
const saved = new Map();
let state;
let captureURL = "";
let line = 0;
const $ = (id) => document.getElementById(id);
const t = (key) => words[key][app.lang === "en" ? 1 : 0];
const element = (tag, className, text) => {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== undefined) item.textContent = text;
  return item;
};
const pointerPart = (value) => String(value).replace(/~/gu, "~0").replace(/\//gu, "~1");
function currentState() {
  if (!saved.has(app.scenario))
    saved.set(app.scenario, {
      mode: "parsed",
      notes: true,
      details: false,
      event: 5,
      expanded: new Set([""]),
      scroll: 0,
      mainScroll: 0,
      allEvents: false,
    });
  return saved.get(app.scenario);
}
function point() {
  if (app.scenario === "missing")
    return { pointer: "", kind: "fault", note: "missing", location: "parent" };
  if (app.scenario === "type")
    return { pointer: "/usage/output_tokens", kind: "fault", note: "type", location: "exact" };
  if (state.event === 5) return { pointer: "/type", kind: "fault", note: "sse", location: "exact" };
  if (state.event === 0)
    return { pointer: "/type", kind: "context", note: "context", location: "related" };
  return { pointer: "", kind: "context", note: null, location: "free_context" };
}
function value() {
  return app.scenario === "sse" ? eventValues[state.event] : JSON.parse(sampleRaw[app.scenario]);
}
function raw() {
  return app.scenario === "sse" ? records[state.event] : sampleRaw[app.scenario];
}
function fullCapture() {
  return app.scenario === "sse" ? records.join("") : raw();
}
function remember() {
  if (!$("evidence-view").hidden) {
    state.scroll = $("json-scroll").scrollTop;
    state.mainScroll = $("main").scrollTop;
  }
}
function writeLocation(push = false) {
  const next = new URLSearchParams({
    scenario: app.scenario,
    lang: app.lang,
    theme: app.theme,
    view: app.view,
  });
  const url = "#" + next.toString();
  if (push) history.pushState({}, "", url);
  else history.replaceState(history.state, "", url);
}
function annotation() {
  const ref = point();
  const note = element("aside", "node-annotation" + (ref.kind === "context" ? " is-context" : ""));
  note.id = "annotation";
  note.setAttribute("aria-label", t("annotation"));
  const heading = element("div", "annotation-heading");
  const title = element(
    "strong",
    "",
    t(ref.kind === "context" ? "related" : app.scenario + "_case"),
  );
  title.id = "note-title";
  heading.append(title, element("span", "annotation-label", t("annotation")));
  note.append(heading, element("p", "", t(ref.note + "_note")));
  if (state.details && ref.kind === "fault") {
    const columns = element("dl", "expected-actual");
    for (const [label, key] of [
      ["expected", "expected"],
      ["observed", "actual"],
    ]) {
      const group = element("div");
      group.append(element("dt", "", t(label)), element("dd", "", t(ref.note + "_" + key)));
      columns.append(group);
    }
    note.append(columns);
  }
  const actions = element("div", "annotation-actions");
  if (ref.kind === "fault") {
    const details = element("button", "link", t(state.details ? "collapse_note" : "details"));
    details.type = "button";
    details.id = "note-details";
    details.setAttribute("aria-expanded", String(state.details));
    actions.append(details);
  }
  if (app.scenario === "sse") {
    const related = element(
      "button",
      "link",
      t(state.event === 5 ? "related_event" : "fault_event"),
    );
    related.type = "button";
    related.id = "related-event";
    actions.append(related);
  }
  note.append(actions);
  return note;
}
function renderJSON() {
  const previousFocus = document.activeElement?.getAttribute("data-fold");
  const focusId = document.activeElement?.id;
  const rows = $("json-rows");
  rows.replaceChildren();
  line = 0;
  const ref = point();
  function row(pointer, depth, text, container, expanded, closing = false) {
    const item = element("div", "data-row");
    item.dataset.pointer = closing ? pointer + "/@close" : pointer;
    const target = !closing && pointer === ref.pointer;
    item.classList.toggle("is-target", target);
    item.classList.toggle("is-fault", target && state.notes && ref.kind === "fault");
    item.tabIndex = -1;
    item.append(element("span", "line-number", String(++line)));
    if (container && !closing) {
      const fold = element("button", "fold");
      fold.type = "button";
      fold.dataset.fold = pointer;
      fold.setAttribute("aria-expanded", String(expanded));
      fold.setAttribute("aria-label", t(expanded ? "fold" : "unfold") + " " + (pointer || "$"));
      fold.append(element("span", "icon"));
      fold.firstChild.setAttribute("aria-hidden", "true");
      item.append(fold);
    } else item.append(element("span"));
    const code = element("code", "node-code", "  ".repeat(depth) + text);
    item.append(code);
    if (container && !expanded && ref.pointer.startsWith(pointer + "/"))
      code.append(element("span", "collapsed-note", t("contains")));
    rows.append(item);
    if (target && state.notes && ref.note) rows.append(annotation());
  }
  function visit(data, pointer, depth, key, comma) {
    const prefix = key === null ? "" : JSON.stringify(key) + ": ";
    if (data !== null && typeof data === "object") {
      const array = Array.isArray(data),
        opening = array ? "[" : "{",
        closing = array ? "]" : "}";
      const expanded = state.expanded.has(pointer),
        entries = Object.entries(data);
      row(
        pointer,
        depth,
        prefix + opening + (expanded ? "" : " … " + closing + comma),
        true,
        expanded,
      );
      if (expanded) {
        entries.forEach(([name, child], index) =>
          visit(
            child,
            pointer + "/" + pointerPart(name),
            depth + 1,
            array ? null : name,
            index < entries.length - 1 ? "," : "",
          ),
        );
        row(pointer, depth, closing + comma, true, true, true);
      }
    } else row(pointer, depth, prefix + JSON.stringify(data) + comma, false, false);
  }
  visit(value(), "", 0, null, "");
  if (previousFocus !== null && previousFocus !== undefined)
    rows
      .querySelector('[data-fold="' + CSS.escape(previousFocus) + '"]')
      ?.focus({ preventScroll: true });
  else if (focusId === "note-details" || focusId === "related-event")
    $(focusId)?.focus({ preventScroll: true });
}
function renderEvents() {
  const focusedEvent = document.activeElement?.getAttribute("data-event");
  const eventList = document.querySelector(".event-list");
  const scroll = eventList.scrollTop;
  $("event-section").hidden = app.scenario !== "sse";
  const rows = $("event-rows");
  rows.replaceChildren();
  if (app.scenario !== "sse") return;
  const included = state.allEvents ? eventValues.map((_, i) => i) : [0, 4, 5, 6];
  for (const index of included) {
    const row = element("tr");
    row.setAttribute("aria-current", String(index === state.event));
    const action = element("button", "", eventValues[index].type);
    action.type = "button";
    action.dataset.event = String(index);
    action.setAttribute("aria-current", String(index === state.event));
    const name = element("td");
    name.append(action);
    row.append(
      element("td", "", String(index)),
      name,
      element(
        "td",
        index === 5 ? "fail" : "",
        t(index === 5 ? "repeated" : index === 0 ? "first" : "surrounding"),
      ),
    );
    rows.append(row);
  }
  $("event-scope").textContent = t(state.allEvents ? "relevant_events" : "all_events");
  eventList.scrollTop = scroll;
  if (focusedEvent !== null && focusedEvent !== undefined)
    rows
      .querySelector('[data-event="' + CSS.escape(focusedEvent) + '"]')
      ?.focus({ preventScroll: true });
}
function render() {
  state = currentState();
  document.documentElement.lang = app.lang === "en" ? "en" : "zh-CN";
  document.documentElement.dataset.theme = app.theme;
  document.querySelectorAll("[data-copy]").forEach((item) => {
    item.textContent = t(item.dataset.copy);
  });
  $("trail").setAttribute("aria-label", t("navigation"));
  document.querySelector(".mode-tabs").setAttribute("aria-label", t("data_view"));
  $("json-scroll").setAttribute("aria-label", t("evidence_data"));
  $("language").textContent = app.lang === "en" ? "中" : "EN";
  $("language").title = app.lang === "en" ? "切换为中文" : "Switch to English";
  $("language").setAttribute("aria-label", $("language").textContent + " · " + $("language").title);
  $("theme").title =
    app.theme === "dark"
      ? app.lang === "zh"
        ? "切换为浅色主题"
        : "Switch to light theme"
      : app.lang === "zh"
        ? "切换为深色主题"
        : "Switch to dark theme";
  $("theme").setAttribute("aria-label", $("theme").title);
  $("theme").firstElementChild.className =
    "icon " + (app.theme === "dark" ? "icon-sun" : "icon-moon");
  $("sample-scenario").value = app.scenario;
  $("problem-view").hidden = app.view !== "problem";
  $("evidence-view").hidden = app.view !== "evidence";
  $("back-problem").hidden = app.view === "problem";
  $("trail-title").textContent = t(app.scenario + "_title");
  $("problem-title").textContent = t(app.scenario + "_title");
  $("problem-name").textContent = t(app.scenario + "_case");
  $("problem-summary").textContent = t(app.scenario + "_note");
  $("capture-context").textContent = t(app.scenario === "sse" ? "stream_capture" : "capture");
  renderEvents();
  $("mode-parsed").setAttribute("aria-pressed", String(state.mode === "parsed"));
  $("mode-raw").setAttribute("aria-pressed", String(state.mode === "raw"));
  $("show-notes").checked = state.notes;
  $("show-notes").disabled = state.mode === "raw";
  $("json-rows").hidden = state.mode === "raw";
  $("raw-source").hidden = state.mode !== "raw";
  $("raw-source").textContent = raw();
  const ref = point();
  $("location-pointer").textContent =
    (app.scenario === "sse" ? "#" + state.event + " · " : "") + (ref.pointer || "$ ");
  $("location-kind").textContent = t(ref.location);
  $("position-count").textContent =
    app.scenario === "sse"
      ? state.event === 5
        ? "1 / 2"
        : state.event === 0
          ? "2 / 2"
          : "— / 2"
      : "1 / 1";
  $("previous-location").disabled = app.scenario !== "sse" || state.event !== 0;
  $("next-location").disabled = app.scenario !== "sse" || state.event !== 5;
  $("source-note").textContent = t(state.mode === "raw" ? "raw_note" : "parsed_note");
  if (captureURL) URL.revokeObjectURL(captureURL);
  captureURL = URL.createObjectURL(
    new Blob([fullCapture()], {
      type: app.scenario === "sse" ? "application/x-ndjson" : "application/json",
    }),
  );
  $("download-capture").href = captureURL;
  $("download-capture").download =
    "sample-" + app.scenario + (app.scenario === "sse" ? ".jsonl" : ".json");
  renderJSON();
  $("json-scroll").scrollTop = state.scroll;
  $("main").scrollTop = state.mainScroll;
  $("status").textContent = "";
}
function locate() {
  state.mode = "parsed";
  if (app.scenario === "sse") state.event = 5;
  const pointer = point().pointer;
  state.expanded.add("");
  const parts = pointer.split("/").slice(1);
  let parent = "";
  for (const part of parts.slice(0, -1)) {
    parent += "/" + part;
    state.expanded.add(parent);
  }
  render();
  const target = $("json-rows").querySelector(".is-target");
  target?.scrollIntoView({ block: "nearest" });
  target?.focus({ preventScroll: true });
}
document.addEventListener("click", async (event) => {
  if (!(event.target instanceof Element)) return;
  const button = event.target.closest("button");
  if (!button) return;
  remember();
  if (button.id === "language") app.lang = app.lang === "zh" ? "en" : "zh";
  else if (button.id === "theme") app.theme = app.theme === "light" ? "dark" : "light";
  else if (button.id === "back-problem" || button.id === "open-evidence") {
    app.view = button.id === "back-problem" ? "problem" : "evidence";
    writeLocation(true);
    render();
    return;
  } else if (button.id === "mode-raw" || button.id === "mode-parsed")
    state.mode = button.id === "mode-raw" ? "raw" : "parsed";
  else if (button.id === "note-details") state.details = !state.details;
  else if (button.id === "event-scope") state.allEvents = !state.allEvents;
  else if (
    button.id === "related-event" ||
    button.id === "previous-location" ||
    button.id === "next-location"
  )
    state.event = state.event === 5 ? 0 : 5;
  else if (button.dataset.event !== undefined) state.event = Number(button.dataset.event);
  else if (button.dataset.fold !== undefined) {
    const pointer = button.dataset.fold;
    if (state.expanded.has(pointer)) state.expanded.delete(pointer);
    else state.expanded.add(pointer);
  } else if (button.id === "locate") {
    locate();
    return;
  } else if (button.id === "copy-source" || button.id === "copy-location") {
    try {
      await navigator.clipboard.writeText(
        button.id === "copy-source"
          ? raw()
          : (app.scenario === "sse" ? "#" + state.event + " " : "") + (point().pointer || "$"),
      );
      $("status").textContent = t("copied");
    } catch {
      $("status").textContent = t("copy_failed");
    }
    return;
  } else return;
  writeLocation();
  render();
});
$("show-notes").addEventListener("change", () => {
  remember();
  state.notes = $("show-notes").checked;
  render();
});
$("sample-scenario").addEventListener("change", () => {
  remember();
  app.scenario = $("sample-scenario").value;
  state = currentState();
  writeLocation(true);
  locate();
});
window.addEventListener("popstate", () => {
  remember();
  const next = new URLSearchParams(location.hash.slice(1));
  app.scenario = ["missing", "type", "sse"].includes(next.get("scenario"))
    ? next.get("scenario")
    : "missing";
  app.view = next.get("view") === "problem" ? "problem" : "evidence";
  state = currentState();
  render();
});
state = currentState();
app.view = params.get("view") === "problem" ? "problem" : "evidence";
writeLocation();
locate();
