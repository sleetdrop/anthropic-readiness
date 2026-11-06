# Anthropic Readiness

Use this repository's Agent Skill to investigate concrete failures on
Anthropic Messages-compatible endpoints. It starts with saved evidence,
identifies the smallest reproducible protocol deviation, and separates that
finding from task or client behavior.

## Install

Use Node 24 LTS. The [Skill directory](skills/anthropic-readiness/) contains
the instructions, references, and helpers. The helpers use Node's built-in
libraries and run without an npm install.

Set `SOURCE` to the absolute path of a checkout at the revision you want to
use, and `REV` to that commit. For a plugin install, set `PLUGIN_DIR` to a
new absolute directory and extract the distributable files:

```sh
mkdir "$PLUGIN_DIR" &&
  git -C "$SOURCE" archive "$REV" -- plugin.json package.json .claude-plugin \
    integrations/opencode skills LICENSE |
  tar -x -C "$PLUGIN_DIR"
```

The plugins and standalone installation share the same Skill.

### Codex plugin

Add the local marketplace:

```sh
codex plugin marketplace add "$PLUGIN_DIR"
```

In the desktop Plugins Directory, select the local marketplace and install
`messages-readiness`. Open a chat in the project that holds your evidence and
select the plugin's `anthropic-readiness` Skill.

### Claude Code plugin

From the project that holds your evidence, load the plugin for one session:

```sh
claude --plugin-dir "$PLUGIN_DIR"
```

Use `/messages-readiness:anthropic-readiness` followed by the symptom and
evidence path.

### OpenCode 2 plugin

Add the plugin directory path to the `plugins` array in the consumer project's
`opencode.json` or `opencode.jsonc`:

```json
{
  "plugins": ["/absolute/path/to/messages-readiness-plugin"]
}
```

Open OpenCode in that project. Use `/anthropic-readiness` followed by the
symptom and evidence path.

### Standalone Skill

For other Skill-capable agents, put the complete
`skills/anthropic-readiness/` directory in a Skill location documented by
your agent. For example, a host that scans project-local `.agents/skills/`
can load this install:

```sh
mkdir -p .agents/skills/anthropic-readiness
git -C "$SOURCE" archive "$REV:skills/anthropic-readiness" |
  tar -x -C .agents/skills/anthropic-readiness
```

In chat, mention **Anthropic Messages** and a symptom such as a stalled
**SSE stream** or a broken **tool continuation**. Include a saved capture
when available. For example:

> Diagnose why this Anthropic Messages stream stalls. Inspect the saved
> `response.sse` offline. The capture is partial.

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
