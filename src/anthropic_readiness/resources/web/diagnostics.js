import { api, ready, csrfToken, showError, setupExports } from "./app.js";
import { object, strings } from "./forms.js";
import { mountWorkbench, patchElement } from "./workbench.js";
import { acceptUIRevision, mountUIUpdates } from "./ui-update.js";
import { mountEvidence } from "./evidence-view.js";
/** @typedef {import("./contracts.js").JsonObject} JsonObject */

/** Read only the display budget; original bytes remain available by download.
 * @param {Response} response @param {number} [limit]
 * @returns {Promise<{text:string,truncated:boolean}>}
 */
export async function readEvidence(response, limit = 262144) {
  if (!Number.isSafeInteger(limit) || limit <= 0) throw new Error("invalid_display_limit");
  if (!response.body) return { text: "", truncated: false };
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let remaining = limit;
  let text = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) return { text: text + decoder.decode(), truncated: false };
      if (value.byteLength > remaining) {
        text += decoder.decode(value.subarray(0, remaining), { stream: true });
        await reader.cancel();
        return { text, truncated: true };
      }
      text += decoder.decode(value, { stream: true });
      remaining -= value.byteLength;
    }
  } finally {
    reader.releaseLock();
  }
}

/** @param {string} id @returns {HTMLElement} */
function element(id) {
  const value = document.getElementById(id);
  if (!value) throw new Error("invalid_page");
  return value;
}
/** @param {string} id @returns {HTMLSelectElement} */
function select(id) {
  return /** @type {HTMLSelectElement} */ (element(id));
}
/** @param {string} id @returns {HTMLButtonElement} */
function button(id) {
  return /** @type {HTMLButtonElement} */ (element(id));
}

/** @param {string} id @param {()=>void} listener */
function buttonIfPresent(id, listener) {
  document.getElementById(id)?.addEventListener("click", listener);
}

