# Development

## Setup and checks

Use Node 24 LTS, as pinned in `.node-version`.

```sh
npm ci
npm run check
```

`npm run check` runs strict TypeScript validation and the complete test suite.
It checks the actual npm archive, generated workbenches, offline inspection,
HTTP capture, protocol rules, task behavior, and reports. Network tests use
synthetic loopback services. Results are written to `artifacts/checks/`.
GitHub Actions runs the same command.

For a focused change:

```sh
npm run check:types
npm run test:protocol
node --test tests/scaffold.test.ts
```

Use normal and faulty fixtures from `tests/fixtures/`. Add a failing control
before fixing a behavior defect. Keep fixtures synthetic and preserve their
exact bytes. See [architecture](architecture.md) for source ownership and the
[offline exercise](offline-exercise.md) for a manual agent test.

## Try the package locally

From the repository root:

```sh
npm pack --pack-destination /tmp
cd /tmp
npx --offline --package=/tmp/sleetdrop-anthropic-readiness-0.1.0.tgz \
  anthropic-readiness init gateway-test
```

Use the filename printed by `npm pack` if the version differs. Choose a new
directory name; initialization refuses to overwrite an existing directory.
Add `--claude-code` to check that Skill layout. The generated `AGENTS.md`
links to the selected Skill location.

The package needs no runtime dependencies. Its contents should be `bin/`,
`templates/`, the package metadata, README, and license. Use `npm pack --dry-run`
to inspect the file list. See [release instructions](releasing.md) before
publishing.
