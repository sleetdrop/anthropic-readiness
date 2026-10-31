# Development

Develop on the host or in the optional checked-in Linux/Python 3.12 Dev Container.
The container supplies pinned uv and Node, browser system libraries and CJK fonts;
its post-create step prepares Python, npm and Playwright Chromium. It remains the
reproducible Linux baseline and does not need to run during ordinary host editing.

For local macOS work, install `uv` 0.13.1, Python 3.12.15 (as selected by
`.python-version`) and Node 24.22.0 with npm 11.19.1. The frontend prerequisite
checks the exact Node version in [the toolchain record](harness/web-toolchain.json).
Make that Node version first on `PATH`, then prepare the locked dependencies:

```sh
uv sync --locked
npm ci --ignore-scripts
npx --no-install playwright install chromium
```

If a global uv configuration selects a different default package index, the lock
check can report that the lock needs updating even when package versions match.
For this lock, set `UV_DEFAULT_INDEX=https://pypi.org/simple` for preparation and
offline checks; do not change the lock to accommodate a machine-local mirror.

Preparation may use the network; verification uses already prepared dependencies
with `UV_OFFLINE=1`. Keep host and container virtual environments separate: the
Dev Container config places its environment outside the mounted checkout. The
Linux-specific CI preparation script downloads Linux binaries and is not the macOS
setup path. Browser installation is only needed when running browser checks.

The fast graph is intended to run on macOS with the prepared locked tools. Full
graph support on macOS is not established: in particular, Linux-specific integration
tests remain. Run the required full graph in Linux CI or the Dev Container. Record
actual environment and missing checks, without skipping required tests to claim a
full pass. See the [local-development ledger](harness/local-development-ledger.md)
for observed checks and limits.

For example, after preparation, use focused checks while developing locally:

```sh
UV_OFFLINE=1 uv run --frozen python -m pytest -q tests/unit
UV_OFFLINE=1 uv run --frozen python -m scripts.check_frontend --suite static --out artifacts/frontend-static-local
```

Use a new output path for each frontend run. Focused checks do not replace the
complete Linux graph or image acceptance.

Run the fast check on the host or in the Dev Container. Run the full check in the
Dev Container or another prepared Linux environment. `serve` can also be used in
a prepared host environment:

```sh
UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite fast
UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite full
uv run --frozen anthropic-readiness serve --data-dir artifacts/local-web --port 8765
```

The port is forwarded when using the Dev Container. The console starts no model request by
itself. Test code uses synthetic fixtures and disposable local services. For direct
pytest work use `uv run --frozen python -m pytest`; the module form keeps repository
harness imports available. See [CONTINUE](CONTINUE.md) for the active W1 plan and
[the ledger](harness/web-console-ledger.md) for observed RED/GREEN evidence and rulings.
Stage A artifacts remain a frozen historical baseline, not W1 acceptance.

## Required graph

Fast includes `lock`, `format`, `lint`, `type` (mypy strict), `architecture`, `schemas`,
`unit` and `frontend-static`. Frontend static includes strict TypeScript checking of
plain JS/JSDoc, ESLint, Prettier, Jinja compilation/asset inventory and Node JUnit.
Plain HTML Prettier is excluded only for Jinja templates because it corrupts control
syntax; compiler, page and browser checks remain required for those files.

Full additionally executes actual Chromium, Python integration/acceptance, isolated
CLI-only/Web wheel installs and documentation/CI validation. Every full environment
must prepare the locked Node/browser first, including supplemental Python 3.11 CI.
Missing tools are BLOCKED; empty, claimed-only or all-skipped JUnit cannot pass.
Gates keep bounded logs, schema-validated frontend records, traces/screenshots and
actual testcase counts. Owned fixture/listener cleanup and timeout process-group
termination are checked. Bootstrap, fast and smoke are not whole-stage acceptance.

Python test gates normally have a 300-second limit. The serial integration gate
allows 600 seconds for complete evidence/import/export workflows. Exceeding a
limit remains BLOCKED and terminates the gate's owned process group; it never
substitutes a partial test count for a completed report.

```sh
UV_OFFLINE=1 uv run --frozen python -m scripts.check_frontend --suite static --out artifacts/frontend-static-new
UV_OFFLINE=1 uv run --frozen python -m scripts.check_frontend --suite browser --out artifacts/browser-new
```

Choose new output paths each time. The browser fixture owns only disposable local
synthetic services and controls; it never uses real provider credentials. Tests
exercise explicit start/idempotency, durable progress, cancellation/reconnection,
secret clearing, hostile fields, exact figure data, focus/accessibility, narrow
layouts, print and direct file HTML with scripts/network disabled. Inspect actual
screenshots; merely generating them is not visual review.

Source fingerprints include Python/frontend code, tests, scripts, workflow/container
configuration, lock/toolchain files and public development guides. Schema/engine
contracts, source evidence and report projections have separate identities. Verify
source bytes before rendering; do not infer support from UI state or task completion.

