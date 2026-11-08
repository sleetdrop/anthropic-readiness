# Publishing

The first npm release is `0.1.0`. Earlier package numbers
and local archives were exploratory, not published releases. Probe-contract
and fixture versions identify rules and evidence independently of npm versions.

## Publish helper

Run the helper in a terminal:

```sh
./scripts/publish.sh
```

It resolves the project directory from its own location. It uses Node 24
from PATH, with an optional lookup through `brew --prefix node@24` when
Homebrew is available. It contains no machine-specific paths and does not
install Node or change shell configuration.

The helper reads the existing `v<package.json version>` Git tag and checks
that the package inputs match it. It confirms the `sleetdrop` npm account,
installs locked tools, runs repository checks, and packs a snapshot of the
tagged commit. Later changes to the helper or development documentation do
not require moving the source tag. npm handles login, OTP, and browser
verification directly. Registry operations target npmjs.org; a conflicting
`@sleetdrop:registry` setting stops the script.

When npm accepts the publication, the helper reports that it was submitted
and exits successfully. npm can take a few minutes to process the package.
The helper does not query or install the package immediately after publishing.
Archives and cache files stay under ignored `artifacts/`. A failed publish
is not retried automatically.

Use `--dry-run` to check and preview the package without signing in or
publishing. Stable versions use the npm dist-tag `latest`; prereleases use
`next`. An optional `latest` or `next` argument selects that channel.
Prereleases cannot use `latest`.

Before a new npm release, update `package.json`, `package-lock.json`, and the
changelog. Review the intended package contents. The archive must not contain
credentials, private targets, captures, or local artifacts. Running the helper
publishes that package version; it does not choose a new version for you.

## Verify later

Once npm has processed the publication, run:

```sh
./scripts/publish.sh --verify-only
```

This checks the registered version, archive integrity, and npm dist-tag, then
initializes a workbench from that registry package in an empty temporary
directory. It uses the saved archive under `artifacts/releases/<version>/`
and does not sign in, publish, or rerun repository checks. If the archive is
missing, `--dry-run` can recreate it from the existing source tag.

Unavailable registry metadata is reported as `Verification pending`, with
exit code 2. Retry verification later; do not repeat publication. Available
metadata that differs from the expected version, integrity, or npm dist-tag
is an error. Verification exits with code 0 only after all checks complete.
Each registry request has a 15-second timeout and no automatic retries.
`--verify-only` cannot be combined with `--dry-run`.

## Git tags and source changes

Git tagging, merging, and pushing are separate from npm publication. They can
happen at different times. The helper only reads Git data; it never creates,
moves, or pushes tags, commits, or branches. A local checkout with the existing
version tag is required. The helper does not fetch tags or require a remote
push before publishing to npm.

When recording a source release, select the intended commit and create a
version tag as a separate Git operation. If the tag is missing or package
inputs differ, the helper stops for review. Do not move a published tag. Remote
Git writes and npm publication each require authorization.
