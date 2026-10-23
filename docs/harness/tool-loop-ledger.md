# Non-stream tool-result round trip

## User outcome and scope

Case `ANT-TOOL-LOOP-001`, version 1, profile `anthropic-tool-loop` adds one formal
endpoint scenario to the original four. It tests whether a tool result survives
the complete round trip and is used by the model. The original profiles and
their case versions remain unchanged. No real target is called during development.

1. Force one `get_weather` call for Hanoi, asking the model to return the eventual
   result's verification token. Check the response using existing message/tool rules.
2. Generate a fresh 128-bit hexadecimal token after receiving the first response.
   Preserve the assistant content, then immediately append a user `tool_result`
   bound to the observed `tool_use_id`. Disable further tool calls and check that
   the final text, apart from surrounding whitespace, equals the token and ends
   normally. Returning an arbitrary answer does not pass.

The result retains two sequential request/response exchanges under the case's
existing `attempts` storage field, indexes 1 and 2. These are conversation steps,
not retries or independent endpoint cases. A partial conversation cannot PASS.
Cancellation/deadline between steps sends no second request; prior evidence stays
available. HTTP/format failures and incomplete capture remain distinct outcomes.

## Use

In the Web configuration, select **Tool result round trip** on its own to reserve
two requests. All three installed profiles together reserve six; the new Web
configuration starts with that explicit request allowance. Saved configurations
retain their own limits. Preview sends no request; Start admits the live plan.

CLI, using a private target file and a new output directory:

```sh
anthropic-readiness run --target /path/to/private/target.yaml \
  --profile anthropic-tool-loop --allow-live --out artifacts/tool-loop-run
```

The target must declare tools and allow at least two requests. Each request and
the whole run retain configured time/capture limits. Single-capture CLI replay
cannot establish this conversation and is rejected explicitly. Complete run
evidence supports inspection, export and same-scope retesting; each retest uses
a fresh token. Protocol/behavior results remain separate.

## Evidence ledger

- Initial RED: all nine initial regressions failed because the profile was absent.
- Initial harness corrections: new tests incorrectly used an already-existing
  output directory and reused the transport's bound cancellation attribute.
  Corrected the test fixtures; retained all original logs.
- Focused engine/result/recipe checks: 46 passed. CLI/Web/report checks: 39 passed
  after adding the CLI test's explicit synthetic live opt-in and updating the
  catalog assertion from four to five. These are tool self-tests, not live endpoint
  compatibility outcomes.
- Fast graph initially failed the stale four-case assertion and lint style;
  type, architecture, schemas and frontend static passed. Final checks pending.
- One independent bounded review found that a final token plus another valid
  tool call could falsely pass. A dedicated RED reproduced PASS for that faulty
  response. Final content must now be text-only; all 17 closed-loop regressions
  passed after correction. A truncated result or checkpoint cannot claim PASS.
- Final strict typing passed for 183 checked source files. Earlier full attempts
  were interrupted and retained: one preceded the review correction; another
  exposed a test annotation issue and legacy browser workflows implicitly
  selecting the expanded default scope. Existing browser workflows now explicitly
  keep their original four cases, and a new browser test covers the expanded
  catalog/default budget and the new two-request case. No old expected outcome
  was weakened.
- New browser smoke passed: three profiles/six-request default, select only the
  round-trip case, zero preview calls, two execution calls, one PASS case. Final
  stable-source new-case browser verification also checks verified evidence.
- Local trial updated before whole-graph completion so the owner can try the
  tested feature. Cached current wheel installed offline into the same locked
  ARM64 Web dependencies; image revision explicitly identifies the worktree and
  image-context remains unknown. No full image matrix or new remote CI is claimed.
  Health/home returned success, new case is present, and the persistent data volume
  was retained. Both existing tasks were completed before restart. Trial service
  remains at http://localhost:8765. No owner endpoint was called by the agent.

