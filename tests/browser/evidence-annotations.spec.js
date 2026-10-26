import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { fixture, control, count, openIssue, choosePresentation } from "./helpers.js";

test.beforeEach(async ({ request }) => control(request, "reset"));

/** @param {import('@playwright/test').Page} page */
async function openBody(page) {
  await openIssue(page);
  const link = page.locator('a[data-evidence-path$="body.bin"]').first();
  await link.click();
  await expect(page.locator(".evidence-marker")).toBeVisible();
  return link;
}

test("real checked missing-field evidence marks its parent without moving or fabricating JSON", async ({
  page,
  request,
}) => {
  await openBody(page);
  await expect(page.locator(".evidence-token")).toHaveText("{");
  const before = await page.locator(".evidence-code").evaluateAll((nodes) =>
    nodes.map((n) => ({
      text: n.textContent,
      x: n.getBoundingClientRect().x,
      y: n.getBoundingClientRect().y,
    })),
  );
  await page.locator(".evidence-marker").click();
  await expect(page.locator("#evidence-annotation")).toBeVisible();
  await expect(page.locator("#evidence-annotation")).toContainText("stop_sequence");
  expect(
    await page.locator(".evidence-code").evaluateAll((nodes) =>
      nodes.map((n) => ({
        text: n.textContent,
        x: n.getBoundingClientRect().x,
        y: n.getBoundingClientRect().y,
      })),
    ),
  ).toEqual(before);
  await page.keyboard.press("Escape");
  await expect(page.locator("#evidence-dialog")).toBeVisible();
  await expect(page.locator("#evidence-annotation")).not.toBeVisible();
  await expect(page.locator(".evidence-marker")).toBeFocused();
  await page.locator("#payload-raw").click();
  const raw = JSON.parse((await page.locator("#evidence-content").textContent()) ?? "null");
  expect(Object.hasOwn(raw, "stop_sequence")).toBe(false);
  expect(await page.locator(".evidence-marker").count()).toBe(0);
  expect((await count(request)).count).toBe(0);
});

test("wrong-type token marker, folding and original download work across themes and widths", async ({
  page,
  request,
}, info) => {
  for (const width of [1280, 737, 390])
    for (const theme of ["light", "dark"]) {
      await page.setViewportSize({ width, height: 800 });
      await page.goto(`/runs/${fixture().completed_id}?view=issues`);
      await choosePresentation(page, "theme", theme);
      await choosePresentation(page, "locale", theme === "light" ? "zh-CN" : "en");
      await page.locator("a[data-issue-key]").first().click();
      const link = page.locator('a[data-evidence-path$="body.bin"]').first();
      const url = await link.getAttribute("href");
      const originalResponse = await page.request.get(url ?? "");
      expect(originalResponse.ok()).toBe(true);
      const original = await originalResponse.text();
      const raw = JSON.stringify({
        type: "message",
        stop_reason: "end_turn",
        stop_sequence: null,
        usage: { input_tokens: 1, output_tokens: "8" },
      });
      await page.route("**" + url, (route) => route.fulfill({ status: 200, body: raw }));
      // Display-only transport override: do not reuse prose from the original missing-field capture.
      await link.evaluate((link) => {
        link.dataset.evidenceExpected = "";
        link.dataset.evidenceActual = "";
      });
      await link.click();
      await expect(page.locator(".evidence-token")).toHaveText('"8"');
      const token = await page.locator(".evidence-token").boundingBox(),
        marker = await page.locator(".evidence-marker").boundingBox();
      if (!token || !marker) throw new Error("missing_token_geometry");
      expect(marker.x).toBeGreaterThanOrEqual(token.x + token.width);
      await page.locator(".evidence-marker").click();
      await expect(page.locator("#evidence-annotation")).toBeVisible();
      const panel = await page.locator("#evidence-annotation").boundingBox();
      if (!panel) throw new Error("missing_panel_geometry");
      expect(panel.x).toBeGreaterThanOrEqual(0);
      expect(panel.x + panel.width).toBeLessThanOrEqual(width + 1);
      await page.screenshot({
        path: info.outputPath(`token-${width}-${theme}.png`),
        fullPage: false,
      });
      await expect(page.locator("#evidence-annotation")).toBeVisible();
      await page.locator(".evidence-marker").click();
      await expect(page.locator("#evidence-annotation")).not.toBeVisible();
      await page.locator('[data-json-fold="/usage"]').click();
      await expect(page.locator(".evidence-marker")).toHaveCount(0);
      await page.locator("#evidence-locate").click();
      await expect(page.locator(".evidence-marker")).toBeVisible();
      const file = page.waitForEvent("download");
      await page.locator("#evidence-download").click();
      const download = await file;
      await download.saveAs(info.outputPath(`source-${width}-${theme}.json`));
      // Native downloads bypass the display route; compare with the actual verified file.
      expect(await readFile(info.outputPath(`source-${width}-${theme}.json`), "utf8")).toBe(
        original,
      );
      await page.locator("#close-evidence").click();
      await page.unroute("**" + url);
    }
  expect((await count(request)).count).toBe(0);
});

