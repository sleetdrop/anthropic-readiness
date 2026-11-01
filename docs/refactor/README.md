# Product delivery route: local-first TypeScript rewrite

Reviewed 2026-11-01 after the owner identified case-by-case drift. This replaces
the earlier migration-first delivery order in this same file; T1/T2 remain completed
implementation records. Read [intent](../../intends.md),
[current state](../CONTINUE.md) and [coverage gaps](coverage.md). These are the
active product route, not another sequence of plan-approval rituals.

## Goal and current shortfall

Deliver a specialized Anthropic Messages compatibility assessment application for
endpoint users and inference-stack maintainers. The complete user workflow is:
configure a target and protocol scope, follow a run, investigate a precise finding,
share reproducible evidence with a colleague/Agent, then verify a repair. Both Web
and CLI use one engine. SDK/client outcomes are separate from wire/task results.

The five-scenario CLI is a working migration checkpoint, not that product. Next/
currently has only catalog/domain, message/SSE validators, HTTP execution and CLI.
There is no new Web server/UI, pinned SDK integration or Claude Code workflow.
The accepted design exists; the old Python application is reference, not evidence
that any of those features have been migrated. Source/controls/run outcomes are
tracked separately in the coverage inventory.

The previous route named remaining goals but did not tie them to a complete
coverage inventory and product exit conditions. It could be followed while
indefinitely adding one case or improving infrastructure. Its CLI-first ordering
also obscured that the owner could not operate the rebuilt application. Correct
those delivery constraints; do not rewrite the product goal around current code.

## Architecture and boundaries

One Node 24 LTS, one TypeScript package, one catalog/plan/execution/result contract
for CLI and loopback Web adapters. Pure validators do not perform I/O. Keep exact
raw captures separate from parsed/assembled data. Use the official SDK for actual
client checks, pinned and with retries disabled; do not substitute it for wire
inspection. Do not build a generic provider/plugin framework or distributed queue.

Next/ is a migration directory, not a permanent second product. No initial Python,
Docker/Compose/Dev Container requirement. Reuse useful fixtures and the accepted
[interaction baseline](../../design.md), including token-adjacent evidence
annotations. Do not restart visual exploration or translate the Python module tree.
Use a Node test peer for browser acceptance. Old private records remain untouched;
archive compatibility must be explicitly implemented/tested or declared absent.

## Delivery order and acceptance

A-D are coherent product outcomes, not individual cases and not requests for the
owner to approve each task. Small commits and focused RED/GREEN controls remain
internal implementation practice. Keep the Web flow runnable while expanding the
catalog; do not defer its first working version until every protocol feature is done.

### A. Usable diagnostic application with trustworthy core results

Integrate a working local Web flow now and broaden the core as one delivery:

- One local Node start command; endpoint/model/auth setup with advanced settings
  secondary, endpoint/model history without stored secrets, explicit scope and
  request/time bounds. Web and CLI submit the same plan and execute the same cases.
- Real progress/cancel/history and exchange details; no fabricated progress. Reuse
  the approved issue -> occurrence -> evidence -> return flow, language/theme pair,
  and precise JSON/event markers without changing copied source data.
- Complete thinking/signature assembly, streamed tool round trip, multiple-tool
  result matching, and multi-turn context cases together with ordinary text/tools.
  Cover each with valid/faulty synthetic controls; keep unimplemented scope visible.
- Separate schema/protocol, model-identity policy, task, transport and untested
  client outcomes. Unknown alias mapping cannot prove misrouting; an unsupported
  thinking rule cannot imply an endpoint defect. Group repeated findings while
  retaining their exact occurrences and source/derived-data distinction.
- Start the protocol field/event/feature manifest from official references and
  bind rules to immutable source references. Preserve the current 2023-06-01 run
  identity; do not silently adopt today's API/SDK definitions. A date/label alone
  does not implement version selection or verified coverage.
- Provide readable offline HTML + structured results and a portable share package
  with scope/limits, expected/actual evidence and references. Use coverage matrices
  and actual execution visuals; do not introduce an invented compatibility score.

A is delivered only when the owner can open the new Node application, run the
expanded core or inspect a clearly labeled synthetic run, investigate evidence and
export it; CLI uses the same engine. Browser verification includes delayed-startup
input preservation, running/cancelled/finished states, evidence return paths,
both languages/themes and no accidental connection to a real endpoint. This is a
hands-on checkpoint, not a complete compatibility claim. Do not deliver only UI
with five old cases or only more validators without an operable application.

### B. Comprehensive selected Messages contract and repair workflow

