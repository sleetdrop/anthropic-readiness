# Current implementation review — 2026-11-05

This is a historical review. Its findings were addressed in subsequent work;
see the [verification record](../verification.md). Paths and commands below
refer to the reviewed checkout.

Reviewed commit: `3503816`. Scope: the active diagnosis Skill, Node CLI,
transport, protocol validators, probe execution, report generation, tests,
development checks, and current documentation. The historical application is
outside this review. No production implementation was changed.

The architecture fits the stated incident-diagnosis goal: pure validators,
separate I/O adapters, explicit execution bounds, preserved response bytes,
and distinct protocol, behavior, and client outcomes. The most important next
work is judgment correctness and evidence fidelity. Four reproducible defects
remain despite the passing repository gate.

## Validation

- Installed locked development tools with `npm --prefix next ci`.
- Ran `npm run check` on Node `v24.22.2`: strict types passed; all 75 tests
  executed and passed, with no skipped, cancelled, or TODO tests.
- The first restricted run could not bind its loopback servers. Repeating the
  same gate with local server access passed; the initial failures were not
  classified as product defects.
- Ran an additional bounded synthetic review driver twice, seven loopback
  requests per invocation. The final invocation compares identical SSE bytes
  through the offline inspector and online engine. Each engine run had a
  two-second deadline. No credentials or real endpoint calls were used.
- Checked the relevant current Anthropic documentation and SDK implementation.
- Browser layout, real SDK/client behavior, hosted CI, and real endpoint
  compatibility were not executed in this review.

Local, ignored reproduction artifacts:

- `artifacts/review-2026-11-05/reproduce.mts`
- `artifacts/review-2026-11-05/results.json`
- `artifacts/review-2026-11-05/normal.sse`
- `artifacts/review-2026-11-05/null-final-stop.sse`
- `next/artifacts/checks/result.json`

Run the review driver with Node 24 from the checkout root:

```sh
node artifacts/review-2026-11-05/reproduce.mts
```

The driver records current behavior; it is not a replacement for regression
tests that assert the corrected outcomes. Its local artifacts are not committed.

## Findings

### R1 — P1: Token-limit probes pass an explicitly over-budget response

Location: `next/src/runner/probes.ts`, lines 516–521; request-specific protocol
checks in `checkResponseContract` also omit the output bound.

The two max-token presets send `max_tokens: 1`, but their task check only tests
`stop_reason === "max_tokens"`. A complete response containing numbers 1–50
and reporting `usage.output_tokens: 100` passes protocol, behavior, and aggregate
checks in both JSON and SSE. The one-token control also passes, so the probe
cannot distinguish compliance from the tested violation.

This can mislead an endpoint assessment into accepting a service that ignores
the generation bound. The existing all-presets test also returns
`output_tokens: 3` for these one-token requests and expects every case to pass.

Add a request-aware protocol rule for the output bound, keeping stop-reason
behavior separate. Include requested and reported values and an evidence
location. Correct the passing fixture and retain over-budget negative controls
for both formats. Do not infer token counts from visible character counts.

