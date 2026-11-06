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

## Try the npm package locally

From the repository root, use Node 24 LTS and run:

```sh
npm pack ./scaffold --pack-destination /tmp
npx --offline --package=/tmp/sleetdrop-anthropic-readiness-0.2.0.tgz \
  anthropic-readiness init gateway-test
```

Use the filename printed by `npm pack` if the version differs. Run the
initialization command from the parent directory where you want the test
project. Open the generated project in your agent for the offline exercise.
The check suite packs and runs the local tarball using an isolated npm cache
and a synthetic loopback endpoint.
