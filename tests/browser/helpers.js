import { readFileSync } from "node:fs";
import { expect } from "@playwright/test";
/** @typedef {import('@playwright/test').Page} Page */
/** @typedef {import('@playwright/test').APIRequestContext} APIRequestContext */
export function fixture() {
  const root = process.env.READINESS_BROWSER_ROOT;
  if (!root) throw new Error("missing_fixture_root");
  return /** @type {{document_paths:Record<string,string>,peer_url:string,import_path:string,omitted_path:string,legacy_path:string,completed_id:string,partial_id:string,offline_path:string,mixed_path:string}} */ (
    JSON.parse(readFileSync(root + "/fixture.json", "utf8"))
  );
}
/** @param {APIRequestContext} request @param {string} action */
export async function control(request, action) {
  const response = await request.post(fixture().peer_url + "/__fixture/" + action);
  expect(response.ok()).toBeTruthy();
}
/** @param {APIRequestContext} request */
export async function count(request) {
  const response = await request.get(fixture().peer_url + "/__fixture/state");
  return /** @type {{count:number,requests:{credential_seen:boolean}[]}} */ (await response.json());
}
/** @param {Page} page @param {string} [model] @param {string|null} [key] */
export async function preview(page, model = "synthetic-pass", key = null) {
  await page.goto("/new");
  await page.locator("#advanced-settings > summary").click();
  await page.locator("#target-name").fill("Browser synthetic assessment");
  await page.locator("#model").fill(model);
  await page.locator("#endpoint").fill(fixture().peer_url + "/v1/messages");
  await page.locator("#scope-settings > summary").click();
  await page.locator('input[value="anthropic-tools-smoke"]').check();
  // These existing workflows retain their original four-case scope and allowance.
  await page.locator('input[value="anthropic-tool-loop"]').uncheck();
  await page.locator(".budget-details > summary").click();
  await page.locator('[data-limit="max_requests"]').fill("4");
  await page.locator(".budget-details > summary").click();
  if (key) {
    await page.locator("#auth-mode").selectOption("api_key");
    await page.locator("#credential").fill(key);
  }
  await page.locator("#preview-button").click();
  await expect(page.locator("#start-button")).toBeEnabled();
}
/** @param {Page} page */
export async function start(page) {
  await page.locator("#start-button").click();
  await expect(page).toHaveURL(/\/runs\/[\w-]+$/u);
  return page.url();
}
/** @param {Page} page */
export async function completed(page) {
  await expect(page.locator("#job-state")).toHaveAttribute("data-lifecycle", "completed", {
    timeout: 30000,
  });
  await expect(page.locator("#workbench[data-active-view=overview]")).toBeVisible();
}

/** Use the actual visible control on either configuration or run pages.
 * @param {Page} page @param {"locale"|"theme"} field @param {string} value
 */
export async function choosePresentation(page, field, value) {
  const select = page.locator(`#${field === "locale" ? "locale" : "theme"}-choice`);
  if (await select.count()) await select.selectOption(value);
  else {
    const attr = field === "locale" ? "lang" : "data-theme";
    for (let turn = 0; turn < 2; turn++) {
      const before = await page.locator("html").getAttribute(attr);
      if (before === value) break;
      await page.locator(field === "locale" ? "#language-toggle" : "#theme-toggle").click();
      await expect(page.locator("html")).not.toHaveAttribute(attr, before ?? "");
    }
  }
  await expect(page.locator("html")).toHaveAttribute(
    field === "locale" ? "lang" : "data-theme",
    value,
  );
}
/** The approved table requires an explicit issue selection.
 * @param {Page} page @param {string} [id]
 */
export async function openIssue(page, id = fixture().completed_id) {
  await page.goto(`/runs/${id}?view=issues`);
  await page.locator("a[data-issue-key]").first().click();
  await expect(page.locator("#issue-inspector")).toBeVisible();
}
