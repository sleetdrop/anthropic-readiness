import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { fixture } from "./helpers.js";

for (const width of [390, 1280]) {
  test(`keyboard, accessible semantics and readable layout at ${width}px`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: 900 });
    for (const path of [
      "/new",
      "/runs/" + fixture().completed_id,
      "/history",
      "/imports",
      "/runs/" + fixture().completed_id + "?view=issues",
      "/runs/" + fixture().completed_id + "?view=cases",
    ]) {
      await page.goto(path);
      const violations = (await new AxeBuilder({ page }).analyze()).violations;
      expect(
        violations.map((item) => ({
          id: item.id,
          impact: item.impact,
          nodes: item.nodes.map((node) => node.target),
        })),
      ).toEqual([]);
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
      ).toBe(true);
      await page.keyboard.press("Tab");
      await expect(page.locator(".skip-link")).toBeFocused();
      await page.keyboard.press("Enter");
      await expect(page.locator("#main")).toBeFocused();
      await page.screenshot({
        path: info.outputPath(
          `${path === "/new" ? "configure" : path === "/history" ? "history" : "report"}-${width}.png`,
        ),
        fullPage: true,
      });
      await page.screenshot({
        path: info.outputPath(
          `${path === "/new" ? "configure" : path === "/history" ? "history" : "report"}-${width}-viewport.png`,
        ),
      });
      if (path.startsWith("/runs/") && !path.includes("?")) {
        await page.locator("#capabilities").scrollIntoViewIfNeeded();
        await page.screenshot({ path: info.outputPath(`matrix-${width}.png`) });
        await page.locator('.view-tabs a[href*="view=activity"]').click();
        await page.screenshot({ path: info.outputPath(`activity-${width}.png`) });
      }
    }
  });
}
