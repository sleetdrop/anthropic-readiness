/** Shared projection helpers. Input objects come from report-view schema 1.0. */
/** @typedef {{[state: string]: number}} StatusCounts */
/** @typedef {{dimensions: {[dimension: string]: StatusCounts}}} Capability */

/**
 * @template {Capability} T
 * @param {T[]} rows
 * @param {string} mode
 * @returns {T[]}
 */
export function filterCapabilities(rows, mode) {
  if (mode !== "attention") return rows.slice();
  return rows.filter((row) =>
    Object.entries(row.dimensions).some(
      ([dimension, counts]) =>
        dimension !== "client" &&
        Object.entries(counts).some(
          ([state, count]) => !["PASS", "not_evaluated"].includes(state) && count > 0,
        ),
    ),
  );
}

/** @template {{id: string}} T @param {{findings: T[]}} view @param {string} id @returns {T|null} */
export function selectFinding(view, id) {
  return view.findings.find((finding) => finding.id === id) ?? null;
}

/** DOM enhancement leaves all essential report content server-rendered. */
export function enhanceReport() {
  const filter = document.querySelector("[data-capability-filter]");
  if (filter instanceof HTMLSelectElement) {
    filter.closest(".js-controls")?.removeAttribute("hidden");
    filter.addEventListener("change", () => {
      for (const row of document.querySelectorAll("[data-capability-row]")) {
        if (row instanceof HTMLElement) {
          row.hidden = filter.value === "attention" && row.dataset.attention !== "true";
        }
      }
    });
  }
  for (const link of document.querySelectorAll("[data-open-detail]")) {
    link.addEventListener("click", () => {
      if (!(link instanceof HTMLAnchorElement)) return;
      const target = document.getElementById(link.hash.slice(1));
      if (target instanceof HTMLDetailsElement) target.open = true;
      if (target instanceof HTMLElement) target.focus({ preventScroll: true });
    });
  }
}

if (typeof document !== "undefined") enhanceReport();
