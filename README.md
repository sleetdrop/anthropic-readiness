# Anthropic Readiness

Anthropic Readiness generates a local agent workbench for assessing the
Anthropic Messages API exposed by your combination of model, inference software, and
API conversion software. Your agent selects tests, reviews retained evidence,
and reports protocol differences and coverage gaps alongside task outcomes.
It can also investigate individual failures using saved captures.

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

The workbench includes `AGENTS.md` with its purpose, file layout, and a link
to the bundled Skill. Agents that load `AGENTS.md` can use that entry point;
otherwise, ask your agent to read it explicitly. The agent needs file access
and Node 24 execution, with no dependency on a particular agent framework.
Instruction discovery follows the host's version and settings; see the
official [Codex](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[OpenCode](https://opencode.ai/docs/instructions/), and
[Claude Code](https://code.claude.com/docs/en/memory#agentsmd) documentation.

The project puts the Skill in `.agents/skills/` by default. For Claude Code,
append `--claude-code` to generate it in `.claude/skills/`. For other agents,
load the generated Skill using their local discovery settings or point the
agent to its `SKILL.md`.

In chat, ask for an **Anthropic Messages** protocol assessment. Include known
inference and conversion software versions so the report can identify the
tested combination. For example:

> Assess the configured endpoint's Anthropic Messages implementation. Preview
> the full core suite, then run it with at most 27 requests within 10 minutes.
> Report protocol differences, task outcomes, evidence, and untested scope.

For an individual failure, provide the symptom and saved evidence:

> Diagnose why this Anthropic Messages stream stalls. Inspect the saved
> `evidence/response.sse` offline. The capture is partial.

## Assess and report

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

The core suite contains 22 cases with a maximum of 27 requests. Select
additional capability profiles according to the assessment scope and their
prerequisites. A compatibility assessment records the tested API version and
the checks actually completed; it does not establish complete conformance
from a partial run.

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
what an assessment and a focused diagnosis should establish.
