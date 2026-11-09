# Anthropic Readiness

Create a local agent workbench for testing an Anthropic Messages API. The
endpoint may combine a model, inference server, and protocol adapter. The
agent runs selected checks and explains the results using saved requests and
responses. Protocol findings, task behavior, and actual client outcomes are
reported separately.

## Quick start

Use Node.js 22.18+ on the 22.x line, or 24.2+ on newer release lines, and an
agent that can read local files and run commands. Use the latest patch of a
maintained LTS release. Compatibility checks cover Node 22, 24, and 26;
newer stable major versions are accepted without an upper version limit.

```sh
npx @sleetdrop/anthropic-readiness init gateway-test
```

For an unpublished local change, use the
[local package workflow](docs/development.md#try-the-package-locally).

The command creates:

```text
gateway-test/
  AGENTS.md
  README.md
  target.json
  token.txt
  evidence/
  runs/
  .agents/skills/anthropic-readiness/
```

Fill in `target.json`:

```json
{
  "endpoint": "https://api.example.com/v1/messages",
  "model": "YOUR_MODEL",
  "apiVersion": "2023-06-01",
  "authMode": "api_key"
}
```

For `api_key` or `bearer` authentication, put the credential on one line in
`token.txt`. These local files and the evidence directories are ignored by
Git. Keep credentials and unredacted service logs out of shared reports.

Open the workbench in your agent. If it does not load `AGENTS.md`
automatically, ask it to read that file. For example:

> Assess this endpoint's Anthropic Messages implementation. Preview the full
> core suite, then run it with at most 27 requests within 10 minutes. Report
> protocol differences, task outcomes, supporting evidence, and untested scope.

The agent previews the plan before making requests. Each run uses a new
subdirectory under `runs/`.

## Agent support

The workbench uses local Markdown instructions, a bundled Skill, and Node
helpers. It does not require a particular agent framework or model provider.
Instruction discovery depends on the host's version and settings. See the
[Codex](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[OpenCode](https://opencode.ai/docs/instructions/), and
[Claude Code](https://code.claude.com/docs/en/memory#agentsmd) documentation.

The default Skill location is `.agents/skills/`. For Claude Code's Skill
layout, use `init gateway-test --claude-code`; it writes `.claude/skills/`
and updates the link in `AGENTS.md`.

## Checks and reports

The core suite has 22 cases and reserves up to 27 requests. Optional profiles
cover structured output, thinking, images, PDF input, citations, caching,
prefill, and API-version migration. Select them according to the assessment
scope and their prerequisites.

Each run retains `result.json`, an HTML check record, and request/response
captures. The agent can combine those records into an English assessment
with findings and evidence links. A passing check establishes only the rules
and behavior actually tested; it does not certify the whole API.

- [Connection and authentication](templates/skills/anthropic-readiness/references/connection.md)
- [Probe catalog and coverage limits](templates/skills/anthropic-readiness/references/probes.md)
- [Assessment reports](templates/skills/anthropic-readiness/references/reporting.md)
- [Offline exercise](docs/offline-exercise.md)

## Development

```sh
npm ci
npm run check
```

The check runs strict TypeScript validation and synthetic tests, including
packing the npm package and creating isolated workbenches. It does not call
real diagnostic endpoints.

See [development](docs/development.md), [architecture](docs/architecture.md),
[contributing](CONTRIBUTING.md), and [release instructions](docs/releasing.md).

## License

[MIT](LICENSE).
