import { test, expect } from "@playwright/test";
import {
  fixture,
  control,
  count,
  preview,
  start,
  choosePresentation,
  openIssue,
} from "./helpers.js";

test.beforeEach(async ({ request }) => control(request, "reset"));

test("locale and theme preserve reviewed execution plan, credentials and focused controls", async ({
  page,
  request,
}) => {
  await preview(page);
  await page.locator("#auth-mode").selectOption("api_key");
  await page.locator("#preview-button").click();
  await expect(page.locator("#start-button")).toBeEnabled();
  await page.locator("#credential").fill("synthetic-ephemeral");
  const original = await page.locator("#plan-preview").textContent();
  await choosePresentation(page, "locale", "en");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.locator("#start-button")).toBeEnabled();
  await expect(page.locator("#credential")).toHaveValue("synthetic-ephemeral");
  await expect(page.locator("#plan-preview")).not.toBeEmpty();
  expect(original).toBeTruthy();
  await expect(page.locator("#plan-preview")).toContainText("Frozen execution plan");
  await page.locator("#theme-choice").focus();
  await choosePresentation(page, "theme", "dark");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.locator("#theme-choice")).toBeFocused();
  expect((await count(request)).count).toBe(0);
  const storage = await page.evaluate(() => ({
    local: { ...localStorage },
    session: { ...sessionStorage },
  }));
  expect(storage.session).toEqual({});
  expect(Object.keys(storage.local)).toEqual(["anthropic-readiness.input-history.v1"]);
  expect(JSON.parse(storage.local["anthropic-readiness.input-history.v1"])).toEqual({
    version: 1,
    endpoints: [fixture().peer_url + "/v1/messages"],
    models: ["synthetic-pass"],
  });
  expect(JSON.stringify(storage)).not.toContain("synthetic-ephemeral");
});

test("tabs, selection, Back and refresh preserve canonical issue location", async ({ page }) => {
  await page.goto("/runs/" + fixture().completed_id);
  await page.locator('.view-tabs a[href*="view=issues"]').click();
  await expect(page.locator(".issues-table")).toBeVisible();
  const last = page.locator("[data-issue-key]").last();
  const key = await last.getAttribute("data-issue-key");
  await last.click();
  await expect(page).toHaveURL(new RegExp("issue=" + key));
  await page.locator('.view-tabs a[href*="view=cases"]').click();
  await expect(page).toHaveURL(/view=cases/u);
  await page.goBack();
  await expect(page.locator('[data-issue-key="' + key + '"]')).toHaveAttribute(
    "aria-current",
    "true",
  );
  await page.reload();
  await expect(page.locator('[data-issue-key="' + key + '"]')).toHaveAttribute(
    "aria-current",
    "true",
  );
});

