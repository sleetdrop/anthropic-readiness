import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { fileURLToPath } from "node:url";

test("the OpenCode plugin registers the shared Skill and forwards the slash command", async () => {
  const root = new URL("../../", import.meta.url);
  const manifest = JSON.parse(await readFile(new URL("package.json", root), "utf8"));
  const { default: plugin } = await import(new URL(manifest.exports["."], root).href);
  const skills = [];
  const commands = [];
  const prompts = [];
  await plugin.setup({
    skill: { transform: (register) => register({ add: (skill) => skills.push(skill) }) },
    command: { transform: (register) => register({ add: (command) => commands.push(command) }) },
    session: { prompt: (prompt) => prompts.push(prompt) },
  });
  const skillFile = new URL("skills/anthropic-readiness/SKILL.md", root);
  assert.equal(skills.length, 1);
  assert.equal(skills[0].path, fileURLToPath(skillFile));
  assert.ok((await readFile(skillFile, "utf8")).endsWith(skills[0].content));
  assert.equal(commands.length, 1);
  assert.equal(commands[0].name, skills[0].id);

  const prompt = { text: "Inspect the saved SSE offline." };
  await commands[0].execute({ sessionID: "offline", prompt, delivery: "queue" });
  assert.deepEqual(prompts, [{
    sessionID: "offline",
    delivery: "queue",
    text: "Use the anthropic-readiness skill for this request.\n\nInspect the saved SSE offline.",
  }]);
});
