import { test, expect } from "@playwright/test";
import { pathToFileURL } from "node:url";
import { fixture, count } from "./helpers.js";

for (const width of [390, 573]) {
  for (const mode of ["web", "offline"]) {
    test(`four-case matrix stays readable and keyboard scrollable: ${mode} ${width}px`, async ({
      page,
      request,
    }, info) => {
      await page.setViewportSize({ width, height: 900 });
      const before = (await count(request)).count;
      /** @type {string[]} */ const networkAttempts = [];
      if (mode === "offline") {
        await page.route(/https?:\/\//u, (route) => {
          networkAttempts.push(route.request().url());
          return route.abort();
        });
      }
      await page.goto(
        mode === "web"
          ? "/runs/" + fixture().completed_id
          : pathToFileURL(fixture().offline_path).href,
      );
      const matrix = page.locator(".capability-matrix");
      await expect(page.locator(".case-detail")).toHaveCount(4);
      const firstColumn = await matrix.locator("thead th").first().boundingBox();
      expect(firstColumn?.width).toBeGreaterThanOrEqual(160);
      const firstRow = await matrix.locator("tbody tr").first().boundingBox();
      expect(firstRow?.height).toBeLessThan(180);
      const region = page.getByRole("region", { name: "能力矩阵，可横向滚动", exact: true });
      await region.scrollIntoViewIfNeeded();
      await page.screenshot({ path: info.outputPath(`matrix-${mode}-${width}.png`) });
      await region.focus();
      await expect(region).toBeFocused();
      expect(await region.evaluate((element) => element.scrollWidth > element.clientWidth)).toBe(
        true,
      );
      await region.press("ArrowRight");
      await expect.poll(() => region.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
      ).toBe(true);
      await page.emulateMedia({ media: "print" });
      await page.setViewportSize({ width: 794, height: 1123 });
      await expect(matrix).toBeVisible();
      const printBox = await matrix.boundingBox();
      expect((printBox?.x ?? 0) + (printBox?.width ?? 0)).toBeLessThanOrEqual(794);
      await page.pdf({
        path: info.outputPath(`matrix-print-${mode}-${width}.pdf`),
        format: "A4",
        printBackground: true,
      });
      expect(networkAttempts).toEqual([]);
      expect((await count(request)).count).toBe(before);
    });
  }
}