test("unsupported, non-failing and incomplete evidence never invent node markers", async ({
  page,
  request,
}) => {
  for (const mode of ["unknown", "indeterminate", "invalid", "truncated"]) {
    await openIssue(page);
    const link = page.locator('a[data-evidence-path$="body.bin"]').first();
    const url = await link.getAttribute("href");
    await link.evaluate((link, mode) => {
      if (mode === "unknown") {
        link.dataset.evidenceReason = "unknown_reason";
        link.dataset.evidencePointerKnown = "false";
      }
      if (mode === "indeterminate") link.dataset.evidenceStatus = "INDETERMINATE";
    }, mode);
    if (mode === "invalid" || mode === "truncated")
      await page.route("**" + url, (route) =>
        route.fulfill({
          status: 200,
          body:
            mode === "invalid"
              ? "{invalid"
              : JSON.stringify({ type: "message", text: "x".repeat(300000) }),
        }),
      );
    await link.click();
    await expect(page.locator("#evidence-notice")).not.toContainText("正在读取");
    await expect(page.locator(".evidence-marker")).toHaveCount(0);
    await expect(page.locator("#evidence-download")).toBeVisible();
    await page.locator("#close-evidence").click();
    await page.unroute("**" + url);
  }
  expect((await count(request)).count).toBe(0);
});

test("duplicate SSE target and first-start context have distinct indicators", async ({
  page,
  request,
}) => {
  await openIssue(page);
  const link = page.locator('a[data-evidence-path$="events.jsonl"]').first(),
    url = await link.getAttribute("href");
  // Display-only fixture: an event-level checked finding supplies the association.
  await link.evaluate((link) => {
    link.dataset.evidenceReason = "duplicate_message_start";
    link.dataset.evidenceEvent = "5";
    link.dataset.evidencePointerKnown = "false";
    link.dataset.evidenceExpected = "";
    link.dataset.evidenceActual = "";
  });
  const records = Array.from(
    { length: 7 },
    (_, sequence) =>
      JSON.stringify({
        sequence,
        event: sequence === 0 || sequence === 5 ? "message_start" : "content_block_delta",
        data: JSON.stringify({
          type: sequence === 0 || sequence === 5 ? "message_start" : "content_block_delta",
        }),
      }) + "\n",
  ).join("");
  await page.route("**" + url, (route) => route.fulfill({ status: 200, body: records }));
  await link.click();
  await expect(page.locator(".evidence-token")).toHaveText('"message_start"');
  await page.locator(".evidence-marker").click();
  await page.locator("#annotation-related").click();
  await expect(page.locator(".evidence-marker.is-context")).toBeVisible();
  await expect(page.locator('#event-rows tr[aria-selected="true"]')).toContainText("0");
  await expect(page.locator("#evidence-annotation")).toContainText("未标为异常");
  await page.locator("#close-annotation").click();
  await page.locator("#evidence-locate").click();
  await expect(page.locator(".evidence-marker.is-context")).toHaveCount(0);
  await expect(page.locator('#event-rows tr[aria-selected="true"]')).toContainText("5");
  expect((await count(request)).count).toBe(0);
});

test("known targets beyond the first 500 rows remain reachable in a bounded reading window", async ({
  page,
}) => {
  await openIssue(page);
  const link = page.locator('a[data-evidence-path$="body.bin"]').first(),
    url = await link.getAttribute("href");
  const body = JSON.stringify({
    type: "message",
    stop_reason: "end_turn",
    stop_sequence: null,
    ...Object.fromEntries(Array.from({ length: 600 }, (_, i) => ["extra" + i, i])),
    usage: { input_tokens: 1, output_tokens: "8" },
  });
  await page.route("**" + url, (route) => route.fulfill({ status: 200, body }));
  await link.click();
  await page.locator("#evidence-locate").click();
  await expect(page.locator(".evidence-marker")).toBeVisible();
  await expect(page.locator(".evidence-token")).toHaveText('"8"');
  expect(await page.locator(".evidence-row").count()).toBeLessThanOrEqual(500);
  await expect(page.locator("#evidence-location")).toContainText("片段");
});
