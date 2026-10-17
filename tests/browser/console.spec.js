import { test, expect } from "@playwright/test";
import { fixture, control, count, preview, start, completed } from "./helpers.js";

test.beforeEach(async ({ request }) => control(request, "reset"));

test("late credentials and equivalent alias order preserve the reviewed plan", async ({
  page,
  request,
}) => {
  await page.goto("/new");
  await page.locator("#model").fill("synthetic-pass");
  await page.locator("#endpoint").fill(fixture().peer_url + "/v1/messages");
  await page.locator("#aliases").fill("later-alias, earlier-alias, later-alias");
  await page.locator("#auth-mode").selectOption("api_key");
  await page.locator("#preview-button").click();
  await expect(page.locator("#start-button")).toBeEnabled();
  await page.locator("#credential").fill("synthetic-late-credential");
  await page.locator("#preview-title").click();
  await expect(page.locator("#start-button")).toBeEnabled();
  await page.locator("#aliases").fill("earlier-alias, later-alias");
  await page.locator("#preview-title").click();
  await expect(page.locator("#start-button")).toBeEnabled();
  expect((await count(request)).count).toBe(0);
  await start(page);
  await completed(page);
  expect((await count(request)).count).toBe(4);
});

test("preview makes zero requests; duplicate explicit admission keeps one run", async ({
  page,
  request,
}) => {
  await preview(page);
  expect((await count(request)).count).toBe(0);
  const admission = page.waitForRequest(
    (item) => item.url().endsWith("/api/v1/runs") && item.method() === "POST",
  );
  await start(page);
  const original = await admission;
  const duplicate = await page.evaluate(
    async ({ payload, token }) => {
      const response = await fetch("/api/v1/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": token ?? "" },
        body: payload,
      });
      return { status: response.status, value: await response.json() };
    },
    { payload: original.postData(), token: await original.headerValue("x-csrf-token") },
  );
  expect(duplicate.status).toBe(202);
  expect(duplicate.value.id).toBe(page.url().split("/").pop());
  await completed(page);
  expect((await count(request)).count).toBe(4);
  await page.reload();
  await completed(page);
  expect((await count(request)).count).toBe(4);
});

test("test_start_clears_submitted_secret", async ({ page, request }) => {
  const key = "synthetic-browser-secret-only";
  await preview(page, "synthetic-hold", key);
  // HTTP 204 leaves the original document in place after admission, so its field
  // can be inspected without blocking the browser's navigation machinery.
  await page.route(/\/runs\/[\w-]+$/u, async (route) => {
    if (route.request().isNavigationRequest()) await route.fulfill({ status: 204 });
    else await route.continue();
  });
  const accepted = page.waitForResponse(
    (response) => response.url().endsWith("/api/v1/runs") && response.status() === 202,
  );
  await page.locator("#start-button").click();
  const run = await (await accepted).json();
  expect(
    await page.evaluate(() => {
      const field = document.getElementById("credential");
      return field instanceof HTMLInputElement ? field.value : "missing";
    }),
  ).toBe("");
  expect(await page.evaluate(() => sessionStorage.length + localStorage.length)).toBe(0);
  expect(JSON.stringify(run)).not.toContain(key);
  await page.unrouteAll({ behavior: "wait" });
  await page.goto("/runs/" + run.id);
  await expect.poll(async () => (await count(request)).count).toBe(1);
  expect((await count(request)).requests[0].credential_seen).toBe(true);
  expect(await page.content()).not.toContain(key);
  await control(request, "release");
  await completed(page);
});

test("closing and reopening only observes; saved progress matches real requests", async ({
  page,
  context,
  request,
}) => {
  await preview(page, "synthetic-hold");
  const url = await start(page);
  await expect.poll(async () => (await count(request)).count).toBe(1);
  await expect(page.locator("#request-progress")).toHaveText(/^1 \/ /u);
  await page.close();
  const reopened = await context.newPage();
  await reopened.goto(url);
  expect((await count(request)).count).toBe(1);
  await control(request, "release");
  await completed(reopened);
  await reopened.locator("#execution-panel summary").first().click();
  await expect(reopened.locator("#case-progress")).toHaveText("4 / 4");
  await expect(reopened.locator("#request-progress")).toHaveText(/^4 \/ /u);
  expect((await count(request)).count).toBe(4);
});