Final closure on 2026-10-23:

- Additional end-to-end repair tests exposed two old single-exchange assumptions:
  comparison rejected repeated rule IDs across conversation steps, and report
  evidence typing rejected the new rule's request/body pair. Both were reproduced
  and corrected. Only this known two-step case combines comparison observations;
  statuses use conservative aggregation, retaining both sets of evidence. Duplicate
  checks within one step and repeated checks for other cases remain rejected.
  A first-step protocol failure cannot be replaced by a second-step PASS.
- Final stable-source fast graph passed all eight gates. Targeted execution,
  CLI/Web, report evidence and comparison checks passed 77 tests, including
  20 round-trip-specific regressions. The new browser flow passed with verified
  evidence. The corrected catalog page and installed packages passed six checks.
- The completed broader graph retained three failures from old four-case catalog
  and four-request browser-fixture expectations. Those expectations were updated
  explicitly and the affected checks reverified. A later 79-test browser run had
  all actual tests pass, but its graph detected unrelated test-source edits during
  execution, so its aggregate is not accepted as unchanged-source verification.
  Final new-case browser/fast checks use stable source. No single green final-source
  full graph, new remote CI or full native image matrix is claimed.
- One direct pytest retry lacked the repository module path; it ran zero tests
  and is retained as a collection error. The module-based retry passed.

The controlled oracle requires a text-only, exact token echo after surrounding
whitespace is removed. Extra explanation or another tool call fails that bounded
task; such failure alone does not prove that a gateway dropped the tool result.
The final trial runs feature commit `eb82c90` at http://localhost:8765. All 157
installed package files match the final source. Health/home checks passed and
both previously completed runs remain present. Five final installed-package
checks also passed after the last code corrections. The feature is local only;
no push or genuine endpoint assessment was performed. Owner trial feedback is
the next checkpoint; no further feature is underway.

Logs are ignored under artifacts/ci-startup-20261022/tool-loop-*.

## Owner trial follow-up: bounded independent raw requests

On 2026-10-23 the owner requested independent endpoint confirmation after a
five-case/six-request run completed all controlled behaviors but failed the
message structure check. Its stored evidence verified successfully. Four
non-stream response copies passed the core check after adding only a null
stop_sequence in memory; original evidence was unchanged. Both stored stream
samples lacked the nullable stop fields but had normal completion events.

Under explicit live opt-in, two independent direct HTTP requests bypassed the
assessment engine: one non-stream and one stream, no authentication, no retry,
128 max_tokens each, 40-second per-call deadline within a 90-second budget.
Both returned HTTP 200 and the requested text in approximately one second.
Missing stop_sequence was reproduced. The new stream also contained a second
message_start between its text delta and content_block_stop, followed by a
normal message_delta/message_stop. Neither earlier stream sample showed that
duplicate; frequency and component attribution are not established.

Nullable-field omission is a contract deviation, not proof of a client failure.
The current official Python Message model defaults stop_sequence to None; the
official TypeScript stream accumulator rejects a second message_start before
message_stop. These source observations explain possible tolerance and risk,
but the owner's installed Claude Code path/version was not tested. The owner
reports that it currently works. No additional live requests or source changes
were made. Private requests/responses and summary remain ignored under
artifacts/live-kimi-field-check-20261023/; do not publish them.

## Limits and protocol reference

This covers one non-stream client-tool call and one successful synthetic result,
with no retries. It does not establish streaming or parallel tools, error-result
recovery, long conversations, SDK/Claude Code workflows or general tool-use
reliability. Detection of a failed token echo alone does not identify which
inference/gateway component caused it. Passing the step does not erase protocol
failures elsewhere in either exchange.

The [official client-tool lifecycle](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls),
consulted 2026-10-22, specifies retaining the assistant tool call and matching its
ID in the immediately following user result. The random-token oracle is this
tool's controlled behavioral check, not an official certification requirement.