test("theme switches preserve inspector nodes, disclosure state, evidence focus and result identity", async ({
  page,
  request,
}) => {
  const id = fixture().completed_id;
  await openIssue(page, id);
  const before = await (await page.request.get(`/api/v1/runs/${id}/workbench`)).json();
  const disclosure = page.locator("#issue-inspector details").last();
  await disclosure.locator("summary").click();
  const retained = await page.locator("#issue-inspector").elementHandle();
  await choosePresentation(page, "theme", "dark");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(disclosure).toHaveJSProperty("open", true);
  expect(
    await retained?.evaluate((node) => node === document.getElementById("issue-inspector")),
  ).toBe(true);
  const opener = page.locator("a[data-evidence-id]").first();
  await opener.focus();
  await opener.press("Enter");
  await expect(page.locator("#evidence-dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(opener).toBeFocused();
  const after = await (await page.request.get(`/api/v1/runs/${id}/workbench`)).json();
  expect(after.facts.source_result_sha256).toBe(before.facts.source_result_sha256);
  expect((await count(request)).count).toBe(0);
});

test("active observation reconnects and cancellation never creates another request", async ({
  page,
  request,
}) => {
  await preview(page, "synthetic-hold");
  await start(page);
  await expect.poll(async () => (await count(request)).count).toBe(1);
  await expect(page.locator("#worker-state")).toHaveAttribute("data-worker-state", "running");
  await choosePresentation(page, "locale", "en");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await page.evaluate(() => {
    window.dispatchEvent(new PageTransitionEvent("pagehide", { persisted: true }));
    window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
  });
  await expect(page.locator("#connection-state")).toContainText("Connected");
  expect((await count(request)).count).toBe(1);
  await page.locator("#cancel-run").click();
  await expect(page.locator("#job-state")).toHaveAttribute(
    "data-lifecycle",
    /cancelled|interrupted/u,
  );
  expect((await count(request)).count).toBe(1);
});

for (const locale of ["zh-CN", "en"]) {
  for (const viewport of [
    { width: 1280, height: 800 },
    { width: 1440, height: 900 },
    { width: 390, height: 844 },
    { width: 640, height: 400 },
  ]) {
    test(`paired theme geometry and unclipped overview: ${locale} ${viewport.width}`, async ({
      page,
    }, info) => {
      await page.setViewportSize(viewport);
      await page.goto("/runs/" + fixture().completed_id);
      await choosePresentation(page, "locale", locale);
      await expect(page.locator("html")).toHaveAttribute("lang", locale);
      await choosePresentation(page, "theme", "light");
      await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
      const boxes = await page
        .locator(".run-heading,.view-tabs,.issue-toolbar,.issues-table")
        .evaluateAll((nodes) =>
          nodes.map((node) => {
            const r = node.getBoundingClientRect();
            return [r.x, r.y, r.width, r.height];
          }),
        );
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
        true,
      );
      if (viewport.width >= 1280)
        expect(
          await page.evaluate(() => document.documentElement.scrollHeight),
        ).toBeLessThanOrEqual(viewport.height);
      await page.screenshot({
        path: info.outputPath(`${locale}-${viewport.width}-light.png`),
        fullPage: true,
      });
      await choosePresentation(page, "theme", "dark");
      await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
      const dark = await page
        .locator(".run-heading,.view-tabs,.issue-toolbar,.issues-table")
        .evaluateAll((nodes) =>
          nodes.map((node) => {
            const r = node.getBoundingClientRect();
            return [r.x, r.y, r.width, r.height];
          }),
        );
      for (let i = 0; i < boxes.length; i++)
        for (let j = 0; j < 4; j++)
          expect(Math.abs(boxes[i][j] - dark[i][j])).toBeLessThanOrEqual(1);
      await page.screenshot({
        path: info.outputPath(`${locale}-${viewport.width}-dark.png`),
        fullPage: true,
      });
    });
  }
}

test("new findings retain selected inspector, raw selection, disclosure and keyboard focus", async ({
  page,
}) => {
  await openIssue(page);
  const first = page.locator("[data-issue-key]").first();
  await first.click();
  await expect(first).toHaveAttribute("aria-current", "true");
  const chosen = await first.getAttribute("data-issue-key");
  const summary = page.locator("#issue-inspector details summary").last();
  await summary.click();
  await summary.focus();
  const result = await page.evaluate(async () => {
    const path = "/assets/web/workbench.js";
    const { patchElement } = await import(path);
    const root = document.getElementById("workbench");
    const inspector = document.getElementById("issue-inspector");
    const raw = inspector?.querySelector("pre");
    const range = document.createRange();
    if (raw?.firstChild) {
      range.selectNodeContents(raw.firstChild);
      getSelection()?.removeAllRanges();
      getSelection()?.addRange(range);
    }
    const selectedText = getSelection()?.toString();
    const incoming = root?.cloneNode(true);
    if (!(root instanceof Element) || !(incoming instanceof Element))
      throw new Error("missing_fixture");
    const list = incoming.querySelector(".view-tabs");
    const arrival = list?.firstElementChild?.cloneNode(true);
    if (arrival instanceof Element) {
      arrival.setAttribute("data-issue-key", "new-synthetic-arrival");
      arrival.removeAttribute("aria-current");
      list?.prepend(arrival);
    }
    patchElement(root, incoming);
    return {
      sameInspector: document.getElementById("issue-inspector") === inspector,
      sameSelection: getSelection()?.toString() === selectedText,
    };
  });
  expect(result).toEqual({ sameInspector: true, sameSelection: true });
  await expect(summary).toBeFocused();
  await expect(page.locator("#issue-inspector details").last()).toHaveJSProperty("open", true);
  await expect(page.locator(`[data-issue-key="${chosen}"]`)).toHaveAttribute(
    "aria-current",
    "true",
  );
});

test("system appearance follows OS while explicit override and cookie survive refresh", async ({
  page,
}) => {
  await page.goto("/runs/" + fixture().completed_id);
  await page.goto("/history");
  await choosePresentation(page, "theme", "system");
  await page.goto("/runs/" + fixture().completed_id);
  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page.locator("html")).toHaveCSS("background-color", "rgb(28, 28, 28)");
  await choosePresentation(page, "theme", "light");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.locator("html")).toHaveCSS("background-color", "rgb(252, 252, 252)");
  await choosePresentation(page, "locale", "en");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
});

