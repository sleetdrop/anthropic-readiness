import assert from "node:assert/strict";
import { execFile, spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

test("the packed initializer creates an isolated project that can run a bounded probe", async (t) => {
  const root = mkdtempSync(join(tmpdir(), "readiness scaffold "));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const npmCli = process.env.npm_execpath;
  const npm = (args: string[]) =>
    spawnSync(npmCli ? process.execPath : "npm", npmCli ? [npmCli, ...args] : args, {
      cwd: root,
      encoding: "utf8",
      env: { ...process.env, npm_config_cache: join(root, "cache"), npm_config_engine_strict: "true" },
      timeout: 15_000,
    });
  const packageRoot = fileURLToPath(new URL("../", import.meta.url));
  const packed = npm(["pack", packageRoot, "--offline", "--json"]);
  assert.equal(packed.status, 0, packed.stderr);
  const [pkg] = JSON.parse(packed.stdout);
  assert.equal(pkg.name, "@sleetdrop/anthropic-readiness");
  assert.ok(pkg.files.some((item: { path: string }) => item.path === "templates/skills/anthropic-readiness/SKILL.md"));
  assert.ok(pkg.files.some((item: { path: string }) => item.path === "templates/AGENTS.md"));
  assert.ok(!pkg.files.some((item: { path: string }) => /(?:^|\/)(?:token\.txt|target\.json|runs|evidence)(?:\/|$)/u.test(item.path)));

  const init = (...args: string[]) => npm([
    "exec", "--offline", "--yes", "--package", join(root, pkg.filename),
    "--", "anthropic-readiness", "init", ...args,
  ]);
  const created = init("gateway test");
  assert.equal(created.status, 0, created.stderr);
  const project = join(root, "gateway test");
  const skill = join(project, ".agents", "skills", "anthropic-readiness");
  assert.ok(existsSync(join(skill, "SKILL.md")));
  assert.equal(readFileSync(join(project, "token.txt"), "utf8"), "");
  assert.equal(readFileSync(join(project, ".gitignore"), "utf8"), "/target.json\n/token.txt\n/evidence/\n/runs/\n");
  const claude = init("claude-project", "--claude-code");
  assert.equal(claude.status, 0, claude.stderr);
  assert.ok(existsSync(join(root, "claude-project", ".claude", "skills", "anthropic-readiness", "SKILL.md")));

  for (const [directory, skillDirectory] of [
    [project, skill],
    [join(root, "claude-project"), join(root, "claude-project", ".claude", "skills", "anthropic-readiness")],
  ] as const) {
    const guidance = readFileSync(join(directory, "AGENTS.md"), "utf8");
    const links = [...guidance.matchAll(/\]\(([^)]+)\)/gu)].map((match) => match[1]!);
    assert.ok(links.some((link) => resolve(directory, link) === join(skillDirectory, "SKILL.md")));
    for (const link of links) assert.ok(existsSync(resolve(directory, link)), link);
  }

  const response = JSON.parse(readFileSync(
    new URL("./fixtures/contracts/core-1.0.0/message-valid-tool.json", import.meta.url),
    "utf8",
  ));
  response.content[0].input = { city: "Hanoi" };
  const requests: { path: string | undefined; authorization: string | undefined }[] = [];
  const server = createServer((req, res) => {
    requests.push({ path: req.url, authorization: req.headers.authorization });
    req.resume();
    res.writeHead(200, { "Content-Type": "application/json" }).end(JSON.stringify(response));
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  t.after(() => { server.closeAllConnections(); server.close(); });
  const address = server.address();
  assert.ok(address && typeof address === "object");
  const targetFile = join(project, "target.json");
  const target = JSON.stringify({
    endpoint: `http://127.0.0.1:${address.port}/v1`,
    model: response.model,
    apiVersion: "2023-06-01",
    authMode: "bearer",
  });
  writeFileSync(targetFile, target);
  assert.notEqual(init("gateway test").status, 0);
  assert.equal(readFileSync(targetFile, "utf8"), target);

  const exec = promisify(execFile);
  const run = (command: string, extra: string[] = []) =>
    exec(process.execPath, [
      join(skill, "scripts", "src", "cli", "main.ts"), command,
      "--target-dir", ".", "--profile", "anthropic-tools-smoke",
      "--max-requests", "1", "--run-ms", "3000", ...extra,
    ], { cwd: project, timeout: 5000 });
  const plan = await run("plan");
  assert.equal(JSON.parse(plan.stdout).plannedRequests, 1);
  assert.equal(requests.length, 0);

  const token = "synthetic-scaffold-token";
  writeFileSync(join(project, "token.txt"), token + "\n");
  const result = await run("run", ["--allow-live", "--out", "runs/first"]);
  assert.match(result.stdout, /PASS/u);
  assert.deepEqual(requests, [{ path: "/v1/messages", authorization: `Bearer ${token}` }]);
  const output = join(project, "runs", "first");
  assert.equal(JSON.parse(readFileSync(join(output, "result.json"), "utf8")).attemptsStarted, 1);
  for (const name of readdirSync(output)) assert.ok(!readFileSync(join(output, name), "utf8").includes(token));
});
