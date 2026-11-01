# Delivery workflow review

Status: historical findings and recommendations, not an implemented CI policy change.
The owner subsequently approved the [local-first TypeScript rewrite](../refactor/README.md),
including no initial container dependency. That decision supersedes the Python CI
optimization proposal below; do not implement both approaches as concurrent projects.
Requested by the owner on 2026-11-01 after publishing accumulated local work.
This review and the associated configuration-startup repair add no endpoint cases.

## Evidence and cost

PR 4 published 50 commits spanning product work, interface prototypes and handoff
records; this was a delayed integration batch, rather than a small merge of a few
commits. It required three PR CI runs and one post-merge run:

| Run | Observation |
| --- | --- |
| [41267386643](https://github.com/sleetdrop/anthropic-readiness/actions/runs/41267386643) | Image-page inventory still assumed four cases; expanded browser suite hit its total deadline. |
| [41268709597](https://github.com/sleetdrop/anthropic-readiness/actions/runs/41268709597) | Corrected image smoke passed; browser suite still exceeded its old deadline. |
| [41270232637](https://github.com/sleetdrop/anthropic-readiness/actions/runs/41270232637) | All required PR jobs passed. Python 3.11 took 11m26s, Python 3.12 14m08s, Dev Container 12m42s. |
| [41271562798](https://github.com/sleetdrop/anthropic-readiness/actions/runs/41271562798) | Python jobs and runtime smoke passed; Dev Container found a configuration startup race. Its browser suite finished in 434s: 108 passed, one failed. |

The retained final host fast graphs took approximately 43 and 47 seconds. These
are limited Mac checks, not substitutes for Linux, installed-image or browser
acceptance. The PR's three full quality/container jobs consumed about 38 runner
minutes in parallel; their wall-clock critical path was about 14 minutes. Do not
add parallel job durations together and call the result user waiting time.

## Findings

1. Integration feedback arrived too late. Product changes and acceptance-harness
   assumptions drifted on a long-lived local branch. Inventory and total-suite
   timing failures should have been found when the fifth case and additional UI
   tests were introduced, rather than during eventual publication.
2. The default workflow repeats the full graph on Python 3.11, Python 3.12 and
   the Python 3.12 Dev Container, then repeats it after merging. This includes the
   same frontend browser suite six times across PR/main. Container configuration
   does need validation, but need not duplicate every product assertion on every
   unrelated change. The weekly full native image matrix also remains available.
3. Cheap and expensive stages are insufficiently separated. A stale image-page
   assertion or static failure still consumes unrelated full browser work. There
   is no convenient supported focused browser-check entry point; callers have to
   assemble fixture, output and cleanup settings themselves.
4. Shared test fixtures limit easy parallelism. Browser tests reset a shared peer
   and use a common fixture root/port. Increasing worker count without per-worker
   isolation would introduce interference rather than reliably shorten CI.
5. Test stability is part of product correctness. The retained failure shows input
   before asynchronous initialization being overwritten; adding retries or sleeps
   would conceal a user-visible race. The proper regression holds session setup
   explicitly, enters data, and verifies preservation and request ordering.
6. Failure summaries lose useful detail. An inner browser timeout was surfaced by
   the outer gate as missing_prerequisite. The real reason required downloading
   artifacts. A small machine-readable stage summary should surface the failing
   leaf, reason, testcase and artifact link directly.
7. Process overhead exceeds the size of some changes. Numerous overlapping
   handoffs and manual ledger updates invite stale status and conflicts. The
   source handoff still said PR 4 was open after it merged; recording final CI in
   another source commit would itself trigger more CI. Repeated log reads and
   broad reruns without a new hypothesis also spend agent time unnecessarily.

## Recommended next policy, in order

- Finish this single startup repair with deterministic RED/GREEN and the related
  configuration/import/browser flows, one fast graph and one independent review.
  Keep workflow redesign out of that behavior patch. Publish when authorized.
- Use one bounded user-visible outcome per branch/PR. Once remote publication is
  authorized, open an early draft rather than accumulate another long local batch.
  Reuse unchanged-source evidence for unaffected checks; do not repeat the whole
  local graph after every documentation or review step.
- Separate one authoritative Linux/Python 3.12 full graph from the supplemental
  Python 3.11 backend compatibility checks. Run the browser suite once per PR.
  Keep runtime image smoke as packaging acceptance. Validate the actual Dev
  Container with a targeted preparation/CLI/Web smoke; run its full graph on
  environment/toolchain changes and scheduled/manual acceptance. Define explicit
  change categories, required jobs and aggregator tests before implementing this.
- For main, retain an installed-artifact smoke and scheduled complete acceptance.
  Reuse PR evidence only when the merged content tree, toolchain and relevant
  environment match and trusted workflow provenance is established. Otherwise run
  the full check. Do not reuse arbitrary fork artifacts as executable input or
  mark an unrun environment PASS. This is a proposal, not existing behavior.
- Cache only public locked dependencies/browser downloads using OS, architecture,
  lock and tool versions. Improve failure summaries and add a supported focused
  browser command before attempting parallelism. Measure warm/cold timings before
  choosing a CI time target; no timing reduction is established by this review.
- Keep CONTINUE as a concise current-state index. Keep historical evidence in its
  original ledger and link immutable Actions runs for final remote outcomes.
  Avoid a new plan, approval cycle or status-only source commit for every small
  step. Wait in one background watcher at the owner's preferred cadence; inspect
  failures once there is an actionable result rather than repeatedly narrating
  unchanged state. Waiting frequency changes detection latency, not runner speed.

Keep strict typing, schemas, meaningful regressions, evidence integrity, explicit
live opt-in and no secret publication. These protect the diagnostic result; the
optimization is to remove redundant execution and coordination, not these rules.
No workflow, required-job policy, repository protection or cache was changed by
this review. It does not certify the remaining broader protocol/client coverage.

## Architecture reconsideration after owner feedback

The owner explicitly permits substantial changes and questions maintaining Python
plus frontend tooling and multiple Python versions. This supersedes any assumption
that the existing stack or compatibility floor must be preserved. Investigation
found Python 3.12.15 selected for development/container execution, a >=3.11 package
floor and two full CI versions; these are distinct choices, not uv/Docker requirements.
The frontend is JavaScript with JSDoc checked by TypeScript, not a separate
TypeScript service. The backend currently uses httpx directly and no Anthropic SDK.

An official TypeScript SDK exists with SSE, raw Response access and custom fetch:
https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/typescript
A TypeScript-only CLI/server/UI is a credible simplification. Protocol-byte
validation still needs independent checks; SDK acceptance is a separate outcome.
Changing language alone does not fix the observed browser startup race or prevent
redundant CI and process overhead. The owner subsequently authorized the rewrite;
the active entry point linked above records its actual implementation status.
The delayed-session regression draft remains unverified and preserved as an ignored
patch; it is not claimed a completed fix in either implementation.
