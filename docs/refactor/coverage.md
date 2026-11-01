# Product coverage inventory

Reviewed 2026-11-01 against the active next/ source at a254a74 and the retained
first real CLI trial. This is a gap inventory, not a completed conformance suite
or a claim that all official fields/features have already been enumerated.
[Intent](../../intends.md) owns the goal; [delivery route](README.md) owns order.

## Current evidence boundary

- Five executable endpoint scenarios, six allowed attempts for their complete run.
  Plain/streamed HELLO, streamed counting, forced tool selection and non-streaming
  tool-result consumption. One owner-selected endpoint sample passed all five
  task behaviors; strict checks failed on omitted fields and configured identity.
- JSON/SSE pure controls and HTTP synthetic tests are implemented. The last full
  Node 24 gate passed strict types and 60 tests; that number is not endpoint coverage.
- API header 2023-06-01, no beta, development rules ID
  typescript-messages-2023-06-01-core/0.2.0-dev. No selectable, immutable source
  manifest or version matrix exists. A hard-coded ID/header does not deliver those.
- New TypeScript Web implementation, SDK and Claude Code execution are absent.
  The older Python GUI and accepted prototypes are not migrated features.

Use implementation, offline controls and real endpoint outcomes as separate
columns when this inventory becomes machine-readable. All planned rows below
remain gaps until code and suitable controls exist; per-target outcomes remain
unrun until that particular target is exercised. A single passing sample cannot
certify all models, versions or workflows.

## Required core for Messages protocol assessment

| Area | Current implementation | Missing diagnostic outcome | Route |
| --- | --- | --- | --- |
| Request/response contract | Partial final-message fields; text/tool blocks; selected usage/stops | Version-specific field/shape inventory, content/stop consistency, request variants, clear precise rule locations | A/B |
| Model identity | Exact name/configured aliases checked inside protocol outcome | Separate protocol structure from operator identity policy; unknown alias mapping cannot establish wrong routing | A |
| Text conversations | Three controlled text scenarios | System instructions, content arrays, multi-turn nonce/context retention, continuation/truncation and applicable stop behavior | A/B |
| Stream framing/lifecycle | Bounded frames, UTF-8/JSON, selected event order/index controls | Complete selected event/delta inventory, termination and cumulative usage rules by snapshot; real transport chunking controls | A/B |
| Thinking | Kept as an unknown block; original events retained | Assemble thinking/signature/redacted variants, preserve round-trip order/data, validate supported shapes; distinguish model prerequisites | A |
| Tool calls | Forced named tool and non-streaming single-tool result | Streaming argument/result round trip, multiple/parallel calls, selection modes, result IDs, tool errors and repeated tool steps | A/B |
| Request validation/errors | Non-200 raw capture is retained and blocks positive cases | Dedicated negative cases with expected status/error envelopes; invalid fields/roles/IDs/header values; legal stream error termination | B |
| Transport/limits | Capture caps, deadlines, cancellation, no retries; synthetic faults | Compression handling, JSON duplicate-key policy, clear partial-evidence results; interrupted/encoded controls | A/B |
| Repeatability | Selected cases retained, revisions, raw request/response bodies/hashes | Durable source snapshot, source-to-rule mapping and non-rewriting offline replay | A/B |

A structural defect, a task failure, a configured identity mismatch, a transport
limit and an unimplemented rule must remain distinct in results. Observations may
share a symptom without proving a common cause. Do not synthesize server errors,
rate-limit behavior or network failures as observed real-target results: disposable
services cover injected faults; live cases cover only safely elicited outcomes.

## Feature-dependent scope, explicitly inventoried

| Area | Current implementation | Required inventory and probe scope | Route |
| --- | --- | --- | --- |
| Generation controls | max_tokens set; no feature probes | Applicable sampling/output controls, stop sequences, supported schemas, version-specific legal/rejected parameters | B |
| Thinking configuration | No configured feature probe | Supported thinking modes/budgets/signatures, thinking + tool prerequisites; no assumption that a DeepSeek/GLM endpoint offers every Claude feature | A/B |
| Cache/usage | Basic input/output counters | Cache-control shapes, usage semantics and applicable multi-turn preservation; do not infer cache hit from task output | B |
| Multimodal/content | Unknown variants conservative | Synthetic image/document probes, citations and other applicable content variants with capability/version prerequisites | B |
| Advanced tool/context features | No probes | Selected snapshot's tool options, server-tool/context features; restricted side effects and explicit support/not-run outcomes | B/C |
| Supplemental APIs | None in next/ | Explicit applicability decisions for token counting, model discovery, Files-dependent Messages flows; do not silently include unrelated Admin/Billing APIs | B/C |

These are product gaps, not permanently excluded features. Establish the selected
snapshot's exhaustive field/event/feature manifest from official references during
A/B; this table is the planning inventory, not that completed technical manifest.
For optional features record prerequisite, selected/not-selected and tested support.
If a user requires one, rejection is a failure of that requested capability rather
than an automatic optional pass. Selection must expose omitted scope, even for an
extensive preset. Budget exhaustion leaves selected cases incomplete.

## Clients, investigation and maintenance

| Outcome | Current state | Remaining delivery | Route |
| --- | --- | --- | --- |
| Official TypeScript SDK | Not implemented/tested | Pinned client, disabled retries, raw/SDK result separation; text, streaming and tools with valid/faulty controls | C |
| Claude Code (optional) | Not implemented/tested in the rewrite | Exact client/platform/config and end-to-end task outcome; no prerequisite for protocol assessment | C, optional |
| Local Web + CLI | CLI only | Same catalog/plan/engine; selected claims/features, simple setup, real progress, history/exchanges, issue-to-evidence flow, Chinese/English and paired themes | A |
| Reports/Agent-readable export | JSON + basic Markdown | Grouped meaningful findings, coverage matrix, useful progress/coverage visuals, offline HTML/JSON/ZIP, references and private-data review | A/C |
| Repeat assessment/comparison | No replay/comparison | Compare implementation/model/version changes with compatible selections and fresh challenges; optional repair rerun retains originals | B/C |
| Protocol versions/updates | Hard-coded header/rules label | Select API/beta/rules/suite snapshots, immutable official-source refs/hashes, update Agent command and explicit version-comparison outcomes | A/C |
| Root cutover | Active next/, historical Python retained | Make Node the only product entry point; decide archive compatibility explicitly; do not overwrite existing private records | C |
| Distribution | Deferred | Container/build publication only after usable mature local operation and separate remote authorization | D |

Client workflow success/failure is supplementary evidence. The core assessment
must operate without Claude Code. Declared protocol capabilities, actual observations,
coverage gaps and verdict limitations are the primary report structure. Keep
controlled-task failures distinct from protocol defects and model-quality rankings.

## Reference and version hygiene

Official sources reviewed for planning on 2026-11-01:

- [Messages](https://platform.claude.com/docs/en/api/messages/create)
- [Streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)
- [Tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [API version history](https://platform.claude.com/docs/en/api/versioning)
- [Migration to 2026-10-21](https://platform.claude.com/docs/en/api/migration-2026-10-21)
- [Official TypeScript SDK](https://github.com/anthropics/anthropic-sdk-typescript)

The live API reference now defaults to 2026-10-21; the current runner sends
2023-06-01. SDK main and live docs are mutable, not pinned evidence for that old
header. Preserve observed missing fields in the first trial, but do not treat its
manual latest-source comparison as a completed version-specific rules audit.
Preserve the current run unchanged. Source review must identify applicable rules
and changes before adding a new snapshot or re-evaluating prior evidence offline.
