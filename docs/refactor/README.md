# TypeScript rewrite

Owner-authorized on 2026-11-01. Purpose: get a useful Anthropic endpoint diagnostic
into regular use, with one local toolchain and short feedback cycles. This decision
supersedes the legacy milestone's stack and container requirements, not the product
purpose in intends.md or the accepted presentation in design.md.

## Structure and boundaries

Use one Node 24 LTS runtime, one package and one shared execution engine. `next/`
is a temporary migration directory; it becomes the root application at cutover.
It is not a second maintained product. Do not translate the Python architecture
module by module or require its tests to develop the new implementation.

| Area | Responsibility |
| --- | --- |
| `next/src/domain.ts`, `catalog.ts` | Shared values, evidence locations and explicit selected-case accounting. Coordinator owns these interfaces. |
| `next/src/protocol/` | Pure JSON/SSE validation against a selected protocol snapshot; no I/O. Bounded collaborator task starts with final-message validation. |
| `next/src/runner/` | Raw HTTP capture, deadlines/cancellation, request accounting, case conversations and progress. SDK checks record their own tested version/outcome. |
| `next/src/cli/`, `server/` | Thin adapters over the same engine; local loopback service. |
| `next/src/web/`, `report/` | Reuse accepted investigation interactions, Chinese/English and paired themes; portable structured results and readable standalone exports. |

Use the official Anthropic TypeScript SDK for client-compatibility checks, with
retries disabled and an explicit version. Preserve raw response/SSE inspection for
fault diagnosis. An SDK success is not proof of strict wire compatibility, and
wire compatibility alone is not proof of Claude Code support. Do not build a
plugin framework, generic multi-provider abstraction or distributed job system.

## Delivery order and hands-on checkpoints

1. Current setup: independent Node package, core contracts and selection controls.
   This is supporting-only work: no TypeScript endpoint runner exists yet.
2. Complete final-message and SSE validators with valid/faulty synthetic controls.
   In parallel by file ownership, integrate bounded raw capture and CLI execution.
   Preserve all five existing scenarios and their six-request complete selection.
   Allow an early CLI trial as soon as that path actually runs; do not wait for a
   redesigned report, container build or all planned features to finish.
3. Add the next useful diagnostic scenarios: streamed tool-argument assembly and
   result round trip, multi-turn context, invalid-request/error handling, and an
   explicitly versioned SDK workflow. These are planned cases, not delivered
   coverage. Present task/protocol/client outcomes and selected/unexecuted counts
   separately. Do not declare the five-case migration the finished product.
4. Expose the shared engine in the local Web flow, reuse the accepted visual
   baseline, preserve records/selected evidence and export reports. Fix the known
   initialization/input race with an explicitly delayed-session/control test.
   Trial the actual tool at each useful checkpoint. Broader client/protocol/version
   coverage remains visible; Docker/Dev Container come only after mature use.

No live endpoint request is authorized by this rewrite instruction. Before a
future real trial, obtain the selected endpoint/model and explicit request/time
budget. Synthetic local services require no repeated permission discussions.
Existing installed data and private reports are not migration fixtures and must
not be overwritten. New machine-format semantics need their own version; do not
claim old archives are supported until a reader is actually tested.

## Work and verify

In `next/`, run `npm ci` once and `npm run check` for strict types and executed Node
tests. Node runs erasable TypeScript directly; no application compiler framework
or Python is needed. Dependencies are locked. Run focused tests during changes,
then the small complete package check at delivery. Browser checks apply when Web
behavior is implemented; their fixture must also run entirely on Node.

No Docker, Compose, Dev Container, image architecture matrix or Python version
matrix is part of this baseline. Legacy workflow definitions are archived outside
the active workflow directory. The checked-in replacement is
one Node job using the shared check entry point, with no duplicated graph. No remote
change or CI result is claimed here. Add one relevant browser run when Web behavior
exists. Keep failed test records and no-empty/no-skipped acceptance; do not require a new status-only source
commit just to mirror Actions' final state.

## Coordination and current status

Coordinator chat: local `01a1387c-a2d6-75b2-a769-9c147b6992bd`.
Branch: `codex/typescript-refactor`. Implementation chat: local
`01a1957d-20a0-7491-aefb-2a509bc9a836`. T1 final-message validation is implemented
and coordinator-reviewed (189ff93, correction 2932a74). Its
[task and exact owned paths](task-01-message-validation.md) remain a scope record,
not a request to repeat the task. The coordinator also implemented the bounded raw
HTTP adapter; SSE validation and CLI case execution remain next.
The same implementation chat now owns [T2 SSE validation](task-02-sse-validation.md);
the coordinator owns runner/CLI integration. No new chat or model change is needed
for this continuation of the protocol direction.
The coordinator integrates/reviews this direction; a second broad agent review of
the same small change is unnecessary. Chats may communicate under the owner's
explicit authorization, without repeatedly routing technical details through them.

The old browser-race test draft is preserved in ignored
`artifacts/configuration-startup-20261101/configure-draft.patch`, not represented as
an executed regression. The prior main failure and trace remain retained. Current
Node scaffolding RED/GREEN logs are in the same ignored directory. Catalog rows
and tool self-test counts do not increase actual endpoint coverage.
