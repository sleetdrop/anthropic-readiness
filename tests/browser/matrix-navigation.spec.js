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

test("Web matrix member selection and refresh preserve the correct target and focus", async ({
  page,
}) => {
  await page.goto("/runs/" + fixture().completed_id);
  const members = page.locator("#matrix-streaming-protocol-FAIL");
  const summary = members.locator("summary");
  await summary.focus();
  await summary.press("Enter");
  await expect(members.locator("a")).toHaveCount(2);
  await page.evaluate(async () => {
    const path = "/assets/web/report.js";
    const { mountReport } = await import(path);
    const panel = document.getElementById("report-panel");
    if (panel) mountReport(panel, panel.innerHTML);
  });
  await expect(members).toHaveJSProperty("open", true);
  await expect(summary).toBeFocused();
  const second = members.locator('a[href="#case-ANT-TEXT-SSE-002"]');
  await second.focus();
  await second.press("Enter");
  const target = page.locator("#case-ANT-TEXT-SSE-002");
  await expect(target).toHaveJSProperty("open", true);
  await expect(target).toBeFocused();
});