Contract: [Create a Message](https://platform.claude.com/docs/en/api/cli/messages/create)
defines `max_tokens` as an absolute generation maximum.

### R2 — P1: Offline SSE inspection accepts an invalid final stop reason

Location: `next/src/cli/inspect.ts`, lines 106–114;
`next/src/protocol/sse.ts`, lines 405–417.

Starting from `stream-valid.sse`, change only the final delta's
`stop_reason: "end_turn"` to `null`, retaining the complete framing and
`message_stop`. The offline inspector returns `PASS` with no findings. The
online engine reports a protocol `FAIL` for the identical response bytes.

The SSE validator permits intermediate null stop reasons but never requires
a valid final reason at termination. The engine additionally validates the
assembled message; the offline inspector only reads the SSE observations.
The primary offline diagnosis workflow therefore misses a fault the engine
already knows how to detect. The fixture's text is not the greeting requested
by the online preset, so the separate online task failure is unrelated to this
protocol comparison.

Share final-message validation between both entry points, or validate final
state in the SSE state machine. Preserve raw event locations where possible,
and keep incomplete captures inconclusive. Add a parity test using identical
bytes with model-identity checking configured consistently.

Contract: [Messages reference](https://platform.claude.com/docs/en/api/typescript/messages)
describes the null initial streaming stop reason and non-null final value.

### R3 — P2: An unfinished stream can be counted as a passed exact-output task

Location: `next/src/runner/assessment.ts`, lines 426–435.

A synthetic peer sends a complete text block containing `HELLO`, then stalls
before `message_delta` and `message_stop`. The capture ends in `read_timeout`
with `messageComplete: false`. Aggregate and protocol outcomes are correctly
`INDETERMINATE`, but `behaviorStatus` is `PASS`. The complete-response control
also reports a task pass.

`addTask` accepts a successful text comparison before considering incomplete
capture state. An exact-output task cannot be established from a prefix:
another text or tool block could have followed. The HTML summary then counts
this unfinished task among passed tasks.

Require sufficient message and capture completion before an exact-output task
can pass. Model individual multi-round stages explicitly so a completed first
stage remains recorded while an unrun or incomplete continuation stays
inconclusive. Add stalled-stream and interrupted-follow-up controls.

### R4 — P2: Assembled SSE usage silently drops cumulative updates

Location: `next/src/protocol/sse.ts`, lines 429–434.

The assembler only copies `message_delta.usage.output_tokens`. A stream with
initial `input_tokens: 2` and final usage `{input_tokens: 9, output_tokens: 1,
cache_read_input_tokens: 7}` passes, but its assembled usage remains
`{input_tokens: 2, output_tokens: 1}`. The raw events retain the correct values.

This makes the derived message in `result.json` inconsistent with its evidence
and can mislead subsequent analysis of input usage and cache behavior. It does
not corrupt the original capture, and the current JSON-only cache preset is
not directly affected.

Validate and overwrite supported cumulative usage fields when present, retain
prior values when omitted, and never add cumulative totals together. Add a
control that compares the final wire usage with the assembled object while
checking that the original event objects remain unchanged.

Reference: the [official TypeScript SDK accumulator](https://github.com/anthropics/anthropic-sdk-typescript/blob/main/src/lib/MessageStream.ts)
updates input and cache counters when supplied by `message_delta`.

## Improvements after the correctness fixes

1. **Make the saved-record path one command.** The Skill currently asks the
   agent to decode `bodyBase64`, verify the hash, inspect encoding and capture
   completeness, then invoke the inspector. Add an adapter for repository
   capture records that performs those operations deterministically. Keep
   protocol validation pure and retain the original bytes.
2. **Select a single case and preview its request.** The CLI accepts profiles
   rather than case IDs. A focused max-token investigation currently selects
   six text cases and reserves seven requests. A case selector and sanitized
   request preview would better support the smallest discriminating probe.
   Maintain explicit live opt-in and request/time caps.
3. **Make evidence links lead to readable protocol data.** Response files are
   persisted before parsing, and their viewers show the capture envelope with
   base64 bodies. Parsed events and assembled messages live in `result.json`.
   Add separate decoded views with event/field anchors and source hashes;
   never replace original evidence. Also retain exchange identity on HTTP and
   task observations so multi-exchange findings can link the right response.
4. **Retain diagnostic timing.** The HTTP adapter measures `headersMs` and
   `firstByteMs`, but `CaptureRecord` discards them. Preserve these fields and,
   if needed for a stalled-stream incident, bounded chunk/event arrival
   metadata. A single run should not be described as latency distribution.
5. **Strengthen test independence.** Prefer paired normal/faulty controls and
   cross-entry-point invariants over merely running more happy-path presets.
   Start with R1–R4. Track rule-to-fixture coverage and pin source/retrieval
   metadata for version-sensitive rules. The current 35-case catalog is a
   useful inventory; it does not establish completeness of the checker.
6. **Keep the architecture small.** Extract a shared capture-evaluation function
   and explicit multi-round stage results where they remove observed drift.
   The current scale does not justify adding a generic plugin system, a new
   standalone web application, or a large orchestration framework.

The existing execution limits, no-redirect transport, restrictive output file
modes, synthetic HTTP tests, raw capture hashes, and separation of client
coverage should be preserved during these changes. Automatic HTML escaping
and a script-hash CSP are also useful properties; this was not a security audit.

## Recommended order

1. Fix R1 and R2 and add meaningful failing controls first.
2. Fix R3 and R4, including report counts and raw/derived evidence consistency.
3. Improve capture-record inspection and targeted case selection.
4. Add evidence navigation and timing only where incident work benefits.

All four findings were open at review time. They were repaired and covered by
synthetic regressions on 2026-11-05; see the [verification record](../verification.md)
for the fixes and final gate. This review makes no blanket compatibility claim.

## Follow-up review — 2026-11-05

Independently reviewed the uncommitted fixes and reran the Node 24.22.2 gate:
strict types and all 81 tests passed. The original seven-request loopback
reproducer confirms the R1–R4 fixes while retaining the normal controls.
One new issue in the saved-record adapter remains open; commit approval was
withheld. No production code was changed during this follow-up review.

### R5 — P2: Saved count-token records are misclassified as Messages

Location: `next/src/cli/inspect.ts`, lines 80–85 and 157.

The new `--record` adapter maps every successful `application/json` response
to `message`, discarding the capture's `route`. The runner's count-token
captures carry `route: "count_tokens"` and legitimately contain only a token
count. A complete HTTP 200 record containing `{"input_tokens":42}` with a
valid SHA-256 hash is therefore reported as `FAIL`, with eight spurious missing
Message-field findings. The existing `validateAuxiliary(..., "count_tokens")`
returns `PASS` for the same body. A normal Message record passes the adapter.

Preserve the route and dispatch count-token records to the existing auxiliary
validator. If the new entry point intentionally supports only Messages,
explicitly reject unsupported routes instead of emitting protocol failures.
Add normal and malformed count-token controls, plus incomplete-capture coverage
so partial evidence cannot produce a passing count result.

The synthetic records and inspector outputs are retained locally under
`artifacts/review-followup-2026-11-05/`. Reproduce the incorrect result with:

```sh
node next/src/cli/inspect.ts --record artifacts/review-followup-2026-11-05/count-tokens.json
```

The normal control is `normal-message.json` in the same directory. This finding
was reproduced offline and required no endpoint requests.

Resolution — the adapter now retains `route: "count_tokens"` and uses the
existing auxiliary validator. Synthetic controls cover valid, malformed and
incomplete count-token records; the existing Message path remains passing. The
regression failed before the fix and the Node 24.22.2 gate passes all 82 tests
afterward. See the [verification record](../verification.md).
