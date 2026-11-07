# Maintainer status

The first workbench release is `0.1.0`. The npm package has not yet been
published. Exploratory commits and earlier test
archives remain available in [development history](history/README.md).

The repository is one npm package. The command is in `bin/`, copied workbench
files are in `templates/`, and checks and tests run from the repository root.
Generated workbenches include `AGENTS.md`, target and credential files,
evidence/run directories, and a self-contained Skill.

## Verification

- Node 24.22.2 strict types and all 93 tests passed, including generated
  workbenches, reports, and eight simulated publish-helper checks.
- The npm archive has 30 files and excludes development tools, tests,
  historical records, and local artifacts.
- Independent consumer trials covered Skill use, full core execution, and
  formal report generation.
- A bounded private assessment selected 32 cases and made 36 requests. The
  tool retained complete evidence and reported protocol differences separately
  from task outcomes. Actual SDK clients were not tested.

Detailed results are in the [verification record](history/verification.md).
Private targets and original live captures stay outside this repository.

## Before publication

Use the [publish helper](releasing.md#publish-helper) for checks, current-package
packing, interactive npm authentication, publication, and registry validation.
Git tagging and pushing are independent source-management actions. The helper
does not use Git or require a tag.
Registry installation remains unverified.
