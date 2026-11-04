import { createHash } from "node:crypto";

// Static script. Report values are read from the document as text and links.
const script = `(() => {
  const contents = document.querySelector(".report-contents");
  const top = document.getElementById("report-top");
  if (!contents || !top) return;

  const dock = document.createElement("details");
  dock.className = "report-jump";
  dock.hidden = true;
  const button = document.createElement("summary");
  const label = contents.getAttribute("aria-label");
  button.textContent = label;
  const menu = document.createElement("nav");
  menu.setAttribute("aria-label", label);
  const list = contents.querySelector("ul").cloneNode(true);
  const topItem = document.createElement("li");
  const topLink = document.createElement("a");
  topLink.href = "#report-top";
  topLink.textContent = contents.dataset.topLabel;
  topItem.append(topLink);
  list.append(topItem);
  menu.append(list);
  dock.append(button, menu);
  document.body.append(dock);

  const original = Array.from(contents.querySelectorAll("a"));
  const copies = Array.from(menu.querySelectorAll("a"));
  const headings = original.map(link => document.getElementById(link.hash.slice(1)));
  let frame = 0;
  let previous = -2;

  function update() {
    frame = 0;
    dock.hidden = contents.getBoundingClientRect().bottom >= 0;
    if (dock.hidden) dock.open = false;
    let active = -1;
    const line = Math.min(120, window.innerHeight * 0.2);
    headings.forEach((heading, index) => {
      if (heading && heading.getBoundingClientRect().top <= line) active = index;
    });
    const page = document.documentElement;
    if (!dock.hidden && window.scrollY + window.innerHeight >= page.scrollHeight - 2)
      active = headings.length - 1;
    if (active === previous) return;
    previous = active;
    original.forEach((link, index) => {
      for (const item of [link, copies[index]]) {
        if (index === active) item.setAttribute("aria-current", "location");
        else item.removeAttribute("aria-current");
      }
    });
    button.textContent = active < 0 ? label : label + " · " + original[active].textContent;
  }

  function schedule() {
    if (!frame) frame = requestAnimationFrame(update);
  }

  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);
  window.addEventListener("hashchange", schedule);
  window.addEventListener("pageshow", schedule);
  menu.addEventListener("click", event => {
    const link = event.target.closest("a");
    if (!link || event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const heading = document.getElementById(link.hash.slice(1));
    if (!heading) return;
    dock.open = false;
    requestAnimationFrame(() => {
      heading.setAttribute("tabindex", "-1");
      heading.focus({ preventScroll: true });
    });
  });
  dock.addEventListener("keydown", event => {
    if (event.key === "Escape" && dock.open) {
      dock.open = false;
      button.focus();
    }
  });
  document.addEventListener("click", event => {
    if (dock.open && !dock.contains(event.target)) dock.open = false;
  });
  update();
})();`;

export const reportNavigation = {
  markup: `<script>${script}</script>`,
  policy: `; script-src 'sha256-${createHash("sha256").update(script).digest("base64")}'`,
};