test("presentation change invalidates reviewed export without changing execution", async ({
  page,
  request,
}) => {
  await page.goto("/runs/" + fixture().completed_id);
  await page.locator("#open-export").click();
  await page.locator("#preview-export").click();
  await expect(page.locator("#create-export")).toBeEnabled();
  await page.locator("#close-export").click();
  await choosePresentation(page, "locale", "en");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await page.locator("#open-export").click();
  await expect(page.locator("#create-export")).toBeDisabled();
  expect((await count(request)).count).toBe(0);
});

test("ordinary links work without scripts and partial evidence stays unavailable", async ({
  browser,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(`/runs/${fixture().partial_id}?view=cases`);
  await expect(page.locator(".source-notice").first()).toContainText("部分记录");
  await page.locator("[data-case-id]").last().click();
  await expect(page).toHaveURL(/view=cases&case=/u);
  await expect(page.locator("#case-inspector")).toContainText("尚无可核验的尝试记录");
  await page.locator('.view-tabs a[href*="view=activity"]').click();
  await expect(page.locator(".activity-summary")).toBeVisible();
  await context.close();
});

test("quiet empty issues and 96-row synthetic list keep primary navigation accessible", async ({
  page,
  request,
}) => {
  await preview(page);
  await start(page);
  await expect(page.locator("#job-state")).toHaveAttribute("data-lifecycle", "completed");
  await page.locator('.view-tabs a[href*="view=issues"]').click();
  await expect(page.locator(".issue-list")).toContainText("本次已评估检查未见异常");
  await page.locator('.view-tabs a[href*="view=cases"]').click();
  await expect(page.locator(".case-item")).toHaveCount(4);
  await page.evaluate(async () => {
    const path = "/assets/web/workbench.js";
    const { patchElement } = await import(path);
    const root = document.getElementById("workbench");
    const incoming = root?.cloneNode(true);
    if (!(root instanceof Element) || !(incoming instanceof Element))
      throw new Error("missing_fixture");
    const list = incoming.querySelector(".case-list");
    const sample = list?.firstElementChild;
    for (let i = 4; i < 96; i++) {
      const member = sample?.cloneNode(true);
      if (member instanceof Element) {
        member.setAttribute("data-case-id", "SYNTHETIC-SCALING-" + i);
        member.removeAttribute("aria-current");
        list?.append(member);
      }
    }
    patchElement(root, incoming);
  });
  await expect(page.locator(".case-item")).toHaveCount(96);
  expect(
    await page.locator(".case-list").evaluate((node) => node.scrollHeight > node.clientHeight),
  ).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.locator(".view-tabs")).toBeVisible();
  expect((await count(request)).count).toBe(4);
});

for (const theme of ["light", "dark"]) {
  test(`text, code, states and meaningful controls meet contrast: ${theme}`, async ({
    page,
  }, info) => {
    await openIssue(page);
    await choosePresentation(page, "theme", theme);
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
    const measurements = await page.evaluate(() => {
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
      /** @param {string} a @param {string} b */
      function contrast(a, b) {
        const x = luminance(rgb(a)),
          y = luminance(rgb(b));
        return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
      }
      const vars = getComputedStyle(document.documentElement);
      const read = (/** @type {string} */ key) => {
        const sample = document.createElement("span");
        sample.style.color = vars.getPropertyValue("--readiness-" + key);
        document.body.append(sample);
        const result = getComputedStyle(sample).color;
        sample.remove();
        return result;
      };
      return [
        ...["text", "muted", "pass", "fail", "waiting", "neutral"].map((fg) => ({
          pair: fg + "/page",
          actual: contrast(read(fg), read("page")),
          required: 4.5,
        })),
        ...["code-text", "code-key", "code-value"].map((fg) => ({
          pair: fg + "/code-surface",
          actual: contrast(read(fg), read("code-surface")),
          required: 4.5,
        })),
        ...["control-border", "focus", "accent"].map((fg) => ({
          pair: fg + "/page",
          actual: contrast(read(fg), read("page")),
          required: 3,
        })),
        {
          pair: "selected-state-edge",
          actual: contrast(read("accent"), read("selected")),
          required: 3,
        },
        {
          pair: "progress-fill/track",
          actual: contrast(read("progress-fill"), read("progress-track")),
          required: 3,
        },
      ];
    });
    await info.attach("contrast.json", {
      body: JSON.stringify(measurements, null, 2),
      contentType: "application/json",
    });
    for (const item of measurements)
      expect(item.actual, item.pair).toBeGreaterThanOrEqual(item.required);
  });
}

