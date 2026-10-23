# Local delivery status

## Simplified entry implemented; final trial refresh pending

The owner approved a bounded entry-flow improvement: endpoint and model are the
only required visible fields; API Key is optional, scope and advanced controls
are collapsed, and the name defaults to the model. Fresh forms keep all five
cases/up to six requests. Existing checks and explicit review/start remain intact;
no diagnostic scenario was added. Read [the ledger](harness/simplified-entry-ledger.md).

Final-source fast checks passed all eight gates with unchanged source. Related
browser checks passed 47 tests; Chinese/English light/dark screenshots and mobile
layout were inspected. One bounded independent review found no material blocker.
The final local trial refresh is recorded below when complete; no remote push,
new remote CI or genuine endpoint call is included in this iteration.

## Tool-result round trip delivered; await owner trial feedback

The owner approved one small addition: `ANT-TOOL-LOOP-001` v1 in profile
`anthropic-tool-loop`. Source and the running local Web trial now provide five
formal scenarios. The new case reserves two sequential non-stream requests and
checks consumption of a fresh tool-result token; it is one scenario, not two
independent cases or retries. Existing two profiles retain their original scope.
The default new Web form selects all three profiles with a six-request allowance;
the owner can select only the round-trip profile to test it separately.

Dedicated fault/timeout/cancellation/evidence checks passed, as did actual CLI,
Web API and the new browser flow against synthetic endpoints. One independent
review's extra-tool false PASS was reproduced and fixed. Final stable-source fast graph passed eight gates; 77 targeted
checks, including 20 round-trip regressions, passed. New-case browser verification
passed with verified evidence; corrected catalog/installed-package checks passed
six tests, with five final installed-package checks reverified after the last
code corrections. A first-step failure stays visible in repair comparison even if the
second step passed. Exports retain both exchanges.
The broader graph's old catalog/budget fixture failures were corrected and
reverified separately; its failed/changed-source records remain intact. No single
green final-source full graph or new remote CI is claimed.
Read [the bounded ledger and usage](harness/tool-loop-ledger.md).

Trial http://localhost:8765 has been updated with a cached-wheel/offline dependency
reuse image. Existing persistent history is retained. Keep this trial running;
stop only the development check container after its work finishes. No agent call
to the owner's endpoint, remote push, image publication or full native matrix.
Final trial revision is local feature commit `eb82c90`; all 157 installed package
files match the source. Health/home checks passed and both prior completed runs
remain present. Development checks are finished; keep the trial service running.
Wait for owner feedback before choosing another feature. The feature is committed
locally and has not been pushed; remote main still has four cases.
Streaming/parallel tool loops, error-result recovery and real client workflows
remain future work. Older four-case observations below are historical.

## Product alignment and remaining coverage

Read [project intent](../intends.md) before selecting further work. The owner
identified that the formal catalog had only four cases despite extensive
presentation and engineering work. Prioritize expanding dependable diagnostic
coverage: expected-rejection scenarios, multi-step tool/result conversations,
streamed tool arguments, multi-turn messages and request/error contracts, then
the remaining protocol/client/version-maintenance goals in intends.md. Existing
W1/W2 scope exclusions are historical milestone boundaries, not completion or
removal of these goals. The first addition above brings the local catalog to five;
the remaining goals are not yet delivered.

The prior private 90-scenario assessment is reference material, not a shipped
suite or 90 independent capabilities. Its script is absent from the inspected
original temporary harness directory; do not promise a direct import without
recovering and auditing actual source. Use retained method/rulings and verified
official protocol sources to reconstruct generic checks where needed.

## Historical four-case trial; superseded by the delivery above

The owner prioritized hands-on use over another verification round. Current-source
Web service is running at http://localhost:8765 in readiness-trial-readiness-1,
with persistent volume readiness-trial_readiness-data. Keep this container
running for the user. Health returned status ok and homepage returned HTTP 200.
No real model request was sent. The installed scope remains four formal cases;
do not describe this trial as comprehensive protocol/client certification.

Current wheel was built using cached build stages and installed offline into the
existing ARM64 Web environment; pyproject.toml, uv.lock and Dockerfile match its
original revision e4e9de4. Package dependency checking passed. A normal Web build
stalled downloading pydantic-core and was interrupted; its log is retained. The
trial image is anthropic-readiness-web:trial-ready, revision a5b66e2; image-context
label is explicitly unknown. This is local trial delivery, not fresh full image
matrix acceptance or registry publication. No additional test graph was run.

Run/stop configuration is ignored artifacts/ci-startup-20261022/trial-compose.yaml,
used with compose.yaml and project readiness-trial. Preserve its data volume.
The post-merge main CI 39758681663 was subsequently confirmed successful in all
five jobs. The earlier running-CI observation below is historical.

## PR 1 merged; main CI running

