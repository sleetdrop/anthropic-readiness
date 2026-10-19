import { object, objects, strings, resolveEndpoint, resolvePreviewState } from "./forms.js";
import { parseExecution, reduceSnapshot } from "./progress.js";
import { mountReport, setupDrawer } from "./report.js";
/** @typedef {import("./forms.js").JsonObject} JsonObject */
/** @typedef {import("./progress.js").ProgressState} ProgressState */
const TERMINAL = new Set(["completed", "cancelled", "interrupted", "error"]);
const LABELS = {
  queued: "排队中",
  running: "执行中",
  cancelling: "正在取消",
  completed: "执行完成",
  cancelled: "已取消",
  interrupted: "已中断",
  error: "执行错误",
  pending: "待评估",
  PASS: "通过",
  FAIL: "未通过",
  INDETERMINATE: "证据不足",
  BLOCKED: "环境阻塞",
  SKIP: "跳过",
};
let csrf = "";

/** @param {string} key @param {Record<string,string|number>} [params] @returns {string} */
export function message(key, params = {}) {
  const bootstrap = object(JSON.parse(document.getElementById("bootstrap")?.textContent ?? "{}"));
  const catalog = object(object(bootstrap.catalogs)[document.documentElement.lang]);
  if (typeof catalog[key] !== "string") throw new Error("missing_message:" + key);
  return String(catalog[key]).replace(/\{([a-z_]+)\}/gu, (_, name) => String(params[name] ?? ""));
}
/** @param {HTMLElement} target @param {string} key @param {Record<string,string|number>} [params] */
function setMessage(target, key, params = {}) {
  target.dataset.i18n = key;
  target.dataset.i18nParams = JSON.stringify(params);
  target.textContent = message(key, params);
}
/** @param {string} tag @param {string} key @param {Record<string,string|number>} [params] */
function localized(tag, key, params = {}) {
  const target = document.createElement(tag);
  setMessage(target, key, params);
  return target;
}
/** @param {string} id @returns {HTMLElement} */
function element(id) {
  const found = document.getElementById(id);
  if (!(found instanceof HTMLElement)) throw new Error("invalid_page");
  return found;
}
/** @param {string} id @returns {HTMLInputElement} */
function input(id) {
  const found = element(id);
  if (!(found instanceof HTMLInputElement)) throw new Error("invalid_page");
  return found;
}
/** @param {string} id @returns {HTMLSelectElement} */
function select(id) {
  const found = element(id);
  if (!(found instanceof HTMLSelectElement)) throw new Error("invalid_page");
  return found;
}
/** @param {string} id @returns {HTMLButtonElement} */
function button(id) {
  const found = element(id);
  if (!(found instanceof HTMLButtonElement)) throw new Error("invalid_page");
  return found;
}
/** @param {string} state @returns {string} */
function label(state) {
  return /** @type {{[key:string]:string}} */ (LABELS)[state] ?? state;
}
/** @param {string} tag @param {string} value @returns {HTMLElement} */
function node(tag, value) {
  const created = document.createElement(tag);
  created.textContent = value;
  return created;
}
/** @param {unknown} error */
export function showError(error) {
  const output = element("app-message");
  const code = error instanceof Error ? error.message : message("error.operation");
  output.textContent =
    {
      session_required: message("error.session"),
      session_recovery_failed: message("error.session_failed"),
      session_restored_not_resent: message("error.session_restored"),
      invalid_url: message("error.invalid_url"),
      ambiguous_base_url: message("error.ambiguous_url"),
      invalid_document: message("error.invalid_document"),
    }[/** @type {"invalid_url"} */ (code)] ?? code;
  output.hidden = false;
}
async function session() {
  const response = await fetch("/api/v1/session", {
    credentials: "same-origin",
    cache: "no-store",
  });
  const value = object(await response.json());
  if (!response.ok || typeof value.csrf_token !== "string") throw new Error("session_required");
  csrf = value.csrf_token;
}

