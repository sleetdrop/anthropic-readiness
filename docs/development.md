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
npx --offline --package=/tmp/sleetdrop-anthropic-readiness-0.1.0.tgz \
  anthropic-readiness init gateway-test
```

Use the filename printed by `npm pack` if the version differs. Run the
initialization command from the parent directory where you want the test
project. Open the generated project in your agent for the offline exercise.
The check suite packs and runs the local tarball using an isolated npm cache
and a synthetic loopback endpoint.

## Release the npm package

The public package lives in `scaffold/`; the repository root and `next/`
remain private development packages. Use `scaffold/package.json` as the
release version, and use `v<version>` for the matching annotated Git tag.
The scaffold's release sequence starts with its first public package.
Exploratory commits, internal package numbers, and local test archives are
retained evidence, not earlier public releases. Private development packages
do not carry a product release version.
Probe-contract and fixture versions identify rules and evidence independently
of the npm package's release version.

1. Pass `npm run check` on Node 24 and complete the generated-project
   acceptance. Retain the tested scope, controls, and report checks in
   `docs/harness/progress.md`.
2. Merge the validated changes into `main`, with a clean working tree.
3. Create the annotated version tag on that `main` commit. Do not move an
   existing release tag to different code.
4. Pack `scaffold/` from the tagged revision and inspect the resulting
   tarball. The package version, tag, and tested package contents must agree.
5. After explicit authorization for remote writes, push `main` and the
   release tag, then publish the inspected tarball to npm with public access.

Local validation, merging, and tagging do not publish the package. Record
registry installation separately after publication; local tarball acceptance
does not establish that the registry command works.