The owner authorized merging PR 1. Rechecked its exact head `6dcd27a`, clean
mergeability and all five successful PR CI jobs, then merged with a head-match
guard. GitHub confirms MERGED at 2026-10-22T09:51:43Z into main, merge commit
`10c7933e76258abd1c1a5f953954287d719a7850`.
The [post-merge main CI](https://github.com/sleetdrop/anthropic-readiness/actions/runs/39758681663)
was observed in progress, not yet passed. Prior successful PR CI remains distinct
from this new run. No full native image matrix or registry publication started.

Local branch and its unpublished observation commits are preserved; no branch
deletion or extra push accompanies this merge. Merge metadata and initial main CI
state are retained in ignored artifacts/ci-startup-20261022/. The earlier open-PR
statements below describe their historical observation points.

## Startup probe correction published; fresh PR CI passed

The owner authorized pushing the correction to the existing feature branch and
observing fresh CI. PR 1 head is `6dcd27a9ce5e68c2c408e5bd331f32e454cb7880`.
The [new PR CI run](https://github.com/sleetdrop/anthropic-readiness/actions/runs/39737268733)
passed all five jobs: quality (3.11), quality (3.12), actual Dev Container,
native AMD64 runtime smoke and ci-required. Downloaded job logs confirm all
thirteen gates passed in each of the three full-check environments, including
acceptance. All four summary/upload pairs succeeded; artifact metadata confirms
retention through 2026-11-05. Full remote JUnit archives were not downloaded or
independently recounted, so the exact local counts below are not remote counts.
The separate feature-branch push run was skipped, not passing verification.

The earlier failed PR run remains historical evidence. The correction now has
fresh remote verification; this does not recover discarded historical stderr.
PR remains open and unmerged. Record this observation in a local-only docs commit
to avoid triggering another unchanged-source CI run. Full native AMD64/ARM64 image
acceptance, repository protection and registry publishing remain separate steps.
New evidence is retained under ignored `artifacts/ci-startup-20261022/new-ci-*`.

## Previous local startup acceptance probe correction

The owner authorized diagnosis and local correction of the failed PR CI. Follow
[the bounded correction plan](superpowers/plans/2026-10-22-ci-startup-probe.md).
Three real-child regressions reproduced discarded stderr, unclosed pipes and
false startup failure for a healthy 300-ms response. The corrected test keeps the
overall five-second readiness deadline and SIGTERM/shutdown assertions, uses the
remaining request budget, and owns/drains/closes the child on failure. Production
source and API/protocol contracts are unchanged. Original related acceptance plus
new regressions passed 17 cases; changed-file Ruff/mypy passed.

A controlled two-burner/single-CPU comparison reproduced original failure at
5.14 seconds with two open pipes; corrected probe passed at 3.93 seconds with none.
This confirms the probe mechanism, not every historical CI circumstance. An
isolated original-probe/GC diagnosis also observed two unclosed-file warnings.
One independent bounded review found no material issue. Final unchanged-source
Linux ARM64/Python 3.12 full verification passed all thirteen gates: 842 Python
(495 unit/harness, 258 integration, 84 acceptance, 5 package), 20 Node and 78
Chromium cases, zero failures/errors/skips. Fingerprint
`f88890a88a999e101ee4a23036db0a911beb3960b89ead4a1d92c76ed4ebed64`;
record SHA-256 `5dd6dbabc83cff9a543d7346eca031db6892c74460da152051db775bc6036452`.
Observed source was the patch on cd88f6d, not a clean future commit.

Retain all evidence under ignored `artifacts/ci-startup-20261022/`, especially
full-final/, observed-summary.json and comparison.json. That local operation
stopped after commit and container shutdown, with PR 1 still on eb82885. The
subsequent owner-authorized publication and successful CI are recorded above.

## PR 1 published: evidence upload verified, acceptance failures remain

The owner authorized pushing `codex/ci-evidence-observability`, creating
[PR 1](https://github.com/sleetdrop/anthropic-readiness/pull/1) and observing CI,
then stopping before merge or full image-matrix dispatch. Code head is `eb82885`.
The [first PR CI run](https://github.com/sleetdrop/anthropic-readiness/actions/runs/39718653050)
completed with failure: Python 3.11 and native AMD64 smoke passed; Python 3.12 and
Dev Container failed acceptance, and `ci-required` correctly failed. The separate
non-default-branch push run was skipped, not a passing verification.

All four summary and upload steps succeeded, including the new Dev Container
artifact. Metadata confirms retention through 2026-11-05. Downloaded Python 3.12
and Dev Container records observed clean PR merge commit `4af5a8e` with unchanged
source fingerprint `946ea1950af2d0b0a78c351c339110db547f6cb1cac846779c3719ae1b9cd3bb`.
Each retained 492 unit/harness, 258 integration, 84 acceptance (82 passed, 2 failed),
5 package, 20 Node and 78 Chromium cases, zero skips; only acceptance failed.
Rendering downloaded failed evidence with the committed summary script preserved
the failures and actual counts. GitHub summary visual rendering was not inspected.

Both first fail `test_real_serve_start_and_signal_shutdown`: no successful health
response within its existing five-second deadline. Subsequent report cases fail on
unclosed-file ResourceWarnings, not report-content assertions. The startup root
cause and allocation/cascade need reproduction; do not label these environmental
flakes or increase deadlines without evidence. No product/test fix or CI rerun was
performed during that publication/observation operation. Raw artifacts, failure
logs and verified accounting remain in ignored
`artifacts/ci-observability-20261022/`, especially `pr-observed-summary.json`.

PR remains open and unmerged. The owner subsequently authorized the local probe
correction and fresh remote verification recorded above. Native
full container matrix, repository protection and registry publishing remain
separate later steps. The earlier local acceptance below is not remote green CI.

## Previous local CI evidence implementation: offline verification passed

The owner approved the first bounded CI follow-up. Changes are on local branch
`codex/ci-evidence-observability`, based on `7fb1bcd`. Dev Container now uploads
its check artifacts; the full image matrix uploads both image and inner developer
evidence. Every environment has an always-run presentation summary. Explicit
outer job budgets, 14-day retention and non-cancelling per-ref full-matrix
concurrency are configured. Existing required jobs, product assertions and test
deadlines remain unchanged. See the
[completed plan and ledger](superpowers/plans/2026-10-22-ci-observability.md).

Final Linux ARM64/Python 3.12 offline verification passed all thirteen gates:
839 Python (492 unit/harness, 258 integration, 84 acceptance, 5 installed-package),
20 Node and 78 Chromium cases, with zero failures/errors/skips. Source remained
unchanged at `946ea1950af2d0b0a78c351c339110db547f6cb1cac846779c3719ae1b9cd3bb`.
One independent bounded review was completed; its numeric-overflow finding and
related nested-metadata concern were reproduced and fixed with regressions.
Original RED and intermediate failed attempts remain retained under ignored
`artifacts/ci-observability-20261022/`; `full-final/` is the accepted local graph.

Stop after the scoped local commit and container shutdown. No push, workflow
dispatch, repository rule change, real endpoint call or registry publication is
included. New remote CI and complete native AMD64/ARM64 matrix execution remain
pending; the prior green remote run below validates its original source only.

## Content-derived analysis reuse: local full and new remote CI passed

Correction commit `7cc574c4b42a700bf310012e3d07ebf202903c5b` is pushed to `main`.
Its first [new CI run](https://github.com/sleetdrop/anthropic-readiness/actions/runs/39645368029)
passed all five jobs: quality (3.11), quality (3.12), actual Dev Container,
native AMD64 smoke and ci-required. Each quality job passed thirteen gates and
831 Python, 20 Node and 78 Chromium tests with zero failures/errors/skips on clean
`7cc574c`, matching the locally verified source fingerprint. The former failing
comparison test took 27.179/32.976 seconds, both under the unchanged 40 seconds;
browser gates took 240.80/268.59 seconds, integration 279.36/351.57 seconds.
Native AMD64 CLI/Web smoke passed 31 checks on inspected current-source images.
Dev Container's log confirms thirteen passed gates; exact case counts were not
retained for that job and are not separately claimed.

The bounded correction is complete. Stop after the docs-only CI observation
commit/push; no further retry, review or full image matrix starts automatically.
The prepared container is stopped again, exit 0. Original failed CI attempts and
all intermediate local attempts remain retained. Source implementation and tests
are unchanged by the final documentation record. Current-source full image
acceptance, real endpoint/client outcomes and registry/package publication are
not established by this CI result. Further work needs its own concrete scope.

The owner approved the measured performance correction. Only compiled Schema
snapshots and content-keyed AST analysis are reused, with bounded caches. Incoming
documents, file hashes, source/module inventory, manifest permissions, dependencies
and evidence are still checked afresh. Schema declaration order is retained so
diagnostic ordering does not change. No assertion, golden, timeout or CI graph
was weakened.

Final Linux ARM64/Python 3.12 full verification passed all thirteen gates on the
unchanged patch: 831 Python tests (484 unit/harness, 258 integration, 84 acceptance,
5 installed-package), 20 Node and 78 Chromium, zero failures/errors/skips.
The former failing comparison browser case completed in 22.8 seconds under its
unchanged 40-second limit; browser gate took 196.58 seconds and integration gate
223.44 seconds under the original 300/600-second child limits. A controlled
four-case comparison/export measurement retained exact output bytes and reduced
median time from 0.9383 to 0.4841 seconds. The separate new remote CI is recorded above.

Evidence: ignored `artifacts/ci-optimization-20261022/`, especially `full-final/`,
`observed-summary.json` and `measurement-final/`. Original failed/intermediate
attempts remain retained, including an additional RED/GREEN check for diagnostic
ordering found during self-review. Full recorded Git is the uncommitted patch on
`ea614a4`; its exact source fingerprint is
`2d7a3e1b454b72f2e38e7b2e36b64432dfd95b832386b8096ab8ad23de7b4fd4`.

The agreed new CI observation passed on this justified correction; exact hashes
and limits are in the publication ledger. Prior image/CI observations keep their original
source identities; full image acceptance for this cache correction is not claimed.
No real endpoint, package/registry publication or new review is included.

## GitHub published; unchanged CI retry confirms a persistent timing problem

The owner-authorized follow-up diagnosis is complete; see the
[measured timing analysis](reviews/2026-10-22-ci-timing-diagnosis.md). Repeated
installed-identity/AST computation and schema meta-validation dominate sampled
comparison and integration CPU work. A process-local controlled experiment reduced
comparison/export median time from 0.905 to 0.385 seconds with identical outputs;
no production optimization or timeout change was made. One existing integration
case passed under profiling. This is diagnostic evidence, not a remote green run.
Next bounded task is a semantics-preserving correction with mutation/corruption
regressions, then measured verification; avoid permanent cached identity/evidence
verdicts. The full rationale, limits, hashes and safe stopping state are in the
analysis and publication ledger. Stop after the local documentation commit.

The owner approved the public repository
https://github.com/sleetdrop/anthropic-readiness, MIT licensing and first push as
`main`, followed by observing GitHub CI. First push `7b69b53` succeeded; GitHub
confirmed the public repository, default `main` and MIT License. The first
[CI run](https://github.com/sleetdrop/anthropic-readiness/actions/runs/39630071527)
completed with failure. Native AMD64 smoke passed 31 checks. Python 3.11 passed
all Python/Node tests but one browser case timed out waiting for comparison export.
Python 3.12 browser/integration gates timed out; Dev Container's browser gate failed.
The aggregate gate correctly failed. Remote CI is not green.

The owner then authorized one unchanged retry if evidence supported environmental
variance. Trace inspection showed the first 40-second browser test had spent
39.52 seconds before beginning its export-response wait; that wait lasted only
0.83 seconds before the global deadline. Exactly one failed-job retry ran on the
same `7b69b53`, with no source/dependency/timeout changes. Attempt 2 also failed:
Python 3.12 reproduced the same comparison-export case at the 40-second deadline;
Python 3.11's browser graph hit 300 seconds; Dev Container's browser gate failed.
Both quality integration suites passed this time, in 594.05 and 529.25 seconds.
The previously successful native AMD64 smoke was retained, not rerun.

This is a repeatable timing/performance sensitivity on CI, not established as a
one-off infrastructure failure. It does not yet identify a product defect versus
an overlarge test/insufficient budget. No observed protocol/report-value assertion
failure was found in the completed reports. Do not retry again without diagnosis.

The subsequent diagnosis above measured repeated CPU work using those retained
traces/records and exact synthetic input files. Its recommended correction remains
separate work.
Do not assume a slow runner explains the export failure, increase limits blindly,
skip assertions or repeatedly rerun until green. No product/test/workflow/budget
change was made during publication or the separately authorized retry. See the
[publication ledger](harness/github-publication-ledger.md) for exact counts,
original failures and safe stopping state. Local correction/source/image baselines
remain below with their original identities. No registry/package publication occurred.

## Current follow-up: correction verification and both image jobs passed

The owner authorized the matching AMD64 job after native ARM64 acceptance. On
clean `eb5e1db9c84b12eea275a9a5b2193101aee6bbe1`, the full AMD64 CLI/Web job
passed all 68 controller checks with no missing required check or error. Runtime
execution was emulated on the ARM64 engine. Its separately prepared, disconnected
developer container ran natively on Linux ARM64/Python 3.12: thirteen full gates,
822 Python, 20 Node and 78 Chromium tests passed, zero failures/errors/skips.
This does not certify native AMD64 development or browser execution.

Both image jobs cover the same current source and image-context fingerprints;
the intervening commits changed only excluded handoff records. F01-F06 and the
integration-budget correction now have complete source verification, native ARM64
image acceptance and emulated AMD64 CLI/Web image acceptance. Do not repeat these
checks or open another review loop without a new change, failure or concrete concern.

AMD64 evidence: ignored `artifacts/review-fixes-20261021/images-amd64-eb5e1db/`
and adjacent `.log`; fresh developer full record:
`artifacts/checks/1792596746304061548/check-result.json`. The packaged schema,
actual JUnit counts, source/image identities and absence of owned containers,
networks and data volumes were checked separately. All initially stopped containers
were preserved; the prepared container is stopped again, exit 0. Public caches and
original blocked/passing observations remain retained. No product/test/harness/
lock/Dockerfile changed, and existing preview services were not upgraded.

Stop after the local documentation commit. Further work needs its own bounded
scope: product/workflow validation or a later milestone, rather than another
automatic verification cycle. Formal coverage remains four installed cases.
Remote CI, native AMD64 development and current-source real endpoint/client checks
remain unrun; publication and account setup remain separately authorized actions.
Keep original records' external statuses and historical W2 identities unchanged.

## Native ARM64 image acceptance baseline

After the owner changed network and authorized a retry, one fresh native ARM64
full CLI/Web job passed on clean `e4e9de4ab0323f28e0897a70dfd623551ead2efa`.
All 68 controller checks passed, with no missing required checks or controller
error. Locked versions, sources, timeouts and assertions were unchanged. The
previous completed build layers were reused; the original blocked job is retained.

The independently prepared Linux ARM64/Python 3.12 developer container was
disconnected from external networking before its full graph. All thirteen gates
passed: 822 Python tests (475 unit/harness, 258 integration, 84 acceptance and 5
installed-package), 20 Node and 78 Chromium tests, zero failures/errors/skips.
CLI replay/signals/host routing and Web import/retest/exports/cancellation/restart
and persistence also passed against the installed images using synthetic peers.
This is current-source native ARM64 image acceptance, not real endpoint or client
certification. Existing preview services and their data were not upgraded.

Evidence: ignored `artifacts/review-fixes-20261021/images-arm64-e4e9de4/` and adjacent
`.log`; its `observed-summary.json` checks actual JUnit counts, source/image
identities, packaged record schema and absence of owned job resources. The fresh
developer record is `artifacts/checks/1792593801435672504/check-result.json`.
Original full records retain their original external statuses and stage readiness.
No product/test/harness/lock/Dockerfile changed. All initially stopped containers
were preserved, and the prepared container is stopped again, exit 0. Public
tool caches and completed build layers remain available.

The subsequently authorized emulated AMD64 full CLI/Web job also passed, as
recorded above, with a native ARM64 developer baseline. Native AMD64 development,
remote CI, publication and current-source real endpoint/client checks remain
unrun. No additional review or verification task starts automatically.

## Previous native ARM64 image attempt: preparation timeout

On 2026-10-21 the owner authorized one native ARM64 full CLI/Web image job from
clean `91275265018f08d45e54aeea720c48057b560960`, whose verified source bytes match
`21653ca`. CLI and Web builds passed, but the dev image reached its configured
7200-second build limit while downloading/preparing Chromium system libraries.
The controller exited 2 with `status=blocked`; BuildKit recorded the build canceled.
It did not reach functional image checks or the fresh developer full graph.
That attempt left all 21 required functional/developer checks unrun and did not
establish Docker acceptance; the separate successful retry is recorded above.

No source/test/harness/lock/Dockerfile changed. The two built images were inspected
for architecture, revision and context identity; these extra metadata observations
do not backfill the controller's unrun checks. No test containers, networks or data
volumes were created. The two preexisting stopped containers remain unchanged.
Built images and completed public build layers remain available locally.

The subsequent retry above completed the locked dev image environment using
completed-layer cache and passed native ARM64 full acceptance with fresh output.
Preserve the blocked attempt, required checks and dependency sources/versions.
Do not silently skip the dev graph, switch to smoke, or start AMD64, a new review,
publishing or real endpoint calls. The complete source verification below remains
current; this environment-preparation timeout does not replace that record.

Evidence: ignored `artifacts/review-fixes-20261021/images-arm64-9127526/` and adjacent
`.log`. The packaged result schema, actual cancellation, image/source identities
and preserved container inventory were verified separately. The prepared container
is stopped again, exit 0. Stop after the local documentation commit.

## Complete source verification baseline

On 2026-10-21 the owner authorized one full-source verification turn on clean
`21653ca84eb4cb76c9f0ef7717d43fbf979b93e1`. All thirteen gates passed on unchanged
source: 822 Python tests (475 unit/harness, 258 integration, 84 acceptance and 5
installed-package), 20 Node and 78 Chromium tests, with no failures/errors/skips.
The actual run took about 12.4 minutes; integration completed in 351.67 seconds
under its bounded 600-second limit. This is a new complete source verification
baseline for F01-F06 and the harness budget correction.

Evidence is retained under ignored
`artifacts/review-fixes-20261021/full-21653ca/`, with the command log at
`artifacts/review-fixes-20261021/full-21653ca.log`. The actual JUnit reports,
thirteen executed gates, clean recorded Git identity and current source fingerprint
were checked separately by `verify_observation.py` and `observed-summary.json`.
No source, test, dependency, assertion, golden or image changed in this turn.
Original blocked and custom-diagnostic records remain unchanged.

The first subsequent native ARM64 Docker attempt was blocked; the fresh retry
above passed. Do not repeat full source tests without a new change/failure,
start another automatic repository
review, or call a real endpoint. Current-source native ARM64 image acceptance passed;
remote CI and real client/endpoint outcomes remain unrun. Historical W2 image
records below belong to their original source. The full result deliberately retains
`stage_readiness=incomplete` and external `not_run` statuses.
The prepared container is stopped again, exit 0. Stop after the local
documentation commit.

## Integration budget correction baseline

On 2026-10-21 the owner authorized one integration-runtime diagnosis and a
justified budget decision. On unchanged source, all 258 integration cases passed
in 349.77 seconds under a bounded 600-second custom diagnostic. The slowest
case, including fixtures, took 10.136 seconds. The 17 cases added since the prior
241-case baseline consumed 86.376 seconds in this run; no historical case was
omitted. This run establishes cumulative suite time beyond the old 300-second
limit, without an observed stuck case. Historical timing is not a controlled
performance comparison.

Only the designated integration gate now allows 600 seconds. All thirteen gates'
commands, required flags, case inventory, report checks, process-group cleanup
and other limits remain unchanged. Fast passed all eight gates (475 Python
unit/harness and 20 Node tests), including actual timeout/failure/cleanup guards.
No product source, test, assertion or golden changed. The runtime budget is
documented in `docs/development.md`.

The subsequent complete source graph passed above. The custom diagnostic and
fast records remain separate, and the original blocked result below is retained.
Evidence and exact source identities are in the correction ledger and ignored
`artifacts/review-fixes-20261021/integration-runtime-cd42a0f/`. Stop after the
local budget-change commit. The container is stopped again, exit 0.

## Previous full verification: integration timeout

On 2026-10-21 the owner authorized one complete source verification turn on clean
`cd955f78cd8ec0938455da1d7df37c2ef66712df`. The unchanged source completed twelve
of thirteen gates; integration was **blocked by its 300-second timeout** and did
not produce a JUnit report. Overall status is `blocked`, stage readiness remains
`incomplete`. No complete integration pass or whole-source acceptance is claimed.

Completed suites passed 475 Python unit/harness, 84 acceptance, 5 installed-package,
20 Node and 78 Chromium tests, with no failures/errors/skips in those reports.
The other completed gates include lock, format, lint, strict typing, architecture,
schemas and documentation. The incomplete integration run is not included in a
whole-suite test total. No assertion failure appears in its partial log, which
does not establish why it exceeded the budget or prove that it would finish.

The subsequent runtime diagnosis, budget change and successful complete source
verification are recorded above. This historical run remains blocked; it is not
rewritten or combined with later runs to claim a pass.

Evidence: ignored `artifacts/review-fixes-20261021/full-cd955f7/`; authoritative
gate records/JUnit reports are under `run-1/`, with a separately verified
`observed-summary.json` at the parent. An initial output-directory startup failure
is retained as `full.log` and executed no checks. No source/test/harness/dependency
was changed in this turn. The development container is stopped again, exit 0;
this turn ends after the local documentation commit.

## F06 verification baseline

On 2026-10-21 the owner authorized F06 only. Writer and report reader now share
one pure assertion-to-evidence-file rule. HTTP/capture checks require response
metadata regardless of a supplied event index; other checks use indexed events
or the response body. Every supplied observation reference must match its kind
and own attempt, in addition to the existing hash/location checks. Invalid proof
remains readable but cannot regain controlled comparison/retest or recovery
claims through export/import. Original inputs are preserved.

Eight wrong-kind variants first failed; two added HTTP/capture event-index bypass
variants also failed before the final correction. Final verification passed
37 core tests, 102 related regressions and all eight fast gates (475 Python
unit/harness and 20 Node tests). Correct response/event proof, healthy recovery,
F05 integrity checks and legacy cached-tail handling remain covered. No schema,
golden, dependency or existing assertion expectation was weakened.

F06 was delivered as `cd955f7` with the container stopped, exit 0. F01-F06 are
locally corrected within their recorded scope. The subsequent full-source attempt
above is blocked, so updated Docker acceptance remains pending. Exact
observations and intermediate RED/GREEN records are in the correction ledger and
ignored `artifacts/review-fixes-20261021/f06/`. The historical full-source record
below still certifies only `9a30567`, not these later F05/F06 patches.

## F05 verification baseline

On 2026-10-21 the owner authorized F05 only. Report-source verification now reuses
the existing capture reader after inventory checks, so its cross-file integrity
checks also govern evidence eligibility. Five contradictory metadata variants
were observed RED first. The corrected source passed 27 core tests, 102 related
regressions and all eight fast gates (475 Python unit/harness and 20 Node tests).
Invalid sources remain readable but cannot regain controlled comparison/retest
or recovery claims through export/import. Complete valid captures with legacy
cached-tail flags remain eligible in capture formats 1.0 and 1.1. No schema,
golden, dependency or assertion expectation was weakened.

F05 was delivered as `12f9217` with the container stopped, exit 0. F06 was
subsequently corrected above. See the correction
ledger and ignored `artifacts/review-fixes-20261021/f05/` for observed checks,
the retained failed command and source identity. The prior full-source record
below remains tied to `9a30567`; it does not certify the new F05 source.

## Bounded review baseline

On 2026-10-21 the owner authorized one independent read-only review of the
F01-F04 correction diff, without another repository-wide review or Docker build.
The reviewed product source remains `9a3056707560c991449c1ae4988781f335b0add7`.
Two synthetic variants reproduced remaining F02-related gaps: contradictory
capture metadata can retain verified evidence eligibility (F05), and observed
PASS assertions can cite only their own request file as proof (F06). Both variants
still permit comparison and an observed-recovery conclusion. The retained response
bodies are valid controls; this does not demonstrate an invalid protocol stream
being classified PASS. No product code was changed during review.

Both findings are corrected locally above; updated whole-source and image
acceptance remain separate follow-ups. The independent report and one synthetic
probe run are retained
under ignored `artifacts/review-fixes-20261021/bounded-review-9a30567/`.
Read [the correction ledger](harness/independent-review-fixes-ledger.md) for author
rulings, scope limits and the safe stopping state. Do not repeat the entire review
or reinterpret the passing source checks below as proof that these gaps are closed.

## F01-F04 complete source verification baseline

On 2026-10-21 the owner authorized one full-source verification turn. Clean commit
`9a3056707560c991449c1ae4988781f335b0add7` passed all thirteen gates on unchanged
source: 805 Python tests (475 unit/harness, 241 integration, 84 acceptance and 5
installed-package tests), 20 Node and 78 Chromium tests, with zero failures,
errors or skips. Locked dependencies were synchronized offline in the existing
Linux ARM64/Python 3.12.15 Dev Container. Exact records and a separately checked
JUnit summary are retained under ignored
`artifacts/review-fixes-20261021/full-9a30567/`. No product code changed in this
verification turn; subsequent notes are documentation only.

The owner requested one complete fix per turn to preserve a safe stopping point
within the available usage allowance. F01 is fixed locally: malformed intermediate
SSE stop fields now retain an event-level failure even if later deltas repair the
final message. Eight negative variants were observed RED before the fix; the
59-test message/stream suite, 26 runner/review/comparison tests and all eight fast
gates passed afterwards (475 Python unit/harness tests and frontend static checks).
The original reviewer's synthetic runner probe now returns exit 1 / not_ready for
the malformed stream while the valid control retains exit 0 / passed.

F02 is also fixed locally after a separately authorized turn. Capture inventories
must include their four declared files with matching hashes, and observed PASS
assertions need proof belonging to their own attempt. Invalid packages remain
readable with explicit evidence limitations, without retest/compare eligibility or
recovery claims; evidence-inclusive export is rejected. Six negative variants were
observed RED before implementation, then 26 core and 60 related tests passed.
All eight fast gates passed again (475 Python unit/harness tests).

F03 is fixed in a separately authorized turn on 2026-10-21. Replay now derives the
pending SSE tail from complete, unchanged response bytes. For transformed or
incomplete captures it conservatively retains either pending signal. Both capture
formats (1.0/1.1), opposite cached flags, redaction and cancellation are covered;
existing cancellation exit code 130 is preserved. The 31 evidence/CLI/review tests,
11 F02/comparison regressions and all eight fast gates passed (475 Python
unit/harness tests). Original capture bytes and metadata remain unchanged on read.

F04 is fixed in a separately authorized turn on 2026-10-21. Final result readers
now reject dimensions that disagree with the required assertion categories, using
the same pure aggregation rule as the runner. Live attempt counts follow the
shipped single-request attempt model; an unsent indeterminate execution failure
may retain zero only without declared capture evidence, while replay remains
zero-request. Nine inconsistent-input variants were observed RED across the
initial and added proof-boundary checks, then the final 24 core tests, 81 related regressions
and all eight fast gates passed (475 Python unit/harness tests). Contradictory
results cannot reach source views, evidence export or ZIP activation, and original
inputs are preserved. A hand-written positive unit sample was completed with its
actual BLOCKED dimensions; its assertions and versioned goldens were not changed.

Read [the follow-up ledger](harness/independent-review-fixes-ledger.md) for evidence
and the four original author correction records. Their original regression cases
pass; the later bounded review above identified two additional F02-related gaps.
Both are now corrected locally with focused verification. Updated whole-source
and Docker image acceptance remain follow-ups.
Do not repeat the whole independent review or reopen the completed W2 plan.
These patches have full-source/browser/install verification but no new image,
remote-CI or real endpoint/client acceptance;
the W2 records below remain historical evidence for their specified source.

## W2 delivery baseline: completed locally

The owner-approved diagnostic workbench/document redesign is implemented on
`codex/local-web-console`; all sixteen sequential tasks (0–15) are complete.
Use the [revision-2 specification](superpowers/specs/2026-10-18-diagnostic-workbench-design.md),
[plan](superpowers/plans/2026-10-18-diagnostic-workbench-implementation.md),
[ledger](harness/diagnostic-workbench-ledger.md),
[acceptance map](harness/diagnostic-workbench-acceptance.json),
[handoff](harness/diagnostic-workbench-handoff.json) and
[review/author closure](reviews/2026-10-18-diagnostic-workbench-review.md).
The operational five-view workbench and offline presentation-3 document now have
separate compositions, shared verified facts, bilingual themes, portable diagnostic
import, original-scope retest and paired repair/regression comparison. New attempts
and localized exports preserve source identities and original evidence bytes.

Verification source is `35b59f5ef8ff4d78740283a81a5090d18b9b0aa5`; subsequent
handoff-only edits preserve source and image fingerprints. The thirteen-gate full
graph passed 768 Python, 20 Node and 78 Chromium tests on unchanged, clean source;
zero failures/errors/skips. Fresh native ARM64 and emulated AMD64 full CLI/Web image
jobs each passed 68 actual checks, including import/retest/comparison/restart.
Each independently prepared/disconnected native Linux ARM64 developer container
also passed the full graph with identical counts. Owned job resources were checked
absent; previews, tool cache and all evidence remain retained.
One independent whole-W2 review completed; one author RED-to-GREEN pass closed
both Important findings. No re-review ran. The sole deferred Minor is English
column labels in the Chinese Markdown technical appendix. Native browser-chrome
200% zoom remains unobserved; the explicit equivalent reflow/density checks passed.

The current synthetic preview is at `http://localhost:8766`; Chinese/system
preferences and the selected issue/case are retained. Its latest observed GUI
export is 7fd04d7b-84e7-4cac-98de-b6a803c8c5d1 (presentation 3), recorded under
artifacts/w2/task15. The older W1 service remains separate at port 8765.
Formal coverage remains four installed cases. Real endpoints/Claude Code workflows,
remote CI, supplemental Python 3.11 and native AMD64 development were not run for
W2. Protocol update tooling and larger catalogs remain later separately scoped
work; no compatibility or client-stability claim follows from these synthetic tests.
Keep the chosen current checkout/prepared Linux Dev Container and local commits.
No push, merge, registry publication or account setup is authorized by W2 completion.
The W2 plan workspace is archived byte-identically (37 files) under ignored
artifacts/w2/plan-workspace-20261020; only its verified working copy was removed.
Use the tracked ledger/handoff for current state, without reopening completed reviews.

## Current milestone: W1 completed locally

The owner requested a local Docker Web interface for configuration, live test
progress and on-demand export, with independent CLI execution retained. Individual
local deployment is confirmed. The owner approved the console/report visual
direction. The [written W1 specification](superpowers/specs/2026-10-16-local-web-console-design.md)
was explicitly approved. Its [implementation plan](superpowers/plans/2026-10-16-local-web-console-implementation.md)
has 14 sequential tasks; self-review and owner approval completed on 2026-10-17.
The owner chose the current checkout and prepared Dev Container. Work is on branch
`codex/local-web-console`; all 14 tasks are complete. One independent whole-W1
review returned With fixes; one author RED/GREEN pass closed all six Important
findings. No re-review ran. The sole deferred Minor is separate failure/unresolved
matrix filters; all raw statuses remain visible. See the
[W1 ledger](harness/web-console-ledger.md),
[acceptance map](harness/web-console-acceptance.json),
[handoff](harness/web-console-handoff.json) and
[review/author closure](reviews/2026-10-18-web-console-review.md).
Verification source is `2297306c538c0354e9519d88716520e6b24be5b4`: 454 Python,
10 Node and22 Chromium cases, zero failures/errors/skips. Fresh native ARM64 and
emulated AMD64 CLI/Web image jobs each passed 58 checks on that unchanged source.
Both use a separately identified native Linux ARM64 developer/browser baseline.
The local Compose service at `http://localhost:8765` contains synthetic demonstration
data; actual GUI export hashes and unchanged original result bytes were verified.
No push, merge or registry publication occurred. Remote CI, native AMD64 developer
execution and supplemental Python 3.11 W1 remain unobserved.
The W1 scratch workspace was archived byte-identically (252 files) under ignored
`artifacts/w1/plan-workspace-20261018/` and removed only after verification; sibling
workspaces were preserved. Use the tracked W1 ledger/handoff for current state,
not a new scratch workspace or the historical Stage A reviewer.
No W1 real endpoint call is authorized by plan approval.
Stage A completion and the private assessment below remain historical baselines.

The approved 12-task Stage A plan is complete on branch `feat/stage-a`.
Read [HANDOFF.md](HANDOFF.md), [the evidence manifest](harness/handoff.json),
[the progress record](harness/progress.md) and
[the implementation ledger](harness/implementation-ledger.md) before further work.

## Private comprehensive assessment finalized

The owner resumed after the account-limit pause. All 127 upstream requests remain
complete; finalization made no new model call. The existing report accounts for
90 API scenarios and seven fixed SDK/Claude Code scenarios, with all seven client
scenarios passing their observable conditions. Final evidence provenance and
cleanup records are retained privately beside the assessment. No run/download is
pending. See [the assessment method](reviews/2026-10-16-private-comprehensive-assessment.md).
Do not repeat these calls or the completed Stage A review merely to resume.

## Report presentation follow-up

The owner approved a bounded readability improvement after the first private
assessment. The current renderer adds a plain Chinese overview, case table, grouped
verified field/model explanations and technical appendix. Presentation 1.2 adds a
compact run summary, linked findings/evidence and local-field comparisons informed
by [public report examples](reviews/2026-10-16-report-reference-study.md).
See [the report ledger](harness/report-readability-ledger.md). The original assessment
and frozen Stage A artifacts stay unchanged; prior image/visual acceptance is not
new acceptance for this renderer. No new API request was made.

## Verified Stage A delivery baseline

- Verification commit: `be168d9962ff3dacd5e480818dd537d9f3438593`. Subsequent handoff-only
  commits update excluded records; source, lock, API bundle and image context stay identical.
- Linux Python 3.12.15 Dev Container and supplemental Python 3.11.17 full graphs
  each passed 166 tests with zero failures, errors or skips. The fast graph passed.
- Final arm64 native and amd64 emulated image jobs passed builds, prepared/disconnected
  dev full checks, nonroot read-only runtime replay, isolated synthetic peers, output
  persistence, SIGINT/SIGTERM and a generic Docker Desktop host-alias path.
- One independent whole-stage review is complete. Six Important findings and two
  regraded documentation defects were fixed in one author RED-to-GREEN pass.
  No re-review or deferred minor remains. Do not repeat this completed review.
- Wheel and sdist are in ignored `artifacts/distribution/be168d9/`; the exported wheel
  was installed and exercised offline in a fresh Linux environment outside source.
- Reports and exact local artifact hashes are listed in the handoff manifest.
  These observations are synthetic developer acceptance, not endpoint certification.

## Next work requires its own scope

Stage A is complete. W1 is the separately scoped Web/report follow-up above.
B owns tool loops, parallel cases and version matrices; C owns real
Claude Code workflows; D owns protocol-update Agent tooling and later maintenance.
The sole API bundle is Messages 2023-06-01 core revision 1.0.0, with no betas.
Capture writers use schema 1.1; readers retain conservative 1.0 support.

The frozen offline handoff did not run a real endpoint. Owner-authorized private
post-handoff assessments have since completed; see [the validation ledger](harness/validation-ledger.md).
A later disposable comprehensive suite also exercised 90 API scenarios and seven
fixed SDK/Claude Code client scenarios; all seven client scenarios passed, with
API differences and limits recorded separately. This did not implement Stage B/C.
The original four behavior checks passed, but the selected protocol/identity contract failed;
do not describe the target as fully compatible. Remote CI and registry publication
remain unrun. Remote repository
creation/push, registry publishing, account setup and real API execution require
the owner's specific authorization. Keep private targets, credentials, original
logs and the historical evaluation workspace outside source/build contexts.
Local commits and synthetic checks remain authorized.

Use the checked-in Linux/Python 3.12 Dev Container for development. The existing
prepared Dev Container is retained; its identifier is an ephemeral local detail.
The completed Stage A plan's scratch workspace is archived locally and removed; its
permanent ledger is tracked under docs/harness.

For future network preparation, retain the original source and wait patiently.
The user requested roughly ten-minute download-progress polling.
