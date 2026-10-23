import { object, objects } from "./forms.js";
/** @typedef {import("./contracts.js").ActivityView} ActivityView */
/** @typedef {import("./contracts.js").WorkbenchState} WorkbenchState */
/** @typedef {import("./contracts.js").WorkbenchEvent} WorkbenchEvent */
const TERMINAL = new Set(["completed", "cancelled", "interrupted", "error"]);

/** @param {import("./progress.js").Execution|null} execution @param {number} nowMs @returns {ActivityView} */
export function deriveActivity(execution, nowMs) {
  if (!execution)
    return {
      updatedAt: null,
      ageMs: null,
      clockDifference: false,
      recordedElapsedMs: null,
      phase: null,
      phaseElapsedMs: null,
      caseId: null,
    };
  const difference = nowMs - Date.parse(execution.updated_at);
  const phase = [...objects(execution.spans)]
    .reverse()
    .find((item) => item.phase !== "case" && item.end_ms === null);
  return {
    updatedAt: execution.updated_at,
    ageMs: Number.isFinite(difference) && difference >= 0 ? difference : null,
    clockDifference: Number.isFinite(difference) && difference < 0,
    recordedElapsedMs: execution.elapsed_ms,
    phase: phase ? String(phase.phase) : null,
    phaseElapsedMs: phase ? Math.max(0, execution.elapsed_ms - Number(phase.start_ms)) : null,
    caseId: phase ? String(phase.case_id) : null,
  };
}

/** @param {WorkbenchState} state @param {WorkbenchEvent} event @returns {WorkbenchState} */
export function reduceWorkbench(state, event) {
  if (event.type === "connection") return { ...state, connection: event.value };
  if (event.type === "selection")
    return { ...state, selectedIssue: event.issue, selectedCase: event.caseId };
  if (event.order <= state.readOrder) return state;
  const incoming = object(event.value.facts);
  if (state.snapshot) {
    const previous = object(state.snapshot.facts);
    if (previous.run_id !== incoming.run_id) return state;
    if (
      previous.execution &&
      (!incoming.execution ||
        Number(object(incoming.execution).sequence) < Number(object(previous.execution).sequence))
    )
      return state;
    if (
      state.snapshot.job &&
      event.value.job &&
      TERMINAL.has(String(object(state.snapshot.job).state)) &&
      !TERMINAL.has(String(object(event.value.job).state))
    )
      return state;
  }
  return { ...state, snapshot: event.value, readOrder: event.order };
}

/** Stable identity for server-owned keyed nodes.
 * @param {Node} node @returns {string|null}
 */
function nodeKey(node) {
  if (!(node instanceof Element)) return null;
  if (node.id) return "id:" + node.id;
  for (const name of [
    "data-issue-key",
    "data-case-id",
    "data-check-key",
    "data-group",
    "data-evidence-id",
  ])
    if (node.hasAttribute(name)) return name + ":" + node.getAttribute(name);
  return null;
}
/** Patch escaped server-owned markup while retaining existing controls and inspectors.
 * @param {Element} current @param {Element} incoming @param {boolean} [preserveControls]
 */
