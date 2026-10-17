import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("browser preserves fractions and measures black on white as 21", async ({ page }) => {
  await page.setContent(
    '<html lang="en"><head><title>Measurement calibration</title><style>body,p{color:#000;background:#fff}</style></head><body><main><h1>Calibration</h1><p>Black on white</p></main></body></html>',
  );
  expect(await page.evaluate(() => String(4.5))).toBe("4.5");
  const result = await new AxeBuilder({ page }).withRules(["color-contrast"]).analyze();
  expect(result.violations).toEqual([]);
  const contrast = result.passes.find((item) => item.id === "color-contrast");
  expect(contrast).toBeDefined();
  expect(contrast?.nodes.length).toBeGreaterThan(0);
  for (const node of contrast?.nodes ?? []) {
    expect(node.any).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ data: expect.objectContaining({ contrastRatio: 21 }) }),
      ]),
    );
  }
});
