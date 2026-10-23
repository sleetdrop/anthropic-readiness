import { test, expect } from "@playwright/test";
import { fixture, control, count, preview, start, choosePresentation } from "./helpers.js";

test.beforeEach(async ({ request }) => control(request, "reset"));

for (const locale of ["zh-CN", "en"]) {
  for (const theme of ["light", "dark"]) {
    test(`approved hierarchy and execution colors: ${locale} ${theme}`, async ({
      page,
      request,
    }, info) => {
      const text = theme === "light" ? "rgb(38, 38, 38)" : "rgb(222, 222, 222)";
      const accent = theme === "light" ? "rgb(65, 107, 123)" : "rgb(147, 182, 197)";
      const neutral = theme === "light" ? "rgb(98, 98, 98)" : "rgb(168, 168, 168)";
      await page.setViewportSize({ width: 737, height: 694 });
      await page.goto(`/runs/${fixture().completed_id}?view=issues`);
      await choosePresentation(page, "locale", locale);
      await choosePresentation(page, "theme", theme);
      // Check rendered CSS after legacy styles cascade, not only token declarations.
      const header = page.locator(".issues-table thead th").first();
      await expect(header).toHaveCSS("font-weight", "600");
      await expect(header).toHaveCSS("color", text);
      await expect(header).toHaveCSS("padding-left", "12px");
      await expect(page.locator(".issues-table thead th").last()).toHaveCSS(
        "padding-right",
        "12px",
      );
      await expect(page.locator(".issue-name a").first()).toHaveCSS("font-weight", "500");
      await expect(page.locator(".issue-name small").first()).toHaveCSS("font-weight", "400");
      await page.screenshot({ path: info.outputPath("completed.png"), fullPage: true });
      expect((await count(request)).count).toBe(0);

      await preview(page, "synthetic-design");
      await start(page);
      await expect(page.locator("#case-progress")).toHaveText("2 / 4");
      await expect(page.locator(".run-heading")).toHaveAttribute("data-state", "running");
      await expect(page.locator("#job-state")).toHaveCSS("color", accent);
      const progress = page.locator(".run-progress progress");
      await expect(progress).toHaveCSS("height", "4px");
      await expect(progress).toHaveCSS("color", accent);
      const titleBox = await page.locator(".run-identity").boundingBox();
      const progressBox = await page.locator(".run-progress").boundingBox();
      if (!titleBox || !progressBox) throw new Error("missing_progress_geometry");
      expect(progressBox.y).toBeLessThan(titleBox.y + titleBox.height);
      await page.screenshot({ path: info.outputPath("running.png"), fullPage: true });
      await control(request, "release");
      await expect(page.locator(".run-heading")).toHaveAttribute("data-state", "completed");
      await expect(progress).toHaveCSS("color", neutral);
      expect((await count(request)).count).toBe(4);
    });
  }
}
