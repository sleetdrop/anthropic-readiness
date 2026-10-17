import { readFileSync } from "node:fs";
import { expect } from "@playwright/test";
/** @typedef {import('@playwright/test').Page} Page */
/** @typedef {import('@playwright/test').APIRequestContext} APIRequestContext */
export function fixture() {
  const root = process.env.READINESS_BROWSER_ROOT;
  if (!root) throw new Error("missing_fixture_root");
  return /** @type {{peer_url:string,completed_id:string,partial_id:string,offline_path:string}} */ (
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
  await page.locator("#target-name").fill("Browser synthetic assessment");
  await page.locator("#model").fill(model);
  await page.locator("#endpoint").fill(fixture().peer_url + "/v1/messages");
  await page.locator('input[value="anthropic-tools-smoke"]').check();
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
  await expect(page.locator("#job-state")).toHaveText("执行完成");
  await expect(page.locator("#report-panel #overview")).toBeVisible();
}
