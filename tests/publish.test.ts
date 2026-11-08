import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test, { type TestContext } from "node:test";

const fakeNpm = String.raw`#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
const args = process.argv.slice(2);
const state = process.env.PUBLISH_TEST_STATE;
const settings = JSON.parse(fs.readFileSync(path.join(state, "settings.json"), "utf8"));
fs.appendFileSync(path.join(state, "calls.jsonl"), JSON.stringify(args) + "\n");
const option = (name) => args[args.indexOf(name) + 1];
const integrity = "sha512-" + createHash("sha512").update("synthetic archive").digest("base64");
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
    console.log(JSON.stringify([{ filename, integrity }]));
    break;
  }
  case "publish":
    if (!args.includes("--dry-run")) {
      if (settings.publishFails) process.exit(7);
      fs.writeFileSync(path.join(state, "published"), "yes");
    }
    break;
  case "view":
    if (settings.registryPending || !fs.existsSync(path.join(state, "published"))) process.exit(1);
    console.log(args[2] === "dist.integrity"
      ? (settings.badIntegrity ? "sha512-other" : integrity)
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
  version?: string; user?: string; publishFails?: boolean; noTag?: boolean;
  badIntegrity?: boolean; registryPending?: boolean; node26?: boolean; noNode24?: boolean; scopeRegistry?: string;
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
  const quote = (value: string) => "'" + value.replaceAll("'", "'\\''") + "'";
  const realGit = execFileSync("/bin/sh", ["-c", "command -v git"], { encoding: "utf8" }).trim();
  const git = (...args: string[]) => execFileSync(realGit, [
    "-c", "user.name=Release Test", "-c", "user.email=release@example.invalid",
    "-c", "commit.gpgsign=false", "-c", "tag.gpgSign=false", ...args,
  ], { cwd: root, encoding: "utf8", stdio: "pipe" });
  git("init", "-q"); git("add", "."); git("commit", "-qm", "Synthetic release");
  if (!options.noTag) git("tag", "-a", `v${version}`, "-m", "Synthetic release tag");
  writeFileSync(join(root, "local-notes"), "not part of the versioned source");
  writeFileSync(join(mockBin, "git"), `#!/bin/sh\ncase "$1" in\n  rev-parse|show|cat-file|diff|archive|describe|status|show-ref) ;;\n  *) echo "$1" >> "$PUBLISH_TEST_STATE/git-writes"; exit 99 ;;\nesac\nexec ${quote(realGit)} "$@"\n`, { mode: 0o755 });
  if (options.node26 || options.noNode24) {
    const runtime = join(temp, "node24");
    mkdirSync(join(runtime, "bin"), { recursive: true });
    symlinkSync(process.execPath, join(runtime, "bin", "node"));
    writeFileSync(join(mockBin, "node"), `#!/bin/sh\nif [ "$1" = "-p" ] && [ "$2" = 'process.versions.node.split(".")[0]' ]; then echo 26; else exec ${quote(process.execPath)} "$@"; fi\n`, { mode: 0o755 });
    writeFileSync(join(mockBin, "brew"), options.noNode24
      ? "#!/bin/sh\nexit 1\n"
      : `#!/bin/sh\nprintf '%s\\n' ${quote(runtime)}\n`, { mode: 0o755 });
  }
  const calls = (): string[][] => {
    try { return readFileSync(join(state, "calls.jsonl"), "utf8").trim().split("\n").filter(Boolean).map((line) => JSON.parse(line)); }
    catch { return []; }
  };
  const run = (...args: string[]) => spawnSync("/bin/bash", [helper, ...args], {
    cwd: dirname(root), encoding: "utf8", timeout: 20_000,
    env: { ...process.env, PATH: `${mockBin}:${dirname(process.execPath)}:${process.env.PATH}`, PUBLISH_TEST_STATE: state },
  });
  return {
    root, calls, run,
    wroteGit: () => existsSync(join(state, "git-writes")),
    refs: () => git("show-ref"),
    seedPublication: () => {
      const release = join(root, "artifacts", "releases", version);
      mkdirSync(release, { recursive: true });
      writeFileSync(join(release, `sleetdrop-anthropic-readiness-${version}.tgz`), "synthetic archive");
      writeFileSync(join(state, "published"), "yes");
    },
  };
}

