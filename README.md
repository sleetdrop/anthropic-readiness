# Anthropic Readiness

Use this repository's Agent Skill to investigate concrete failures on
Anthropic Messages-compatible endpoints. It starts with saved evidence,
identifies the smallest reproducible protocol deviation, and separates that
finding from task or client behavior.

## Install in a Codex project

Use Node 24 LTS. The [Skill directory](skills/anthropic-readiness/) contains
the instructions, references, and helpers. The helpers use Node's built-in
libraries and run without an npm install.

From the root of the project where you want to use the Skill, set `SOURCE` to
the absolute path of this source repository and `REV` to the commit to install.
Extract that commit's Skill into a fresh project-local directory:

```sh
mkdir -p .agents/skills/anthropic-readiness
git -C "$SOURCE" archive "$REV:skills/anthropic-readiness" |
  tar -x -C .agents/skills/anthropic-readiness
```

Open a Codex chat in that project. Select `anthropic-readiness` and give it
the symptom and any saved response. For a manual check from the same project:

```sh
SKILL_DIR="$PWD/.agents/skills/anthropic-readiness"
node "$SKILL_DIR/scripts/src/cli/inspect.ts" \
  --file response.sse --format sse --capture partial
```

Use `--capture complete` when you have evidence the capture is complete.
The inspector reads JSON or server-sent events (SSE) offline.

## Diagnose and report

For a live endpoint, provide the agent with the endpoint URL, model name,
authentication mode, credential environment variable name, and an agreed
request/time limit. The [connection guide](skills/anthropic-readiness/references/connection.md)
covers remote API keys, Bearer tokens and unauthenticated local proxies.
Use `--use-env` to read `AR_DIAG_ENDPOINT_URL`, `AR_DIAG_MODEL`,
`AR_DIAG_AUTH_MODE`, `AR_DIAG_AUTH_TOKEN` and `AR_DIAG_API_VERSION`.
Command-line arguments override their corresponding values. Keep the token
in the local environment.

Try the [offline exercise](docs/offline-exercise.md)
to see the workflow on a known fault and a comparison sample. If the capture
leaves a specific question open, the
[preset probe guide](skills/anthropic-readiness/references/probes.md)
describes the available request shapes and how to bound an authorized run.

For an assessment across one or more runs, the
[report guide](skills/anthropic-readiness/references/reporting.md)
explains how the agent writes an English synthesis and uses the Skill's
renderer to generate HTML with evidence links and JSON viewers.

## Develop

The checkout contains the Skill and its synthetic test fixtures. The
standalone Python/Web application and container configuration are retained in
Git history at `8048934`.

For development, see [contributing](CONTRIBUTING.md) and
[local checks](docs/development.md). The [project intent](intends.md) defines
what a useful diagnosis should establish.
