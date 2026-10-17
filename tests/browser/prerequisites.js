import { readFileSync } from "node:fs";
const suite = process.argv[2];
try {
  const locked = JSON.parse(readFileSync("docs/harness/web-toolchain.json", "utf8"));
  if (process.versions.node !== locked.node_version) throw new Error("locked_node_missing");
  const { chromium } = await import("@playwright/test");
  if (suite === "browser") {
    const browser = await chromium.launch();
    try {
      if (browser.version() !== locked.selected_browsers[0].browser_version)
        throw new Error("locked_chromium_missing");
    } finally {
      await browser.close();
    }
  }
} catch {
  process.stderr.write(
    "Locked frontend prerequisites unavailable; prepare Node/npm/Chromium first.\n",
  );
  process.exitCode = 2;
}
