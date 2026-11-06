# Anthropic Readiness

Create a local project for diagnosing an Anthropic Messages-compatible endpoint
with an agent. Use Node 24 LTS.

```sh
npx @sleetdrop/anthropic-readiness init gateway-test
```

The command creates a new directory with a target configuration template,
an empty local credential file, and the bundled `anthropic-readiness` Skill.
Use `--claude-code` to generate the Skill in Claude Code's project directory.
Fill in the target and open the generated project in your agent. Its README
describes how to provide evidence and authorize a bounded live probe.
