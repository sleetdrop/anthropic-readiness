import { test, expect } from "@playwright/test";
import { fixture, control, count, choosePresentation } from "./helpers.js";

test.beforeEach(async ({ request }) => control(request, "reset"));

for (const locale of ["zh-CN", "en"]) {
  for (const theme of ["light", "dark"]) {
    test(`narrow issue regions stack without squeezing their content: ${locale} ${theme}`, async ({
      page,
      request,
    }, info) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(`/runs/${fixture().completed_id}?view=overview`);
      await choosePresentation(page, "locale", locale);
      await choosePresentation(page, "theme", theme);
      for (const view of ["overview", "issues"]) {
        await page.goto(`/runs/${fixture().completed_id}?view=${view}`);
        const title = await page.locator(".issue-list > h1").boundingBox();
        const lead = await page.locator(".issue-list > .lead").boundingBox();
        const tools = await page.locator(".issue-toolbar").boundingBox();
        if (!title || !lead || !tools) throw new Error("missing_issue_regions");
        expect(title.width).toBeGreaterThan(330);
        expect(lead.y).toBeGreaterThanOrEqual(title.y + title.height);
        expect(tools.y).toBeGreaterThanOrEqual(lead.y + lead.height);
        await expect(page.locator(".issue-list")).toHaveCSS("display", "block");
        await page.screenshot({ path: info.outputPath(`${view}.png`), fullPage: true });
      }
      expect((await count(request)).count).toBe(0);
    });
  }
}

test("an updated deployment is announced without discarding unsaved input", async ({
  page,
  request,
}) => {
  await page.goto("/new");
  await page.locator("#endpoint").fill("http://synthetic.invalid/v1/messages");
  await page.locator("#model").fill("synthetic-unsaved");
  await page.route("**/health", async (route) => {
    await route.fulfill({
      status: 200,
      headers: { "content-type": "application/json", "x-readiness-ui-revision": "f".repeat(64) },
      body: '{"status":"ok"}',
    });
  });
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page.locator("#ui-update-notice")).toBeVisible();
  await expect(page.locator("#endpoint")).toHaveValue("http://synthetic.invalid/v1/messages");
  await expect(page.locator("#model")).toHaveValue("synthetic-unsaved");
  await page.unroute("**/health");
  await page.locator("#reload-ui").click();
  await expect(page.locator("#endpoint")).toHaveValue("");
  expect((await count(request)).count).toBe(0);
});

test("a new document revision cannot patch old workbench scripts and styles", async ({ page }) => {
  await page.goto(`/runs/${fixture().completed_id}?view=issues`);
  const html = await (await page.request.get(page.url())).text();
  const replacement = html.replace(
    /(<meta name="readiness-ui-revision" content=")[a-f0-9]+("\s*\/?>)/u,
    `$1${"e".repeat(64)}$2`,
  );
  expect(replacement).not.toBe(html);
  await page.route("**/runs/*?view=cases", (route) =>
    route.fulfill({ status: 200, contentType: "text/html", body: replacement }),
  );
  await page.locator('.view-tabs a[href*="view=cases"]').click();
  await expect(page.locator("#ui-update-notice")).toBeVisible();
  await expect(page.locator("#workbench")).toHaveAttribute("data-active-view", "issues");
  await expect(page).toHaveURL(/view=issues/u);
});

test("history and execution tables keep the same outer insets and heading hierarchy", async ({
  page,
}) => {
  for (const path of ["/history", `/runs/${fixture().completed_id}?view=activity`]) {
    await page.goto(path);
    const table = page.locator("table").first();
    await expect(table.locator("th").first()).toHaveCSS("padding-left", "12px");
    await expect(table.locator("thead th").first()).toHaveCSS("font-weight", "600");
    await expect(table.locator("thead th").last()).toHaveCSS("padding-right", "12px");
  }
});

test("returning from the browser page cache resumes deployment checks", async ({ page }) => {
  await page.goto("/new");
  await page.route("**/health", (route) =>
    route.fulfill({
      status: 200,
      headers: { "x-readiness-ui-revision": "c".repeat(64) },
      body: '{"status":"ok"}',
    }),
  );
  await page.evaluate(() => {
    window.dispatchEvent(new PageTransitionEvent("pagehide", { persisted: true }));
    window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
    window.dispatchEvent(new Event("focus"));
  });
  await expect(page.locator("#ui-update-notice")).toBeVisible();
});

test("a legacy document without UI identity cannot enter a new workbench", async ({ page }) => {
  await page.goto(`/runs/${fixture().completed_id}?view=issues`);
  const html = await (await page.request.get(page.url())).text();
  const legacy = html.replace(/<meta name="readiness-ui-revision"[^>]*>/u, "");
  expect(legacy).not.toBe(html);
  await page.route("**/runs/*?view=cases", (route) =>
    route.fulfill({ status: 200, contentType: "text/html", body: legacy }),
  );
  await page.locator('.view-tabs a[href*="view=cases"]').click();
  await expect(page.locator("#ui-update-notice")).toBeVisible();
  await expect(page.locator("#workbench")).toHaveAttribute("data-active-view", "issues");
  await expect(page).toHaveURL(/view=issues/u);
});

for (const status of [200, 503]) {
  test(`unknown deployment identity does not announce an update: HTTP ${status}`, async ({
    page,
    request,
  }) => {
    await page.goto("/new");
    await page.route("**/health", (route) =>
      route.fulfill({ status, contentType: "application/json", body: "{}" }),
    );
    const read = page.waitForResponse((response) => response.url().endsWith("/health"));
    await page.evaluate(() => window.dispatchEvent(new Event("focus")));
    await read;
    await expect(page.locator("#ui-update-notice")).toBeHidden();
    expect((await count(request)).count).toBe(0);
  });
}

test("tabs avoid vertical scrolling and retain keyboard access", async ({ page }) => {
  await page.goto(`/runs/${fixture().completed_id}?view=issues`);
  await expect(page.locator(".view-tabs")).toHaveCSS("overflow-y", "hidden");
  await page.locator(".view-tabs a").first().focus();
  await expect(page.locator(".view-tabs a").first()).toBeFocused();
  await expect(page.locator(".view-tabs a").first()).toHaveCSS("outline-offset", "-2px");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator(".view-tabs a").last().click();
  await expect(page).toHaveURL(/view=activity/u);
});