async function mount() {
  await ready;
  mountUIUpdates();
  const bootstrap = object(JSON.parse(element("bootstrap").textContent ?? "{}"));
  const catalogs = object(bootstrap.catalogs);
  let presentation = object(bootstrap.presentation);
  let desiredPresentation = {
    locale: String(presentation.locale),
    theme: String(presentation.theme),
  };
  /** @param {string} key @param {Record<string,string|number>} [params] */
  function text(key, params = {}) {
    const messages = object(catalogs[String(presentation.locale)]);
    const resolved = key in messages ? key : key + (Number(params.count) === 1 ? ".one" : ".other");
    if (typeof messages[resolved] !== "string") throw new Error("missing_message:" + key);
    return String(messages[resolved]).replace(/\{([a-z_]+)\}/gu, (_, name) =>
      String(params[name] ?? ""),
    );
  }
  function labels() {
    for (const node of document.querySelectorAll("[data-i18n]")) {
      if (!(node instanceof HTMLElement)) continue;
      const params = node.dataset.i18nParams ? JSON.parse(node.dataset.i18nParams) : {};
      node.textContent = text(node.dataset.i18n ?? "", params);
    }
    for (const attr of ["placeholder", "aria-label", "title"])
      for (const node of document.querySelectorAll(`[data-i18n-${attr}]`))
        node.setAttribute(attr, text(node.getAttribute(`data-i18n-${attr}`) ?? ""));
  }
  let changeOrder = 0;
  // Serialize cookie writes so a slower response cannot restore an older choice.
  let saving = Promise.resolve();
  function syncAppearance() {
    const language = document.getElementById("language-toggle");
    const theme = document.getElementById("theme-toggle");
    if (language) {
      language.textContent = presentation.locale === "en" ? "中" : "EN";
      language.title = text(
        presentation.locale === "en" ? "console.switch_zh" : "console.switch_en",
      );
      language.setAttribute("aria-label", language.textContent + " · " + language.title);
    }
    if (theme) {
      const dark =
        presentation.theme === "dark" ||
        (presentation.theme === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
      theme.title = text(dark ? "console.switch_light" : "console.switch_dark");
      theme.setAttribute("aria-label", theme.title);
    }
  }
  syncAppearance();
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", syncAppearance);
  /** @param {{locale:string,theme:string}} requested */
  function savePresentation(requested) {
    desiredPresentation = requested;
    const ticket = ++changeOrder;
    saving = saving
      .then(async () => {
        const saved = await api("/api/v1/preferences", { method: "POST", body: requested });
        if (ticket !== changeOrder) return;
        presentation = saved;
        document.documentElement.lang = String(saved.locale);
        document.documentElement.dataset.theme = String(saved.theme);
        labels();
        syncAppearance();
        const exportForm = document.getElementById("export-form");
        exportForm?.dispatchEvent(new Event("change"));
        if (bootstrap.page === "workbench")
          window.dispatchEvent(new Event("readiness:presentation"));
        else {
          const response = await fetch(location.href, {
            credentials: "same-origin",
            cache: "no-store",
          });
          if (!response.ok) throw new Error("invalid_document");
          const page = new DOMParser().parseFromString(await response.text(), "text/html");
          if (
            !acceptUIRevision(
              page.querySelector('meta[name="readiness-ui-revision"]')?.getAttribute("content") ??
                null,
            )
          )
            return;
          const incoming = page.getElementById("main");
          if (ticket !== changeOrder) return;
          if (incoming) patchElement(element("main"), incoming, true);
          document.title = page.title;
          labels();
        }
      })
      .catch((error) => {
        if (ticket === changeOrder)
          desiredPresentation = {
            locale: String(presentation.locale),
            theme: String(presentation.theme),
          };
        showError(error);
      });
  }
  for (const id of ["locale-choice", "theme-choice"]) {
    document.getElementById(id)?.addEventListener("change", () =>
      savePresentation({
        locale: select("locale-choice").value,
        theme: select("theme-choice").value,
      }),
    );
  }
  buttonIfPresent("language-toggle", () =>
    savePresentation({
      locale: desiredPresentation.locale === "en" ? "zh-CN" : "en",
      theme: desiredPresentation.theme,
    }),
  );
  buttonIfPresent("theme-toggle", () => {
    const dark =
      desiredPresentation.theme === "dark" ||
      (desiredPresentation.theme === "system" &&
        matchMedia("(prefers-color-scheme: dark)").matches);
    savePresentation({ locale: desiredPresentation.locale, theme: dark ? "light" : "dark" });
  });

  if (bootstrap.page === "workbench") {
    mountWorkbench(bootstrap, { api, error: showError, text });
    const exportDialog = document.getElementById("export-dialog");
    if (exportDialog instanceof HTMLDialogElement) {
      setupExports(
        String(bootstrap.run_id),
        () => document.getElementById("workbench")?.querySelector("#open-export") !== null,
      );
      document.addEventListener("click", (event) => {
        if (!(event.target instanceof Element)) return;
        if (event.target.closest("#open-export")) exportDialog.showModal();
        if (event.target.closest("#close-export")) exportDialog.close();
      });
    }
    mountEvidence({ read: readEvidence, text, api });
  }

  if (bootstrap.page === "import") {
    /** @type {string|null} */ let previewId = null;
    let inFlight = false;
    const file = /** @type {HTMLInputElement} */ (element("import-file"));
    file.addEventListener("change", () => {
      previewId = null;
      button("commit-import").disabled = true;
      element("import-preview").textContent = "";
    });
    element("import-form").addEventListener("submit", (event) => {
      event.preventDefault();
      if (inFlight || !file.files?.[0]) return;
      const selected = file.files[0];
      if (selected.size > 256 * 1024 * 1024) {
        showError(new Error(text("import.too_large")));
        return;
      }
      inFlight = true;
      previewId = null;
      button("preview-import").disabled = true;
      button("commit-import").disabled = true;
      element("import-preview").textContent = text("import.inspecting");
      void fetch("/api/v1/diagnostics/imports/preview", {
        method: "POST",
        credentials: "same-origin",
        cache: "no-store",
        headers: { "Content-Type": "application/zip", "X-CSRF-Token": csrfToken() },
        body: selected,
      })
        .then(async (response) => {
          const value = object(await response.json());
          if (!response.ok) throw new Error(String(object(value.error).message));
          if (file.files?.[0] !== selected) return;
          previewId = String(value.preview_id);
          const eligibility = object(value.eligibility);
          const content = element("import-preview");
          content.replaceChildren();
          for (const line of [
            text(eligibility.retest ? "import.ready" : "import.readonly"),
            ...strings(value.disclosures),
            ...strings(eligibility.reasons),
          ]) {
            const paragraph = document.createElement("p");
            paragraph.textContent = line;
            content.append(paragraph);
          }
          button("commit-import").disabled = false;
        })
        .catch(showError)
        .finally(() => {
          inFlight = false;
          button("preview-import").disabled = false;
        });
    });
    button("commit-import").addEventListener("click", () => {
      if (!previewId || inFlight) return;
      inFlight = true;
      button("commit-import").disabled = true;
      void api("/api/v1/diagnostics/imports/commit", {
        method: "POST",
        body: { preview_id: previewId },
      })
        .then((value) => location.assign("/baselines/" + String(value.id)))
        .catch(showError)
        .finally(() => {
          inFlight = false;
          button("commit-import").disabled = !previewId;
        });
    });
  }
}
if (typeof document !== "undefined") void mount().catch(showError);
