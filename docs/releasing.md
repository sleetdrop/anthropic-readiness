# Publishing

The first npm release is being prepared as `0.1.0`. Earlier package numbers
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

The helper confirms the `sleetdrop` npm account, installs locked tools, runs
repository checks, and packs the current working directory. npm handles
login, OTP, and browser verification directly. Registry operations target
npmjs.org; a conflicting `@sleetdrop:registry` setting stops the script.

After publication, it checks the registered version, archive integrity, and
npm dist-tag, then initializes a workbench from that registry package in an
empty temporary directory. Archives and cache files stay under ignored
`artifacts/`. A failed publish is not retried automatically.

Use `--dry-run` to check and preview the package without signing in or
publishing. Stable versions use the npm dist-tag `latest`; prereleases use
`next`. An optional `latest` or `next` argument selects that channel.
Prereleases cannot use `latest`.

Before a new npm release, update `package.json`, `package-lock.json`, and the
changelog. Review the intended package contents. The archive must not contain
credentials, private targets, captures, or local artifacts. Running the helper
publishes that package version; it does not choose a new version for you.

## Git tags and source changes

Git tagging, merging, and pushing are separate from npm publication. They can
happen at different times. The helper does not read or modify Git state, and
it works without a Git checkout or a version tag.

When recording a source release, select the intended commit and create a
version tag as a separate Git operation. Do not move a published tag. Remote
Git writes and npm publication each require authorization.
