# Development

Use the checked-in Linux/Python 3.12 Dev Container. It contains pinned uv and Node
24, browser system libraries and CJK fonts. Reopening the container prepares
`uv sync --locked`, `npm ci --ignore-scripts` and the npm-locked Playwright Chromium.
Preparation may use the network; verification uses already prepared dependencies
with `UV_OFFLINE=1`. Host-specific Python is not the development environment.

```sh
UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite fast
UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite full
uv run --frozen anthropic-readiness serve --data-dir artifacts/local-web --port 8765
```

The port is forwarded by the Dev Container. The console starts no model request by
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
Python; product builds/tests stay in Linux containers. The default development and
runtime configurations mount no Docker socket. See [container usage](container-usage.md)
and [CONTRIBUTING](../CONTRIBUTING.md) for delivery checks and Agent handoff.
