# Development

From the repository root, use Node 24 LTS and run:

```sh
npm --prefix next ci
npm run check
```

The check runs TypeScript validation and the Node test suite, including
disposable local HTTP peers. It also copies the Skill into an isolated
consumer project and exercises inspection, probe preview, and offline report
rendering there. It records results under `next/artifacts/checks/`.
GitHub Actions runs the same check in one Node 24 job. There is no repository
pre-commit framework or container requirement. For changes to the diagnosis workflow,
try the [offline exercise](offline-exercise.md) with the affected controls.
