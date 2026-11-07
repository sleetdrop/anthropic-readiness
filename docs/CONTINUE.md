# Maintainer status

The portable agent workbench is preparing its first public npm release,
`0.1.0`. No version has been published. Exploratory commits and earlier test
archives remain available in [development history](history/README.md).

The repository is one npm package. The command is in `bin/`, copied workbench
files are in `templates/`, and checks and tests run from the repository root.
Generated workbenches include `AGENTS.md`, target and credential files,
evidence/run directories, and a self-contained Skill.

## Verification

- Node 24.22.2 strict types and all 85 synthetic tests passed after the
  repository cleanup, including both generated Skill layouts and reports.
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

Complete the [release sequence](releasing.md): validate the package, merge to
`main`, create the version tag, then push and publish with authorization.
Registry installation remains unverified.