/** @param {string} path @param {{method?:string,body?:JsonObject}} [options] @param {boolean} [recovered] @returns {Promise<JsonObject>} */
export async function api(path, options = {}, recovered = false) {
  const method = options.method ?? "GET";
  const response = await fetch(path, {
    method,
    credentials: "same-origin",
    cache: "no-store",
    headers: options.body ? { "Content-Type": "application/json", "X-CSRF-Token": csrf } : {},
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const value = object(await response.json());
  if (!response.ok) {
    const failure = object(value.error);
    if (["session_required", "csrf_invalid"].includes(String(failure.code))) {
      if (recovered) throw new Error("session_recovery_failed");
      await session();
      if (method === "GET") return api(path, options, true);
      throw new Error("session_restored_not_resent");
    }
    throw new Error(String(failure.message ?? message("error.operation")));
  }
  return value;
}

/** @param {string} path @param {string} filename */
export async function download(path, filename) {
  let response = await fetch(path, { credentials: "same-origin", cache: "no-store" });
  if (response.status === 401) {
    await session();
    response = await fetch(path, { credentials: "same-origin", cache: "no-store" });
  }
  if (!response.ok) {
    const failure = object(object(await response.json()).error);
    throw new Error(String(failure.message ?? message("error.download")));
  }
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** @param {HTMLElement} root @param {string} name @returns {string[]} */
function checked(root, name) {
  return Array.from(root.querySelectorAll(`input[name="${name}"]:checked`))
    .filter((value) => value instanceof HTMLInputElement)
    .map((value) => /** @type {HTMLInputElement} */ (value).value);
}

/** @param {JsonObject} bootstrap */
function configure(bootstrap) {
  const candidate = element("assessment-form");
  if (!(candidate instanceof HTMLFormElement)) throw new Error("invalid_page");
  const form = candidate;
  const catalog = object(bootstrap.catalog);
  const contracts = objects(catalog.contracts);
  const base = object(bootstrap.target);
  /** @type {import("./forms.js").PreviewState} */
  let state = { target: structuredClone(base), previewId: null };
  let baseTarget = structuredClone(base);
  let operation = "";
  let previewing = false;
  let starting = false;
  let reviewedProfiles = "";
  let presets = objects(bootstrap.presets);
  /** @type {string|null} */
  let selectedPreset = null;

  /** @returns {JsonObject} */
  function target() {
    const contract = contracts[Number(select("contract").value)];
    if (!contract) throw new Error(message("form.select_contract"));
    const credentialSource = select("credential-source").value;
    /** @type {JsonObject} */
    const limits = {};
    for (const field of form.querySelectorAll("[data-limit]")) {
      if (!(field instanceof HTMLInputElement)) continue;
      const value = Number(field.value);
      const name = field.dataset.limit ?? "";
      if (
        !Number.isFinite(value) ||
        value <= 0 ||
        (!name.endsWith("_s") && !Number.isInteger(value))
      )
        throw new Error(message("form.positive_limits"));
      limits[name] = value;
    }
    return {
      ...baseTarget,
      name: input("target-name").value,
      model: input("model").value,
      messages_url: resolveEndpoint(input("endpoint").value, select("endpoint-mode").value),
      api_version: contract.api_version,
      beta_headers: contract.beta_headers,
      protocol_contract: { id: contract.id, revision: contract.revision },
      auth:
        select("auth-mode").value === "api_key"
          ? {
              mode: "api_key",
              credential_env:
                credentialSource === "browser" ? "BROWSER_AUTH_TOKEN" : credentialSource,
            }
          : { mode: "none" },
      capabilities: {
        ...object(baseTarget.capabilities),
        streaming: input("supports-streaming").checked,
        tools: input("supports-tools").checked,
      },
      response_model_policy: select("model-policy").value,
      response_model_aliases: input("aliases")
        .value.split(",")
        .map((value) => value.trim())
        .filter(Boolean),
      limits,
    };
  }
  function authVisibility() {
    const enabled = select("auth-mode").value === "api_key";
    element("credential-source-field").hidden = !enabled;
    element("credential-field").hidden =
      !enabled || select("credential-source").value !== "browser";
    if (!enabled) input("credential").value = "";
  }
  function invalidate() {
    try {
      const current = target();
      state = resolvePreviewState(state, current);
      element("effective-url").textContent = String(current.messages_url);
      if (JSON.stringify(checked(form, "profile")) !== reviewedProfiles) state.previewId = null;
    } catch {
      state.previewId = null;
      element("effective-url").textContent = "输入有效地址后显示";
    }
    if (!state.previewId) {
      button("start-button").disabled = true;
      element("preview-state").textContent = "配置或范围已变化，请重新预览。";
    }
    authVisibility();
  }
  /** @param {JsonObject} value */
  function fill(value) {
    baseTarget = structuredClone(value);
    input("target-name").value = String(value.name);
    input("model").value = String(value.model);
    input("endpoint").value = String(value.messages_url);
    select("endpoint-mode").value = "messages";
    select("model-policy").value = String(value.response_model_policy);
    input("aliases").value = strings(value.response_model_aliases).join(", ");
    const auth = object(value.auth);
    select("auth-mode").value = String(auth.mode);
    const reference = String(auth.credential_env ?? "browser");
    select("credential-source").value = strings(catalog.credential_refs).includes(reference)
      ? reference
      : "browser";
    const capabilities = object(value.capabilities);
    input("supports-streaming").checked = capabilities.streaming === true;
    input("supports-tools").checked = capabilities.tools === true;
    const contract = object(value.protocol_contract);
    const index = contracts.findIndex(
      (item) => item.id === contract.id && item.revision === contract.revision,
    );
    select("contract").value = String(Math.max(index, 0));
    for (const field of form.querySelectorAll("[data-limit]"))
      if (field instanceof HTMLInputElement)
        field.value = String(object(value.limits)[field.dataset.limit ?? ""]);
    input("credential").value = "";
    state.previewId = null;
    invalidate();
  }
  function presetOptions() {
    const picker = select("preset");
    const option = new Option(message("form.new_config"), "");
    option.dataset.i18n = "form.new_config";
    picker.replaceChildren(option);
    for (const preset of presets) {
      const value = object(preset.target);
      picker.add(new Option(`${value.name} · ${value.model}`, String(preset.id)));
    }
    picker.value = selectedPreset ?? "";
    button("update-preset").hidden = !selectedPreset;
  }
  fill(base);
  presetOptions();
  form.addEventListener("input", (event) => {
    if (event.target !== input("credential")) invalidate();
  });
  form.addEventListener("change", invalidate);
  select("preset").addEventListener("change", () => {
    selectedPreset = select("preset").value || null;
    const saved = presets.find((item) => item.id === selectedPreset);
    if (saved) fill(object(saved.target));
    button("update-preset").hidden = !selectedPreset;
  });
  /** @param {boolean} update */
  async function save(update) {
    if (!form.reportValidity()) return;
    const saved = await api(
      update && selectedPreset ? "/api/v1/presets/" + selectedPreset : "/api/v1/presets",
      { method: update ? "PUT" : "POST", body: { target: target() } },
    );
    selectedPreset = String(saved.id);
    presets = objects((await api("/api/v1/presets")).items);
    presetOptions();
    setMessage(element("app-message"), "form.preset_saved");
    element("app-message").hidden = false;
  }
  button("save-preset").addEventListener("click", () => {
    void save(false).catch(showError);
  });
  button("update-preset").addEventListener("click", () => {
    void save(true).catch(showError);
  });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (previewing || !form.reportValidity()) return;
    previewing = true;
    button("preview-button").disabled = true;
    void (async () => {
      const value = target();
      const profiles = checked(form, "profile");
      if (!profiles.length) throw new Error(message("form.select_profile"));
      const retest = typeof bootstrap.baseline_id === "string" && bootstrap.baseline_id;
      const prepared = await api(retest ? "/api/v1/diagnostics/retests/preview" : "/api/v1/plans", {
        method: "POST",
        body: retest ? { baseline_id: retest, target: value } : { target: value, profiles },
      });
      const frozen = retest ? object(prepared.plan) : prepared;
      const current = target();
      if (
        JSON.stringify(
          resolvePreviewState({ target: value, previewId: "pending" }, current).previewId,
        ) !== '"pending"' ||
        JSON.stringify(checked(form, "profile")) !== JSON.stringify(profiles)
      ) {
        invalidate();
        throw new Error(message("preview.changed"));
      }
      state = { target: object(frozen.target), previewId: String(frozen.id) };
      operation = crypto.randomUUID();
      reviewedProfiles = JSON.stringify(profiles);
      const plan = object(frozen.plan);
      const resolved = object(frozen.target);
      const limits = object(plan.limits);
      const content = element("plan-preview");
      content.replaceChildren(localized("h3", "preview.frozen"));
      const facts = document.createElement("dl");
      facts.className = "preview-facts";
      for (const [key, value] of [
        ["preview.address", resolved.messages_url],
        ["preview.model", resolved.model],
        [
          "preview.api",
          `${resolved.api_version} / ${strings(resolved.beta_headers).join(", ") || message("common.none")}`,
        ],
        [
          "preview.requests",
          message("preview.request_limits", {
            planned: String(plan.planned_requests),
            limit: String(limits.max_requests),
          }),
        ],
        [
          "preview.time",
          message("preview.time_limits", {
            run: String(limits.run_timeout_s),
            attempt: String(limits.attempt_timeout_s),
          }),
        ],
        ["preview.policy", resolved.response_model_policy],
        [
          "preview.aliases",
          strings(resolved.response_model_aliases).join(", ") || message("common.none"),
        ],
        ["preview.method", message("preview.single_attempt")],
      ]) {
        const detail = node("dd", String(value));
        if (key === "preview.requests")
          setMessage(detail, "preview.request_limits", {
            planned: String(plan.planned_requests),
            limit: String(limits.max_requests),
          });
        if (key === "preview.time")
          setMessage(detail, "preview.time_limits", {
            run: String(limits.run_timeout_s),
            attempt: String(limits.attempt_timeout_s),
          });
        if (key === "preview.method") setMessage(detail, "preview.single_attempt");
        if (key === "preview.aliases" && !strings(resolved.response_model_aliases).length)
          setMessage(detail, "common.none");
        facts.append(localized("dt", String(key)), detail);
      }
      content.append(facts);
      const list = document.createElement("ol");
      list.className = "preview-list";
      for (const item of objects(plan.cases))
        list.append(
          localized("li", item.required ? "preview.case_required" : "preview.case_optional", {
            id: String(item.id),
            version: String(item.version),
          }),
        );
      content.append(list);
      setMessage(element("preview-state"), "preview.expiry", {
        time: new Date(String(frozen.expires_at)).toLocaleTimeString(),
        revision: String(object(resolved.protocol_contract).revision),
      });
      button("start-button").disabled = false;
    })()
      .catch(showError)
      .finally(() => {
        previewing = false;
        button("preview-button").disabled = false;
      });
  });
  button("start-button").addEventListener("click", () => {
    if (starting || !state.previewId || button("start-button").disabled) return;
    const planId = state.previewId;
    starting = true;
    button("start-button").disabled = true;
    void (async () => {
      /** @type {JsonObject} */
      const body = { plan_id: planId, live_consent: true, idempotency_key: operation };
      if (select("auth-mode").value === "api_key") {
        const source = select("credential-source").value;
        if (source !== "browser") body.credential_ref = source;
        else {
          const credential = input("credential").value;
          if (!credential.trim()) throw new Error(message("form.need_credential"));
          body.credential = credential;
        }
      }
      const job = await api("/api/v1/runs", { method: "POST", body });
      input("credential").value = "";
      location.assign("/runs/" + String(job.id));
    })()
      .catch(showError)
      .finally(() => {
        starting = false;
        button("start-button").disabled = !state.previewId;
      });
  });
}

/** @param {JsonObject} bootstrap */
function runPage(bootstrap) {
  let record = object(bootstrap.run);
  const runId = String(object(record.job).id);
  const frozen = object(record.plan);
  const plan = object(frozen.plan);
  const limits = object(plan.limits);
  /** @type {ProgressState} */
  let observed = { execution: parseExecution(record.execution), needsSnapshot: false };
  let jobState = String(object(record.job).state);
  let terminalSeen = TERMINAL.has(jobState);
  /** @type {EventSource|null} */ let stream = null;
  /** @type {number|undefined} */ let retryTimer;
  let closed = false;
  let reportBusy = false;
  let reportPending = false;
  const panel = element("report-panel");
  setupDrawer(panel);

  function render() {
    if (!terminalSeen && TERMINAL.has(jobState)) {
      const executionPanel = document.getElementById("execution-panel");
      if (executionPanel instanceof HTMLDetailsElement) executionPanel.open = false;
      terminalSeen = true;
    }
    const execution = observed.execution;
    element("job-state").textContent = label(jobState);
    const complete =
      execution?.case_states.filter((item) => !["pending", "running"].includes(item.state))
        .length ?? 0;
    element("case-progress").textContent = `${complete} / ${objects(plan.cases).length}`;
    element("request-progress").textContent =
      `${execution?.actual_requests ?? 0} / ${limits.max_requests}`;
    element("elapsed-progress").textContent =
      `${((execution?.elapsed_ms ?? 0) / 1000).toFixed(1)} / ${limits.run_timeout_s} s`;
    if (execution) {
      element("last-activity").textContent = execution.updated_at;
      for (const item of execution.case_states) {
        const row = document.querySelector(`[data-progress-case="${CSS.escape(item.case_id)}"]`);
        const cell = row?.querySelector("[data-case-state]");
        if (cell instanceof HTMLElement) {
          cell.textContent =
            TERMINAL.has(jobState) && ["pending", "running"].includes(item.state)
              ? `任务已停止；最后记录 ${label(item.state)}，未形成最终判定 · ${item.state}`
              : `${label(item.state)} · ${item.state}`;
          cell.className = "status " + item.state;
        }
      }
    }
    button("cancel-run").disabled = TERMINAL.has(jobState) || jobState === "cancelling";
    button("preview-export").disabled = !TERMINAL.has(jobState);
  }
  async function refreshReport() {
    if (reportBusy) {
      reportPending = true;
      return;
    }
    reportBusy = true;
    try {
      const response = await fetch(`/runs/${runId}?fragment=report`, {
        credentials: "same-origin",
        cache: "no-store",
      });
      if (!response.ok) throw new Error("报告片段暂不可用；任务状态保留，可稍后刷新查看。 ");
      const markup = await response.text();
      if (markup.trim()) mountReport(panel, markup);
    } finally {
      reportBusy = false;
      if (reportPending) {
        reportPending = false;
        void refreshReport().catch(showError);
      }
    }
  }
  async function refreshSnapshot() {
    record = await api("/api/v1/runs/" + runId);
    const incoming = String(object(record.job).state);
    if (!TERMINAL.has(jobState) || TERMINAL.has(incoming)) jobState = incoming;
    observed = reduceSnapshot(observed, { type: "snapshot", value: record.execution });
    render();
  }
  function connect() {
    if (closed || TERMINAL.has(jobState)) {
      element("connection-state").textContent = "本机记录已结束";
      return;
    }
    stream?.close();
    stream = new EventSource(
      `/api/v1/runs/${runId}/events?after=${observed.execution?.sequence ?? 0}`,
    );
    stream.onopen = () => {
      element("connection-state").textContent = "已连接 · 只读观测";
    };
    for (const type of ["snapshot", "reset", "progress"])
      stream.addEventListener(type, (event) => {
        void (async () => {
          const value = object(JSON.parse(/** @type {MessageEvent<string>} */ (event).data));
          if (type === "snapshot" || type === "reset") {
            observed = reduceSnapshot(observed, { type, value: value.execution });
            jobState = String(object(value.job).state);
          } else {
            observed = reduceSnapshot(observed, { type, value });
            if (value.kind === "job_transition" && observed.execution)
              jobState = observed.execution.state;
            if (value.kind === "transport_phase") {
              const payload = object(value.payload);
              const phases = {
                awaiting_headers: "等待响应头",
                headers_received: "已收到响应头",
                receiving: "接收数据（不等同于首 token）",
                validating: "验证断言",
                saving: "写入证据",
              };
              element("active-phase").textContent =
                /** @type {{[key:string]:string}} */ (phases)[String(payload.phase)] ??
                String(payload.phase);
            }
            if (value.kind === "case_committed" || value.kind === "result_committed")
              void refreshReport().catch(showError);
          }
          if (observed.needsSnapshot) {
            stream?.close();
            await refreshSnapshot();
            connect();
          }
          render();
          if (TERMINAL.has(jobState)) {
            stream?.close();
            element("connection-state").textContent = "本机记录已结束";
            await refreshSnapshot();
            await refreshReport();
          }
        })().catch(showError);
      });
    stream.onerror = () => {
      stream?.close();
      element("connection-state").textContent = "连接中断，任务继续；正在恢复观测";
      void refreshSnapshot()
        .then(() => {
          if (TERMINAL.has(jobState)) {
            element("connection-state").textContent = "本机记录已结束";
            return refreshReport();
          }
          retryTimer = window.setTimeout(connect, 1500);
        })
        .catch((error) => {
          showError(error);
          if (!closed) retryTimer = window.setTimeout(connect, 3000);
        });
    };
  }
  button("cancel-run").addEventListener("click", () => {
    button("cancel-run").disabled = true;
    void api(`/api/v1/runs/${runId}/cancel`, { method: "POST", body: {} })
      .then(async () => {
        await refreshSnapshot();
        if (TERMINAL.has(jobState)) await refreshReport();
      })
      .catch(showError);
  });
  window.addEventListener("pagehide", () => {
    closed = true;
    stream?.close();
    window.clearTimeout(retryTimer);
  });
  window.addEventListener("pageshow", (event) => {
    if (!event.persisted) return;
    closed = false;
    void refreshSnapshot().then(connect).catch(showError);
  });
  render();
  connect();
  setupExports(runId, () => TERMINAL.has(jobState));
}

/** @param {string} runId @param {()=>boolean} terminal */
export function setupExports(runId, terminal) {
  const form = element("export-form");
  let reviewed = "";
  /** @returns {JsonObject} */
  const policy = () => ({
    formats: checked(form, "format"),
    include_evidence: input("include-evidence").checked,
  });
  form.addEventListener("change", () => {
    reviewed = "";
    button("create-export").disabled = true;
  });
  button("preview-export").addEventListener("click", () => {
    if (!terminal()) return;
    const chosen = policy();
    if (!strings(chosen.formats).length) {
      showError(new Error(message("export.choose_format")));
      return;
    }
    void api(`/api/v1/runs/${runId}/exports/preview`, { method: "POST", body: chosen })
      .then((value) => {
        if (JSON.stringify(policy()) !== JSON.stringify(chosen)) return;
        const content = element("export-preview");
        content.replaceChildren(
          node("p", value.partial ? message("export.partial") : message("export.freeze")),
        );
        content.append(
          node(
            "p",
            chosen.include_evidence
              ? message("export.with_evidence")
              : message("export.without_evidence"),
          ),
        );
        const list = document.createElement("ul");
        for (const name of strings(value.files)) list.append(node("li", name));
        content.append(
          list,
          node("p", message("export.omissions", { items: strings(value.omissions).join(", ") })),
        );
        reviewed = JSON.stringify(chosen);
        button("create-export").disabled = false;
      })
      .catch(showError);
  });
  button("create-export").addEventListener("click", () => {
    const chosen = policy();
    if (!terminal() || reviewed !== JSON.stringify(chosen)) return;
    button("create-export").disabled = true;
    void api(`/api/v1/runs/${runId}/exports`, { method: "POST", body: chosen })
      .then((value) => {
        const id = String(value.export_id);
        const links = element("export-downloads");
        const options = [
          {
            format: "zip",
            title: message("export.zip_download"),
            filename: "anthropic-readiness.zip",
          },
          ...strings(chosen.formats).map((format) => ({
            format,
            title: message("export.file_download", { format: format.toUpperCase() }),
            filename:
              format === "html"
                ? "report.html"
                : format === "markdown"
                  ? "report.md"
                  : "report-view.json",
          })),
        ];
        for (const option of options) {
          const link = document.createElement("a");
          link.className = "button secondary";
          link.href = `/api/v1/runs/${runId}/exports/${id}?format=${option.format}`;
          link.textContent = option.title;
          link.addEventListener("click", (event) => {
            event.preventDefault();
            void download(link.getAttribute("href") ?? "", option.filename).catch(showError);
          });
          links.append(link);
        }
        setMessage(element("app-message"), "export.created");
        element("app-message").hidden = false;
      })
      .catch(showError)
      .finally(() => {
        button("create-export").disabled = reviewed !== JSON.stringify(policy());
      });
  });
}

async function bootstrap() {
  const data = object(JSON.parse(element("bootstrap").textContent ?? "{}"));
  await session();
  if (data.page === "configure") configure(data);
  if (data.page === "run") runPage(data);
}
export const ready =
  typeof document !== "undefined" ? bootstrap().catch(showError) : Promise.resolve();
export function csrfToken() {
  return csrf;
}