test("activity age advances locally without inventing new upstream activity", async ({
  page,
  request,
}) => {
  await page.clock.install();
  await page.goto("/runs/" + fixture().completed_id);
  await expect(page.locator("#connection-state")).toHaveText("观测已结束");
  const last = page.locator("#last-activity");
  const recorded = await last.getAttribute("title");
  const before = await last.textContent();
  await page.clock.fastForward(65000);
  await expect(last).not.toHaveText(before ?? "");
  await expect(last).toHaveAttribute("title", recorded ?? "");
  expect((await count(request)).count).toBe(0);
});

test("approved active composition uses actual two-checkpoint and three-request evidence", async ({
  browser,
  request,
}, info) => {
  const context = await browser.newContext({
    baseURL: `http://127.0.0.1:${process.env.READINESS_BROWSER_PORT ?? "18765"}`,
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1.24,
  });
  const page = await context.newPage();
  await preview(page, "synthetic-design");
  await start(page);
  await expect.poll(async () => (await count(request)).count).toBe(3);
  await expect(page.locator("#job-state")).toHaveAttribute("data-lifecycle", "running");
  await expect(page.locator("#case-progress")).toHaveText("2 / 4");
  await expect(page.locator("#request-progress")).toHaveText("3 / 4");
  await expect(page.locator("#active-phase")).toHaveText("正在等待响应头");
  expect(await page.evaluate(() => document.documentElement.scrollHeight)).toBeLessThanOrEqual(800);
  await expect(page.locator(".issues-table tbody tr")).toHaveCount(2);
  for (const theme of ["light", "dark"]) {
    await choosePresentation(page, "theme", theme);
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
    await expect(page.locator("#worker-state")).toHaveAttribute("data-worker-state", "running");
    await expect(page.locator("#connection-state")).toHaveText("已连接");
    await page.screenshot({ path: info.outputPath(`active-${theme}.png`), fullPage: true });
  }
  await page.locator('.view-tabs a[href*="view=issues"]').click();
  await page.locator("a[data-issue-key]").first().click();
  await expect(page.locator("#issue-inspector")).toContainText("stop_sequence");
  await page.screenshot({ path: info.outputPath("active-issue-dark.png"), fullPage: true });
  expect((await count(request)).count).toBe(3);
  await control(request, "release");
  await context.close();
});

test("saved appearance is present in initial HTML before scripts or styles", async ({
  browser,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false, colorScheme: "light" });
  const origin = `http://127.0.0.1:${process.env.READINESS_BROWSER_PORT ?? "18765"}`;
  await context.addCookies([
    {
      name: "readiness_preferences",
      value: "v1.en.dark",
      url: origin,
      httpOnly: true,
      sameSite: "Strict",
    },
  ]);
  const page = await context.newPage();
  const response = await page.goto(origin + "/runs/" + fixture().completed_id);
  expect(await response?.text()).toContain('<html lang="en" data-theme="dark">');
  await expect(page.locator("html")).toHaveCSS("background-color", "rgb(28, 28, 28)");
  await expect(page.locator(".view-tabs")).toContainText("Overview");
  await context.close();
});

test("long bilingual target names keep primary actions reachable", async ({
  page,
  request,
}, info) => {
  await preview(page);
  await page.locator("#target-name").fill("兼容性排查 / Compatibility investigation / ".repeat(4));
  await page.locator("#preview-button").click();
  await expect(page.locator("#start-button")).toBeEnabled();
  await start(page);
  await expect(page.locator("#job-state")).toHaveAttribute("data-lifecycle", "completed");
  for (const width of [1280, 390]) {
    await page.setViewportSize({ width, height: 800 });
    for (const locale of ["zh-CN", "en"]) {
      await choosePresentation(page, "locale", locale);
      await expect(page.locator("html")).toHaveAttribute("lang", locale);
      const action = await page.locator("#open-export").boundingBox();
      expect(action?.x).toBeGreaterThanOrEqual(0);
      expect((action?.x ?? 0) + (action?.width ?? 0)).toBeLessThanOrEqual(width);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
        true,
      );
      await page.screenshot({
        path: info.outputPath(`long-name-${locale}-${width}.png`),
        fullPage: true,
      });
    }
  }
  expect((await count(request)).count).toBe(4);
});