## CI and contribution workflow

Pull requests/default-branch pushes run Python 3.11/3.12 full jobs, the actual Dev
Container full graph, and CLI/Web amd64 image smoke. Every child is required by the
stable `ci-required` aggregator; missing/skipped/cancelled children cannot pass.
Node archives and image/tool versions are frozen in the toolchain record; actions
remain pinned SHAs with read-only permissions. Weekly/manual native amd64/arm64 jobs
run the full CLI/Web image matrix. No secrets, real model calls or publishing are
required for fork PRs. Remote outcomes remain unrun until those workflows execute.

Each environment writes an Actions step summary from its recorded check/image JSON
and actual JUnit testcase nodes, retaining failed/blocked states and unknown counts.
The summary is a presentation aid, not a gate or evidence-integrity validator.
Download the job's artifact for result JSON, logs, JUnit and browser traces. The
Dev Container uploads `artifacts/checks/`; the full image matrix uploads both
`artifacts/images/` and its inner developer `artifacts/checks/`. Evidence uploads
and summaries use `always()` so ordinary test failures retain diagnostics; a job
timeout or forced cancellation can still prevent finalization. Missing evidence
is explicitly unavailable, never passed. New artifacts are retained for 14 days;
download evidence needed longer before expiration.

Outer CI job budgets are 30 minutes for each quality job, 45 for Dev Container,
15 for image smoke, 5 for aggregation and 180 for each full image-matrix job.
These bound runner use without increasing individual test deadlines. Full matrix
runs on the same ref are serialized without cancelling active acceptance; GitHub
may replace a pending run with a newer one. Existing push/PR concurrency is unchanged.
Caching, coverage repartitioning, repository protection and registry publication
are separate changes. Locally verified workflow configuration is not proof that a
remote job ran successfully.

Keep `uv.lock`, `package-lock.json`, Docker pins and
[harness/web-toolchain.json](harness/web-toolchain.json) synchronized when intentionally
updating tooling. Review primary upstream sources; record versions and hashes, then
prepare and verify the updated environments. Do not regenerate protocol assertions
or golden expectations merely to obtain a green result.

The editor entry point is Reopen in Container. A pinned Dev Container CLI can also
run on the host:

```sh
npm exec --yes --package @devcontainers/cli@0.89.0 -- devcontainer up --workspace-folder .
npm exec --yes --package @devcontainers/cli@0.89.0 -- devcontainer exec --workspace-folder . env UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite full
```

Image orchestration runs on the Docker host or independent runner using stdlib
Python; image acceptance builds and tests the product in Linux containers. The default development and
runtime configurations mount no Docker socket. See [container usage](container-usage.md)
and [CONTRIBUTING](../CONTRIBUTING.md) for delivery checks and Agent handoff.

Full image acceptance retains only platform/revision-labelled public browser caches
between disposable development containers. It still executes the locked installer
and disconnected browser checks. Runtime images contain no browser cache. The
synthetic host-route fixture uses Desktop loopback or a validated private Docker
gateway on Linux; the user-facing Web port remains loopback on both.

The image controller selects developer tooling using the Docker engine's observed
native architecture, independently of the requested runtime image architecture.
All Python/browser gates remain required on that Linux baseline. CLI/Web images
still execute their own requested native/emulated runtime checks. Image-result 2.1
records both environments; an emulated developer browser that loses fractional
numbers is explicitly unaccepted. The prerequisite rejects invalid arithmetic before
UI judgment, and full acceptance also calibrates black/white contrast without
disabling any Axe rule. Native amd64 CI is a separate observation from local arm64.

## Diagnostic workbench and document changes

The W2 flows use the same locked developer environment and required CI graph.
Useful focused checks (the full graph remains required):

```sh
UV_OFFLINE=1 uv run --frozen python -m pytest -q \
  tests/acceptance/test_diagnostic_handoff.py \
  tests/acceptance/test_diagnostic_documents.py \
  tests/acceptance/test_web_package.py
```

The first test transfers only an archive between fresh A/B data roots, shuts down
A's peer, supplies B's own target/credential and retests all four original cases.
It checks real validator recovery/persistent/new-failure transitions, unchanged
source bytes, archive inventory and zero import/preview/read requests. Installed
Web checks re-open an imported baseline after a real service restart. Image full
checks repeat import, explicit retest, comparison/export and restart in a separate
receiver volume. Smoke requires actual import but does not substitute for full
retest/persistence/host-route/development checks.

Report presentation is separate from source judgment. New file/CLI/Web-control
outputs use document-view 1.0/presentation 3.0, a checked document-manifest 2.0 and
export-manifest 2.0. Existing report-view/presentation-2 resources and old HTTP
export variants remain compatibility paths. Check both locales and paired themes,
no-script/core print reading, local file controls without storage/network, source
hashes, scope denominators and privacy-field omission. Credential reference names
can equal verdict/model strings; never redact them by global word replacement.
