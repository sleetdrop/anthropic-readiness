import { test, expect } from "@playwright/test";
import { fixture, control, count } from "./helpers.js";

test.beforeEach(async ({ request }) => control(request, "reset"));

test("long event records search beyond context, retain source view and bound rendered rows", async ({
  page,
  request,
}) => {
  // Synthetic display transport only; no protocol verdict is produced from these records.
  const records = Array.from(
    { length: 300 },
    (_, sequence) =>
      JSON.stringify({
        sequence,
        event: sequence === 0 ? "message_start" : "content_block_delta",
        data: JSON.stringify({ type: "content_block_delta", text: `needle-${sequence}` }),
      }) + "\n",
  ).join("");
  await page.goto(`/runs/${fixture().completed_id}?view=issues`);
  await page.locator("a[data-issue-key]").first().click();
  const evidence = page.locator('a[data-evidence-path$="events.jsonl"]').first();
  const url = await evidence.getAttribute("href");
  await page.route("**" + url, (route) =>
    route.fulfill({ status: 200, contentType: "application/x-ndjson", body: records }),
  );
  await evidence.click();
  await expect(page).toHaveURL(/case=ANT-TEXT-SSE-001/u);
  await page.locator("#event-all").click();
  await expect(page.locator("#event-rows button[data-event]")).toHaveCount(100);
  await page.locator("#event-search").fill("needle-299");
  await expect(page.locator("#event-rows button[data-event]")).toHaveCount(1);
  await page.locator('#event-rows button[data-event="299"]').click();
  await page.locator("#payload-raw").click();
  await expect(page.locator("#evidence-content")).toContainText('"sequence":299');
  await page.keyboard.press("Escape");
  await evidence.click();
  await expect(page.locator("#event-search")).toHaveValue("needle-299");
  await expect(page.locator('#event-rows tr[aria-selected="true"]')).toContainText("299");
  await expect(page.locator("#payload-raw")).toHaveAttribute("aria-pressed", "true");
  expect((await count(request)).count).toBe(0);
});

test("real issue table searches, drills into an occurrence and returns with its filter", async ({
  page,
  request,
}, info) => {
  await page.goto(`/runs/${fixture().completed_id}?view=issues`);
  await expect(page.locator("#issue-inspector")).toHaveCount(0);
  await expect(page.locator(".issues-table tbody tr")).not.toHaveCount(0);
  await expect(page.locator("#completion-bar")).toHaveAttribute("value", "4");
  await page.locator("#issue-search").fill("stop_sequence");
  await page.locator("#issue-search").press("Enter");
  await expect(page).toHaveURL(/q=stop_sequence/u);
  await page.locator("[data-issue-key]").first().click();
  await expect(page.locator("#issue-inspector")).toContainText("stop_sequence");
  await page.locator('[data-observation-case="ANT-TEXT-SSE-001"]').click();
  await expect(page).toHaveURL(/case=ANT-TEXT-SSE-001/u);
  await page.locator('a[data-evidence-path$="events.jsonl"]').first().click();
  await expect(page.locator("#evidence-dialog")).toBeVisible();
  await expect(page.locator("#event-rows button[data-event]").first()).toBeVisible();
  await page.locator("#event-search").fill("message_stop");
  await expect(page.locator("#event-rows")).toContainText("message_stop");
  await page.locator("#event-rows button[data-event]").first().click();
  await page.locator("#payload-raw").click();
  await expect(page.locator("#evidence-content")).toContainText("message_stop");
  await page.screenshot({ path: info.outputPath("evidence-light.png"), fullPage: true });
  await page.locator("#close-evidence").click();
  await expect(page).toHaveURL(/case=ANT-TEXT-SSE-001/u);
  await page.locator('a[data-evidence-path$="events.jsonl"]').first().click();
  await expect(page.locator("#event-search")).toHaveValue("message_stop");
  await expect(page.locator("#payload-raw")).toHaveAttribute("aria-pressed", "true");
  await page.keyboard.press("Escape");
  await page.locator(".back").click();
  await expect(page.locator("#issue-search")).toHaveValue("stop_sequence");
  await expect(page.locator("#issue-inspector")).toHaveCount(0);
  await page.locator("#language-toggle").click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.locator(".issue-list h1")).toContainText("Results");
  await page.locator("#theme-toggle").click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.locator("#issue-search")).toHaveValue("stop_sequence");
  await page.screenshot({ path: info.outputPath("issues-dark.png"), fullPage: true });
  expect((await count(request)).count).toBe(0);
});

test("empty results, browser Back and narrow layouts retain reachable controls", async ({
  page,
  request,
}, info) => {
  await page.goto(`/runs/${fixture().completed_id}?view=issues`);
  await page.locator("#issue-search").fill("never-in-fixture");
  await page.locator("#issue-search").press("Enter");
  await expect(page).toHaveURL(/q=never-in-fixture/u);
  await expect(page.locator("[data-issue-key]")).toHaveCount(0);
  await page.goBack();
  await expect(page.locator("#issue-search")).toHaveValue("");
  for (const width of [737, 390]) {
    await page.setViewportSize({ width, height: 694 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    await expect(page.locator("#theme-toggle")).toBeVisible();
    await expect(page.locator("#open-export")).toBeVisible();
    await page.screenshot({ path: info.outputPath(`issues-${width}.png`), fullPage: true });
  }
  expect((await count(request)).count).toBe(0);
});

test("an event beyond the display budget remains unavailable without a substitute verdict", async ({
  page,
}) => {
  await page.goto(`/runs/${fixture().completed_id}?view=issues`);
  await page.locator("a[data-issue-key]").first().click();
  const evidence = page.locator('a[data-evidence-path$="events.jsonl"]').first();
  // Display-only fixture: the reference is deliberately outside the bounded prefix.
  await evidence.evaluate((link) => {
    link.dataset.evidenceEvent = "299";
  });
  const url = await evidence.getAttribute("href");
  const records = Array.from(
    { length: 300 },
    (_, sequence) =>
      JSON.stringify({
        sequence,
        event: sequence === 0 ? "message_start" : "content_block_delta",
        data: JSON.stringify({ type: "content_block_delta", text: "x".repeat(2000) }),
      }) + "\n",
  ).join("");
  await page.route("**" + url, (route) => route.fulfill({ status: 200, body: records }));
  await evidence.click();
  await expect(page.locator("#evidence-location")).toContainText("299");
  await expect(page.locator('#event-rows tr[aria-selected="true"]')).toHaveCount(0);
  await expect(page.locator("#evidence-location")).not.toContainText("目标字段缺失");
  await expect(page.locator("#evidence-download")).toBeVisible();
  await page.locator('#event-rows button[data-event="0"]').click();
  await expect(page.locator('#event-rows button[data-event="0"]')).toBeFocused();
  await expect(page.locator("#evidence-location")).not.toContainText("目标字段缺失");
});