test("initial selected issue is pinned before later persisted findings can arrive", async ({
  page,
}) => {
  await openIssue(page);
  const key = await page.locator("[data-issue-key][aria-current]").getAttribute("data-issue-key");
  await expect(page).toHaveURL(new RegExp("issue=" + key));
});

test("keyboard filters expose an actual empty set without silently choosing a case", async ({
  page,
}) => {
  await page.goto(`/runs/${fixture().completed_id}?view=cases`);
  await page.locator("#case-filter").selectOption("PASS");
  await page.locator(".view-toolbar button").focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/filter=PASS/u);
  await expect(page.locator(".case-item")).toHaveCount(0);
  await expect(page.locator(".case-list")).toContainText("当前筛选下没有用例");
});

test("200 percent equivalent reflow keeps actions usable at 640 CSS pixels and density 2", async ({
  browser,
}, info) => {
  const context = await browser.newContext({
    viewport: { width: 640, height: 400 },
    deviceScaleFactor: 2,
  });
  const page = await context.newPage();
  const origin = `http://127.0.0.1:${process.env.READINESS_BROWSER_PORT ?? "18765"}`;
  await page.goto(origin + "/runs/" + fixture().completed_id);
  for (const locale of ["zh-CN", "en"]) {
    await choosePresentation(page, "locale", locale);
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
    for (const theme of ["light", "dark"]) {
      await choosePresentation(page, "theme", theme);
      await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
      expect(await page.evaluate(() => ({ width: innerWidth, density: devicePixelRatio }))).toEqual(
        { width: 640, density: 2 },
      );
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
        true,
      );
      await page.locator("#open-export").click();
      await expect(page.locator("#export-dialog")).toBeVisible();
      await page.locator("#close-export").click();
      await page.screenshot({
        path: info.outputPath(`zoom200-${locale}-${theme}.png`),
        fullPage: true,
      });
    }
  }
  await context.close();
});

test("matrix cell selects matching dimension members and Back restores the full list", async ({
  page,
}) => {
  await page.goto(`/runs/${fixture().completed_id}?view=cases`);
  const row = page.locator(".coverage-matrix tbody tr").filter({ hasText: "流式消息" });
  const link = row.locator("td").nth(1).getByRole("link", { name: "未通过 2", exact: true });
  await link.focus();
  await link.press("Enter");
  await expect(page).toHaveURL(/filter=matrix%3Astreaming%3Aprotocol%3AFAIL/u);
  await expect(page.locator(".case-item")).toHaveCount(2);
  await expect(page.locator("#case-filter")).toHaveValue("matrix:streaming:protocol:FAIL");
  await expect(page.locator("#case-inspector")).toContainText("ANT-TEXT-SSE-001");
  await page.goBack();
  await expect(page.locator(".case-item")).toHaveCount(4);
  await expect(page.locator("#case-filter")).toHaveValue("all");
});

test("paired inspector geometry and verified field composition", async ({ browser }, info) => {
  const context = await browser.newContext({
    baseURL: `http://127.0.0.1:${process.env.READINESS_BROWSER_PORT ?? "18765"}`,
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1.24,
  });
  const page = await context.newPage();
  await openIssue(page);
  const boxes = [];
  for (const theme of ["light", "dark"]) {
    await choosePresentation(page, "theme", theme);
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
    await expect(page.locator("#issue-inspector")).toContainText("stop_sequence");
    await page.evaluate(() => window.scrollTo(0, 0));
    boxes.push(
      await page.locator(".run-heading,.view-tabs,#issue-inspector").evaluateAll((nodes) =>
        nodes.map((node) => {
          const r = node.getBoundingClientRect();
          return [r.x, r.y, r.width, r.height];
        }),
      ),
    );
    await page.screenshot({ path: info.outputPath(`inspector-${theme}.png`), fullPage: true });
    await page
      .locator(".field-comparison")
      .screenshot({ path: info.outputPath(`fields-${theme}.png`) });
  }
  for (let i = 0; i < boxes[0].length; i++)
    for (let j = 0; j < 4; j++)
      expect(Math.abs(boxes[0][i][j] - boxes[1][i][j])).toBeLessThanOrEqual(1);
  await context.close();
});

