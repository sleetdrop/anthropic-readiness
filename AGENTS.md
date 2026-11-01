# Repository guide

Build a focused Anthropic Messages compatibility diagnostic tool with a shared
CLI/Web engine. Read [intends.md](intends.md) first for product purpose and delivery
priorities, then `docs/CONTINUE.md` and the referenced milestone specification/plan.
A milestone's limited scope does not retire unfinished core product goals.
Before choosing work, identify its user-visible diagnostic outcome. At delivery,
state added/changed endpoint scenarios, detectable faults, how to use them and
remaining gaps; explicitly identify supporting-only work. Keep endpoint coverage
separate from assertions, self-test counts and CI success. Do not infer endpoint
internals or mark untested capabilities as supported.

Before interface/report presentation changes, read [design.md](design.md) for the
owner-approved baseline, reference images and scope. Preserve accepted patterns
and semantic colors; record intentional refinements instead of following older
visual experiments. Prototype acceptance is separate from product implementation.

## Active TypeScript rewrite

The owner authorized replacing the Python implementation on 2026-11-01. Read
`docs/refactor/README.md` for the bounded delivery sequence and task ownership.
`next/` is the active implementation until cutover; do not grow a permanent dual
stack. Python source and previous milestone documents are historical reference.
Current owner instructions supersede their mandatory-container and multi-version
acceptance requirements. Preserve observed failures and useful protocol controls.

- Work locally with Node 24 LTS. In `next/`: `npm ci`, then `npm run check`.
- New development and checks must not invoke Python, Docker, Compose or Dev
  Container. Container packaging is deferred until actual use warrants it.
- Keep CLI/Web on one execution engine; keep raw protocol and SDK outcomes separate.
- A catalog or scaffolding test is not an implemented endpoint scenario.
- The owner will create an economical-model chat for the bounded protocol task.
  Use its documented file ownership; the coordinating chat integrates and reviews.
  Do not create per-step agents or restart broad reviews for every small edit.
- Root Python/npm/CI commands below belong to the legacy implementation. They are
  not prerequisites for new TypeScript work. Replace old CI at runnable cutover;
  do not report its container jobs as current rewrite acceptance.

## Legacy development reference

- Develop locally or in the checked-in Linux/Python 3.12 Dev Container. Follow
  `docs/development.md` for locked tools, known macOS gaps and Linux/container
  verification; do not treat a local run as evidence for another environment.
- Preparation: `uv sync --locked`. Verification: set `UV_OFFLINE=1` and run
  `uv run --frozen python scripts/check.py --suite fast` or `--suite full`.
- Source is in `src/anthropic_readiness`; tests use synthetic data in `tests`.
- Bootstrap checks are not whole-stage acceptance. Record missing checks honestly.
- The current plan is executed sequentially; do not create implementer agents
  per task. Arrange one independent whole-stage review at the end.

## Engineering contracts

- Write source, comments, machine fields and commits in English. Reports default
  to Simplified Chinese. Keep all JSON schemas/contracts packaged as resources.
- Run meaningful failing tests before implementing behavior. Fix and rerun local
  disposable-fixture tests without seeking repeated approval.
- Keep framing/domain/validators pure. I/O belongs to adapters. Preserve strict
  typing, schema validation, evidence integrity and required-case accounting.
- Never silently weaken assertions, change golden expectations or erase failed
  attempts to get a green result. Version intentional contract changes.
- Never put real target configuration, credentials, original service logs or
  the historical evaluation workspace into source, images or public artifacts.
- Real API calls require explicit live opt-in and a request/time budget.
- Local commits are part of delivery. Remote writes, registry publishing and
  account setup require the user's explicit authorization for that operation.

## Evidence and handoff

Record observed checks and material rulings in `docs/harness/progress.md` and
the plan ledger. Keep large logs in ignored `artifacts/`. Distinguish source
implementation, offline verification, container acceptance, remote CI and
real endpoint outcomes. A missing tool, zero tests or unrun job is never PASS.
