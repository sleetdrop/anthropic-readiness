import { test, expect } from "@playwright/test";
import { pathToFileURL } from "node:url";
import { fixture } from "./helpers.js";

for (const javaScriptEnabled of [true, false]) {
  test(`direct file report is complete without network; scripts=${javaScriptEnabled}`, async ({
    browser,
  }, info) => {
    const context = await browser.newContext({
      javaScriptEnabled,
      viewport: { width: 1280, height: 900 },
    });
    const page = await context.newPage();
    /** @type {string[]} */ const attempted = [];
    await context.route(/https?:\/\//u, (route) => {
      attempted.push(route.request().url());
      return route.abort();
    });
    await page.goto(pathToFileURL(fixture().offline_path).href);
    await expect(page.locator("#overview h1")).toBeVisible();
    await expect(page.locator(".capability-matrix tbody tr")).toHaveCount(3);
    await expect(page.locator("figure svg")).toHaveCount(3);
    await expect(page.locator("figure figcaption")).toHaveCount(4);
    await expect(page.locator("#references")).toContainText("Anthropic");
    await page
      .locator(".figure-data")
      .first()
      .evaluate((element) => element.setAttribute("open", ""));
    await expect(page.locator("table[data-figure]").first()).toBeVisible();
    expect(attempted).toEqual([]);
    await page.screenshot({
      path: info.outputPath(`offline-${javaScriptEnabled}.png`),
      fullPage: true,
    });
    await page.emulateMedia({ media: "print" });
    await expect(page.locator("#overview")).toBeVisible();
    await expect(page.locator(".capability-matrix")).toBeVisible();
    await expect(page.locator("#references")).toBeVisible();
    await expect(page.locator(".case-detail table").first()).toBeVisible();
    await expect(page.locator(".technical pre").first()).toBeHidden();
    await page.pdf({
      path: info.outputPath(`print-${javaScriptEnabled}.pdf`),
      printBackground: true,
      format: "A4",
    });
    await page.screenshot({
      path: info.outputPath(`print-${javaScriptEnabled}.png`),
      fullPage: true,
    });
    await page.screenshot({ path: info.outputPath(`print-${javaScriptEnabled}-viewport.png`) });
    expect(attempted).toEqual([]);
    await context.close();
  });
}

test("server-rendered completed and interrupted records retain essentials without scripts", async ({
  browser,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  const web = `http://127.0.0.1:${process.env.READINESS_BROWSER_PORT ?? "18765"}`;
  await page.goto(web + "/runs/" + fixture().completed_id);
  await expect(page.locator(".run-heading h1")).toBeVisible();
  const box = await page.locator(".run-heading h1").boundingBox();
  expect(box?.y).toBeLessThan(450);
  await page.goto(web + "/runs/" + fixture().partial_id + "?view=cases");
  await expect(page.locator(".source-notice").first()).toContainText("部分记录");
  await expect(
    page.locator(".case-item .last-recorded-state").filter({ hasText: "执行中" }),
  ).toContainText("执行中");
  await context.close();
});
