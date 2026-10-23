import { test, expect } from "@playwright/test";
import { fixture, control, count, start, completed } from "./helpers.js";

test.beforeEach(async ({ request }) => control(request, "reset"));

test("new catalog offers a separate two-request tool round trip", async ({ page, request }) => {
  await page.goto("/new");
  await expect(page.locator('input[name="profile"]:checked')).toHaveCount(3);
  await expect(page.locator('[data-limit="max_requests"]')).toHaveValue("6");
  await page.locator('input[value="anthropic-basic"]').uncheck();
  await page.locator('input[value="anthropic-tools-smoke"]').uncheck();
  await page.locator("#model").fill("synthetic-pass");
  await page.locator("#endpoint").fill(fixture().peer_url + "/v1/messages");
  await page.locator("#preview-button").click();
  await expect(page.locator("#start-button")).toBeEnabled();
  expect((await count(request)).count).toBe(0);
  await start(page);
  await completed(page);
  expect((await count(request)).count).toBe(2);
  const id = page.url().split("/").pop();
  const response = await page.request.get("/api/v1/runs/" + id);
  const run = await response.json();
  expect(run.report.summary.planned_cases).toBe(1);
  expect(run.report.summary.actual_requests).toBe(2);
  expect(run.report.cases[0].case_id).toBe("ANT-TOOL-LOOP-001");
  expect(run.report.cases[0].status).toBe("PASS");
  expect(run.report.evidence_verification.status).toBe("verified");
});
