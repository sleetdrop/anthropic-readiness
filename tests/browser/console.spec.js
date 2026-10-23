import { test, expect } from "@playwright/test";
import { fixture, control, count, preview, start, completed } from "./helpers.js";

test.beforeEach(async ({ request }) => control(request, "reset"));

test("late credentials and equivalent alias order preserve the reviewed plan", async ({
  page,
  request,
}) => {
  await page.goto("/new");
  await page.locator("#scope-settings > summary").click();
  await page.locator("#advanced-settings > summary").click();
  await page.locator('input[value="anthropic-tool-loop"]').uncheck();
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
  const storage = await page.evaluate(() => ({
    local: { ...localStorage },
    session: { ...sessionStorage },
  }));
  expect(storage.session).toEqual({});
  expect(Object.keys(storage.local)).toEqual(["anthropic-readiness.input-history.v1"]);
  expect(JSON.parse(storage.local["anthropic-readiness.input-history.v1"])).toEqual({
    version: 1,
    endpoints: [fixture().peer_url + "/v1/messages"],
    models: ["synthetic-hold"],
  });
  expect(JSON.stringify(storage)).not.toContain(key);
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
  await expect(queued.locator("#job-state")).toHaveAttribute("data-lifecycle", "cancelled");
  await queued.locator('.view-tabs a[href*="view=cases"]').click();
  await expect(queued.locator(".case-item .status").first()).toHaveText("待评估");
  await page.locator("#cancel-run").click();
  await expect(page.locator("#job-state")).toHaveAttribute(
    "data-lifecycle",
    /cancelled|interrupted/u,
  );
  expect((await count(request)).count).toBe(1);
  await page.locator('.view-tabs a[href*="view=cases"]').click();
  const saved = await (
    await page.request.get(page.url().replace("/runs/", "/api/v1/runs/"))
  ).json();
  for (const item of saved.execution.case_states) {
    const cell = page.locator(`[data-case-id="${item.case_id}"] .status`);
    await expect(cell).toHaveClass(new RegExp("status-" + item.state.toLowerCase()));
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

test("coverage counts, checked field observations and evidence dialog preserve source facts", async ({
  page,
}, info) => {
  await page.goto(`/runs/${fixture().completed_id}?view=cases`);
  const data = await page.locator("#bootstrap").textContent();
  const facts = JSON.parse(data ?? "{}").workbench.facts;
  expect(facts.cases).toHaveLength(4);
  await expect(page.locator(".coverage-matrix tbody tr")).toHaveCount(3);
  await expect(page.locator(".case-item")).toHaveCount(4);
  const filter = page.locator("#case-filter");
  await filter.selectOption("FAIL");
  await filter.focus();
  await page.evaluate(async () => {
    const path = "/assets/web/workbench.js";
    const { patchElement } = await import(path);
    const root = document.getElementById("workbench");
    if (root) patchElement(root, root.cloneNode(true));
  });
  await expect(filter).toBeFocused();
  await expect(filter).toHaveValue("FAIL");
  await page.locator('.view-tabs a[href*="view=issues"]').click();
  await expect(page.locator("#issue-inspector")).toContainText("stop_sequence");
  const opener = page.locator("a[data-evidence-id]").first();
  await opener.focus();
  await opener.press("Enter");
  await expect(page.locator("#evidence-dialog")).toBeVisible();
  await page.screenshot({ path: info.outputPath("evidence-dialog.png") });
  await page.keyboard.press("Escape");
  await expect(opener).toBeFocused();
});

test("on-demand export previews selected files and downloads without model requests", async ({
  page,
  request,
}, info) => {
  await page.goto("/runs/" + fixture().completed_id);
  await page.locator("#open-export").click();
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
  await page.locator('.view-tabs a[href*="view=issues"]').click();
  await page.locator("[data-issue-key]").last().click();
  await expect(page.locator("#issue-inspector")).toContainText("</script>");
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
