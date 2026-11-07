import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test, { type TestContext } from "node:test";

const fakeNpm = String.raw`#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
const args = process.argv.slice(2);
const state = process.env.PUBLISH_TEST_STATE;
const settings = JSON.parse(fs.readFileSync(path.join(state, "settings.json"), "utf8"));
fs.appendFileSync(path.join(state, "calls.jsonl"), JSON.stringify(args) + "\n");
const option = (name) => args[args.indexOf(name) + 1];
switch (args[0]) {
  case "config": console.log(settings.scopeRegistry ?? "undefined"); break;
  case "ci": case "run": break;
  case "whoami":
    if (!fs.existsSync(path.join(state, "identity"))) process.exit(1);
    console.log(fs.readFileSync(path.join(state, "identity"), "utf8"));
    break;
  case "login": fs.writeFileSync(path.join(state, "identity"), "sleetdrop"); break;
  case "pack": {
    if (fs.readFileSync(path.join(args[1], "templates/marker"), "utf8") !== "tagged") process.exit(8);
    if (fs.existsSync(path.join(args[1], "local-notes"))) process.exit(9);
    const filename = "sleetdrop-anthropic-readiness-" + settings.version + ".tgz";
    fs.writeFileSync(path.join(option("--pack-destination"), filename), "synthetic archive");
    console.log(JSON.stringify([{ filename, integrity: "sha512-synthetic" }]));
    break;
  }
  case "publish":
    if (!args.includes("--dry-run")) {
      if (settings.publishFails) process.exit(7);
      fs.writeFileSync(path.join(state, "published"), "yes");
    }
    break;
  case "view":
    if (!fs.existsSync(path.join(state, "published"))) process.exit(1);
    console.log(args[2] === "dist.integrity"
      ? (settings.badIntegrity ? "sha512-other" : "sha512-synthetic")
      : settings.version);
    break;
  case "exec": {
    if (fs.existsSync(path.join(process.cwd(), "package.json"))) process.exit(11);
    const project = args.at(-1);
    fs.mkdirSync(path.join(project, ".agents/skills/anthropic-readiness"), { recursive: true });
    fs.writeFileSync(path.join(project, "AGENTS.md"), "Synthetic instructions");
    fs.writeFileSync(path.join(project, ".agents/skills/anthropic-readiness/SKILL.md"), "Synthetic Skill");
    break;
  }
  default: process.exit(10);
}
`;

function fixture(t: TestContext, options: {
  version?: string; user?: string; noTag?: boolean; publishFails?: boolean;
  badIntegrity?: boolean; node26?: boolean; scopeRegistry?: string;
} = {}) {
  const temp = mkdtempSync(join(tmpdir(), "readiness publish "));
  t.after(() => rmSync(temp, { recursive: true, force: true }));
  const root = join(temp, "project");
  const mockBin = join(temp, "mock-bin");
  const state = join(temp, "state");
  for (const directory of [join(root, "scripts"), join(root, "templates"), mockBin, state])
    mkdirSync(directory, { recursive: true });
  const helper = join(root, "scripts", "publish.sh");
  copyFileSync(new URL("../scripts/publish.sh", import.meta.url), helper);
  const version = options.version ?? "0.1.0";
  writeFileSync(join(root, "package.json"), JSON.stringify({ name: "@sleetdrop/anthropic-readiness", version }));
  writeFileSync(join(root, "templates", "marker"), "tagged");
  writeFileSync(join(state, "settings.json"), JSON.stringify({ ...options, version }));
  if (options.user) writeFileSync(join(state, "identity"), options.user);
  writeFileSync(join(mockBin, "npm"), fakeNpm, { mode: 0o755 });
  writeFileSync(join(mockBin, "sleep"), "#!/bin/sh\nexit 0\n", { mode: 0o755 });
  const git = (...args: string[]) => execFileSync("git", [
    "-c", "user.name=Release Test", "-c", "user.email=release@example.invalid",
    "-c", "commit.gpgsign=false", "-c", "tag.gpgSign=false", ...args,
  ], { cwd: root, stdio: "pipe" });
  git("init", "-q"); git("add", "."); git("commit", "-qm", "Synthetic release");
  if (!options.noTag) git("tag", "-a", `v${version}`, "-m", "Synthetic release tag");
  writeFileSync(join(root, "local-notes"), "not part of the tagged source");
  if (options.node26) {
    const runtime = join(temp, "node24");
    mkdirSync(join(runtime, "bin"), { recursive: true });
    symlinkSync(process.execPath, join(runtime, "bin", "node"));
    const quote = (value: string) => "'" + value.replaceAll("'", "'\\''") + "'";
    writeFileSync(join(mockBin, "node"), `#!/bin/sh\nif [ "$1" = "-p" ] && [ "$2" = 'process.versions.node.split(".")[0]' ]; then echo 26; else exec ${quote(process.execPath)} "$@"; fi\n`, { mode: 0o755 });
    writeFileSync(join(mockBin, "brew"), `#!/bin/sh\nprintf '%s\\n' ${quote(runtime)}\n`, { mode: 0o755 });
  }
  const calls = (): string[][] => {
    try { return readFileSync(join(state, "calls.jsonl"), "utf8").trim().split("\n").filter(Boolean).map((line) => JSON.parse(line)); }
    catch { return []; }
  };
  const run = (...args: string[]) => spawnSync("/bin/bash", [helper, ...args], {
    cwd: dirname(root), encoding: "utf8", timeout: 20_000,
    env: { ...process.env, PATH: `${mockBin}:${dirname(process.execPath)}:${process.env.PATH}`, PUBLISH_TEST_STATE: state },
  });
  return { root, calls, run };
}

