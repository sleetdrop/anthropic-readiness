import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const skillName = "anthropic-readiness";
const skill = new URL("../../skills/anthropic-readiness/SKILL.md", import.meta.url);

export default {
  id: "messages-readiness",
  async setup(ctx) {
    const source = await readFile(skill, "utf8");
    const frontmatter = /^---\r?\n([\s\S]*?)\r?\n---\r?\n/u.exec(source);
    const description = frontmatter?.[1].match(/^description: (.+)$/mu)?.[1];
    if (!frontmatter || !description) throw new Error("Missing Anthropic Readiness skill description");

    await ctx.skill.transform((editor) => {
      editor.add({
        id: skillName,
        name: skillName,
        description,
        path: fileURLToPath(skill),
        content: source.slice(frontmatter[0].length),
      });
    });
    await ctx.command.transform((editor) => {
      editor.add({
        name: skillName,
        description,
        async execute({ sessionID, prompt, delivery }) {
          await ctx.session.prompt({
            ...prompt,
            sessionID,
            delivery,
            text: `Use the ${skillName} skill for this request.\n\n${prompt.text ?? ""}`,
          });
        },
      });
    });
  },
};
