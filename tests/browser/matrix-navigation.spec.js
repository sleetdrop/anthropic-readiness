import { test, expect } from "@playwright/test";
import { pathToFileURL } from "node:url";
import { fixture } from "./helpers.js";

for (const javaScriptEnabled of [true, false]) {
  test(`mixed matrix navigation follows its status without network; scripts=${javaScriptEnabled}`, async ({
    browser,
  }) => {
    const context = await browser.newContext({ javaScriptEnabled });
    const page = await context.newPage();
    /** @type {string[]} */ const attempts = [];
    await context.route(/https?:\/\//u, (route) => {
      attempts.push(route.request().url());
      return route.abort();
    });
    await page.goto(pathToFileURL(fixture().mixed_path).href);
    const row = page.locator(".capability-matrix tbody tr").filter({ hasText: "流式消息" });
    const passing = row.locator("td").nth(1).locator("a").filter({ hasText: "PASS" });
    await expect(passing).toHaveAttribute("href", "#case-ANT-TEXT-SSE-002");
    await passing.click();
    await expect(page).toHaveURL(/#case-ANT-TEXT-SSE-002$/u);
    const target = page.locator("#case-ANT-TEXT-SSE-002");
    if (javaScriptEnabled) {
      await expect(target).toHaveJSProperty("open", true);
      await expect(target).toBeFocused();
    } else {
      await target.locator("summary").click();
      await expect(target).toHaveJSProperty("open", true);
    }
    const members = row.locator("td").nth(3).locator("details");
    const summary = members.locator("summary");
    await summary.focus();
    await summary.press("Enter");
    await expect(members).toHaveJSProperty("open", true);
    await expect(members.locator("a")).toHaveCount(2);
    await summary.press("Enter");
    await expect(members).toHaveJSProperty("open", false);
    await expect(summary).toBeFocused();
    expect(attempts).toEqual([]);
    await context.close();
  });
}

test("Web case selection and keyed refresh preserve the correct target and focus", async ({
  page,
}) => {
  await page.goto(`/runs/${fixture().completed_id}?view=cases&case=ANT-TEXT-SSE-002`);
  const target = page.locator('[data-case-id="ANT-TEXT-SSE-002"]');
  await expect(target).toHaveAttribute("aria-current", "true");
  const summary = page.locator("#case-inspector details summary").first();
  await summary.click();
  await summary.focus();
  const open = await summary.locator("..").evaluate((node) => node.hasAttribute("open"));
  await page.evaluate(async () => {
    const path = "/assets/web/workbench.js";
    const { patchElement } = await import(path);
    const root = document.getElementById("workbench");
    if (root) patchElement(root, root.cloneNode(true));
  });
  await expect(summary).toBeFocused();
  expect(await summary.locator("..").evaluate((node) => node.hasAttribute("open"))).toBe(open);
  await expect(target).toHaveAttribute("aria-current", "true");
  await expect(page.locator("#case-inspector")).toContainText("ANT-TEXT-SSE-002");
});
