# T2: bounded SSE validation and message assembly

Delivered in da4c677 and corrected after review in 7fc630b (2026-11-01).
Coordinator integration adds official-spec controls for repeated message_delta,
intermediate null stop reasons and whitespace around JSON null payloads. This task
is a scope record, not a request to restart implementation. Resource-policy limits
are environment/BLOCKED, not protocol violations; a legal error stream need not
complete the normal successful-message lifecycle.

This continues the same protocol
implementation direction; no new chat, model or planning/approval cycle is needed.
Read this task and the current domain/message validator, not the entire old history.

## Outcome and ownership

Detect duplicate/out-of-order streaming events, invalid content indexes, malformed
JSON/UTF-8, incomplete framing and broken text/tool argument assembly. Preserve
proven faults when transport is interrupted; incomplete evidence cannot pass.
This is a pure module, not HTTP execution or a client/SDK test.

Own next/src/protocol/sse.ts, optional next/src/protocol/sse-framing.ts and
next/test/protocol/sse.test.ts. Do not change T1, shared types, runner/CLI, dependency
files or docs. The coordinator owns next/src/runner/, next/src/cli/ and integration
tests. Only stage your owned files; do not switch branches or clear others' work.

## Public interface (export from sse.ts)

```ts
import type { MessageValidationContext, Observation } from "../domain.ts";
export interface SseEvent {
  readonly index: number; // zero-based dispatched event index
  readonly event: string;
  readonly data: string; // complete original data payload, without SSE field syntax
  readonly value: unknown; // parsed JSON, null for invalid/unparsed payloads
}
export interface SseResult {
  readonly events: readonly SseEvent[];
  readonly observations: readonly Observation[];
  readonly message: Readonly<Record<string, unknown>> | null;
}
export function validateSse(
  body: Uint8Array,
  context: MessageValidationContext,
  options: { completeCapture: boolean; maxEvents: number; maxEventBytes: number },
): SseResult;
```

Validate limits before processing. No filesystem/network/SDK imports. Body is already
content-decoded application bytes; the caller owns HTTP/content-encoding outcomes.

## Required behavior and controls

- Frame SSE using LF/CRLF/CR, optional initial UTF-8 BOM, comments and multiline
  data. Dispatch only at an actual blank-line boundary. Preserve original payload
  and indexes. Bound frame/event storage; never parse arbitrary captured text as
  unlimited events. Invalid UTF-8 is not silently repaired into a passing message.
  Distinguish an incomplete trailing UTF-8 sequence from a proven malformed prefix.
- Observe known message_start, content_block_start/delta/stop, message_delta,
  message_stop, ping and error events. Match known envelope/data type, retain a
  first message_start rather than overwrite it, and validate initial message shape
  including empty content, explicit null stop fields and valid initial usage.
- Require legal lifecycle order and nonnegative sequential block indexes. Reject
  known deltas of the wrong block kind, writes after block close and events after
  message termination. Check required delta field shapes and token counters.
- Assemble text and partial_json tool input fragments without trimming or guessing.
  Parse the concatenated tool JSON only at block completion; require an object.
  Preserve block order and the observed final stop/usage values. Unknown event,
  block or delta extensions are INDETERMINATE, not assumed invalid or supported.
- Return SSE observations and the assembled message. Do not return T1 final-message
  observations against a fictional raw JSON document; the caller will validate
  the derived message with a separate derived-evidence capture ID. SSE locations
  refer only to actual event JSON using context.captureId and eventIndex; use a
  real parent plus missingKey, or omit an unsupported location. Never fabricate.
- EOF with missing required events or unfinished framing is FAIL when the capture
  is complete; timeout/cancel/limit makes unobserved completion INDETERMINATE.
  Actual observed defects survive either case. A partial tail must not turn a
  previously proven duplicate start into a pass or erase that observation.
- Error events are retained with honest non-success behavior outcome; do not infer
  the failing inference/gateway layer. Unknown service error structure is not a
  fabricated successful message. Keep the scope conservative and explicit.

First write meaningful RED controls. Reuse the four synthetic stream fixtures in
 tests/fixtures/contracts/core-1.0.0 as read-only references: valid, duplicate start,
invalid index and invalid tail. Add text split across events, tool JSON fragments,
wrong event/data type, unfinished/interrupted streams, duplicate/late events,
unknown extensions, UTF-8 and per-frame/event limits. A valid complete stream must
aggregate to PASS; a partial stream must not; known faults must remain FAIL. Do not
change old golden files. Historical code is reference, not current instructions.

## Delivery

Run focused SSE tests, then npm --prefix next run check once the coordinator's
parallel code is stable. Record RED/GREEN under ignored artifacts. No skipped/todo
controls, new dependencies, broad review restart, remote push or real endpoint calls.
One local owned-file commit, then send the coordinator interface/coverage/test
results and any remaining concrete uncertainty. The coordinator reviews/integrates.
