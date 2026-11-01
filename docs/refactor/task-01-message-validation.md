# T1: pure final-message validator

Ready for the owner-created economical-model chat. This is implementation, not a
new brainstorming/approval cycle. Read AGENTS.md, intends.md, this task,
README.md in this directory, and next/src/domain.ts before editing. The latest
owner instructions permit a TypeScript rewrite and defer all container tooling.

## User-visible diagnostic outcome

Given a complete decoded response, identify concrete malformed message fields,
model-identity mismatches and unrecognized extensions, with exact JSON locations
for later evidence annotation. This module alone makes no endpoint calls and does
not implement a runner, task correctness or SDK/Claude Code support.

## Interface and owned paths

Create `next/src/protocol/messages.ts` with:

```ts
import type { MessageValidationContext, Observation } from "../domain.ts";
export function validateMessage(
  value: unknown, context: MessageValidationContext,
): readonly Observation[];
```

Own only `next/src/protocol/messages.ts` and `next/test/protocol/messages.test.ts`.
Create those directories as needed. Other files and dependency/lock changes belong
to the coordinator. Raise a concrete interface issue before changing shared types.
Use the shared branch/directory without changing checkout; stage only owned paths.
Do not overwrite another chat's edits. Do not create or switch worktrees or branches.

## Behavior and focused controls

- Require a JSON object with nonempty string id/model, type message, role assistant,
  array content, explicit stop_reason and explicit stop_sequence, and nonnegative
  integer input/output token counts. Booleans are not integers. Missing fields
  differ from null. Report the specific failing field rather than one opaque error.
- Validate known text/tool_use block shapes: text must be a string; tool_use needs
  nonempty string id/name and object input. Unknown block types must not earn a
  complete protocol pass or be asserted malformed merely for being new.
- Match the requested model or explicit aliases when identity checking is enabled.
  Otherwise record an optional SKIP, not a verified identity pass.
- Use context.stopReasons for the selected snapshot. An unknown string stop reason
  is inconclusive; a wrong type is a proven structural fault. For stop_sequence,
  require a string when that is the stop reason and null otherwise. A valid custom
  stopping sequence must pass; do not copy the old always-null assumption.
- Every failing field observation locates a real JSON node. Missing members use a
  real parent pointer plus missingKey; never invent a value at a nonexistent node.
  Use valid RFC 6901 paths for known fields/indexes. Root uses the empty pointer. Preserve
  captureId; do not invent SSE event indexes in this final-message-only module.
- Return granular required protocol observations with stable English rule/reason
  identifiers and ruleVersion 1. Use concise expected/actual descriptions. Keep
  behavior/client judgments out of this function. Unknown values are data, not HTML.

Write meaningful failing controls first. Cover legal text/tool messages, each
required field missing, wrong types including token booleans/fractions/negative
values, alias/mismatch/identity-disabled, legal custom stop sequence, unknown stop
reason/block type and nested/missing-parent evidence locations. Add controls for
object-versus-array distinctions. Do not weaken old golden files or silently bless
known legacy bugs. Validate rules against the selected official contract/reference;
the current Python validator is a useful comparison, not the specification.

Useful read-only references: src/anthropic_readiness/validation/messages.py,
tests/fixtures/contracts/core-1.0.0/message-*.json, and the bundled
src/anthropic_readiness/contracts.py and src/anthropic_readiness/resources/contracts.
Legacy imports,
Python execution, Docker and network calls to model endpoints are out of scope.

## Verification and handoff

From `next/`: `npm run test:protocol`, then `npm run check`. Both must execute real
tests, with no skipped/todo controls or placeholder implementation. Keep RED/GREEN
logs in ignored artifacts. No runtime dependency should be necessary for this
bounded structural validator. Report observations and important unvalidated fields;
do not describe these unit tests as endpoint scenarios.

Make one local commit of owned paths after checks. No remote push, CI trigger,
new plan/ledger, dependency upgrade or unrelated rewrite. Send a concise completion
message with commit, test commands/outcomes and any concrete contract uncertainty
to the coordinator chat, under the owner's cross-chat communication authorization.
Stop at this task; the coordinator handles integration and further scope.
