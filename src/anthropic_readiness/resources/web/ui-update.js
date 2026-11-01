/** Validate deployment identity without reading endpoint configuration or evidence. */
/** @param {unknown} value */
export function validUIRevision(value) {
  return typeof value === "string" && /^[a-f0-9]{64}$/u.test(value);
}
/** @param {unknown} current @param {unknown} incoming */
export function sameUIRevision(current, incoming) {
  return !validUIRevision(current) || !validUIRevision(incoming) || current === incoming;
}

/** @param {string|null} revision @returns {boolean} */
export function acceptUIRevision(revision) {
  const current = document
    .querySelector('meta[name="readiness-ui-revision"]')
    ?.getAttribute("content");
  if (validUIRevision(current) && validUIRevision(revision) && current === revision) return true;
  window.dispatchEvent(new Event("readiness:update-available"));
  return false;
}

/** Check only while visible. Never reload or discard a form automatically. */
export function mountUIUpdates() {
  const notice = document.getElementById("ui-update-notice");
  const refresh = document.getElementById("reload-ui");
  if (!notice || !refresh) return;
  let busy = false;
  let closed = false;
  const announce = () => {
    notice.hidden = false;
  };
  window.addEventListener("readiness:update-available", announce);
  refresh.addEventListener("click", () => location.reload());
  const check = async () => {
    if (busy || closed || document.hidden || !notice.hidden) return;
    busy = true;
    try {
      const response = await fetch("/health", {
        cache: "no-store",
        credentials: "same-origin",
        signal: AbortSignal.timeout(5000),
      });
      const incoming = response.headers.get("X-Readiness-UI-Revision");
      const current = document
        .querySelector('meta[name="readiness-ui-revision"]')
        ?.getAttribute("content");
      if (response.ok && !closed && !sameUIRevision(current, incoming)) acceptUIRevision(incoming);
    } catch {
      // A failed local connection is not evidence that a new UI was deployed.
    } finally {
      busy = false;
    }
  };
  const focus = () => {
    void check();
  };
  window.addEventListener("focus", focus);
  document.addEventListener("visibilitychange", focus);
  let timer = setInterval(focus, 30000);
  window.addEventListener("pagehide", () => {
    closed = true;
    clearInterval(timer);
  });
  window.addEventListener("pageshow", () => {
    if (!closed) return;
    closed = false;
    timer = setInterval(focus, 30000);
    focus();
  });
}
