# Development

## Setup and checks

Use Node 24 LTS for development and publication, as pinned in `.node-version`.
Consumer runtime support covers Node 22.18+ (22.x) or 24.2+; use the latest
patch of a maintained LTS release.

```sh
npm ci
npm run check
```

`npm run check` runs strict TypeScript validation and the complete test suite.
It checks the actual npm archive, generated workbenches, offline inspection,
HTTP capture, protocol rules, task behavior, and reports. Network tests use
synthetic loopback services. Results are written to `artifacts/checks/`.
GitHub Actions runs the same command on the latest Node 22, 24, and 26 releases.
The `ci-required` job requires all three matrix runs to succeed. The packed
consumer test uses strict engine checks and executes initialization, preview,
and a bounded synthetic probe using that job's Node version. Historical minor
releases are not part of this matrix. Version-guard tests simulate unsupported
and future versions; those simulations do not establish runtime compatibility.

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
