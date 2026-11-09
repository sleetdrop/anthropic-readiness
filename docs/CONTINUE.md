# Maintainer status

The first workbench release, `0.1.0`, is available on npm. Its version, archive
integrity, `latest` tag, and workbench initialization from the registry were
verified after npm finished processing the publication. Exploratory commits
and earlier test archives remain in [development history](history/README.md).

The unreleased working version broadens consumer runtime requirements to
`^22.18.0 || >=24.2.0`. The initializer accepts supported older and future
stable releases instead of requiring Node 24. Development and publication
remain on Node 24. The published `0.1.0` package and its source tag are
unchanged; this compatibility change needs a new package release.

The repository is one npm package. The command is in `bin/`, copied workbench
files are in `templates/`, and checks and tests run from the repository root.
Generated workbenches include `AGENTS.md`, target and credential files,
evidence/run directories, and a self-contained Skill.

## Verification

- Node 22.23.4, 24.22.2, and 26.13.0 each passed strict types and all 99 tests,
  including strict-engine packed workbenches, reports, and twelve simulated
  publish-helper checks. Per the owner's scope, historical minor releases
  were not tested. Version-guard simulations do not establish compatibility
  with future Node releases.
- CI now checks the latest 22, 24, and 26 release lines and requires all three
  to pass. This workflow change has been checked locally, not run on GitHub.
- The npm archive has 30 files and excludes development tools, tests,
  historical records, and local artifacts.
- Independent consumer trials covered Skill use, full core execution, and
  formal report generation.
- A bounded private assessment selected 32 cases and made 36 requests. The
  tool retained complete evidence and reported protocol differences separately
  from task outcomes. Actual SDK clients were not tested.

Detailed results are in the [verification record](history/verification.md).
Private targets and original live captures stay outside this repository.

## Publication

Use the [publish helper](releasing.md#publish-helper) for checks, packing from
an existing version tag, interactive npm authentication, and publication.
Run `--verify-only` later for registry and installation checks. Publishing
does not query the registry afterward; unavailable metadata during explicit
verification is reported as pending. Git tagging and pushing are independent
source-management actions. The helper only reads Git data; it never creates
or pushes tags.
