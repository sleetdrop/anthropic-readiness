import { enhanceReport } from "../report-v2.js";

const TAGS = new Set([
  "section",
  "article",
  "div",
  "h1",
  "h2",
  "h3",
  "h4",
  "p",
  "span",
  "strong",
  "small",
  "a",
  "br",
  "figure",
  "figcaption",
  "svg",
  "title",
  "text",
  "rect",
  "circle",
  "details",
  "summary",
  "table",
  "caption",
  "thead",
  "tbody",
  "tr",
  "th",
  "td",
  "pre",
  "code",
  "ul",
  "ol",
  "li",
  "dl",
  "dt",
  "dd",
  "label",
  "select",
  "option",
  "time",
  "noscript",
]);
const ATTRIBUTES = new Set([
  "class",
  "id",
  "href",
  "rel",
  "role",
  "aria-label",
  "aria-labelledby",
  "scope",
  "tabindex",
  "hidden",
  "open",
  "value",
  "data-open-detail",
  "data-capability-row",
  "data-attention",
  "data-capability-filter",
  "data-figure",
  "data-ongoing",
  "viewbox",
  "xmlns",
  "x",
  "y",
  "width",
  "height",
  "fill",
  "rx",
  "cx",
  "cy",
  "r",
]);

/** Only accept the server's escaped report vocabulary; never mount arbitrary capture HTML.
 * @param {string} markup @returns {DocumentFragment}
 */
export function reportFragment(markup) {
  const parsed = new DOMParser().parseFromString(markup, "text/html");
  for (const element of parsed.body.querySelectorAll("*")) {
    if (!TAGS.has(element.localName)) {
      element.remove();
      continue;
    }
    for (const attribute of Array.from(element.attributes)) {
      const key = attribute.name.toLowerCase();
      if (
        !ATTRIBUTES.has(key) ||
        (key === "href" &&
          !attribute.value.startsWith("#") &&
          !attribute.value.startsWith("https://"))
      )
        element.removeAttribute(attribute.name);
    }
  }
  const fragment = document.createDocumentFragment();
  fragment.append(...Array.from(parsed.body.childNodes));
  return fragment;
}

/** @param {HTMLElement} container @param {string} markup */
export function mountReport(container, markup) {
  const filter = container.querySelector("[data-capability-filter]");
  const mode = filter instanceof HTMLSelectElement ? filter.value : "all";
  const focusedFilter = document.activeElement === filter;
  const open = Array.from(container.querySelectorAll("details[open]")).map((element) => element.id);
  const focused = document.activeElement instanceof HTMLElement ? document.activeElement.id : "";
  const scroll = window.scrollY;
  container.replaceChildren(reportFragment(markup));
  enhanceReport();
  const replacement = container.querySelector("[data-capability-filter]");
  if (replacement instanceof HTMLSelectElement) {
    replacement.value = mode;
    replacement.dispatchEvent(new Event("change"));
  }
  for (const id of open) {
    const element = document.getElementById(id);
    if (element instanceof HTMLDetailsElement) element.open = true;
  }
  if (focused) document.getElementById(focused)?.focus({ preventScroll: true });
  else if (focusedFilter && replacement instanceof HTMLSelectElement)
    replacement.focus({ preventScroll: true });
  window.scrollTo({ top: scroll, behavior: "instant" });
}

/** @param {HTMLElement} container */
export function setupDrawer(container) {
  const dialog = document.getElementById("finding-drawer");
  const content = document.getElementById("drawer-content");
  const close = document.getElementById("close-drawer");
  if (!(dialog instanceof HTMLDialogElement) || !content || !close) return;
  /** @type {HTMLElement|null} */
  let opener = null;
  let openerHref = "";
  let openerIndex = 0;
  let scroll = 0;
  let pushed = false;
  let navigating = false;
  const dismiss = () => {
    if (pushed) history.back();
    else dialog.close();
  };
  container.addEventListener("click", (event) => {
    const anchor =
      event.target instanceof Element ? event.target.closest('a[href^="#finding-"]') : null;
    if (!(anchor instanceof HTMLAnchorElement)) return;
    const article = document.getElementById(anchor.hash.slice(1));
    if (!article || !container.contains(article)) return;
    event.preventDefault();
    const clone = article.cloneNode(true);
    if (!(clone instanceof HTMLElement)) return;
    clone.removeAttribute("id");
    for (const element of clone.querySelectorAll("[id]")) element.removeAttribute("id");
    opener = anchor;
    openerHref = anchor.getAttribute("href") ?? "";
    openerIndex = Array.from(container.querySelectorAll("a"))
      .filter((link) => link.getAttribute("href") === openerHref)
      .indexOf(anchor);
    scroll = window.scrollY;
    navigating = false;
    content.replaceChildren(clone);
    history.pushState({ reportFinding: anchor.hash }, "", anchor.hash);
    pushed = true;
    dialog.showModal();
    close.focus();
  });
  close.addEventListener("click", dismiss);
  dialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    dismiss();
  });
  window.addEventListener("popstate", () => {
    if (dialog.open) {
      pushed = false;
      dialog.close();
    }
  });
  content.addEventListener("click", (event) => {
    const anchor =
      event.target instanceof Element ? event.target.closest('a[href^="#case-"]') : null;
    if (!(anchor instanceof HTMLAnchorElement)) return;
    event.preventDefault();
    navigating = true;
    pushed = false;
    history.replaceState(null, "", anchor.hash);
    dialog.close();
    const target = document.getElementById(anchor.hash.slice(1));
    if (target instanceof HTMLDetailsElement) target.open = true;
    target?.scrollIntoView();
    target?.focus({ preventScroll: true });
  });
  dialog.addEventListener("close", () => {
    if (!navigating) {
      const restored = opener?.isConnected
        ? opener
        : Array.from(container.querySelectorAll("a")).filter(
            (link) => link.getAttribute("href") === openerHref,
          )[openerIndex];
      restored?.focus({ preventScroll: true });
      window.scrollTo({ top: scroll, behavior: "instant" });
    }
  });
}
