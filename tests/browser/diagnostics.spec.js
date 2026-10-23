import { writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { test, expect } from "@playwright/test";
import {
  fixture,
  control,
  count,
  preview,
  start,
  completed,
  choosePresentation,
} from "./helpers.js";

test.beforeEach(async ({ request }) => control(request, "reset"));
test("import preview and activation never invoke the endpoint or reuse its address", async ({
  page,
  request,
}) => {
  await page.goto("/imports");
  await page.locator("#import-file").setInputFiles(fixture().import_path);
  await page.locator("#preview-import").click();
  await expect(page.locator("#commit-import")).toBeEnabled();
  await page.locator("#commit-import").click();
  await expect(page).toHaveURL(/\/baselines\/[\w-]+$/u);
  await expect(page.locator("#workbench")).toHaveAttribute("data-read-only", "true");
  await page.locator('.heading-actions a[href^="/new?baseline="]').click();
  await expect(page.locator("#endpoint")).toHaveValue("");
  await expect(page.locator('input[name="profile"]:checked')).toHaveCount(2);
  await page.locator("#endpoint").fill(fixture().peer_url + "/v1/messages");
  expect(
    await page
      .locator("#assessment-form :invalid")
      .evaluateAll((nodes) => nodes.map((node) => node.id || node.getAttribute("data-limit"))),
  ).toEqual([]);
  await page.locator("#preview-button").click();
  await expect(page.locator("#start-button")).toBeEnabled();
  expect((await count(request)).count).toBe(0);
});

for (const kind of ["omitted_path", "legacy_path"]) {
  test(`missing proof or unknown lineage never grants controlled retest: ${kind}`, async ({
    page,
    request,
  }) => {
    await page.goto("/imports");
    await page
      .locator("#import-file")
      .setInputFiles(fixture()[/** @type {"omitted_path"|"legacy_path"} */ (kind)]);
    await page.locator("#preview-import").click();
    await expect(page.locator("#commit-import")).toBeEnabled();
    await expect(page.locator("#import-preview")).toContainText("暂不满足受控复测条件");
    await page.locator("#commit-import").click();
    await expect(page).toHaveURL(/\/baselines\/[\w-]+$/u);
    await expect(page.locator(".heading-actions a")).toContainText("当前");
    if (kind === "omitted_path") {
      await page.locator('.view-tabs a[href*="view=issues"]').click();
      await expect(page.locator("a[data-evidence-id]")).toHaveCount(0);
    }
    expect((await count(request)).count).toBe(0);
  });
}

test("original-scope retest and comparison render actual paired repair evidence", async ({
  page,
  request,
}, info) => {
  await page.goto("/imports");
  await page.locator("#import-file").setInputFiles(fixture().import_path);
  await page.locator("#preview-import").click();
  await expect(page.locator("#commit-import")).toBeEnabled();
  await page.locator("#commit-import").click();
  await expect(page).toHaveURL(/\/baselines\/[\w-]+$/u);
  const baseline = page.url().split("/").pop();
  await page.locator('.heading-actions a[href^="/new?baseline="]').click();
  await page.locator("#endpoint").fill(fixture().peer_url + "/v1/messages");
  await page.locator("#preview-button").click();
  await expect(page.locator("#start-button")).toBeEnabled();
  await page.locator("#start-button").click();
  await expect(page).toHaveURL(/\/runs\/[\w-]+$/u);
  await expect(page.locator("#job-state")).toHaveAttribute("data-lifecycle", "completed");
  await page.locator('.view-tabs a[href*="view=compare"]').click();
  await page.locator("#comparison-baseline").selectOption("baseline:" + baseline);
  await page.locator(".compare-picker button").click();
  await expect(page).toHaveURL(/baseline=baseline%3A/u);
  await expect(page.locator(".comparison-counts")).toBeVisible();
  const html = await (await page.request.get(page.url())).text();
  const serialized = html.match(
    /<script id="bootstrap" type="application\/json">([\s\S]*?)<\/script>/u,
  )?.[1];
  const comparison = JSON.parse(serialized ?? "{}").workbench.comparison;
  expect(comparison.comparable).toBe(true);
  expect(comparison.summary.recovered).toBeGreaterThan(0);
  expect(comparison.summary.new_failure).toBe(0);
  expect(comparison.coverage.matched_cases).toBe(4);
  for (const theme of ["light", "dark"]) {
    await choosePresentation(page, "theme", theme);
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
    await page.screenshot({ path: info.outputPath(`comparison-${theme}.png`), fullPage: true });
  }
  expect((await count(request)).count).toBe(4);
});

test("comparison keeps recoveries, persistent failures, regressions and gaps together", async ({
  page,
  request,
}, info) => {
  await preview(page, "synthetic-repair");
  const before = await start(page);
  await completed(page);
  const baseline = new URL(before).pathname.split("/").pop();
  await control(request, "repair-after");
  await preview(page, "synthetic-repair");
  await start(page);
  await completed(page);
  await page.locator('.view-tabs a[href*="view=compare"]').click();
  await page.locator("#comparison-baseline").selectOption("run:" + baseline);
  await page.locator(".compare-picker button").click();
  await expect(page.locator(".comparison-counts")).toBeVisible();
  const html = await (await page.request.get(page.url())).text();
  const serialized = html.match(
    /<script id="bootstrap" type="application\/json">([\s\S]*?)<\/script>/u,
  )?.[1];
  const comparison = JSON.parse(serialized ?? "{}").workbench.comparison;
  expect(comparison.comparable).toBe(true);
  for (const key of ["recovered", "persistent", "new_failure", "gap"])
    expect(comparison.summary[key], key).toBeGreaterThan(0);
  expect(comparison.all_previous_failures_passed).toBe(false);
  expect(comparison.coverage.matched_cases).toBe(4);
  await expect(page.locator(".comparison-group-table tbody tr")).toHaveCount(5);
  await expect(page.locator("#comparison-technical")).toHaveJSProperty("open", false);
  await expect(page.locator("#comparison-technical tbody tr")).toHaveCount(comparison.pairs.length);
  await expect(page.locator('[data-comparison-after="missing"]').first()).toHaveText("检查缺失");
  await page.evaluate(() => scrollTo(0, 0));
  await page.screenshot({ path: info.outputPath("mixed-comparison-viewport.png") });
  await page
    .locator(".comparison-counts")
    .screenshot({ path: info.outputPath("mixed-counts.png") });
  await page.evaluate(() => scrollTo(0, 0));
  await page.screenshot({ path: info.outputPath("mixed-comparison-light.png"), fullPage: true });
  await choosePresentation(page, "theme", "dark");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.screenshot({ path: info.outputPath("mixed-comparison-dark.png"), fullPage: true });
  const member = page.locator(".comparison-group-table details").first();
  await member.locator("summary").focus();
  await member.locator("summary").press("Enter");
  await expect(member).toHaveJSProperty("open", true);
  await choosePresentation(page, "locale", "en");
  await expect(page.locator(".comparison-observations h2")).toHaveText("Observed checks");
  await expect(member).toHaveJSProperty("open", true);
  await page.locator("#comparison-technical summary").click();
  await expect(page.locator("#comparison-technical table")).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath("mixed-comparison-narrow.png"), fullPage: true });
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.locator("#open-export").click();
  await page.locator('#export-form input[value="json"]').check();
  await page.locator("#preview-export").click();
  await expect(page.locator("#export-preview")).toContainText("comparison.json");
  await expect(page.locator("#export-preview")).toContainText("en");
  const created = page.waitForResponse(
    (response) => response.url().endsWith("/exports") && response.request().method() === "POST",
  );
  await page.locator("#create-export").click();
  const response = await created;
  expect(response.status()).toBe(201);
  const record = await response.json();
  const runId = new URL(page.url()).pathname.split("/").pop();
  const exported = await page.request.get(
    `/api/v1/runs/${runId}/exports/${record.export_id}?format=json`,
  );
  expect(exported.ok()).toBe(true);
  const document = await exported.json();
  expect(document.comparison.summary).toEqual(comparison.summary);
  expect(document.comparison.pairs).toHaveLength(comparison.pairs.length);
  expect(JSON.stringify(document)).not.toContain(fixture().peer_url);
  const report = await page.request.get(
    `/api/v1/runs/${runId}/exports/${record.export_id}?format=html`,
  );
  expect(report.ok()).toBe(true);
  const reportPath = info.outputPath("mixed-assessment.html");
  writeFileSync(reportPath, await report.text());
  const reading = await page.context().newPage();
  await reading.route(/https?:\/\//u, (route) => route.abort());
  await reading.goto(pathToFileURL(reportPath).href);
  await expect(reading.locator("#comparison-matrix tbody tr")).toHaveCount(5);
  for (const theme of ["light", "dark"]) {
    await reading.locator("#document-theme").selectOption(theme);
    await reading.screenshot({ path: info.outputPath(`report-${theme}-viewport.png`) });
    await reading.screenshot({ path: info.outputPath(`report-${theme}.png`), fullPage: true });
  }
  await reading.close();
  expect((await count(request)).count).toBe(8);
});
