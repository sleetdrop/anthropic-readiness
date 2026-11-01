import { pointerValue, readingTarget, jsonRows } from "./evidence-json.js";
export { locatePointer } from "./evidence-json.js";
/** Reading projections only. These never validate or rescore protocol behavior. */
/** @typedef {import("./contracts.js").JsonValue} JsonValue */
/** @typedef {{event:number,label:string,raw:string,value:JsonValue,parsed:boolean}} EvidenceFrame */
/** @param {string} raw @returns {{value:JsonValue,parsed:boolean}} */
function parse(raw) {
  try {
    return { value: /** @type {JsonValue} */ (JSON.parse(raw)), parsed: true };
  } catch {
    return { value: null, parsed: false };
  }
}
/** @param {string} raw @param {boolean|"events"} [stream] @returns {EvidenceFrame[]} */
export function evidenceFrames(raw, stream = false) {
  if (stream === "events") {
    return raw.split(/(?<=\n)/u).flatMap((line, index) => {
      const record = parse(line);
      const frame = record.value;
      if (
        !record.parsed ||
        !frame ||
        typeof frame !== "object" ||
        Array.isArray(frame) ||
        frame.sequence !== index ||
        typeof frame.data !== "string"
      )
        return [];
      return [
        { event: index, label: String(frame.event || "message"), raw: line, ...parse(frame.data) },
      ];
    });
  }
  if (!stream) return [{ event: 0, label: "JSON", raw, ...parse(raw) }];
  /** @type {EvidenceFrame[]} */ const frames = [];
  for (const block of raw.match(/[^]*?(?:\r\n\r\n|\n\n|\r\r|$)/gu) ?? []) {
    let label = "message";
    /** @type {string[]} */ const data = [];
    for (const line of block.split(/\r\n|\r|\n/u)) {
      if (line.startsWith("event:")) label = line.slice(6).replace(/^ /u, "");
      if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /u, ""));
    }
    if (data.length)
      frames.push({ event: frames.length, label, raw: block, ...parse(data.join("\n")) });
  }
  return frames;
}
/** Full loaded-capture search; context also retains the first lifecycle anchor.
 * @param {EvidenceFrame[]} frames @param {number} selected @param {string} query
 */
