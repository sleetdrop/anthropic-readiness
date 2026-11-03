# Current rewrite progress

Use [the active harness index](README.md), [development](../development.md) and
[the rewrite entry point](../refactor/README.md). The prior 2,213-line mixed
progress record is preserved verbatim as [historical evidence](progress-legacy.md).
Its environment requirements and PASS results do not apply to the rewrite.

## 2026-11-01: rewrite baseline 7f836d1

Owner-approved local-first TypeScript/Node replacement, with containers deferred.
Added next/ shared observations/evidence locations, five-case/six-request migration
inventory and five core controls. Initial missing-implementation RED preceded
passing strict types and five Node tests. An isolated copy installed its own
locked dependencies offline and passed; an earlier offline preparation cache miss
was preserved separately. No Python/container dependency or endpoint runner.
The old delayed-session browser test draft remains an ignored patch, not an
executed fix. Original main CI failures/traces and PR 4 outcome remain retained.

## 2026-11-01: active harness cleanup

Reviewed current guidance, hooks, contribution/PR templates, CI and historical
entry points. Removed active Python/container/full-matrix requirements, archived
old guidance/workflows and reduced current navigation to short entry points.
Pre-commit, root check forwarding and the single Node CI job now use the same
TypeScript check command. Added actual-test-report acceptance that rejects empty,
skipped/todo/cancelled, inconsistent and failing executions, with saved logs and
machine-readable outcomes. A regression reproduced the legacy runtime references
before hooks/CI were changed. Final strict types and seven executed Node tests
passed with zero failures/skips/todos; root forwarding also passed. Local links
were checked across 67 Markdown documents. The new CI YAML and hook were reviewed
locally, not run on GitHub or installed as a global hook. Existing historical
records/workflows were copied byte-for-byte before replacing active entry points.

This is supporting-only work: no additional endpoint scenario, protocol fault
validator, SDK workflow or actual model call was implemented by the cleanup.
No remote push, Actions execution, registry change or existing data migration.

## 2026-11-01: T1 integration and bounded HTTP capture

Owner-created chat 01a1957d-20a0-7491-aefb-2a509bc9a836 delivered T1 in 189ff93.
One coordinator review reproduced an overly strong judgment for unknown stop
reasons paired with string stop_sequence; correction 2932a74 keeps that relation
inconclusive, retains proven type defects and improves whole-result valid controls.
The root-shape observation no longer claims every message field is complete.
T1 implemented JSON node/parent-missing locations without changing shared types.

The coordinator independently implemented a one-attempt Node HTTP adapter with
exact encoded application bytes, duplicate response headers, explicit Host,
no redirect following/retry, bounded byte retention, connect/TLS/idle/absolute
limits and cancellation. Safe error codes do not echo private request data.
Initial raw-header requests lacked Host and yielded synthetic HTTP400; the
correction passed the same controls. A separate RED reproduced missing-limit
acceptance before explicitly validating every limit. Initial denied loopback
binds remain recorded separately from permitted local-service verification.

Final integrated strict types and 29 executed Node tests passed, with no skips,
todos or failures: 12 T1, 10 transport and seven earlier core/harness controls.
Evidence is ignored under artifacts/configuration-startup-20261101/ and
next/artifacts/protocol-t1-20261101/. No new endpoint case execution, real model
call, SDK workflow, SSE validator, CLI/Web flow or remote CI is established here.

## 2026-11-01: T2 protocol direction continues in the existing chat

Assigned bounded SSE framing/lifecycle/assembly work to the same implementation
chat under docs/refactor/task-02-sse-validation.md, retaining its model and context.
The coordinator owns runner/CLI paths; T2 owns only the listed pure protocol/test
files. The public SSE result contract is specified before parallel integration.
No new execution or acceptance is claimed by this task assignment; CLI integration
and a usable first migrated endpoint run remain the next hands-on checkpoint.

## 2026-11-01: reviewed five-scenario Node CLI trial

T2 da4c677/7fc630b was integrated after limited review: preserve captured event
objects during assembly, classify parser resource caps as environment limits,
retain incomplete capture, keep valid empty tool input, avoid fabricated JSON
locations and distinguish service-error termination from the successful lifecycle.
Coordinator controls also corrected repeated message_delta/intermediate null stop
reasons against official streaming/SDK sources, and a whitespace JSON-null bug.
References: https://platform.claude.com/docs/en/build-with-claude/streaming and
https://github.com/anthropics/anthropic-sdk-typescript/blob/main/src/resources/messages/messages.ts