test("publish helper reads an existing version tag without changing Git refs", (t) => {
  const { root, run, calls, wroteGit, refs } = fixture(t);
  const before = refs();
  const result = run();
  assert.equal(result.status, 0, result.stderr);
  const commands = calls();
  assert.deepEqual(commands.filter((c) => c[0] === "run"), [["run", "check"]]);
  assert.equal(commands.filter((c) => c[0] === "login").length, 1);
  assert.notEqual(commands.find((c) => c[0] === "pack")?.[1], root);
  assert.equal(wroteGit(), false);
  assert.equal(refs(), before);
  const publishes = commands.filter((c) => c[0] === "publish");
  assert.equal(publishes.length, 1);
  assert.match(publishes[0]![1]!, /sleetdrop-anthropic-readiness-0\.1\.0\.tgz$/u);
  assert.ok(publishes[0]!.includes("public") && publishes[0]!.includes("latest"));
  assert.ok(!commands.some((c) => ["view", "exec"].includes(c[0]!)));
  for (const command of commands.filter((c) => ["ci", "login", "whoami", "publish", "view", "exec"].includes(c[0]!)))
    assert.ok(command.includes("https://registry.npmjs.org/"), command.join(" "));

  const verification = run("--verify-only");
  assert.equal(verification.status, 0, verification.stderr);
  const verificationCommands = calls().slice(commands.length);
  assert.ok(verificationCommands.some((c) => c[0] === "exec" && c.includes("@sleetdrop/anthropic-readiness@0.1.0")));
  assert.ok(!verificationCommands.some((c) => ["whoami", "login", "ci", "run", "pack", "publish"].includes(c[0]!)));
  assert.equal(wroteGit(), false);
  assert.equal(refs(), before);
});

test("successful publication does not query a registry that is still processing", (t) => {
  const { run, calls } = fixture(t, { registryPending: true });
  const result = run();
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Publication submitted/u);
  assert.match(result.stdout, /--verify-only/u);
  assert.ok(!/Published and verified|verification failed/u.test(result.stdout + result.stderr));
  assert.equal(calls().filter((c) => c[0] === "publish").length, 1);
  assert.ok(!calls().some((c) => ["view", "exec"].includes(c[0]!)));
});

test("missing tags and mismatched package inputs stop publication without creating tags", (t) => {
  for (const noTag of [true, false]) {
    const { root, run, calls, wroteGit, refs } = fixture(t, { noTag });
    if (!noTag) writeFileSync(join(root, "templates", "marker"), "changed");
    const before = refs();
    assert.notEqual(run().status, 0);
    assert.deepEqual(calls(), []);
    assert.equal(wroteGit(), false);
    assert.equal(refs(), before);
  }
});

test("publish dry-run skips sign-in, registry verification, and real publication", (t) => {
  const { run, calls } = fixture(t);
  const result = run("--dry-run");
  assert.equal(result.status, 0, result.stderr);
  assert.ok(calls().some((c) => c[0] === "publish" && c.includes("--dry-run")));
  assert.ok(!calls().some((c) => ["whoami", "login", "view", "exec"].includes(c[0]!)));
});

test("publish helper stops before npm actions when Node 24 is unavailable", (t) => {
  const { run, calls } = fixture(t, { noNode24: true });
  const result = run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Node 24 LTS is required/u);
  assert.deepEqual(calls(), []);
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

test("verify-only reports an integrity mismatch without publishing", (t) => {
  const { run, calls, seedPublication } = fixture(t, { badIntegrity: true });
  seedPublication();
  const result = run("--verify-only");
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Archive integrity mismatch/u);
  assert.ok(!calls().some((c) => ["whoami", "login", "publish"].includes(c[0]!)));
  assert.ok(!calls().some((c) => c[0] === "exec"));
});

test("verify-only reports unavailable metadata as pending without republishing", (t) => {
  const { run, calls, seedPublication } = fixture(t, { registryPending: true });
  seedPublication();
  const result = run("--verify-only");
  assert.equal(result.status, 2);
  assert.match(result.stdout, /Verification pending/u);
  assert.ok(!/error:|verification failed/u.test(result.stdout + result.stderr));
  assert.ok(!calls().some((c) => ["whoami", "login", "ci", "run", "pack", "publish", "exec"].includes(c[0]!)));
});

test("verification requires the saved archive and cannot be combined with dry-run", (t) => {
  const { run, calls } = fixture(t);
  const result = run("--verify-only");
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Saved publish archive is missing/u);
  assert.ok(!calls().some((c) => ["whoami", "login", "publish"].includes(c[0]!)));
  const before = calls().length;
  assert.equal(run("--verify-only", "--dry-run").status, 1);
  assert.equal(calls().length, before);
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
