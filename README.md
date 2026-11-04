# Anthropic Incident Diagnosis

Use this repository's Agent Skill to investigate concrete failures on
Anthropic Messages-compatible endpoints. It starts with saved evidence,
identifies the smallest reproducible protocol deviation, and separates that
finding from task or client behavior.

Open this checkout in your agent and point it to the
[Skill instructions](skills/anthropic-incident-diagnosis/SKILL.md) and the
captured response. The local inspector runs with Node 24 and reads JSON or
server-sent events (SSE) without contacting the endpoint.

Try the [offline exercise](skills/anthropic-incident-diagnosis/references/offline-exercise.md)
to see the workflow on a known fault and a comparison sample. If the capture
leaves a specific question open, the [preset probe guide](docs/probes.md)
describes the available request shapes and how to bound an authorized run.

For development, see [contributing](CONTRIBUTING.md) and
[local checks](docs/development.md). The [project intent](intends.md) defines
what a useful diagnosis should establish.