Baseline 1706639 introduced shared execution and the actual CLI. One independent
limited review found three behavior false-passes; RED controls reproduced them.
Plain/streamed text now asks for exact HELLO, counting exact 1 2 3 4 5, and tool
result completion rejects extra tool calls. Relevant cases advance to revision 2;
no old golden/capture was changed. Request bodies/hashes retain the nonce evidence,
without request auth headers. Tokens and all time/capture bounds are configurable.
The rewrite has its own development rule snapshot and typescript-run/1 result,
not an assertion that the old bundle/readers have been ported unchanged.

Final Node24 strict types and 60 executed tests passed, zero skips/todos/failures.
A real CLI subprocess ran all five cases/six requests against synthetic services,
wrote reports and pre-validation raw captures, excluded authentication values,
refused directory reuse, and verified fresh nonces across repeated runs. Original
REDs and denied loopback attempts remain in ignored artifacts. Test transcripts:
artifacts/configuration-startup-20261101/cli-delivery-final-check.log and earlier
review/negative-control logs; next/artifacts/protocol-t2-review-20261101/.

This implements the five migrated endpoint scenarios in TypeScript, not broader
live coverage: only synthetic services were tested. No actual model, SDK/Claude
Code workflow, new Web UI, compressed-body decoder, duplicate-key parser, HTML/ZIP
export or legacy archive reader is established. No remote push/CI or container run.
See docs/refactor/cli-trial.md for preview/live opt-in and remaining scope. The
implementation chat received final closure after a quota-blocked notification was
successfully retried; no further broad review or new planning cycle was started.

## 2026-11-01: first real Node CLI trial

With owner authorization, revision 058cec9 ran all five migrated scenarios against
the selected private local endpoint, without authentication, capped at six
attempts/five minutes (30 seconds per attempt). All six responses were HTTP200,
complete, and finished in about 8.6 seconds. All five task outcomes passed,
including nonce-only tool-result consumption. No retries or additional calls.

Raw inspection confirmed omitted stop_sequence fields in all six final messages;
both stream starts also omitted stop_reason/stop_sequence, and their message_delta
omitted stop_sequence. Requested and reported model names differed; the default
identity rule failed, but this alone cannot establish wrong routing. A maintainer
can confirm an explicit alias in a future run. Thinking/delta inconclusive results
are an unsupported validator scope, not confirmed endpoint defects; the derived
message does not assemble thinking fragments, while original event data survives.
Manual source comparison used the official SDK Message/RawMessageDeltaEvent,
ThinkingBlock and SignatureDelta definitions; it did not update the rule snapshot.

Private original evidence and a Chinese interpretation are retained outside source
at /private/tmp/readiness-live-20261101-01/. All six request/response body hashes
were independently recomputed and matched. No target names, credentials or original
captures were added to tracked artifacts. SDK/Claude Code remain untested. This
trial adds real sampled outcomes, not new scenarios or comprehensive compatibility.
No source behavior changed, so the unchanged 60-test evidence was reused rather
than rerunning offline checks. No remote write, container or remote CI run.

## 2026-11-01: product direction audit and delivery correction

The owner identified repeated reactive, case-by-case delivery and the absence of
a visible rewritten application. Reviewed intends, active guides/source/catalog,
design baseline and CI. Intent still includes broad Messages coverage, CLI/Web,
real clients, version maintenance and colleague/Agent repair verification. Active
source has only five scenarios/CLI; naming future goals had not constrained the
migration-first delivery sequence. There is no new Node Web server/UI or client
workflow. Offline test counts and one successful task sample do not close those gaps.

Updated the existing route rather than adding another implementation-plan chain:
A is a usable application with expanded core Agent workflows; B completes selected
Messages contract coverage and repair replay/reruns; C closes actual-client,
snapshot-maintenance/handoff and cutover; D defers distribution. Added a single
product coverage/gap inventory, linked it from intent/entry guides, and made
coherent checkpoints rather than individual-case approval the delivery unit.
No protocol cases, UI, rules or source behavior were implemented by these notes.

Official version history/reference reviewed on 2026-11-01 documents 2026-10-21:
https://platform.claude.com/docs/en/api/versioning and
https://platform.claude.com/docs/en/api/migration-2026-10-21.
Current runner still sends 2023-06-01. Its hard-coded rules label is not an immutable
source manifest. Earlier manual comparison to SDK main/latest docs supports a
source comparison, not a completed version-specific audit. Original observed fields
and report remain unchanged; future snapshots/replay must state exact applicability.