export function patchElement(current, incoming, preserveControls = false) {
  const protectedAttributes = new Set();
  if (current instanceof HTMLDetailsElement) protectedAttributes.add("open");
  if (
    preserveControls &&
    current.matches(
      "input,textarea,select,button,output,#plan-preview,#preview-state,#app-message,#import-preview,#commit-import",
    )
  )
    return;
  for (const attr of current.attributes)
    if (!protectedAttributes.has(attr.name) && !incoming.hasAttribute(attr.name))
      current.removeAttribute(attr.name);
  for (const attr of incoming.attributes)
    if (!protectedAttributes.has(attr.name) && current.getAttribute(attr.name) !== attr.value)
      current.setAttribute(attr.name, attr.value);
  if (current instanceof HTMLSelectElement && incoming instanceof HTMLSelectElement) {
    const chosen = current.value;
    for (const source of incoming.options) {
      const existing = Array.from(current.options).find((option) => option.value === source.value);
      if (existing) existing.textContent = source.textContent;
      else current.add(/** @type {HTMLOptionElement} */ (source.cloneNode(true)));
    }
    current.value = chosen;
    return;
  }
  if (current.matches("input,textarea")) return;
  /** @type {Set<Node>} */ const retained = new Set();
  for (const expected of incoming.childNodes) {
    const key = nodeKey(expected);
    let actual = key
      ? Array.from(current.childNodes).find((item) => !retained.has(item) && nodeKey(item) === key)
      : Array.from(current.childNodes).find(
          (item) =>
            !retained.has(item) &&
            !nodeKey(item) &&
            item.nodeType === expected.nodeType &&
            (!(item instanceof Element) ||
              (expected instanceof Element && item.tagName === expected.tagName)),
        );
    const position = current.childNodes[retained.size];
    if (!actual) {
      actual = /** @type {ChildNode} */ (expected.cloneNode(true));
      current.insertBefore(actual, position ?? null);
    } else {
      if (actual !== position) current.insertBefore(actual, position ?? null);
      if (actual instanceof Element && expected instanceof Element)
        patchElement(actual, expected, preserveControls);
      else if (actual.nodeValue !== expected.nodeValue) actual.nodeValue = expected.nodeValue;
    }
    retained.add(actual);
  }
  for (const old of Array.from(current.childNodes)) if (!retained.has(old)) old.remove();
}