test("publish helper checks, logs in, publishes the tagged archive, and verifies registry installation", (t) => {
  const { run, calls } = fixture(t);
  const result = run();
  assert.equal(result.status, 0, result.stderr);
  const commands = calls();
  assert.deepEqual(commands.filter((c) => c[0] === "run"), [["run", "check"]]);
  assert.equal(commands.filter((c) => c[0] === "login").length, 1);
  const publishes = commands.filter((c) => c[0] === "publish");
  assert.equal(publishes.length, 1);
  assert.match(publishes[0]![1]!, /sleetdrop-anthropic-readiness-0\.1\.0\.tgz$/u);
  assert.ok(publishes[0]!.includes("public") && publishes[0]!.includes("latest"));
  assert.ok(commands.some((c) => c[0] === "exec" && c.includes("@sleetdrop/anthropic-readiness@0.1.0")));
  for (const command of commands.filter((c) => ["ci", "login", "whoami", "publish", "view", "exec"].includes(c[0]!)))
    assert.ok(command.includes("https://registry.npmjs.org/"), command.join(" "));
});

test("publish dry-run skips sign-in, registry verification, and real publication", (t) => {
  const { run, calls } = fixture(t);
  const result = run("--dry-run");
  assert.equal(result.status, 0, result.stderr);
  assert.ok(calls().some((c) => c[0] === "publish" && c.includes("--dry-run")));
  assert.ok(!calls().some((c) => ["whoami", "login", "view", "exec"].includes(c[0]!)));
});

test("publish helper refuses missing tags and changed package inputs before npm actions", (t) => {
  for (const missing of [true, false]) {
    const { root, run, calls } = fixture(t, { noTag: missing });
    if (!missing) writeFileSync(join(root, "templates", "marker"), "changed");
    const result = run();
    assert.notEqual(result.status, 0);
    assert.deepEqual(calls(), []);
  }
});

test("publish helper refuses a different account and never retries a failed publish", (t) => {
  for (const options of [{ user: "someone-else" }, { user: "sleetdrop", publishFails: true }]) {
    const { run, calls } = fixture(t, options);
    const result = run();
    assert.notEqual(result.status, 0);
    assert.equal(calls().filter((c) => c[0] === "publish").length, options.publishFails ? 1 : 0);
    assert.ok(!calls().some((c) => c[0] === "exec"));
  }
});

test("prereleases use next and cannot move latest", (t) => {
  const { run, calls } = fixture(t, { version: "0.2.0-beta.1", user: "sleetdrop" });
  assert.equal(run("latest").status, 1);
  assert.deepEqual(calls(), []);
  const result = run();
  assert.equal(result.status, 0, result.stderr);
  assert.ok(calls().find((c) => c[0] === "publish")?.includes("next"));
});

test("registry integrity mismatch fails verification without repeating publication", (t) => {
  const { run, calls } = fixture(t, { user: "sleetdrop", badIntegrity: true });
  const result = run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /may have succeeded/u);
  assert.equal(calls().filter((c) => c[0] === "publish").length, 1);
  assert.ok(!calls().some((c) => c[0] === "exec"));
});

test("publish helper can select an installed Homebrew Node 24", (t) => {
  const { run } = fixture(t, { node26: true });
  const result = run("--dry-run");
  assert.equal(result.status, 0, result.stderr);
});

test("a scoped registry cannot redirect the release away from npmjs.org", (t) => {
  const { run, calls } = fixture(t, { scopeRegistry: "https://mirror.example.invalid/" });
  const result = run();
  assert.notEqual(result.status, 0);
  assert.ok(!calls().some((c) => ["whoami", "login", "publish"].includes(c[0]!)));
});
