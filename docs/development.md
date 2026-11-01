# Development

The active implementation is next/: TypeScript on Node 24 LTS. Its default selected
version is in next/.node-version. Install the locked dependencies once:

```sh
npm --prefix next ci
```

Current work needs no Python, Docker, Compose or Dev Container. Browser tooling
is added when the new Web flow exists. The former setup and environment evidence
are [historical reference](development-python-legacy.md), not prerequisites.

## One check entry point

```sh
npm --prefix next run check
```

Root `npm run check` and the optional existing pre-commit integration use this same
entry point. It runs strict TypeScript checking followed by the executed Node test
suite. Failed types stop before tests; missing, empty, failed, cancelled, skipped
or todo test reports cannot pass. Logs and a machine-readable outcome are written
to next/artifacts/checks/ (ignored). Node process timeouts are bounded; this is a
small current harness, not proof of future browser/packaging acceptance.

For focused implementation work:

```sh
npm --prefix next run check:types
npm --prefix next test
npm --prefix next run test:protocol
```

The protocol command runs the implemented message/SSE controls; an absent suite
is not PASS. Repeat the complete check after material changes, not after every note.
The root's other npm scripts and Python tools are legacy; do not run them for new
TypeScript work. Preserve failed evidence and state any unrun checks honestly.

## CI

The checked-in workflow now defines one Node job named ci-required, with locked
installation, this same check command and retained check artifacts. Its permissions
remain read-only; actions are pinned. No Python/browser/container/architecture
matrix is active. Browser acceptance will be added once for the new Web flow.
The old CI and scheduled image workflow are preserved under harness/legacy/ outside
GitHub's active workflow directory. Local workflow edits are not a remote CI run.
No credentials, live model requests or publishing are needed by these checks.
