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
function showError(error) {
  const message = element("app-message");
  const code = error instanceof Error ? error.message : "操作未完成";
  message.textContent =
    {
      invalid_url: "请输入不含认证、查询参数或片段的有效 HTTP 地址。",
      ambiguous_base_url: "Base URL 只能是源站或 /v1；其他路径请使用完整 Messages URL。",
      invalid_document: "本机响应格式异常，请刷新页面查看已有记录。",
    }[/** @type {"invalid_url"} */ (code)] ?? code;
  message.hidden = false;
}
/** @param {string} message */
function announce(message) {
  element("app-message").textContent = message;
  element("app-message").hidden = false;
}

async function session() {
  const response = await fetch("/api/v1/session", {
    credentials: "same-origin",
    cache: "no-store",
  });
  const value = object(await response.json());
  if (!response.ok || typeof value.csrf_token !== "string")
    throw new Error("无法恢复本机会话，请刷新页面；已有任务仍保留。 ");
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
      if (recovered)
        throw new Error("本机会话恢复未成功，请检查浏览器是否允许本机 Cookie；已有任务仍保留。 ");
      await session();
      if (method === "GET") return api(path, options, true);
      throw new Error("本机会话已恢复；未自动重发操作。请先查看历史任务，再重新预览或明确重试。 ");
    }
    throw new Error(String(failure.message ?? "本机操作未完成"));
  }
  return value;
}

/** @param {string} path @param {string} filename */
async function download(path, filename) {
  let response = await fetch(path, { credentials: "same-origin", cache: "no-store" });
  if (response.status === 401) {
    await session();
    response = await fetch(path, { credentials: "same-origin", cache: "no-store" });
  }
  if (!response.ok) {
    const failure = object(object(await response.json()).error);
    throw new Error(String(failure.message ?? "下载未完成"));
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
    if (!contract) throw new Error("请选择已安装规则快照。");
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
        throw new Error("预算必须为有限正数；请求、事件和字节上限必须为整数。 ");
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
    picker.replaceChildren(new Option("新配置", ""));
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
    announce("预设已保存；不包含凭据，也不会改变已有任务。 ");
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
      if (!profiles.length) throw new Error("至少选择一个配置组。");
      const frozen = await api("/api/v1/plans", {
        method: "POST",
        body: { target: value, profiles },
      });
      const current = target();
      if (
        JSON.stringify(
          resolvePreviewState({ target: value, previewId: "pending" }, current).previewId,
        ) !== '"pending"' ||
        JSON.stringify(checked(form, "profile")) !== JSON.stringify(profiles)
      ) {
        invalidate();
        throw new Error("预览期间配置已变化，请重新预览。 ");
      }
      state = { target: object(frozen.target), previewId: String(frozen.id) };
      operation = crypto.randomUUID();
      reviewedProfiles = JSON.stringify(profiles);
      const plan = object(frozen.plan);
      const resolved = object(frozen.target);
      const limits = object(plan.limits);
      const content = element("plan-preview");
      content.replaceChildren(node("h3", "已冻结的执行计划"));
      const facts = document.createElement("dl");
      facts.className = "preview-facts";
      for (const [key, value] of [
        ["有效地址", resolved.messages_url],
        ["请求模型", resolved.model],
        [
          "API / beta",
          `${resolved.api_version} / ${strings(resolved.beta_headers).join(", ") || "无"}`,
        ],
        ["计划 / 上限", `${plan.planned_requests} / ${limits.max_requests} 次请求`],
        ["时间上限", `${limits.run_timeout_s} 秒 / 单次 ${limits.attempt_timeout_s} 秒`],
        ["模型策略", resolved.response_model_policy],
        ["允许别名", strings(resolved.response_model_aliases).join(", ") || "无"],
        ["执行方式", "每用例一次；不重试"],
      ]) {
        facts.append(node("dt", String(key)), node("dd", String(value)));
      }
      content.append(facts);
      const list = document.createElement("ol");
      list.className = "preview-list";
      for (const item of objects(plan.cases))
        list.append(
          node("li", `${item.id} · v${item.version} · ${item.required ? "必需" : "诊断"}`),
        );
      content.append(list);
      element("preview-state").textContent =
        `有效至 ${new Date(String(frozen.expires_at)).toLocaleTimeString()}；规则 ${object(resolved.protocol_contract).revision}。`;
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
          if (!credential.trim())
            throw new Error("开始前请输入本次凭据，或选择已允许的服务器变量。 ");
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
function setupExports(runId, terminal) {
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
      showError(new Error("至少选择一种导出格式。 "));
      return;
    }
    void api(`/api/v1/runs/${runId}/exports/preview`, { method: "POST", body: chosen })
      .then((value) => {
        if (JSON.stringify(policy()) !== JSON.stringify(chosen)) return;
        const content = element("export-preview");
        content.replaceChildren(
          node(
            "p",
            value.partial
              ? "部分执行记录；不包含最终 result.json。"
              : "冻结本次结果与所选报告格式。",
          ),
        );
        content.append(
          node(
            "p",
            chosen.include_evidence
              ? "ZIP 包含所列证据；单独 HTML 不内嵌捕获。分享前请检查业务内容。"
              : "未附证据文件；接收者无法独立复核。",
          ),
        );
        const list = document.createElement("ul");
        for (const name of strings(value.files)) list.append(node("li", name));
        content.append(list, node("p", "省略项：" + strings(value.omissions).join(", ")));
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
            title: "下载 ZIP（所选格式与清单）",
            filename: "anthropic-readiness.zip",
          },
          ...strings(chosen.formats).map((format) => ({
            format,
            title: "单独下载 " + format.toUpperCase(),
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
        announce("导出已生成；旧导出继续保留，可重复下载。 ");
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
if (typeof document !== "undefined") void bootstrap().catch(showError);
