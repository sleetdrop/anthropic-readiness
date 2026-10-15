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
