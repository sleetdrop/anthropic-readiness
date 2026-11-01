# Repository guide

Build an Anthropic Messages compatibility assessment tool for consumers and
providers of self-hosted APIs claiming that protocol. Read [intends.md](intends.md), [current status](docs/CONTINUE.md)
and [the rewrite entry point](docs/refactor/README.md). Read a task's owned paths
before editing; read [design.md](design.md) for presentation changes.

## Current development contract

- The owner authorized a local-first TypeScript/Node rewrite on 2026-11-01.
  `next/` is active until cutover; Python source is migration reference.
- Use Node 24 LTS. Prepare with `npm --prefix next ci`. The single complete check
  entry point is `npm --prefix next run check`; root `npm run check` forwards to it.
  Focused test/type commands are documented in docs/development.md.
- New development, checks, hooks and CI must not require Python, Docker, Compose,
  Dev Container, an architecture matrix or another Node version. Container delivery
  is deferred until the diagnostic tool is useful and mature.
- Reuse protocol rules, synthetic faults and the approved interaction baseline;
  do not translate the old module architecture or grow a permanent second stack.
- Write source, comments, machine fields and commits in English. User-facing
  interfaces/reports support Chinese and English, with the approved paired themes.
- Run a meaningful failing control before changing behavior. Keep validators pure
  and I/O in adapters. Preserve strict typing, explicit selected-case accounting
  and separate raw-protocol, task-behavior and client outcomes.
- Zero, skipped, todo, failed or unrun checks are never a complete passing gate.
  Keep original failures. Do not weaken rules/goldens to obtain green results.
- Keep credentials, private targets and original service logs out of source and
  public artifacts. Live endpoint calls need explicit opt-in and request/time bounds.
  Synthetic disposable services do not need repeated permission discussions.

## Collaboration and delivery

- The owner authorizes a bounded implementation chat and direct coordination with
  the main chat. Respect task file ownership; do not overwrite another chat's work.
  Coordinate an interface change before editing shared files. The coordinator
  integrates and reviews the implementation direction once; avoid per-step agents.
- Reuse unchanged-source evidence. Run focused checks during development and the
  small complete TypeScript check at delivery. Add browser acceptance when browser
  behavior exists; its fixture must run on Node. No speculative infrastructure gates.
- A useful diagnostic or concrete usability fix is the delivery outcome. State
  endpoint scenarios/faults added, how to use them and remaining gaps. Supporting
  work and tool self-test counts do not increase endpoint coverage.
- Keep docs/CONTINUE.md concise and current. Record material outcomes in
  docs/harness/progress.md; large logs belong in ignored artifacts. Do not create a
  new plan/ledger/approval loop for every small edit or a status-only CI rerun.
- Choose work from the delivery route in docs/refactor/README.md and the gaps in
  docs/refactor/coverage.md. Deliver coherent runnable workflows; the owner need
  not approve individual cases. Small commits are implementation units, not
  substitutes for the product checkpoint. Planning does not increase coverage.
- Evaluate the selected protocol scope and declared capabilities systematically.
  Client-specific workflows are optional supplementary assessments with separate
  results; the core tool must operate independently of them.
- Make scoped local commits. Remote writes, registry publication and account
  changes need explicit authorization. Do not claim local checks establish remote CI.

## Historical material is evidence, not active instructions

`src/anthropic_readiness`, root Python tooling, legacy root npm scripts/config,
`*.python.md`, `*-legacy.md`, docs/superpowers, old docs/harness manifests/ledgers,
and docs/harness/legacy describe the previous implementation. Their mandatory
container, Python-matrix, stage-order and skill-approval language does not apply
to this rewrite. Consult a specific old rule/fixture only when it helps the current
outcome; do not recursively read or execute old plans. A prior PASS belongs to its
recorded revision and environment, never the rewrite. Current owner instructions
and this guide govern work; preserve historical evidence instead of rewriting it.
