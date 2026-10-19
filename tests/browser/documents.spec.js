import { test, expect } from "@playwright/test";
import { pathToFileURL } from "node:url";
import { fixture } from "./helpers.js";

for (const locale of ["zh-CN", "en"]) {
  for (const theme of ["light", "dark", "system"]) {
    for (const scripts of [false, true]) {
      test(`standalone document ${locale} ${theme} scripts=${scripts}`, async ({
        browser,
      }, info) => {
        const context = await browser.newContext({
          javaScriptEnabled: scripts,
          viewport: { width: 1280, height: 900 },
          colorScheme: "dark",
        });
        const page = await context.newPage();
        /** @type {string[]} */ const requests = [];
        /** @type {string[]} */ const errors = [];
        page.on("pageerror", (error) => errors.push(error.message));
        page.on("console", (message) => {
          if (message.type() === "error") errors.push(message.text());
        });
        await context.route(/https?:\/\//u, (route) => {
          requests.push(route.request().url());
          return route.abort();
        });
        await page.goto(pathToFileURL(fixture().document_paths[`${locale}-${theme}`]).href);
        await expect(page.locator("html")).toHaveAttribute("lang", locale);
        await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
        await expect(page.locator("#conclusion")).toBeVisible();
        await expect(page.locator("#coverage-matrix tbody tr")).toHaveCount(3);
        await expect(page.locator("#findings article")).toHaveCount(2);
        await expect(page.locator("#evidence")).toContainText("Anthropic");
        await expect(page.locator("#scope")).toContainText(
          locale === "en" ? "Passing / assessed" : "通过 / 已评估",
        );
        await expect(page.locator("#coverage-matrix")).not.toContainText("not_evaluated");
        const original = await page.locator("#document-data").textContent();
        const controls = page.locator(".document-controls");
        if (scripts) {
          await expect(controls).toBeVisible();
          await page.locator("#document-language").selectOption(locale === "en" ? "zh-CN" : "en");
          await expect(page.locator("html")).toHaveAttribute(
            "lang",
            locale === "en" ? "zh-CN" : "en",
          );
          await expect(page.locator("#scope")).toContainText(
            locale === "en" ? "通过 / 已评估" : "Passing / assessed",
          );
          await expect(page.locator('#document-theme option[value="system"]')).toHaveText(
            locale === "en" ? "跟随系统" : "System",
          );
          await page.locator("#document-theme").selectOption("dark");
          await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
          expect(
            await page.evaluate(() => ({
              local: localStorage.length,
              session: sessionStorage.length,
            })),
          ).toEqual({ local: 0, session: 0 });
        } else await expect(controls).toBeHidden();
        expect(await page.locator("#document-data").textContent()).toBe(original);
        await page.screenshot({ path: info.outputPath("screen.png"), fullPage: true });
        const selectedLanguage = await page.locator("html").getAttribute("lang");
        await page.emulateMedia({ media: "print" });
        expect(
          await page.locator("body").evaluate((node) => getComputedStyle(node).backgroundColor),
        ).toBe("rgb(250, 251, 249)");
        await expect(page.locator("html")).toHaveAttribute("lang", selectedLanguage || locale);
        await expect(controls).toBeHidden();
        await expect(page.locator("#findings article").first()).toBeVisible();
        await page.pdf({ path: info.outputPath("print.pdf"), format: "A4", printBackground: true });
        expect(requests).toEqual([]);
        expect(errors).toEqual([]);
        await context.close();
      });
    }
  }
}

for (const locale of ["zh-CN", "en"]) {
  for (const theme of ["light", "dark"]) {
    test(`document narrow tables and semantic contrast ${locale} ${theme}`, async ({
      browser,
    }, info) => {
      const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
      const page = await context.newPage();
      await page.goto(pathToFileURL(fixture().document_paths[`${locale}-${theme}`]).href);
      await info.attach("overflow.json", {
        body: JSON.stringify(
          await page.evaluate(() =>
            Array.from(document.querySelectorAll("body *"))
              .filter(
                (node) => !node.closest(".table-scroll") && node.scrollWidth > node.clientWidth + 1,
              )
              .map((node) => ({
                tag: node.tagName,
                id: node.id,
                class: node.className,
                width: node.clientWidth,
                content: node.scrollWidth,
              })),
          ),
          null,
          2,
        ),
        contentType: "application/json",
      });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
        true,
      );
      const matrix = page.locator("#coverage-matrix").locator("..");
      expect(await matrix.evaluate((node) => node.scrollWidth > node.clientWidth)).toBe(true);
      await matrix.focus();
      await matrix.press("ArrowRight");
      await expect.poll(() => matrix.evaluate((node) => node.scrollLeft)).toBeGreaterThan(0);
      const pairs = await page.evaluate(() => {
        /** @param {string} value */
        function rgb(value) {
          return (value.match(/[\d.]+/gu) ?? []).slice(0, 3).map(Number);
        }
        /** @param {number[]} value */
        function luminance(value) {
          return value
            .map((n) => {
              n /= 255;
              return n <= 0.04045 ? n / 12.92 : ((n + 0.055) / 1.055) ** 2.4;
            })
            .reduce((sum, n, i) => sum + n * [0.2126, 0.7152, 0.0722][i], 0);
        }
        /** @param {string} role */
        function color(role) {
          const node = document.createElement("span");
          node.style.color = `var(--readiness-${role})`;
          document.body.append(node);
          const value = getComputedStyle(node).color;
          node.remove();
          return luminance(rgb(value));
        }
        return [
          ...["text", "muted", "pass", "fail", "waiting"].map((fg) => ({
            fg,
            bg: "page",
            required: 4.5,
          })),
          { fg: "code-text", bg: "code-surface", required: 4.5 },
          ...["control-border", "focus"].map((fg) => ({ fg, bg: "page", required: 3 })),
          { fg: "progress-fill", bg: "progress-track", required: 3 },
        ].map((pair) => {
          const a = color(pair.fg),
            b = color(pair.bg);
          return { ...pair, actual: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) };
        });
      });
      for (const pair of pairs)
        expect(pair.actual, `${pair.fg}/${pair.bg}`).toBeGreaterThanOrEqual(pair.required);
      await info.attach("contrast.json", {
        body: JSON.stringify(pairs, null, 2),
        contentType: "application/json",
      });
      await page.screenshot({ path: info.outputPath("narrow.png"), fullPage: true });
      await context.close();
    });
  }
}
