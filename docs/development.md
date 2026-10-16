# Development

The supported development environment is the checked-in Linux Dev Container.
Its image and Python toolchain are pinned; host Python is not required.

Preparation may download locked dependencies. Verification must use already
prepared dependencies with `UV_OFFLINE=1`. Run tests with
`uv run --frozen python -m pytest`; run the project gates through
`uv run --frozen python scripts/check.py --suite fast` or `--suite full`.

See [the approved plan](superpowers/plans/2026-10-15-stage-a-implementation.md)
for the current stage. Bootstrap acceptance is narrower than Stage A.
Neither implies that a real endpoint has passed any test.

## Stable gates

Fast: `lock`, `format`, `lint`, `type`, `architecture`, `schemas`, `unit`.
Full adds `integration`, `acceptance`, `packaging`, `documentation`. Each command
has a timeout and a retained log; pytest gates require nonzero executed tests
and a clean JUnit report. Deliberately broken disposable projects verify lint,
typing, architecture, schema, missing executable and missing wheel resources.
Missing/skipped/cancelled required CI jobs fail `ci-required`.

Check manifests record UTC times, Git commit/dirty state, lock hash, tools and a
source fingerprint. The fingerprint covers source/tests/scripts/examples,
workflows, Dev Container files, project configuration, root guides, architecture,
development/container docs and the acceptance map. It excludes generated evidence,
progress/review notes and caches so checks can record their own results without
changing the tested source. A change during a run fails that run. This fingerprint
is not a signature or a claim that all Git content was checked.

CI runs the full graph on Linux/Python 3.11 and 3.12, the actual Dev Container and
an amd64 runtime smoke. Weekly/manual matrix jobs build dev/runtime on both
architectures. Fork PRs need no secrets, model calls, privileged source workflow
or registry access. Nothing publishes images. The stable required branch check is
`ci-required`; select it in repository settings after remote CI first succeeds.

Actions are pinned to verified commit SHAs (checkout v7.0.1, setup-python v7.0.0,
upload-artifact v7.0.2, setup-buildx-action v4.4.1). The matrix uses GitHub's
[documented native runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
Updating pins is a reviewed maintenance change. Caches are deliberately omitted
initially to keep preparation and fork trust behavior simple; uv's local cache
supports subsequent offline verification. Remote outcomes remain `not_run` until
the owner connects and runs the workflows.

The editor entry point is “Reopen in Container”. Without an editor, use a pinned
Dev Container CLI on the host:

```sh
npm exec --yes --package @devcontainers/cli@0.89.0 -- devcontainer build --workspace-folder .
npm exec --yes --package @devcontainers/cli@0.89.0 -- devcontainer up --workspace-folder .
npm exec --yes --package @devcontainers/cli@0.89.0 -- devcontainer exec --workspace-folder . env UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite full
```

The Docker socket is not mounted into the default container. Image orchestration
runs on the host or independent CI runner; its stdlib Python does not import the
product. Product builds and tests still execute in Linux containers.
