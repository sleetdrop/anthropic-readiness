import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";

const styles = readFileSync(
  new URL("../../src/anthropic_readiness/resources/themes.css", import.meta.url),
  "utf8",
);

for (const theme of [null, "system", "dark"]) {
  test(`theme foundation follows explicit/system appearance and prints light: ${theme}`, async ({
    page,
  }) => {
    await page.setContent("<!doctype html><html><body><main>Theme probe</main></body></html>");
    await page.addStyleTag({
      content: `${styles}\nbody { background: var(--readiness-page); color: var(--readiness-text); }`,
    });
    await page.emulateMedia({ media: "screen", colorScheme: "dark" });
    await page.locator("html").evaluate((element) => element.setAttribute("data-theme", "light"));
    await expect(page.locator("body")).toHaveCSS("background-color", "rgb(250, 251, 249)");
    await page.locator("html").evaluate((element, choice) => {
      if (choice === null) element.removeAttribute("data-theme");
      else element.setAttribute("data-theme", choice);
    }, theme);
    await expect(page.locator("body")).toHaveCSS("background-color", "rgb(32, 34, 38)");
    await page.emulateMedia({ media: "print", colorScheme: "dark" });
    await expect(page.locator("body")).toHaveCSS("background-color", "rgb(250, 251, 249)");
    await expect(page.locator("body")).toHaveCSS("color", "rgb(32, 39, 43)");
  });
}
