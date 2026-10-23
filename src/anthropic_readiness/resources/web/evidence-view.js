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
/** @param {JsonValue} value @param {string} pointer */
export function locatePointer(value, pointer) {
  let current = value;
  let existing = "";
  if (pointer && !pointer.startsWith("/")) return { pointer: "", missing: true };
  for (const part of pointer ? pointer.slice(1).split("/") : []) {
    const key = part.replace(/~1/gu, "/").replace(/~0/gu, "~");
    if (current === null || typeof current !== "object" || !Object.hasOwn(current, key))
      return { pointer: existing, missing: true };
    current = /** @type {Record<string,JsonValue>} */ (current)[key] ?? null;
    existing += "/" + part;
  }
  return { pointer: existing, missing: false };
}
/** @param {JsonValue} value @param {string} pointer @returns {JsonValue} */
function pointerValue(value, pointer) {
  let current = value;
  for (const part of pointer ? pointer.slice(1).split("/") : []) {
    if (!current || typeof current !== "object") return null;
    current =
      /** @type {Record<string,JsonValue>} */ (current)[
        part.replace(/~1/gu, "/").replace(/~0/gu, "~")
      ] ?? null;
  }
  return current;
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
  /** @typedef {{selected:number,query:string,all:boolean,raw:boolean,scroll:number,eventScroll:number,dialogScroll:number,limit:number}} ReadingState */
  /** @type {Map<string,ReadingState>} */ const saved = new Map();
  /** @type {ReadingState} */ let state = {
    selected: 0,
    query: "",
    all: false,
    raw: false,
    scroll: 0,
    eventScroll: 0,
    dialogScroll: 0,
    limit: 100,
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
  /** @param {string} id @param {boolean} pressed */
  function pressed(id, pressed) {
    element(id).setAttribute("aria-pressed", String(pressed));
  }
  function renderPayload() {
    const frame = frames.find((item) => item.event === state.selected);
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
    const location = locatePointer(frame.value, frame.event === focusEvent ? pointer : "");
    element("evidence-location").textContent =
      text(location.missing ? "console.missing_parent" : "console.at_pointer", {
        pointer: location.pointer || "$",
      }) + (path.endsWith("events.jsonl") ? ` · #${frame.event}` : "");
    content.textContent = state.raw
      ? frame.raw
      : frame.parsed
        ? JSON.stringify(pointerValue(frame.value, location.pointer), null, 2)
        : text("console.no_parse");
  }
  function render() {
    for (const id of [
      "payload-parsed",
      "payload-raw",
      "event-context",
      "event-all",
      "event-search",
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
    key = [link.dataset.evidenceId, link.dataset.evidenceEvent, pointer].join(":");
    const target = Number(link.dataset.evidenceEvent || 0);
    focusEvent = target;
    state = saved.get(key) ?? {
      selected: target,
      query: "",
      all: false,
      raw: false,
      scroll: 0,
      eventScroll: 0,
      dialogScroll: 0,
      limit: 100,
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
      frames = evidenceFrames(value.text, path.endsWith("events.jsonl") ? "events" : false);
      render();
      content.scrollTop = state.scroll;
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
    order++;
    request?.abort();
    state.scroll = content.scrollTop;
    state.eventScroll = element("event-rows").closest(".event-table")?.scrollTop ?? 0;
    state.dialogScroll = dialog.scrollTop;
    state.limit = visibleLimit;
    saved.delete(key);
    saved.set(key, { ...state });
    if (saved.size > 8) saved.delete(saved.keys().next().value ?? "");
    if (opener?.isConnected) opener.focus({ preventScroll: true });
    frames = [];
  });
  window.addEventListener("readiness:presentation", () => {
    if (dialog.open) render();
  });
}