Documentation-only validation: changed-file local links and git diff --check;
unchanged 60-test source evidence reused, no new test/CI/live outcome claimed.

## 2026-11-01: owner updates the product purpose

The original private model incident has ceased to be the product driver. The owner
defines the tool as a systematic assessment of the actual Anthropic Messages
compatibility of self-hosted APIs claiming that protocol. Consumers and providers,
selected version/features, actual behavior/deviations and explicit coverage limits
now define the workflow. A particular colleague, model problem or Claude Code
incident is not a prerequisite. Sharing and repair reruns remain optional uses.

Updated intent, current guides, coverage inventory and existing delivery route.
SDK/Claude Code assessments remain separate supplementary features; their absence
does not block the core protocol tool or determine its overall verdict. Controlled
tasks exercise protocol behavior rather than rank model quality. Generic across
Anthropic-compatible implementations does not expand this project to OpenAI or
other protocol families. Accepted design and local-first Node constraints remain.

Documentation-only change: checked affected local links and diff whitespace;
no scenarios, assertions or UI were added. Reused unchanged-source verification;
no additional live calls, remote writes or CI result.

## 2026-11-01: existing alternatives found; feature development stopped

The owner requested fresh research and explicitly directed abandoning further
development if this category already has tools. Primary repository/package/site
inspection found direct matches: llm-comply (actual Anthropic test definitions,
local CLI/Web and schema refresh) and ModelsExam (Web assessment/reporting).
PyPI records llm-comply 0.5.0 on 2026-09-12; it predates this project's October
development. The earlier lack-of-alternatives assumption was incomplete research.
See docs/reviews/2026-11-01-existing-tools.md for sources and verification limits.

Stopped feature development under that instruction and marked intent, entry guides,
the retained route and coverage accordingly. No candidate installed or run; no
private target/config/credential sent to any service. No data deletion, GitHub
archival or remote push. This documentation-only disposition adds no scenarios;
local link/whitespace checks suffice and unchanged tests were not rerun.

## 2026-11-02: pinned candidate maturity assessment

Reviewed llm-comply at 78421338385e69f6ae2b055074d03be2ff8739a4, its release
metadata, actual definitions/runner/validators, CI and scheduled refresh logs.
Alpha release 0.5.0 has nine Anthropic cases; head has 19 and is 109 commits ahead.
Head CI passed. The latest inspected scheduled refresh failed on a Google schema
count after download, blocking its PR; not an Anthropic network failure.

With an in-memory synthetic transport, baseline stream passed and missing-stop
control failed. Repeated message_start, unopened-index text delta, malformed
event JSON, invalid streamed-usage type and invalid error envelope passed their
selected head checks. Non-Claude thinking selection skipped. Additional semantic
checks/serialization inspection exposed task-consumption and portable-evidence
limits. Full non-streaming schemas/upstream suite/GUI were not run. No source rule
was modified for these probes. Used existing local Python/jsonschema only as a
research utility, adding no Python dependency to the Node project.

The earlier existence research did not establish a mature full replacement;
corrected that inference without automatically resuming independent development.
Recommendation: retain stopped source/evidence and favor adoption/contribution or
a narrow fork over restarting the whole product. See
docs/reviews/2026-11-02-llm-comply-maturity.md and ignored
artifacts/llm-comply-maturity-20261102/ for source, probes, output and metadata.
No third-party installation, model requests, public issue, remote write or product
implementation occurred. Local documentation links/whitespace checked; unchanged
product tests were not rerun.

## 2026-11-04: incident diagnosis Skill prototype

The owner authorized an incident-first prototype after discussing Skill, MCP and
plugin roles. Added a repository-scoped Skill, offline exercise and read-only Node
inspector for successful Messages JSON/SSE bodies. It reuses existing validators,
returns located findings plus evidence hashes, and keeps incomplete capture and
unchecked identity explicit. Fresh probes refer to the existing CLI and require
their own authorization and bounds. No new live endpoint scenario was added.

Three focused checks initially failed because the inspector did not exist; all
passed once implemented. The first full check found a readonly return mismatch;
the diagnostic is retained in ignored artifacts/incident-skill-20261104/. After
correction, Node 24.22.0 strict types and all 63 tests passed, no skips or failures.
Skill metadata validation passed. A local walkthrough located the duplicate
message_start at zero-based event index 1; the valid and faulty fixtures differ
only by that event. The partial stream remained inconclusive. This was not an
independent Agent run, live model/client test or installation. Standalone
development remains stopped; no remote operation was performed.
