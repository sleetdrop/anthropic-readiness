import { test, expect } from "@playwright/test";
import { fixture, control, count, start, completed } from "./helpers.js";

test.beforeEach(async ({ request }) => control(request, "reset"));

test("two fields prepare the complete default scope without contacting the model", async ({
  page,
  request,
}) => {
  await page.goto("/new");
  await expect(page.locator("#advanced-settings")).not.toHaveAttribute("open", "");
  await expect(page.locator("#scope-settings")).not.toHaveAttribute("open", "");
  await expect(page.locator("#scope-summary")).toContainText("5");
  await expect(page.locator("#scope-summary")).toContainText("6");
  await expect(page.locator("#target-name")).not.toBeVisible();
  await expect(page.locator("#credential")).toBeVisible();
  await expect(page.locator("#start-button")).not.toBeVisible();
  await page.locator("#endpoint").fill(fixture().peer_url);
  await page.locator("#model").fill("synthetic-pass");
  await page.locator("#preview-button").click();
  await expect(page.locator("#start-button")).toBeEnabled();
  expect((await count(request)).count).toBe(0);
  await expect(page.locator("#plan-preview")).toContainText(fixture().peer_url + "/v1/messages");
  await start(page);
  await completed(page);
  const id = page.url().split("/").pop();
  const run = await (await page.request.get("/api/v1/runs/" + id)).json();
  expect(run.plan.target.name).toBe("synthetic-pass");
  expect(run.plan.target.auth).toEqual({ mode: "none" });
  expect(run.plan.target.response_model_policy).toBe("request_or_alias");
  expect(run.report.summary.planned_cases).toBe(5);
  expect((await count(request)).count).toBe(6);
});

test("optional key selects authentication without leaking into preview or saved presets", async ({
  page,
  request,
}) => {
  await page.goto("/new");
  await page.locator("#endpoint").fill(fixture().peer_url + "/v1");
  await page.locator("#model").fill("synthetic-pass");
  await page.locator("#credential").fill("synthetic-simplified-secret");
  await page.locator("#preview-button").click();
  await expect(page.locator("#start-button")).toBeEnabled();
  await expect(page.locator("#plan-preview")).not.toContainText("synthetic-simplified-secret");
  await page.locator("#credential").fill("");
  await expect(page.locator("#start-button")).toBeDisabled();
  await page.locator("#credential").fill("synthetic-simplified-secret");
  await page.locator("#preview-button").click();
  await expect(page.locator("#start-button")).toBeEnabled();
  await page.locator("#advanced-settings > summary").click();
  const saved = page.waitForResponse(
    (response) => response.url().endsWith("/api/v1/presets") && response.status() === 201,
  );
  await page.locator("#save-preset").click();
  expect(await (await saved).text()).not.toContain("synthetic-simplified-secret");
  expect((await count(request)).count).toBe(0);
  await start(page);
  await completed(page);
  expect((await count(request)).requests.every((item) => item.credential_seen)).toBe(true);
});

test("scope changes update counts; both locales and themes keep the entry compact", async ({
  page,
  request,
}, info) => {
  await page.goto("/new");
  for (const width of [1280, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const locale of ["zh-CN", "en"]) {
      await page.locator("#locale-choice").selectOption(locale);
      for (const theme of ["light", "dark"]) {
        await page.locator("#theme-choice").selectOption(theme);
        await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
          true,
        );
        const action = await page.locator("#preview-button").boundingBox();
        expect(action?.y).toBeGreaterThan(0);
        expect((action?.y ?? 0) + (action?.height ?? 0)).toBeLessThanOrEqual(900);
        await page.screenshot({ path: info.outputPath(`entry-${width}-${locale}-${theme}.png`) });
      }
    }
  }
  await page.locator("#scope-settings > summary").click();
  await page.locator('input[value="anthropic-basic"]').uncheck();
  await page.locator('input[value="anthropic-tools-smoke"]').uncheck();
  await expect(page.locator("#scope-summary")).toHaveText("Test cases: 1 · Requests: up to 2.");
  expect((await count(request)).count).toBe(0);
});
