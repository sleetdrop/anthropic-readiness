#!/usr/bin/env node
import { copyFile, cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { parseArgs } from "node:util";

const usage = "Usage: npx @sleetdrop/anthropic-readiness init <directory> [--claude-code]";
const skillSource = new URL("../templates/skills/anthropic-readiness/", import.meta.url);
const readmeSource = new URL("../templates/README.md", import.meta.url);
const agentsSource = new URL("../templates/AGENTS.md", import.meta.url);
const target = { endpoint: "", model: "", apiVersion: "2023-06-01", authMode: "api_key" };

async function main() {
  const { positionals, values } = parseArgs({
    allowPositionals: true,
    options: { help: { type: "boolean", short: "h" }, "claude-code": { type: "boolean" } },
  });
  if (values.help || positionals.length === 0) {
    console.log(usage);
    return;
  }
  const [command, directory] = positionals;
  if (command !== "init" || !directory || positionals.length !== 2) throw new Error(usage);
  if (process.versions.node.split(".")[0] !== "24") throw new Error("Use Node 24 LTS.");

  const root = resolve(directory);
  try {
    await mkdir(root, { mode: 0o700 });
  } catch (error) {
    if (error?.code === "EEXIST") throw new Error("Choose a new directory. The target already exists.");
    if (error?.code === "ENOENT") throw new Error("Create the parent directory first.");
    throw error;
  }
  const skillPath = join(values["claude-code"] ? ".claude" : ".agents", "skills", "anthropic-readiness");
  try {
    await writeFile(join(root, ".gitignore"), "/target.json\n/token.txt\n/evidence/\n/runs/\n", { flag: "wx" });
    await writeFile(join(root, "target.json"), JSON.stringify(target, null, 2) + "\n", { flag: "wx", mode: 0o600 });
    await writeFile(join(root, "token.txt"), "", { flag: "wx", mode: 0o600 });
    await mkdir(join(root, "evidence"), { mode: 0o700 });
    await mkdir(join(root, "runs"), { mode: 0o700 });
    await copyFile(readmeSource, join(root, "README.md"));
    await cp(skillSource, join(root, skillPath), { recursive: true, errorOnExist: true, force: false });
    const guidance = (await readFile(agentsSource, "utf8"))
      .replaceAll("{{SKILL_PATH}}", skillPath.replaceAll("\\", "/"));
    await writeFile(join(root, "AGENTS.md"), guidance, { flag: "wx" });
  } catch (error) {
    await rm(root, { recursive: true, force: true });
    throw error;
  }
  console.log(`Created ${root}\nSkill: ${skillPath}\nFill target.json and follow README.md.`);
}

try {
  await main();
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