Complete the selected snapshot's manifest across request/response fields,
content/event variants, tool choices/parallelism/errors, multi-turn state,
truncation/stops and negative requests. Inventory generation, thinking, cache,
structured-output, multimodal and advanced feature prerequisites explicitly.
Include relevant supplemental API decisions; unrelated Anthropic administrative
services do not silently enter this focused Messages product.

Implement cases/rules in related groups, not by asking the owner to choose each
one. Each manifest entry has source, applicability, case/rule links, controls and
honest implementation/run status. A deliberately invalid request has an expected
rejection outcome; a network timeout proves no protocol violation. Injected
server/network faults remain synthetic evidence, not claimed live-target behavior.
Handle compression and a deliberate duplicate-key policy; retain all selected but
unexecuted work under budget/cancellation limits. Support offline replay and
repair reruns/comparison without overwriting original evidence or reusing a fixed
challenge. Reports expose remaining coverage rather than silently hiding it.

B acceptance: the selected manifest has no undisclosed/unowned gaps; applicable
implemented entries have suitable valid/faulty controls and end-to-end scenarios.
Rows still unsupported/not run remain visible and prevent a full-coverage claim.
An automated coverage check should catch missing mappings using that same manifest,
not add a parallel manually maintained ledger or mandatory per-case paperwork.

### C. Actual clients, maintained snapshots and Node cutover

Run pinned SDK workflows and deterministic Claude Code coding/tool workflows,
recording exact versions/platform/scope. A client can succeed despite a wire
finding; report that distinction. Never infer Claude Code readiness from HTTP200.
Add explicit API/beta/rules/suite selection and version comparisons. Review both
the retained 2023-06-01 compatibility target and the now-documented 2026-10-21
version against authoritative changes before selecting/claiming support for them.

Ship the repository Agent command for protocol-source review: compare official
changes, propose new snapshot/rules/cases with controls, preserve old snapshots and
flag affected client workflows. Produce a reviewable update rather than silently
rewriting installed rules or fetching an unpinned latest contract during a test.
Locking recommendations require observed client evidence; API dates do not lock
model behavior. Finish the portable colleague/Agent repair package and compatible
run comparison. Cut over the root entry points to Node and archive obsolete
Python instructions/dependencies once corresponding delivery is real.

C acceptance: the owner/colleague can assess a chosen supported snapshot, inspect
wire/task/actual-client results, share evidence and verify a repair. All inventory
rows have explicit dispositions; required unfinished rows remain blockers. This
closes the local product baseline, not every possible future protocol/model state.

### D. Distribution after mature local use

Only then restore optional container delivery and relevant build/publication
support. Keep one proportionate CI graph and contribution guidance. Remote writes,
registry configuration/pushes and account operations still need explicit owner
authorization. Do not let distribution work replace diagnostic/catalog progress.

## Operating rules and responsibility

- The coordinator owns the route, scope gaps and integrated result. Do not ask the
  owner to manage one case, test or implementation chat at a time. A bounded
  existing implementation chat can help with owned paths; no new chat is required.
- Deliver usable product checkpoints; show the running new application, entry
  command, implemented endpoint scope and remaining gaps. A CLI command or source
  commit alone is not evidence that the Web application exists. Do not reopen the
  design direction when migrating accepted behavior.
- Use focused controls during development and one small complete check at delivery:
  npm --prefix next run check. Add the relevant Node browser check when Web exists.
  Reuse unchanged-source evidence; no review chain or infrastructure matrix for
  every case. CI/offline self-tests never substitute for endpoint/client outcomes.
- Catalog growth changes request budgets. Preview the complete chosen selection;
  never silently reduce it. Previous live authorization has its stated target,
  scope and finite limits; it is not unlimited permission for expanded probes.
  Synthetic services do not need repeated permission discussions.
- Keep only current facts in CONTINUE, this route and the gap inventory. Record
  material verification in progress; large/failed/private evidence stays ignored.
  Do not create overlapping stage ledgers. Commit locally; push only when authorized.

## Evidence and completed migration records

Source baseline at this review: a254a74 (no product changes in this document).
Five-case CLI implementation/corrections: 1706639 and 058cec9; 60 executed tests
passed under Node 24.22.0. One real trial completed six requests/all five tasks;
field omissions and identity-policy failures were observed. Latest-source manual
comparison is not an immutable historical-protocol audit. See [progress](../harness/progress.md)
and [the CLI trial guide](cli-trial.md) for current use and evidence boundaries.

T1: 189ff93/2932a74; T2: da4c677/7fc630b. Their task files are completed scope
records. The existing implementation chat is local 01a1957d-20a0-7491-aefb-2a509bc9a836;
coordinator local 01a1387c-a2d6-75b2-a769-9c147b6992bd. No newly assigned work or
review is implied by listing them. Earlier startup-race evidence and the unexecuted
repair draft remain retained; migrating Web must reproduce and test that behavior.
