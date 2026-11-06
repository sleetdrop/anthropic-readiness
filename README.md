# Anthropic Readiness

Anthropic Readiness generates a local project for diagnosing an Anthropic
Messages-compatible endpoint with your agent. The bundled Skill starts from
saved evidence, identifies the smallest reproducible protocol deviation,
and separates that finding from task or client behavior.

## Create a test project

Use Node 24 LTS. One project contains one target, the diagnostic helpers, and
the Anthropic Readiness Skill for your agent.

```sh
npx @sleetdrop/anthropic-readiness init gateway-test
```

Choose a new directory name in place of `gateway-test`. This registry command
requires a published package version. To try the current checkout before
publication, [pack it locally](docs/development.md#try-the-npm-package-locally).

Fill in the generated `target.json` with the endpoint, exact model name,
API version, and authentication mode. For authenticated targets, enter the
credential in the local `token.txt` file. Add any saved capture to
`evidence/` and open the directory in your agent.

The project puts the Skill in `.agents/skills/` by default. For Claude Code,
append `--claude-code` to generate it in `.claude/skills/`. For other agents,
load the generated Skill using their local discovery settings or point the
agent to its `SKILL.md`.

In chat, mention **Anthropic Messages** and the symptom, such as a stalled
**SSE stream** or a broken **tool continuation**. For example:

> Diagnose why this Anthropic Messages stream stalls. Inspect the saved
> `evidence/response.sse` offline. The capture is partial.

## Diagnose and report

For a live probe, authorize the configured target, a maximum request count,
and a total time limit. The agent previews the selected probes, executes
within those bounds, and stores the run under `runs/`. The
[connection guide](scaffold/skills/anthropic-readiness/references/connection.md)
describes the file format and the environment and explicit argument modes.

Try the [offline exercise](docs/offline-exercise.md)
to see the workflow on a known fault and a comparison sample. If the capture
leaves a specific question open, the
[preset probe guide](scaffold/skills/anthropic-readiness/references/probes.md)
describes the available request shapes and how to bound an authorized run.

For an assessment across one or more runs, the
[report guide](scaffold/skills/anthropic-readiness/references/reporting.md)
explains how the agent writes an English synthesis and uses the Skill's
renderer to generate HTML with evidence links and JSON viewers.

## Develop

The checkout contains the npm scaffold, its bundled Skill, and synthetic
tests. The standalone Python/Web application and container configuration
are retained in Git history at `8048934`.

For development, see [contributing](CONTRIBUTING.md) and
[local checks](docs/development.md). The [project intent](intends.md) defines
what a useful diagnosis should establish.
