// Standalone presentation controls: no service, cookies, storage or source mutation.
const catalogsNode = document.getElementById("document-catalogs");
const catalogs = /** @type {Record<string, Record<string, string>>} */ (
  JSON.parse(catalogsNode?.textContent || "{}")
);
const language = /** @type {HTMLSelectElement|null} */ (
  document.getElementById("document-language")
);
const theme = /** @type {HTMLSelectElement|null} */ (document.getElementById("document-theme"));
const controls = /** @type {HTMLElement|null} */ (document.querySelector(".document-controls"));
if (controls) controls.style.display = "flex";
language?.addEventListener("change", () => {
  const selected = language.value;
  const catalog = catalogs[selected];
  if (!catalog) return;
  document.querySelectorAll("[data-document-key]").forEach((node) => {
    const key = node.getAttribute("data-document-key") || "";
    let message = catalog[key];
    if (!message) return;
    const params = /** @type {Record<string, string|number>} */ (
      JSON.parse(node.getAttribute("data-document-params") || "{}")
    );
    for (const [key, value] of Object.entries(params))
      message = message.replaceAll(`{${key}}`, String(value));
    node.textContent = message;
  });
  document.querySelectorAll("[data-document-aria]").forEach((node) => {
    const key = node.getAttribute("data-document-aria") || "";
    if (catalog[key]) node.setAttribute("aria-label", catalog[key]);
  });
  document.documentElement.lang = selected;

  const title = catalog["document.title"];
  if (title) document.title = title;
});
theme?.addEventListener("change", () => {
  if (["light", "dark", "system"].includes(theme.value))
    document.documentElement.dataset.theme = theme.value;
});
