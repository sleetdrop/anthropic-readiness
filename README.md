# Anthropic Readiness

An evidence-led, black-box CLI for a scoped subset of Anthropic Messages.
It records observed behavior, required-case coverage and uncertainty. It cannot
infer an endpoint's internals or certify an untested client workflow.

Stage A contains four versioned cases: non-stream text, a streamed greeting,
a streamed count from 1 to 5, and a forced non-stream tool call with schema
validation. The `anthropic-basic` profile runs three cases;
`anthropic-tools-smoke` runs one. The bundled contract is Messages `2023-06-01`, revision
`1.0.0`, with no beta headers. Tool loops, version matrices, Claude Code client
tests and protocol-maintenance commands belong to later stages.

## Start without a real endpoint

Use the checked-in [Dev Container](.devcontainer/devcontainer.json), then:

```sh
uv sync --locked
UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite fast
uv run --frozen anthropic-readiness validate --target examples/target.yaml
uv run --frozen anthropic-readiness run --target examples/target.yaml --dry-run
uv run --frozen anthropic-readiness replay --target examples/target.yaml \
  --capture tests/fixtures/captures/valid/evidence/ANT-TEXT-SSE-001/fixture-attempt/response.json \
  --case ANT-TEXT-SSE-001 --out artifacts/replay-example
```

Replay is synthetic evidence, not an endpoint result. Each run writes structured
`result.json`, a restrained Chinese `report.html`, `report.md` and an evidence
manifest. Reports include assertion versions, scope, references and an offline
reader guide for humans and Agents. [Architecture](docs/architecture.md) explains
the trust boundaries.

For a real target, copy the example outside the repository, supply its named
credential environment variable and explicitly select `--allow-live`. Review the
dry-run's selected cases and finite request/time budget first. Never commit
private configuration or original service logs. Exit codes: 0 pass, 1 observed
failure, 2 invalid input, 3 incomplete/blocked, 4 internal error, 130/143 signal.

See [container usage](docs/container-usage.md), [development](docs/development.md)
and [contribution guide](CONTRIBUTING.md). The source is intended for a personal
GitHub repository; remote CI and registry publishing are not performed by local
checks. Choose an appropriate license before public distribution; no license has
been selected on the owner's behalf.