/** @typedef {import("./contracts.js").JsonObject} JsonObject */
/** @param {JsonObject} bootstrap @param {{api:(path:string,options?:{method?:string,body?:JsonObject})=>Promise<JsonObject>,error:(value:unknown)=>void,text:(key:string,params?:Record<string,string|number>)=>string}} ports */
export function mountWorkbench(bootstrap, ports) {
  let root = document.getElementById("workbench");
  if (!root) throw new Error("invalid_page");
  const runId = String(bootstrap.run_id);
  const readOnly = bootstrap.read_only === true;
  /** @type {WorkbenchState} */
  let state = {
    snapshot: object(bootstrap.workbench),
    readOrder: 0,
    selectedIssue: new URL(location.href).searchParams.get("issue"),
    selectedCase: new URL(location.href).searchParams.get("case"),
    connection: "loading",
  };
  function pinSelection() {
    if (!root) return;
    const url = new URL(location.href);
    const selected = root.querySelector(
      "[data-issue-key][aria-current], [data-case-id][aria-current]",
    );
    if (selected instanceof HTMLElement)
      url.searchParams.set(
        selected.hasAttribute("data-issue-key") ? "issue" : "case",
        selected.dataset.issueKey ?? selected.dataset.caseId ?? "",
      );
    const observation = root.querySelector("[data-observation-case][aria-current]");
    if (observation instanceof HTMLElement)
      url.searchParams.set("case", observation.dataset.observationCase ?? "");
    if (url.href !== location.href) history.replaceState(history.state, "", url);
    state = reduceWorkbench(state, {
      type: "selection",
      issue: url.searchParams.get("issue"),
      caseId: url.searchParams.get("case"),
    });
  }
  pinSelection();
  // Accepted facts and the last successfully patched document can differ after a failed read.
  let renderedGeneration = state.snapshot?.generation;
  let readOrder = 0;
  let closed = false;
  let busy = false;
  let lastRefresh = 0;
  /** @type {EventSource|null} */ let stream = null;
  /** @type {number|undefined} */ let timer;
  /** @type {number|undefined} */ let retryTimer;
  let navigation = 0;
  /** @type {Map<string, number[]>} */ const positions = new Map();
  let renderedLocation = location.href;
  /** @type {number|undefined} */ let activityTimer;
  const terminal = () =>
    !state.snapshot?.job || TERMINAL.has(String(object(state.snapshot.job).state));
  function renderObservation() {
    const connection = document.getElementById("connection-state");
    if (connection) connection.textContent = ports.text("connection." + state.connection);
    const worker = document.getElementById("worker-state");
    if (worker && state.snapshot) {
      const observation = object(state.snapshot.worker);
      worker.textContent = ports.text("worker." + observation.state);
      worker.setAttribute("data-worker-state", String(observation.state));
      worker.title = String(observation.observed_at ?? "");
    }
    const execution = state.snapshot ? object(state.snapshot.facts).execution : null;
    const activity = deriveActivity(
      execution
        ? /** @type {import("./progress.js").Execution} */ (/** @type {unknown} */ (execution))
        : null,
      Date.now(),
    );
    const last = document.getElementById("last-activity");
    if (last && activity.updatedAt) {
      last.title = activity.updatedAt;
      const age = activity.ageMs === null ? null : Math.floor(activity.ageMs / 1000);
      const [unit, divisor] =
        age === null
          ? ["seconds", 1]
          : age >= 86400
            ? ["days", 86400]
            : age >= 3600
              ? ["hours", 3600]
              : age >= 60
                ? ["minutes", 60]
                : ["seconds", 1];
      last.textContent = activity.clockDifference
        ? ports.text("activity.clock_difference")
        : age === null
          ? "—"
          : ports.text("activity.age_" + unit, { count: Math.floor(age / divisor) });
    }
  }
  /** @param {string} url @param {boolean} [push] @param {boolean} [restoreControls] */
  async function renderPage(url, push = false, restoreControls = false) {
    const ticket = ++navigation;
    const order = ++readOrder;
    positions.set(renderedLocation, [window.scrollX, window.scrollY]);
    if (positions.size > 40) positions.delete(positions.keys().next().value ?? "");
    const response = await fetch(url, { credentials: "same-origin", cache: "no-store" });
    if (!response.ok) throw new Error("workbench_unavailable");
    const page = new DOMParser().parseFromString(await response.text(), "text/html");
    if (ticket !== navigation || closed) return;
    const incoming = page.getElementById("workbench");
    if (!incoming || !root) throw new Error("invalid_document");
    const data = object(JSON.parse(page.getElementById("bootstrap")?.textContent ?? "{}"));
    const accepted = reduceWorkbench(state, {
      type: "snapshot",
      value: object(data.workbench),
      order,
    });
    if (accepted === state) return;
    state = accepted;
    const scrolling =
      push || restoreControls ? (positions.get(url) ?? [0, 0]) : [window.scrollX, window.scrollY];
    if (push) history.pushState({}, "", url);
    patchElement(root, incoming);
    if (push || restoreControls) {
      for (const source of incoming.querySelectorAll("select")) {
        const existing = document.getElementById(source.id);
        if (existing instanceof HTMLSelectElement) existing.value = source.value;
      }
      const search = document.getElementById("issue-search");
      const incomingSearch = incoming.querySelector("#issue-search");
      if (search instanceof HTMLInputElement && incomingSearch instanceof HTMLInputElement)
        search.value = incomingSearch.value;
    }
    document.title = page.title;
    pinSelection();
    renderedLocation = location.href;
    window.scrollTo({ left: scrolling[0], top: scrolling[1], behavior: "instant" });
    renderObservation();
    renderedGeneration = state.snapshot?.generation;
  }
  async function refresh() {
    if (busy || closed || readOnly) return;
    busy = true;
    lastRefresh = Date.now();
    const order = ++readOrder;
    try {
      const baseline = new URL(location.href).searchParams.get("baseline");
      const value = await ports.api(
        `/api/v1/runs/${runId}/workbench` +
          (baseline ? "?baseline=" + encodeURIComponent(baseline) : ""),
      );
      state = reduceWorkbench(state, { type: "snapshot", value, order });
      state = reduceWorkbench(state, {
        type: "connection",
        value: terminal() ? "ended" : "connected",
      });
      if (renderedGeneration !== state.snapshot?.generation) await renderPage(location.href);
      renderObservation();
      if (terminal()) stream?.close();
    } catch {
      state = reduceWorkbench(state, { type: "connection", value: "reconnecting" });
      renderObservation();
    } finally {
      busy = false;
      if (
        !closed &&
        !readOnly &&
        (!terminal() ||
          state.connection === "reconnecting" ||
          renderedGeneration !== state.snapshot?.generation)
      )
        timer = window.setTimeout(() => {
          void refresh();
        }, 5000);
    }
  }
  function connect() {
    stream?.close();
    if (closed || readOnly || terminal()) return;
    stream = new EventSource(
      `/api/v1/runs/${runId}/events?after=${Number(object(state.snapshot?.facts ?? {}).execution && object(object(state.snapshot?.facts ?? {}).execution).sequence) || 0}`,
    );
    stream.onopen = () => {
      state = reduceWorkbench(state, { type: "connection", value: "connected" });
      renderObservation();
    };
    stream.onerror = () => {
      state = reduceWorkbench(state, { type: "connection", value: "reconnecting" });
      renderObservation();
      stream?.close();
      if (!closed) retryTimer = window.setTimeout(connect, 5000);
    };
    // Ordered events signal that persisted facts changed; the bounded local read is authoritative.
    for (const kind of ["snapshot", "reset", "progress"])
      stream.addEventListener(kind, () => {
        if (Date.now() - lastRefresh >= 5000 && !busy) {
          window.clearTimeout(timer);
          void refresh();
        }
      });
  }
  root.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const anchor = target.closest("a");
    if (anchor?.hasAttribute("data-evidence-id") && anchor.dataset.evidenceCase) {
      const url = new URL(location.href);
      if (
        url.searchParams.get("case") !== anchor.dataset.evidenceCase &&
        !event.ctrlKey &&
        !event.metaKey &&
        !event.shiftKey &&
        event.button === 0
      ) {
        url.searchParams.set("case", anchor.dataset.evidenceCase);
        void renderPage(url.href, true).catch(ports.error);
      }
    }
    if (
      anchor &&
      anchor.pathname === location.pathname &&
      !anchor.hasAttribute("data-evidence-id") &&
      !event.ctrlKey &&
      !event.metaKey &&
      !event.shiftKey &&
      event.button === 0
    ) {
      event.preventDefault();
      void renderPage(anchor.href, true).catch(ports.error);
    }
    if (target.closest("#cancel-run")) {
      const button = target.closest("button");
      if (button) button.disabled = true;
      void ports
        .api(`/api/v1/runs/${runId}/cancel`, { method: "POST", body: {} })
        .then(() => renderPage(location.href))
        .catch(ports.error);
    }
  });
  root.addEventListener("submit", (event) => {
    if (!(event.target instanceof HTMLFormElement) || event.target.method !== "get") return;
    event.preventDefault();
    const url = new URL(location.href);
    url.search = new URLSearchParams(
      /** @type {string[][]} */ (
        /** @type {unknown} */ (
          Array.from(new FormData(event.target), ([name, value]) => [name, String(value)])
        )
      ),
    ).toString();
    void renderPage(url.href, true).catch(ports.error);
  });
  window.addEventListener("popstate", () => {
    void renderPage(location.href, false, true).catch(ports.error);
  });
  window.addEventListener("readiness:presentation", () => {
    void renderPage(location.href).catch(ports.error);
  });
  window.addEventListener("pagehide", () => {
    closed = true;
    stream?.close();
    window.clearTimeout(timer);
    window.clearTimeout(retryTimer);
    window.clearInterval(activityTimer);
  });
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) {
      closed = false;
      activityTimer = window.setInterval(renderObservation, 1000);
      void refresh().then(connect);
    }
  });
  activityTimer = window.setInterval(renderObservation, 1000);
  if (readOnly) state = reduceWorkbench(state, { type: "connection", value: "ended" });
  void refresh().then(connect);
  renderObservation();
}
