import { test, expect } from "@playwright/test";
import { fixture, control, count } from "./helpers.js";

const key = "anthropic-readiness.input-history.v1";

test.beforeEach(async ({ request }) => control(request, "reset"));

test("recent inputs survive refresh as suggestions without restoring credentials or sending requests", async ({
  page,
  request,
}) => {
  await page.goto("/new");
  await page.locator("#endpoint").fill(fixture().peer_url);
  await page.locator("#model").fill("synthetic-pass");
  await page.locator("#credential").fill("synthetic-history-secret");
  await page.locator("#preview-button").focus();
  const remembered = await page.evaluate((name) => localStorage.getItem(name), key);
  expect(JSON.parse(remembered ?? "null")).toEqual({
    version: 1,
    endpoints: [fixture().peer_url],
    models: ["synthetic-pass"],
  });
  expect(remembered).not.toContain("synthetic-history-secret");
  expect((await count(request)).count).toBe(0);
  await page.reload();
  await expect(page.locator("#endpoint")).toHaveValue("");
  await expect(page.locator("#model")).toHaveValue("");
  await expect(page.locator("#credential")).toHaveValue("");
  await expect(page.locator("#endpoint")).toHaveAttribute("list", "endpoint-history");
  await expect(page.locator("#model")).toHaveAttribute("list", "model-history");
  await expect(page.locator("#endpoint-history option")).toHaveAttribute(
    "value",
    fixture().peer_url,
  );
  await expect(page.locator("#model-history option")).toHaveAttribute("value", "synthetic-pass");
  await page.evaluate(() => localStorage.setItem("unrelated-preference", "keep"));
  await page.locator("#clear-input-history").click();
  expect(await page.evaluate((name) => localStorage.getItem(name), key)).toBeNull();
  expect(await page.evaluate(() => localStorage.getItem("unrelated-preference"))).toBe("keep");
  await expect(page.locator("#endpoint-history option")).toHaveCount(0);
  await expect(page.locator("#model-history option")).toHaveCount(0);
  await page.reload();
  await expect(page.locator("#clear-input-history")).not.toBeVisible();
  expect((await count(request)).count).toBe(0);
});

test("blocked browser storage leaves preview and explicit start available", async ({
  page,
  request,
}) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", {
      get() {
        throw new DOMException("Disabled for synthetic test", "SecurityError");
      },
    });
  });
  await page.goto("/new");
  await page.locator("#endpoint").fill(fixture().peer_url);
  await page.locator("#model").fill("synthetic-pass");
  await page.locator("#preview-button").click();
  await expect(page.locator("#start-button")).toBeEnabled();
  await expect(page.locator("#app-message")).not.toBeVisible();
  expect((await count(request)).count).toBe(0);
});
