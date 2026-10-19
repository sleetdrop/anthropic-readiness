import { object, objects } from "./forms.js";
/** @param {string} href @param {string[]} caseIds @param {string[]} findingIds @returns {URL|null} */
export function legacyLocation(href, caseIds, findingIds) {
  const url = new URL(href);
  let fragment;
  try {
    fragment = decodeURIComponent(url.hash.slice(1));
  } catch {
    return null;
  }
  let view;
  /** @type {[string,string]|undefined} */ let selection;
  if (fragment === "capabilities") {
    view = "cases";
  } else if (findingIds.includes(fragment)) {
    view = "issues";
    selection = ["issue", fragment];
  } else if (fragment.startsWith("case-") && caseIds.includes(fragment.slice(5))) {
    view = "cases";
    selection = ["case", fragment.slice(5)];
  } else {
    return null;
  }
  url.searchParams.set("view", view);
  url.searchParams.delete("issue");
  url.searchParams.delete("case");
  if (selection) url.searchParams.set(...selection);
  url.hash = "";
  return url;
}

if (typeof window !== "undefined" && typeof document !== "undefined") {
  const bootstrap = object(JSON.parse(document.getElementById("bootstrap")?.textContent ?? "{}"));
  if (bootstrap.page === "workbench") {
    const facts = object(object(bootstrap.workbench).facts);
    const destination = legacyLocation(
      window.location.href,
      objects(facts.cases).map((item) => String(item.case_id)),
      objects(facts.findings).map((item) => String(item.id)),
    );
    if (destination) window.location.replace(destination.href);
  }
}
