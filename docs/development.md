# Development

From the repository root, use Node 24 LTS and run:

```sh
npm --prefix next ci
npm run check
```

The check runs TypeScript validation and the Node test suite, including
disposable local HTTP peers. It records results under `next/artifacts/checks/`.
GitHub Actions runs the same check. For changes to the diagnosis workflow,
try the [offline exercise](../skills/anthropic-incident-diagnosis/references/offline-exercise.md)
with the affected controls.
