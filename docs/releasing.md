# Releasing

The first public release is being prepared as `0.1.0`. Earlier package numbers
and local archives were exploratory. They are not a published release history.
Probe-contract and fixture versions identify rules and evidence independently
of the npm package version.

## Publish helper

Once the version tag has been created and pushed, run:

```sh
./scripts/publish.sh
```

The helper can run from any directory. It uses Node 24 from your PATH, or an
installed Homebrew `node@24`. It confirms the `sleetdrop` npm account, installs
locked tools, runs the repository checks, and packs the matching Git tag.
Package inputs must match that tag. npm handles login, OTP, and browser
verification directly in the terminal.
The registry is pinned to npmjs.org; a conflicting `@sleetdrop:registry`
setting stops the script before authentication or publication.

After publishing, the helper verifies the version, archive integrity, and npm
dist-tag, then creates a temporary workbench from the registry package. Local
archives and npm cache files stay under ignored `artifacts/`. It does not
create or push Git tags.

Use `./scripts/publish.sh --dry-run` to run checks and preview publication
without signing in or publishing. Stable versions use `latest`; prereleases
use `next`. An optional `latest` or `next` argument selects the npm dist-tag;
prereleases cannot use `latest`. A failed publish is not retried automatically.

## Release sequence

1. Set the package version in `package.json`, update `package-lock.json`, and
   move the relevant changelog entries under that version.
2. Run `npm ci` and `npm run check` on Node 24. Try the packed archive in a new
   workbench and record the tested scope in `docs/history/verification.md`.
3. Merge the validated changes into `main` with a clean working tree. Create
   an annotated `v<version>` tag on that commit. Do not move a published tag.
4. From the tagged checkout, run `npm pack --pack-destination /tmp`. Inspect
   the archive. Its version and contents must match the validated source;
   it must contain no targets, credentials, captures, tests, or local artifacts.
5. With explicit authorization, push `main` and the version tag, then run
   `./scripts/publish.sh` to publish and verify the tagged package.
6. Create a fresh directory from the registry package and verify initialization
   before announcing the release. Record registry verification separately from
   local archive testing.

Local commits, merges, and tags do not publish the package. Do not contact a
real diagnostic endpoint as part of release checks without authorization and
request/time bounds.
