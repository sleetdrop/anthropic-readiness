# CI Startup Probe Correction

**Scope:** Owner-authorized diagnosis and local correction of PR 1 acceptance failures. Continue sequentially in the existing checkout/container; no remote rerun, push or merge in this task.

**Observed evidence:** Both remote Python 3.12 environments failed the five-second startup probe, followed by unclosed-pipe warnings in later report tests. The original probe discards child diagnostics on failure and does not close stdout/stderr there. Local original startup/report acceptance passed 14 cases. A controlled two-burner/single-CPU diagnostic observed listening at 2.94 seconds but no complete health response until 6.49 seconds with repeated 200-ms request timeouts; the same setup with a one-second request allowance returned healthy at 3.63 seconds. This reproduces a false-negative probe mechanism, not proof of the unrecorded historical CI timing.

**Design:** Keep the overall five-second readiness deadline and existing signal/shutdown assertions. Let each health request use the remaining readiness budget instead of cancelling healthy cold responses at 200 ms and repeatedly resending them. Detect early child exit; preserve its return code/stdout/stderr. Own Popen through a context and always terminate/reap it on exceptional paths. No production API, schema, assertion inventory, package or global gate deadline changes.

## Sequential task and ledger

- [x] Observe RED for real-child early-exit diagnostics/pipe cleanup and a delayed healthy local response inside the existing five-second budget.
- [x] Apply the minimal probe correction; observe GREEN for all regression and original startup/report cases. Retain failed attempts.
- [x] Re-run the controlled unchanged-budget experiment using the corrected request policy, then static checks and the full offline Linux graph.
- [x] One independent bounded review, fix material findings, update current handoff/progress; deliver a scoped local commit and stop the container. No remote write or retry.

**Review focus:** Child exits before ready; child stays alive but never ready; a valid cold health response exceeds 200 ms but fits the shared deadline; SIGTERM semantics and optional-dependency behavior remain intact; no pipe/listener/subprocess leaks or warning suppression.

**Limits:** Prior CI lacks child stderr on startup failure. Preserve this uncertainty even after a successful local correction. The extreme eight-burner probe exceeded its diagnostic window and was killed; do not represent it as a healthy startup observation. Measurement artifacts are ignored under `artifacts/ci-startup-20261022/`.

## Observations and rulings

- Baseline original startup/report acceptance: 14 passed in 4.19 seconds. Native startup probe measured 1.57 seconds to health; this does not reproduce historical CI failure by itself.
- RED: Real child exiting 23 demonstrated open stdout/stderr and discarded synthetic stderr in two cases. A real local 300-ms health response failed under repeated 200-ms cancellation. Logs red-probe.log and red-cold-response.log are retained.
- GREEN: All three regressions plus original startup/report cases passed (17 total, 4.04 seconds). Ruff passed. Initial mypy objected to accessing an imported module attribute through the acceptance module; patching the already shared subprocess module directly fixed typing without behavioral changes, then mypy passed.
- Controlled old/new comparison under the same two-burner/single-CPU setup: original failed at 5.138 seconds with two open pipes; corrected passed at 3.929 seconds with zero. The diagnostic comparison initially missed the repository harness import path, then was rerun with PYTHONPATH set; both attempts are retained.
- Ruling: Remove the accidental 200-ms per-request cancellation, not the five-second readiness deadline. A success arriving after that deadline is explicitly rejected. Failure now includes child return code, last HTTP status/error and captured streams; Popen context closes pipes on every exit. No warning is suppressed, and the original eight-second SIGTERM and two-second cleanup limits remain intact.
- Historical CI root-cause limit: The old test erased startup stderr, so local causal reproduction supports the fix without proving that every historical failure had identical scheduling. A future remote run must validate the correction separately; none is dispatched here.
- Warning cascade: An isolated diagnostic invoked the original failed probe and forced garbage collection; it observed exactly two unclosed-file ResourceWarnings from the two text pipe wrappers. Diagnostic warning capture is isolated; formal warnings-as-errors settings remain unchanged.
- Independent review: One fresh-context bounded static reviewer found no material issue. It checked failure-path termination/pipe ownership, retained diagnostics, five-second success deadline, original SIGTERM assertion and real-child regressions. The reviewer did not run another suite or mutate files. Final whole-graph execution remains the author's check.
- Final full Linux ARM64/Python 3.12.15 graph: all thirteen gates passed, unchanged source. Actual JUnit: 495 unit/harness, 258 integration, 84 acceptance, 5 package (842 Python), 20 Node and 78 Chromium, zero failures/errors/skips. Browser gate 191.76 seconds, integration 230.37 seconds, acceptance 57.88 seconds. All original global deadlines remain intact.
- Final evidence: full-final/check-result.json SHA-256 `5dd6dbabc83cff9a543d7346eca031db6892c74460da152051db775bc6036452`; source fingerprint `f88890a88a999e101ee4a23036db0a911beb3960b89ead4a1d92c76ed4ebed64`. The run tested the uncommitted patch on cd88f6d. Independent accounting verified all expected positive counts, zero defects/skips and matching current bytes. See ignored observed-summary.json and complete original/final logs.
- Delivery boundary: local commit and stopped container only. PR code head/failed run are unchanged; do not claim remote repair or dispatch another job. Further remote publication requires the owner's authorization.
