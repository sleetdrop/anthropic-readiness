# Anthropic Readiness

A local Web console and independent CLI for black-box checks of a scoped subset
of Anthropic Messages. Preview a fixed plan, explicitly start it, observe real
progress, and inspect or export the evidence-led report. Execution completion and
protocol compatibility are separate outcomes; untested capabilities stay untested.

The installed scope is four versioned cases: non-stream text, a streamed greeting,
a streamed count from 1 to 5, and a forced non-stream tool call. `anthropic-basic`
runs three cases; `anthropic-tools-smoke` runs one. The sole bundled contract is
Messages `2023-06-01`, revision `1.0.0`, without betas. Tool loops, version matrices,
Claude Code workflows and protocol-update Agent commands belong to later stages.
The API date alone does not prove client pinning semantics or workflow stability.

## Local Web console

From this checkout with Docker Compose:

```sh
docker compose up --build -d
```

Open [http://localhost:8765](http://localhost:8765). The published port binds only
to this computer. Enter the endpoint and exact model, review the installed cases
and request/time limits, then choose **Preview** and **Start**. Configuration and
preview send no model request. Start is the explicit live opt-in.

A base URL helper accepts an origin or `/v1`; a complete Messages URL is also
supported. Container `127.0.0.1` means the container itself. Docker Desktop users
can explicitly choose `host.docker.internal` for a host proxy; Linux host routing
is described in [container usage](docs/container-usage.md). Addresses are never
silently substituted.

Closing or refreshing the page only ends observation. Use **Cancel** to stop a
job, and reopen it from history to read saved progress. The service executes one
job at a time with eight waiting slots. Presets omit secrets; browser credentials
are submitted only at start and held in task memory. Restarted services retain
records but never resume or automatically resend an interrupted assessment.

Web reports are generated on demand. Export selected HTML, Markdown or JSON, or a
ZIP with a file/hash manifest and optional sanitized evidence. Standalone HTML
contains its own styles, figures and data tables and works offline; it does not
embed capture files. Report-only and partial exports explain their limitations.
Check business content before sharing captures. Hashes establish byte integrity,
not provider authenticity or independent certification.

```sh
docker compose stop              # preserve history and the named data volume
docker compose up -d             # reopen the same local workspace
```

## CLI without a real endpoint

Use the checked-in [Dev Container](.devcontainer/devcontainer.json), then:

```sh
uv sync --locked
UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite fast
uv run --frozen anthropic-readiness validate --target examples/target.yaml
uv run --frozen anthropic-readiness run --target examples/target.yaml --out artifacts/dry-plan --dry-run
uv run --frozen anthropic-readiness replay --target examples/target.yaml \
  --capture tests/fixtures/captures/valid/evidence/ANT-TEXT-SSE-001/fixture-attempt/response.json \
  --case ANT-TEXT-SSE-001 --out artifacts/replay-example
```

Replay uses synthetic captures and makes no endpoint request. CLI execution retains
automatic `result.json`, `report.html`, `report.md`, visual `report-view.json` and
report/evidence manifests. The Chinese report includes scope, a capability matrix,
status/impact charts, recorded timing when available, assertions and citations for
human and Agent interpretation. No score or invented token/latency metric is used.

Minimal Python installation needs only the core dependencies; install the optional
`anthropic-readiness[web]` extra to use `serve`. The Docker `runtime` target retains
the CLI, and the separate `web` target provides the local console. Neither ships
Node, Chromium, development tools or a source checkout.

For an explicitly authorized real target, put configuration outside the build
context, prepare the named credential variable, inspect `--dry-run`, and select
`--allow-live` with finite request/time budgets. Never commit private configuration
or original service logs. Exit codes: 0 pass, 1 observed failure, 2 invalid input,
3 incomplete/blocked, 4 internal error, 130/143 signal.

See [container usage](docs/container-usage.md), [development](docs/development.md),
[architecture](docs/architecture.md), [contribution guide](CONTRIBUTING.md) and
[current milestone/evidence](docs/CONTINUE.md). Local checks, installed packages,
images, independent review, remote CI and real endpoints are distinct evidence.
GitHub CI and container builds do not publish images. Docker Hub account setup and
push credentials can be configured with the owner when publishing is authorized.
Choose an appropriate license before public distribution; none has been selected
on the owner's behalf.
