# Private comprehensive assessment method and boundary

The owner requested broader real testing of the most recently assessed private
model and removed API call cost as a constraint. This follow-up is a disposable
black-box assessment, not implementation or acceptance of shipped Stage B/C.
Private endpoint configuration, model identifiers, prompts, captures and detailed
reports remain outside the repository and image build context.

## Scope and execution

The frozen primary plan contained 79 direct API scenarios. Nine additional
confirmation/prerequisite scenarios and two valid-predecessor malformed-ID probes
brought the API inventory to 90. Four official Python SDK cases and three fixed
Claude Code workflows are recorded separately: 97 scenarios in total.

The shared authorization envelope was at most 200 upstream requests and 60 minutes.
The two recorded execution containers sent 123 and four requests respectively,
127 total; the second four-request/ten-minute cap remained within the original
aggregate envelope. Direct probes and Python SDK calls disabled retries. All 11
Claude Code request bodies were distinct; no automatic retry was observed, but the
CLI's internal retry setting was not explicitly overridden. Confirmation samples
have separate IDs and records; they do not replace failed attempts.

A private recording relay enforced the upstream budget, restricted destination
routes and stripped authentication before forwarding. Capture location is the
client request received at this relay; it is not visibility into service internals.
Direct probes and SDK traffic used API 2023-06-01 without beta headers, except
explicit missing/invalid-version controls. Claude Code's actual beta combinations
were captured per request; acceptance does not prove every beta's semantics.

The main container had a read-only root/source/harness, bounded tmpfs workspace,
ordinary-user execution and no host HOME, credentials or Docker socket. Generated
client workspaces were copied out before the tmpfs was removed. Public client
preparation was separate from real requests:

- Python SDK 1.15.0 was installed into an isolated temporary target; the project
  lock file and host Python were unchanged.
- Claude Code 2.1.292 Linux arm64 came from the official release channel. The slow
  raw download was stopped and retained as a partial artifact; the same version's
  compressed range downloads passed official compressed and binary SHA-256 checks.
- The primary disposable test harness passed six offline positive/negative controls.
  Seven additional offline applicability/audit controls passed after observed RED.
  These limited controls are not the shipped product's full acceptance graph.

## Observed results

The explicit reader-1.1 applicability audit reports 90/90 accounted API scenarios:
61 PASS, 18 FAIL, eight INDETERMINATE, one rejected optional endpoint request and
two BLOCKED prerequisites. These include different success criteria, so they are
not a unified compatibility percentage. Original probe checks and verdicts remain
in their immutable source files; the audit is a separate derived interpretation.

All four SDK cases passed: ordinary response, strict response parsing, streaming
assembly and a random-result tool loop. All three Claude Code workflows passed:
exact output-file bytes, repair of a Python function with unchanged independent
tests, and an actual Bash command producing a checked marker. Relay histories
also show the real Read/Write/Edit/Bash tool interactions. A fresh disconnected
container independently passed 100 generated arithmetic pairs against the repaired
function after the client finished. The client request split
was five SDK and 11 Claude Code calls; the remaining 111 calls were API probes.

Observed differences include missing stop fields, an unallowlisted declared model
name, fenced output under JSON Schema mode, incorrect stop-sequence metadata,
incomplete request validation and nonstandard error envelopes. A complex nonstream
tool-input sample failed once; three separately recorded confirmations passed.
Two valid named custom-tool prerequisites were rejected before the malformed-ID
request could be sent. A later real streaming predecessor enabled both ID controls:
an unmatched ID was accepted with HTTP 200, while a missing ID was rejected.

Manual/adaptive thinking requests did not establish a visible structured thinking
channel. Cache acceptance did not establish a cache hit. The token-count endpoint
returned 404. A single synthetic image-color answer does not establish general
vision support. No internal routing/weight attribution is made.

## Material interpretation rulings

1. Negative requests expect rejection, so generic positive-response 2xx checks are
   inapplicable to their outcome. The original checks are retained, not deleted.
2. Relay read/deadline interruptions are INDETERMINATE. A relay-generated 502 is
   not reported as an endpoint-generated HTTP 502; missing termination in an
   interrupted stream cannot establish a completed-response stop defect.
3. Current official Messages documentation permits max_tokens=0 for cache prewarming.
   The original negative oracle expecting rejection was incorrect. A separately
   versioned audit checks empty content, max_tokens termination and zero output
   tokens against the saved bytes instead; the observed response still fails this
   corrected condition. Both interpretations remain available.
4. A failed prerequisite cannot establish malformed-ID handling. The two initially
   blocked controls remain recorded, alongside the later valid-predecessor probes.
5. SDK/client tolerance does not rescore the fixed core rules. Defaults added by
   a client parser do not alter captured response bytes. A successful workflow is
   scoped to that fixed client/platform/task/sample, not complete compatibility.

Primary references consulted on 2026-10-16:
[Messages](https://platform.claude.com/docs/en/api/messages/create),
[tool definitions](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools),
[thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking),
[structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs),
[errors](https://platform.claude.com/docs/en/api/errors),
[cache prewarming](https://platform.claude.com/docs/en/build-with-claude/prompt-caching),
[Claude Code programmatic use](https://code.claude.com/docs/en/headless).

## Evidence and limits

The final offline report verified 799 file-hash references without errors. Machine
results include original plans/captures/checks, a separate quality audit, request
ledgers, per-request header combinations, tool histories, client outputs and
independent generated-artifact checks. Report links and status counts are checked
separately. Static reader-summary layout was inspected with all URL fetching
blocked; browser interaction and full print acceptance were not performed.

This is author-run private evidence, with no new independent whole-stage review.
The published CLI still exposes Stage A only. No source implementation, image
rebuild, remote CI, push or registry publication occurred. Complete cloud-service
coverage, arbitrary beta combinations, version-selection semantics, automatic
compaction, context-window limits and long-run reliability remain unproven.
