# Anthropic Incident Diagnosis

Use this repository's Agent Skill to investigate concrete failures on
Anthropic Messages-compatible endpoints. It starts with saved evidence,
identifies the smallest reproducible protocol deviation, and separates that
finding from task or client behavior.

Open this checkout in your agent and point it to the
[Skill instructions](skills/anthropic-incident-diagnosis/SKILL.md) and the
captured response. Use Node 24. Run the helpers from the checkout root.
The runtime uses Node's built-in libraries. Development checks require
`npm --prefix next ci`.

For a live endpoint, provide the agent with the endpoint URL, model name,
authentication mode, credential environment variable name, and an agreed
request/time limit. The [connection guide](skills/anthropic-incident-diagnosis/references/connection.md)
covers remote API keys, Bearer tokens and unauthenticated local proxies.
Keep the token value in the local environment.

For a saved response, the offline inspector reads JSON or server-sent events
(SSE) without contacting the endpoint.

Try the [offline exercise](skills/anthropic-incident-diagnosis/references/offline-exercise.md)
to see the workflow on a known fault and a comparison sample. If the capture
leaves a specific question open, the [preset probe guide](docs/probes.md)
describes the available request shapes and how to bound an authorized run.

For an assessment across one or more runs, the
[report guide](skills/anthropic-incident-diagnosis/references/reporting.md)
explains how the agent writes an English synthesis and uses the Skill's
renderer to generate HTML with evidence links and JSON viewers.

The current checkout contains the diagnosis Skill, Node helpers and synthetic
fixtures. The standalone Python/Web application and container configuration
are retained in Git history at `8048934`.

For development, see [contributing](CONTRIBUTING.md) and
[local checks](docs/development.md). The [project intent](intends.md) defines
what a useful diagnosis should establish.