test("active and queued cancellation preserve honest partial states", async ({
  page,
  context,
  request,
}) => {
  await preview(page, "synthetic-hold");
  await start(page);
  await expect.poll(async () => (await count(request)).count).toBe(1);
  const queued = await context.newPage();
  await preview(queued);
  await start(queued);
  await expect(queued.locator("#job-state")).toHaveText("排队中");
  await queued.locator("#cancel-run").click();
  await expect(queued.locator("#job-state")).toHaveText("已取消");
  await queued.locator("#execution-panel summary").first().click();
  await expect(queued.locator("[data-case-state].pending").first()).toContainText("最后记录");
  await page.locator("#cancel-run").click();
  await expect(page.locator("#job-state")).toHaveText(/已取消|已中断/u);
  expect((await count(request)).count).toBe(1);
  await page.locator("#execution-panel summary").first().click();
  const saved = await (
    await page.request.get(page.url().replace("/runs/", "/api/v1/runs/"))
  ).json();
  for (const item of saved.execution.case_states) {
    const cell = page.locator(`[data-progress-case="${item.case_id}"] [data-case-state]`);
    await expect(cell).toContainText(item.state);
    if (["pending", "running"].includes(item.state)) await expect(cell).toContainText("最后记录");
  }
});

test("expired session and persisted pageshow recover reads without resending", async ({
  page,
  request,
}) => {
  await preview(page, "synthetic-hold");
  await start(page);
  await expect.poll(async () => (await count(request)).count).toBe(1);
  await control(request, "expire");
  const recovered = page.waitForResponse(
    (response) => response.url().endsWith("/api/v1/session") && response.status() === 200,
  );
  await page.evaluate(() => {
    window.dispatchEvent(new PageTransitionEvent("pagehide", { persisted: true }));
    window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
  });
  await recovered;
  expect((await count(request)).count).toBe(1);
  await control(request, "release");
  await completed(page);
  expect((await count(request)).count).toBe(4);
});

test("matrix, figure tables, drawer and focus preserve the verified data", async ({
  page,
}, info) => {
  await page.goto("/runs/" + fixture().completed_id);
  const data = await page.locator("#bootstrap").textContent();
  const report = /** @type {{cases:unknown[],figures:{id:string,rows:unknown[][]}[]}} */ (
    JSON.parse(data ?? "{}").run.report
  );
  expect(report.cases).toHaveLength(4);
  await expect(page.locator(".capability-matrix tbody tr")).toHaveCount(3);
  for (const figure of report.figures) {
    const table = page.locator(`table[data-figure="${figure.id}"]`);
    await expect(table.locator("tbody tr")).toHaveCount(figure.rows.length);
    expect(await table.locator("tbody tr").allTextContents()).toEqual(
      figure.rows.map((row) => row.map((value) => (value === null ? "—" : String(value))).join("")),
    );
  }
  const filter = page.locator("[data-capability-filter]");
  await filter.selectOption("attention");
  await filter.focus();
  await page.evaluate(async () => {
    // The same module used by live fragment refreshes must preserve keyboard location.
    const path = "/assets/web/report.js";
    const { mountReport } = await import(path);
    const panel = document.getElementById("report-panel");
    if (panel) mountReport(panel, panel.innerHTML);
  });
  await expect(filter).toBeFocused();
  await expect(filter).toHaveValue("attention");
  const opener = page.locator('a[href^="#finding-"]').first();
  await opener.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#finding-drawer")).toBeVisible();
  await expect(page.locator("#drawer-content")).toContainText("stop_sequence");
  await page.screenshot({ path: info.outputPath("finding-drawer.png") });
  await page.keyboard.press("Escape");
  await expect(opener).toBeFocused();
});

test("on-demand export previews selected files and downloads without model requests", async ({
  page,
  request,
}, info) => {
  await page.goto("/runs/" + fixture().completed_id);
  await page.locator("#include-evidence").check();
  await page.locator("#preview-export").click();
  await expect(page.locator("#create-export")).toBeEnabled();
  await expect(page.locator("#export-preview")).toContainText("result.json");
  await expect(page.locator("#export-preview")).toContainText("ZIP 包含所列证据");
  await page.locator("#create-export").click();
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "下载 ZIP（所选格式与清单）", exact: true }).click();
  const file = await download;
  expect(file.suggestedFilename()).toBe("anthropic-readiness.zip");
  await file.saveAs(info.outputPath("synthetic-export.zip"));
  expect(await file.failure()).toBeNull();
  expect((await count(request)).count).toBe(0);
});

test("hostile upstream strings remain inert in source and live fragments", async ({
  page,
  request,
}) => {
  /** @type {string[]} */ const unexpected = [];
  page.on("request", (item) => {
    if (!item.url().startsWith("http://127.0.0.1:")) unexpected.push(item.url());
  });
  await preview(page, "synthetic-hostile");
  await start(page);
  await completed(page);
  await expect(page.locator("#findings")).toContainText("</script>");
  const saved = await (
    await page.request.get(page.url().replace("/runs/", "/api/v1/runs/"))
  ).json();
  expect(
    saved.report.cases.map(
      (/** @type {{dimensions:{behavior:string}}} */ item) => item.dimensions.behavior,
    ),
  ).toEqual(["PASS", "PASS", "PASS", "PASS"]);
  expect(await page.evaluate(() => Object.hasOwn(window, "injected"))).toBe(false);
  expect(await page.locator('img[src*="invalid.example"]').count()).toBe(0);
  expect(unexpected).toEqual([]);
  expect((await count(request)).count).toBe(4);
});
