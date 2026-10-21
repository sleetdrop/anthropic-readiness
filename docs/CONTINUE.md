# Local delivery status

## Current follow-up: F06 corrected locally; full verification is next

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

The container is stopped again, exit 0. Stop after the local F06 commit.
F01-F06 are now locally corrected within their recorded scope. Next is a separate
complete source verification turn, followed by updated Docker acceptance. Do not
automatically start another review, image build or real endpoint run. Exact
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
