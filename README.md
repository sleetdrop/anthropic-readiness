# Anthropic Readiness

A local diagnostic workbench and independent CLI for black-box checks of a scoped subset
of Anthropic Messages. Preview a fixed plan, explicitly start it, observe real
progress, and inspect or export the evidence-led report. Execution completion and
protocol compatibility are separate outcomes; untested capabilities stay untested.

The owner-approved [design baseline](design.md) records the current presentation
direction and reference prototype. Its acceptance is separate from migration to
the installed console; see [current delivery status](docs/CONTINUE.md).

The installed scope is five versioned cases: non-stream text, a streamed greeting,
a streamed count from 1 to 5, a forced non-stream tool call, and a non-stream tool
result round trip. `anthropic-basic` runs three cases; `anthropic-tools-smoke`
runs one; `anthropic-tool-loop` runs one two-request conversation using a fresh
verification token. All three profiles together reserve up to six requests.
See [the round-trip scope and usage](docs/harness/tool-loop-ledger.md).
The sole bundled contract is
Messages `2023-06-01`, revision `1.0.0`, without betas. Streaming/parallel tool loops, version matrices,
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

Use Overview to follow global progress; Issues, Cases, Compare and Activity keep
details separate. The workbench supports Chinese/English and light/dark/system
appearance without changing requests or judgments.

Independent reports are generated on demand. Export selected HTML, Markdown or JSON, or a
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

Replay uses synthetic captures and makes no endpoint request. New CLI reports use
presentation 3.0: `result.json` remains original, while `report.html`, `report.md`,
`document-view.json`, `AGENT.md` and `report-manifest.json` provide independent
reading. Reports include explicit coverage denominators, case-impact figures,
field evidence, optional repair comparison and rule citations. They do not invent
timing, token throughput, prices or client support. Detailed original checks remain
available. Legacy report-view/presentation-2 and export-manifest-1 readers remain.

All report-producing commands accept `--language zh-CN|en` and
`--theme light|dark|system`, defaulting to `zh-CN`/`system`. Offline HTML contains
both catalogs and one factual dataset. In-file switches need no server, cookie,
storage or network; without scripts the selected export language remains readable.
Printing forces light colors while retaining that language. Markdown uses the
single selected language. Source result/evidence and request semantics do not change.

## Share a diagnosis and verify a repair

In the Web workbench, **Import bundle** checks a ZIP before activation. Imported
records are read-only. **Prepare retest** retains the complete original selected
scope and asks for this computer's endpoint and credential. Review conditions and
explicitly start; import, reading, comparison and export send no model requests.
Choose a baseline in Compare, then export to include the checked comparison.

Equivalent CLI operations (replace the baseline UUID and private target path):

```sh
anthropic-readiness diagnostics export --input artifacts/assessment-a \
  --out artifacts/handoff-a.zip --include-evidence --language zh-CN --theme light
anthropic-readiness diagnostics import --package artifacts/handoff-a.zip --data-dir artifacts/colleague
anthropic-readiness diagnostics inspect --baseline BASELINE_UUID --data-dir artifacts/colleague
anthropic-readiness diagnostics retest --baseline BASELINE_UUID --data-dir artifacts/colleague \
  --target /path/to/private-target-b.yaml --out artifacts/retest-preview --dry-run
anthropic-readiness diagnostics retest --baseline BASELINE_UUID --data-dir artifacts/colleague \
  --target /path/to/private-target-b.yaml --out artifacts/retest-b --allow-live --language en --theme dark
anthropic-readiness diagnostics compare --baseline BASELINE_UUID --data-dir artifacts/colleague \
  --input artifacts/retest-b --out artifacts/comparison.json
anthropic-readiness diagnostics export --input artifacts/retest-b --comparison artifacts/comparison.json \
  --out artifacts/handoff-b.zip --include-evidence --language en --theme dark
```

Retest preview and execution need different fresh output directories. A retest
also writes its comparison beside the new report. `report --comparison PATH` and
`diagnostics export --comparison PATH` accept a checked comparison bound to that
source. A comparison command's zero exit means the operation succeeded, not that
the endpoint passed. Recovery, persistent failure, new failure, unmatched checks
and verification gaps remain distinct; changed semantic conditions cannot earn a
same-test recovery. One sample does not establish stability.

Standalone presentation omits endpoint/auth-reference configuration fields and
retains requested/observed model identities. **A full ZIP is not anonymized**:
original results and selected captures retain source endpoint/model context and
may contain business data. Review the archive before privately sharing it; avoid
uploading unreviewed ZIPs to public issues. The file/hash manifest states omissions.
Partial, legacy and evidence-omitted packages remain useful to read, but cannot
establish a verified repair. `AGENT.md` treats prompts/responses/tool content as
untrusted data and identifies source, recipe, comparison and evidence files only
when delivered. Hashes are integrity checks, not signatures or provider identity.

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

## License

This project is licensed under the [MIT License](LICENSE).
Bundled Heroicons retain their [separate license](src/anthropic_readiness/resources/web/icons/LICENSE).