export function contextFrames(frames, selected, query) {
  const search = query.toLocaleLowerCase();
  if (search)
    return frames.filter((frame) =>
      (frame.raw + JSON.stringify(frame.value)).toLocaleLowerCase().includes(search),
    );
  const anchor = frames.find((frame) => frame.label === "message_start");
  return frames.filter((frame) => frame === anchor || Math.abs(frame.event - selected) <= 2);
}
/** @param {{read:(r:Response)=>Promise<{text:string,truncated:boolean}>,text:(key:string,params?:Record<string,string|number>)=>string,api:(path:string)=>Promise<unknown>}} ports */
export function mountEvidence(ports) {
  const dialog = document.getElementById("evidence-dialog");
  if (!(dialog instanceof HTMLDialogElement)) return;
  const text = ports.text;
  /** @param {string} id */
  const element = (id) => {
    const node = document.getElementById(id);
    if (!node) throw new Error("invalid_evidence_page");
    return node;
  };
  const content = element("evidence-content");
  const search = /** @type {HTMLInputElement} */ (element("event-search"));
  const download = /** @type {HTMLAnchorElement} */ (element("evidence-download"));
  const panel = element("evidence-annotation");
  const notes = /** @type {HTMLInputElement} */ (element("evidence-annotations"));
  /** @typedef {{selected:number,query:string,all:boolean,raw:boolean,scroll:number,left:number,eventScroll:number,dialogScroll:number,limit:number,notes:boolean,expanded:Record<string,string[]>,jsonLimit:number}} ReadingState */
  /** @type {Map<string,ReadingState>} */ const saved = new Map();
  /** @type {ReadingState} */ let state = {
    selected: 0,
    query: "",
    all: false,
    raw: false,
    scroll: 0,
    left: 0,
    eventScroll: 0,
    dialogScroll: 0,
    limit: 100,
    notes: true,
    expanded: {},
    jsonLimit: 500,
  };
  /** @type {EvidenceFrame[]} */ let frames = [];
  /** @type {HTMLElement|null} */ let opener = null;
  /** @type {AbortController|null} */ let request = null;
  let order = 0,
    key = "",
    pointer = "",
    path = "",
    context = "";
  let truncated = false,
    loading = false,
    unavailable = false,
    visibleLimit = 100;
  let focusEvent = 0;
  let pointerKnown = false,
    eventKnown = false,
    failed = false;
  let reason = "",
    expected = "",
    actual = "",
    check = "";
  /** @type {import('./evidence-json.js').ReadingTarget|null} */ let location = null;
  let related = false;
  /** @param {string} tag @param {string} className @param {string} [value] */
  function node(tag, className, value) {
    const result = document.createElement(tag);
    result.className = className;
    if (value !== undefined) result.textContent = value;
    return result;
  }
  /** @param {boolean} [restore] */
  function closeNote(restore = false) {
    if (!panel.matches(":popover-open")) return;
    panel.hidePopover();
    const marker = content.querySelector(".evidence-marker");
    marker?.setAttribute("aria-expanded", "false");
    if (restore && marker instanceof HTMLElement) marker.focus({ preventScroll: true });
  }
  /** @param {HTMLElement} marker */
  function openNote(marker) {
    panel.replaceChildren();
    panel.classList.toggle("is-context", related);
    const heading = node("div", "annotation-heading");
    const title = node("strong", "", related ? text("annotation.related") : context);
    title.id = "evidence-note-title";
    const close = node("button", "annotation-close", text("action.close"));
    close.setAttribute("type", "button");
    close.id = "close-annotation";
    heading.append(title, close);
    panel.append(heading, node("p", "annotation-label", text("annotation.separate")));
    const frame = frames.find((item) => item.event === state.selected);
    if (related) panel.append(node("p", "", text("annotation.context_hint")));
    else {
      if (location?.missing)
        panel.append(
          node("p", "", text("console.missing_parent", { pointer: location.pointer || "$" })),
        );
      const columns = node("dl", "annotation-values");
      for (const [label, value] of [
        ["issue.expected", expected || text("annotation.no_expected")],
        [
          "issue.actual",
          actual ||
            (frame && location ? JSON.stringify(pointerValue(frame.value, location.pointer)) : ""),
        ],
      ]) {
        const group = node("div", "");
        group.append(node("dt", "", text(label)), node("dd", "", value.slice(0, 2000)));
        columns.append(group);
      }
      panel.append(columns, node("code", "annotation-check", check + " · " + reason));
    }
    const first =
      reason === "duplicate_message_start"
        ? frames.find((item) => item.label === "message_start" && item.event < focusEvent)
        : null;
    if (first) {
      const button = node(
        "button",
        "annotation-related",
        text(related ? "annotation.return_target" : "annotation.first_event", {
          event: related ? focusEvent : first.event,
        }),
      );
      button.id = "annotation-related";
      button.setAttribute("type", "button");
      button.dataset.event = String(related ? focusEvent : first.event);
      panel.append(button);
    }
    panel.showPopover();
    marker.setAttribute("aria-expanded", "true");
    const range = document.createRange();
    range.selectNodeContents(marker.closest(".evidence-code") ?? marker);
    const target = range.getBoundingClientRect(),
      edge = 12,
      gap = 10;
    panel.style.maxHeight = Math.min(420, innerHeight - 24) + "px";
    const width = panel.getBoundingClientRect().width;
    let height = panel.getBoundingClientRect().height;
    const right = Math.max(
      ...Array.from(content.querySelectorAll(".evidence-code"), (code) => {
        const r = document.createRange();
        r.selectNodeContents(code);
        return r.getBoundingClientRect().right;
      }),
    );
    let left, top;
    if (innerWidth > 650 && right + gap + width <= innerWidth - edge) {
      left = right + gap;
      top = Math.max(edge, Math.min(target.top, innerHeight - height - edge));
    } else {
      const below = innerHeight - target.bottom - gap - edge,
        above = target.top - gap - edge;
      const useBelow = below >= height || below >= above;
      panel.style.maxHeight = Math.max(40, Math.min(420, useBelow ? below : above)) + "px";
      height = panel.getBoundingClientRect().height;
      left = Math.max(edge, Math.min(target.left, innerWidth - width - edge));
      top = useBelow ? target.bottom + gap : target.top - height - gap;
      if (innerWidth <= 650 && useBelow) top = innerHeight - edge - height;
    }
    panel.style.left = left + "px";
    panel.style.top = top + "px";
    close.focus({ preventScroll: true });
  }
  function locate() {
    const frame = frames.find((item) => item.event === state.selected);
    if (!frame || !location) return;
    const expanded = new Set(state.expanded[String(frame.event)] ?? [""]);
    expanded.add("");
    let parent = "";
    for (const part of location.pointer.slice(1).split("/").slice(0, -1)) {
      parent += "/" + part;
      expanded.add(parent);
    }
    state.expanded[String(frame.event)] = [...expanded];
    state.raw = false;
    renderPayload();
    content.querySelector(".evidence-target")?.scrollIntoView({ block: "nearest" });
  }
  /** @param {string} id @param {boolean} pressed */
  function pressed(id, pressed) {
    element(id).setAttribute("aria-pressed", String(pressed));
  }
  function renderPayload() {
    closeNote();
    const scroll = content.scrollTop,
      left = content.scrollLeft;
    const frame = frames.find((item) => item.event === state.selected);
    notes.checked = state.notes;
    notes.disabled = state.raw || !failed || loading || unavailable;
    location = null;
    related = false;
    pressed("payload-parsed", !state.raw);
    pressed("payload-raw", state.raw);
    if (!frame) {
      element("evidence-location").textContent = text("console.target_unloaded", {
        event: state.selected,
      });
      content.textContent = text("console.target_unloaded_hint");
      return;
    }
    if (!frame.parsed) {
      element("evidence-location").textContent = text("console.no_parse");
      content.textContent = state.raw ? frame.raw : text("console.no_parse");
      return;
    }
    const stream = path.endsWith("events.jsonl");
    related =
      failed &&
      reason === "duplicate_message_start" &&
      frame.event < focusEvent &&
      frame === frames.find((item) => item.label === "message_start");
    if (
      failed &&
      (!stream || eventKnown) &&
      (!truncated || stream) &&
      (frame.event === focusEvent || related)
    )
      location = readingTarget(frame.value, pointerKnown && !related ? pointer : null, reason);
    element("evidence-location").textContent =
      (location
        ? text(location.missing ? "console.missing_parent" : "console.at_pointer", {
            pointer: location.pointer || "$",
          })
        : text("annotation.no_location")) + (stream ? ` · #${frame.event}` : "");
    if (related)
      element("evidence-location").textContent = text("annotation.related") + ` · #${frame.event}`;
    if (state.raw) {
      content.textContent = frame.raw;
      return;
    }
    const frameKey = String(frame.event);
    if (!Object.hasOwn(state.expanded, frameKey)) {
      const expanded = new Set([""]);
      let parent = "";
      for (const part of location?.pointer.slice(1).split("/").slice(0, -1) ?? []) {
        parent += "/" + part;
        expanded.add(parent);
      }
      state.expanded[frameKey] = [...expanded];
    }
    const projection = jsonRows(
      frame.value,
      new Set(state.expanded[frameKey]),
      state.jsonLimit,
      location?.pointer ?? null,
    );
    if (projection.start)
      element("evidence-location").textContent +=
        " · " + text("annotation.window", { line: projection.start + 1 });
    if (projection.rows.some((row) => row.depthLimited))
      element("evidence-location").textContent += " · " + text("annotation.depth_limit");
    const focusPointer = document.activeElement?.getAttribute("data-json-fold");
    content.replaceChildren();
    for (const [index, row] of projection.rows.entries()) {
      const item = node("div", "evidence-row");
      item.dataset.pointer = row.pointer;
      const target = !row.closing && location?.pointer === row.pointer;
      item.classList.toggle("evidence-target", target);
      item.append(node("span", "evidence-line", String(projection.start + index + 1)));
      if (row.container) {
        const fold = node("button", "evidence-fold");
        fold.setAttribute("type", "button");
        fold.dataset.jsonFold = row.pointer;
        fold.setAttribute("aria-expanded", String(row.expanded));
        fold.setAttribute(
          "aria-label",
          text(row.expanded ? "annotation.fold" : "annotation.expand", {
            pointer: row.pointer || "$",
          }),
        );
        const icon = node("span", "icon");
        icon.setAttribute("aria-hidden", "true");
        fold.append(icon);
        item.append(fold);
      } else item.append(node("span", ""));
      const code = node("code", "evidence-code", row.text);
      if (target && state.notes) {
        const token = node(
          "span",
          "evidence-token",
          row.text.slice(row.start, row.start + row.length),
        );
        const marker = node("button", "evidence-marker" + (related ? " is-context" : ""));
        marker.setAttribute("type", "button");
        marker.setAttribute("popovertarget", "evidence-annotation");
        marker.setAttribute("aria-expanded", "false");
        marker.setAttribute("aria-haspopup", "dialog");
        marker.setAttribute("aria-controls", "evidence-annotation");
        marker.setAttribute("aria-label", text(related ? "annotation.related" : "annotation.open"));
        marker.title = marker.getAttribute("aria-label") ?? "";
        marker.style.left = `calc(100% + ${row.text.length - row.start - row.length}ch + 6px)`;
        const icon = node("span", "icon");
        icon.setAttribute("aria-hidden", "true");
        marker.append(icon);
        token.append(marker);
        code.replaceChildren(
          document.createTextNode(row.text.slice(0, row.start)),
          token,
          document.createTextNode(row.text.slice(row.start + row.length)),
        );
      }
      item.append(code);
      content.append(item);
    }
    if (projection.limited) {
      const more = node("button", "", text("annotation.more"));
      more.id = "json-more";
      more.setAttribute("type", "button");
      content.append(more);
    }
    content.scrollTop = scroll;
    content.scrollLeft = left;
    if (focusPointer !== null && focusPointer !== undefined)
      /** @type {HTMLElement|null} */ (
        content.querySelector(`[data-json-fold="${CSS.escape(focusPointer)}"]`)
      )?.focus({ preventScroll: true });
  }
  function render() {
    closeNote();
    for (const id of [
      "payload-parsed",
      "payload-raw",
      "event-context",
      "event-all",
      "event-search",
      "evidence-locate",
    ])
      /** @type {HTMLButtonElement|HTMLInputElement} */ (element(id)).disabled =
        loading || unavailable;
    element("evidence-context").textContent = context + " · " + path;
    element("evidence-notice").textContent = loading
      ? text("evidence.loading")
      : unavailable
        ? text("evidence.unavailable")
        : text(path.endsWith("events.jsonl") ? "console.event_records" : "console.body_record") +
          (truncated ? " " + text("evidence.truncated") : "");
    element("event-inspector").hidden = !path.endsWith("events.jsonl") || loading || unavailable;
    download.hidden = loading || unavailable;
    pressed("event-context", !state.all);
    pressed("event-all", state.all);
    if (loading || unavailable) {
      notes.disabled = true;
      content.textContent = text(loading ? "evidence.loading" : "evidence.unavailable");
      return;
    }
    const rows = element("event-rows");
    rows.replaceChildren();
    const shown =
      state.query || !state.all ? contextFrames(frames, focusEvent, state.query) : frames;
    for (const frame of shown.slice(0, visibleLimit)) {
      const row = document.createElement("tr");
      row.setAttribute("aria-selected", String(frame.event === state.selected));
      const number = document.createElement("td");
      number.textContent = String(frame.event);
      const label = document.createElement("td");
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = frame.label;
      button.dataset.event = String(frame.event);
      label.append(button);
      row.append(number, label);
      rows.append(row);
    }
    if (shown.length > visibleLimit) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 2;
      const more = document.createElement("button");
      more.type = "button";
      more.id = "events-more";
      more.textContent = text("console.load_more");
      cell.append(more);
      row.append(cell);
      rows.append(row);
    }
    element("event-count").textContent = shown.length
      ? text("console.event_range", {
          shown: Math.min(visibleLimit, shown.length),
          total: frames.length,
        })
      : text("console.empty_events");
    renderPayload();
  }
  document.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    if (event.target.closest("#close-evidence")) dialog.close();
    const link = event.target.closest("a[data-evidence-id]");
    if (
      !(link instanceof HTMLAnchorElement) ||
      event.ctrlKey ||
      event.metaKey ||
      event.shiftKey ||
      event.button !== 0
    )
      return;
    event.preventDefault();
    opener = link;
    path = link.dataset.evidencePath ?? "";
    context = link.dataset.evidenceContext ?? link.textContent ?? "";
    pointer = link.dataset.evidencePointer ?? "";
    pointerKnown = link.dataset.evidencePointerKnown === "true";
    eventKnown = link.dataset.evidenceEvent !== "" && link.dataset.evidenceEvent !== undefined;
    failed = link.dataset.evidenceStatus === "FAIL";
    reason = link.dataset.evidenceReason ?? "";
    check = link.dataset.evidenceCheck ?? "";
    expected = link.dataset.evidenceExpected ?? "";
    actual = link.dataset.evidenceActual ?? "";
    key = [link.dataset.evidenceId, link.dataset.evidenceEvent, pointer, check, reason].join(":");
    const target = Number(link.dataset.evidenceEvent || 0);
    focusEvent = target;
    state = saved.get(key) ?? {
      selected: target,
      query: "",
      all: false,
      raw: false,
      scroll: 0,
      left: 0,
      eventScroll: 0,
      dialogScroll: 0,
      limit: 100,
      notes: true,
      expanded: {},
      jsonLimit: 500,
    };
    search.value = state.query;
    download.href = link.href;
    const ticket = ++order;
    request?.abort();
    request = new AbortController();
    const signal = AbortSignal.any([request.signal, AbortSignal.timeout(15000)]);
    frames = [];
    truncated = false;
    loading = true;
    unavailable = false;
    visibleLimit = state.limit;
    render();
    dialog.showModal();
    void (async () => {
      let response = await fetch(link.href, {
        credentials: "same-origin",
        cache: "no-store",
        signal,
      });
      if (response.status === 401) {
        await ports.api("/api/v1/catalog");
        response = await fetch(link.href, {
          credentials: "same-origin",
          cache: "no-store",
          signal,
        });
      }
      if (!response.ok) throw new Error("evidence_unavailable");
      const value = await ports.read(response);
      if (ticket !== order || !dialog.open) return;
      truncated = value.truncated;
      loading = false;
      const raw =
        truncated && path.endsWith("events.jsonl")
          ? value.text.slice(0, value.text.lastIndexOf("\n") + 1)
          : value.text;
      frames = evidenceFrames(raw, path.endsWith("events.jsonl") ? "events" : false);
      render();
      content.scrollTop = state.scroll;
      content.scrollLeft = state.left;
      element("event-rows").closest(".event-table")?.scrollTo({ top: state.eventScroll });
      dialog.scrollTop = state.dialogScroll;
    })().catch(() => {
      if (ticket === order && dialog.open) {
        loading = false;
        unavailable = true;
        render();
      }
    });
  });
  search.addEventListener("input", () => {
    state.query = search.value;
    visibleLimit = 100;
    render();
  });
  dialog.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    const target = event.target.closest("button");
    if (!target) return;
    if (target.classList.contains("evidence-marker")) {
      event.preventDefault();
      if (panel.matches(":popover-open")) closeNote(true);
      else openNote(target);
      return;
    }
    if (target.id === "close-annotation") {
      closeNote(true);
      return;
    }
    if (target.id === "annotation-related") {
      state.selected = Number(target.dataset.event);
      render();
      const marker = content.querySelector(".evidence-marker");
      if (marker instanceof HTMLElement) openNote(marker);
      return;
    }
    if (target.dataset.jsonFold !== undefined) {
      const expanded = new Set(state.expanded[String(state.selected)] ?? [""]);
      if (expanded.has(target.dataset.jsonFold)) expanded.delete(target.dataset.jsonFold);
      else expanded.add(target.dataset.jsonFold);
      state.expanded[String(state.selected)] = [...expanded];
      renderPayload();
      return;
    }
    if (target.id === "json-more") {
      state.jsonLimit += 500;
      renderPayload();
      return;
    }
    if (target.id === "evidence-locate") {
      state.selected = focusEvent;
      render();
      locate();
      return;
    }
    if (target.dataset.event !== undefined) {
      state.selected = Number(target.dataset.event);
      render();
      /** @type {HTMLElement|null} */ (
        dialog.querySelector(`button[data-event="${state.selected}"]`)
      )?.focus({ preventScroll: true });
    }
    if (target.id === "event-context" || target.id === "event-all") {
      state.all = target.id === "event-all";
      state.query = "";
      search.value = "";
      visibleLimit = 100;
      render();
    }
    if (target.id === "payload-parsed" || target.id === "payload-raw") {
      state.raw = target.id === "payload-raw";
      renderPayload();
    }
    if (target.id === "events-more") {
      visibleLimit += 100;
      render();
    }
  });
  dialog.addEventListener("close", () => {
    closeNote();
    order++;
    request?.abort();
    state.scroll = content.scrollTop;
    state.left = content.scrollLeft;
    state.eventScroll = element("event-rows").closest(".event-table")?.scrollTop ?? 0;
    state.dialogScroll = dialog.scrollTop;
    state.limit = visibleLimit;
    saved.delete(key);
    saved.set(key, { ...state });
    if (saved.size > 8) saved.delete(saved.keys().next().value ?? "");
    if (opener?.isConnected) opener.focus({ preventScroll: true });
    frames = [];
  });
  notes.addEventListener("change", () => {
    state.notes = notes.checked;
    renderPayload();
  });
  panel.addEventListener("toggle", (event) => {
    content
      .querySelector(".evidence-marker")
      ?.setAttribute("aria-expanded", String(event.newState === "open"));
  });
  dialog.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && panel.matches(":popover-open")) {
      event.preventDefault();
      event.stopPropagation();
      closeNote(true);
    }
  });
  window.addEventListener(
    "scroll",
    (event) => {
      if (!(event.target instanceof Node) || !panel.contains(event.target)) closeNote();
    },
    true,
  );
  window.addEventListener("resize", () => closeNote());
  window.addEventListener("readiness:presentation", () => {
    if (dialog.open) render();
  });
}