test("issue inspector shows one selected case while retaining full affected scope", async ({
  page,
}) => {
  await openIssue(page);
  await expect(page.locator("#issue-inspector .field-comparison pre")).toHaveCount(2);
  await expect(page.locator("[data-observation-case]")).toHaveCount(4);
  await expect(page.locator("#issue-inspector header")).toContainText("影响 4 个不同用例");
  await page.locator('[data-observation-case="ANT-TEXT-SSE-001"]').click();
  await expect(page).toHaveURL(/case=ANT-TEXT-SSE-001/u);
  await expect(page.locator('[data-observation-case="ANT-TEXT-SSE-001"]')).toHaveAttribute(
    "aria-current",
    "true",
  );
  await expect(page.locator("#issue-inspector .field-comparison pre")).toHaveCount(2);
  await expect(page.locator("#issue-inspector .field-comparison")).toContainText("stop_reason");
  await expect(page.locator("#issue-inspector .observation-table a[data-evidence-id]")).toHaveCount(
    4,
  );
});

test("an unavailable evidence response is shown inside the active dialog", async ({ page }) => {
  await openIssue(page);
  await page.route(/\/api\/v1\/runs\/[^/]+\/evidence\//u, (route) =>
    route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({
        error: { code: "evidence_not_found", message: "synthetic unavailable source" },
      }),
    }),
  );
  await page.locator("a[data-evidence-id]").first().click();
  await expect(page.locator("#evidence-dialog")).toBeVisible();
  await expect(page.locator("#evidence-content")).toHaveText("证据不可用");
});

test("expired evidence reads recover once without resending model work", async ({
  page,
  request,
}) => {
  const initial = page.waitForResponse(
    (response) => response.url().endsWith("/workbench") && response.status() === 200,
  );
  await openIssue(page);
  await expect(page.locator("#connection-state")).toContainText("观测已结束");
  // Wait for the initial checked local read before expiring this session.
  await expect(page.locator("#workbench")).toHaveAttribute("data-read-only", "false");
  await initial;
  let reads = 0;
  page.on("request", (item) => {
    if (item.url().includes("/evidence/")) reads++;
  });
  await control(request, "expire");
  await page.locator("a[data-evidence-id]").first().click();
  await expect(page.locator("#evidence-content")).toContainText("stop_reason");
  expect(reads).toBe(2);
  expect((await count(request)).count).toBe(0);
});

test("terminal snapshot retries an unrendered generation after one HTML read failure", async ({
  page,
  request,
}) => {
  await preview(page, "synthetic-hold");
  let terminalSeen = false;
  let failedReads = 0;
  let recoveredReads = 0;
  await page.route("**/api/v1/runs/*/workbench*", async (route) => {
    // A running snapshot can be followed by completed HTML before the next poll.
    // Hold this read until the server itself returns the terminal generation so
    // the test actually exercises its intended failure and recovery path.
    /** @type {import('@playwright/test').APIResponse | undefined} */
    let terminalResponse;
    await expect
      .poll(async () => {
        const response = await route.fetch();
        const snapshot = await response.json();
        if (snapshot.job.state === "completed") terminalResponse = response;
        return snapshot.job.state;
      })
      .toBe("completed");
    if (!terminalResponse) throw new Error("terminal_snapshot_missing");
    terminalSeen = true;
    await route.fulfill({ response: terminalResponse });
  });
  await start(page);
  await expect.poll(async () => (await count(request)).count).toBe(1);
  const runPath = new URL(page.url()).pathname;
  await expect
    .poll(async () => {
      const response = await page.request.get(`/api/v1${runPath}/workbench`);
      expect(response.ok()).toBeTruthy();
      return (await response.json()).job.state;
    })
    .toBe("running");
  await page.route(
    (url) => url.pathname === runPath,
    async (route) => {
      if (route.request().resourceType() === "fetch" && terminalSeen) {
        if (failedReads === 0) {
          failedReads++;
          await route.fulfill({ status: 503, body: "synthetic transient HTML failure" });
          return;
        }
        recoveredReads++;
      }
      await route.continue();
    },
  );
  await control(request, "release");
  await expect.poll(() => failedReads).toBe(1);
  await expect(page.locator("#job-state")).toHaveAttribute("data-lifecycle", "completed", {
    timeout: 20000,
  });
  expect(recoveredReads).toBeGreaterThanOrEqual(1);
  expect((await count(request)).count).toBe(4);
  await page.locator('.view-tabs a[href*="view=cases"]').click();
  await expect(page.locator(".case-item")).toHaveCount(4);
  expect((await count(request)).count).toBe(4);
});
