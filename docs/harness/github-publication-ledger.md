# GitHub publication ledger

## First publication preparation — 2026-10-21

The owner explicitly approved creating the public repository
`sleetdrop/anthropic-readiness`, selecting the MIT License, and first pushing the
current implementation as `main`, followed by observing GitHub CI. This does not
authorize a registry push, package release or Docker Hub account configuration.

Repository: https://github.com/sleetdrop/anthropic-readiness

Preparation started from clean `3d81586`. GitHub identity was confirmed as
`sleetdrop`; no origin or target repository existed. The public repository was
created without generated files, and the local origin was configured. The existing
implementation branches and all ignored local evidence are retained.

The project-level MIT License names `sleetdrop`, year 2026. The README links it and
preserves the distinct upstream Heroicons notice. No product source, tests, lock,
image recipe or workflow changed. The README change updates the broad source
fingerprint; previous acceptance records keep their exact original identities.
The image context and tested implementation bytes remain unchanged.

Before publication, a targeted check inspected 1,007 reachable historical blobs
(16,853,594 bytes) for known private target/model strings, provider/GitHub key
patterns, private-key blocks and private-network endpoint URLs: no match. No
tracked artifacts, private `.env` or `target.local` configuration was found.
This is a targeted publication preflight, not a comprehensive security audit.
Ignored evidence: `artifacts/publication-20261021/history-preflight.json`.

Linux/Python 3.12 documentation checks passed after the license/README edit.
The earlier full source graph and native ARM64/emulated AMD64 image jobs remain
their recorded observations; no redundant full graph was run for licensing prose.
At preparation, GitHub CI remained pending until the first push and actual completion.
Never reinterpret scheduled/unrun jobs as passing. Existing weekly/manual full
container workflows remain separate from push CI; neither publishes images.

## First push and remote CI observation — 2026-10-22 (Asia/Shanghai)

First push succeeded with `7b69b530f3997785808448b0cf1687c3bba3dfaa` on `main`.
GitHub confirmed PUBLIC visibility, default branch `main`, MIT detection and active
CI/container-matrix workflows. No force push, old-branch deletion or registry
write occurred. Only `main` was pushed. The first push CI ran without manual
dispatch; the separate scheduled/manual full container matrix was not started.

Run: https://github.com/sleetdrop/anthropic-readiness/actions/runs/39630071527

| Job | Observed outcome |
| --- | --- |
| runtime-amd64 | Passed: native Linux AMD64 smoke, 31 checks, no missing required smoke check; not full image acceptance |
| quality (3.11) | Failed: 12 gates passed; browser gate failed. All 822 Python and 20 Node tests passed; 77 of 78 browser cases passed, one error, no skips |
| quality (3.12) | Failed job with blocked graph: browser timeout at 301.60 seconds and integration timeout at 600.05 seconds. Remaining 11 gates passed |
| devcontainer | Failed: environment creation succeeded, then browser gate returned nonzero; other 12 gates reported passed in the job log |
| ci-required | Failed, correctly retaining failed child outcomes |

Python 3.11's failed browser case was `comparison keeps recoveries, persistent
failures, regressions and gaps together` at `tests/browser/diagnostics.spec.js:148`:
its 40-second test limit expired while waiting for POST /exports. This identifies
the observed failure boundary, not a proven root cause. The trace, screenshots,
JUnit and error context are retained. Do not assume increasing a timeout fixes it.
Python 3.12 produced no browser or integration JUnit after those gate timeouts;
no counts or pass are invented. Its completed reports contain 475 unit/harness,
84 acceptance, 5 installed-package and 20 Node tests, with zero failures/skips.
The Dev Container job has no full-report upload step; only its log establishes
gate outcomes, so exact browser testcase counts are not claimed for that job.

Both uploaded quality records observed clean `7b69b53`, unchanged source and
fingerprint `8c93fbb11a42050d945a43ae29ca2b5751fac3575a6797d3788a554245ff9423`.
The README licensing edit explains the difference from the earlier local broad
fingerprint; tested product/image inputs remain unchanged. Original local passing
records are not rewritten, combined with remote partial runs or used to mask CI.

Ignored evidence root: `artifacts/publication-20261021/`. Original remote logs,
watch log, downloaded artifacts and final run JSON are retained. The GitHub CLI
initially refused raw log control codes; the retry saved raw bytes to files and
text inspection stripped ANSI codes. This was a read-only log download issue,
not a workflow retry or suppression of a failing test.

| Record | SHA-256 |
| --- | --- |
| ci-first-result.json | 31b0fec6ab08b1d5a7536cab09ee41e1287aeda81f5f2cc842aa0a5088b7c38d |
| ci-py311/1792598170721910774/check-result.json | 5697ec6db402f8ead69752f40be3bf544c786cdfec42469ffed29e0ec1dd4bab |
| ci-py312/1792598160582137850/check-result.json | 45177b184658d374f8b5426fc76b3076c7f8cdcb520e2b20c0bcb1d54edc70fe |
| ci-runtime-amd64/1792598138338695832-amd64/image-result.json | 9fa3ac44b0284112eac3c62052b32905c10c91c9d24eee3ae270af03468bfa65 |

Next is one bounded diagnosis using the remote failure evidence, followed by a
meaningful reproduction and justified correction if needed. No budget, assertion,
test, workflow or product code was changed, and no workflow rerun was requested.
The publication closeout commit uses `[skip ci]` only for this documentation-only
record of the failed run; it neither retries nor claims to repair that run.
Documentation/schema/evidence checks passed locally in Linux. The prepared
container was restored to stopped, exit 0; no local test/build task remains running.
The first remote run is terminal. Stop after pushing this honest closeout record.

## One unchanged failed-job retry — 2026-10-22

The owner asked whether the failures were environmental or implementation-related,
and authorized one retry if environmental variance was plausible. Systematic
inspection of retained traces preceded the retry. The original failing test's
first trace step to export-response wait consumed 39,524.59 ms of its configured
40,000-ms test budget; the wait then lasted only 827.14 ms before timeout/teardown.
The request was actually sent. This is not evidence that an export hung for forty
seconds. No browser page exception or content-assertion failure was observed in
that trace. Broader gate timing differed materially across the original runners.

Exactly one `gh run rerun 39630071527 --failed` was requested, without changing
source, locks, dependencies, assertions or any time budget. It became attempt 2 on
the original `7b69b530f3997785808448b0cf1687c3bba3dfaa`. The original attempt's
local logs, machine records, artifacts and hashes remain unchanged. The passed
runtime-amd64 result retains its original 15:55–15:56 UTC execution, not a new run.

Attempt 2 completed with failure. It ran the failed jobs between 16:23 and 16:42
UTC on 2026-10-21 (00:23–00:42 Asia/Shanghai on 2026-10-22).

| Job | Retry observation |
| --- | --- |
| quality (3.11) | Browser graph blocked at 301.06 seconds, no browser JUnit; all other 12 gates passed. All 822 Python and 20 Node tests passed; integration took 594.05 seconds |
| quality (3.12) | Browser gate failed; the same comparison-export test hit its 40-second total limit, 77 other browser cases passed. All 822 Python and 20 Node tests passed; integration took 529.25 seconds |
| devcontainer | Browser gate failed, remaining 12 gates passed per log; no per-case report upload exists for this job |
| runtime-amd64 | Prior native AMD64 smoke success retained; not rerun |
| ci-required | Failed, correctly retaining unsuccessful child outcomes |

The second browser trace reached the export-response wait after 38,306.30 ms;
that wait lasted 1,992.98 ms until timeout/teardown. Thus the same composite test
again exhausted its total deadline near export, rather than proving an export
specific forty-second hang. These two traces do not independently prove that
export would complete or rule out a performance defect. Browser suite limits
and integration limits are separate from this per-test deadline.

Conclusion: CI timing/performance sensitivity persists across the sole unchanged
retry; it cannot be dismissed as one transient infrastructure failure. Completed
reports contain no observed protocol/report-value mismatch. Product hot-path cost,
composite test design and budget calibration remain competing causes requiring
measurement. No new timeout or test expectation was introduced to obtain green.
Next is one bounded diagnosis of actual CI/local stage timings and the slow
comparison/render/export path, then a justified correction with meaningful
verification. Do not start another unchanged retry or general review loop.

Retained evidence is under `artifacts/publication-20261021/`:
`ci-retry-result.json`, `ci-retry-watch.log`, `ci-retry-devcontainer.log`, explicit
new artifact-ID ZIPs/extractions (`ci-retry-py311`, `ci-retry-py312`) and both trace
budget observations. New artifacts were downloaded by ID to avoid overwriting
same-name attempt-1 artifacts. Result/schema/JUnit checks ran separately in Linux.

| Record | SHA-256 |
| --- | --- |
| ci-retry-result.json | bea2d241e2cff8b7c123d0cd26701c9717026c9888015b6070dcb447fd62b5e1 |
| ci-retry-py311/1792599825748240293/check-result.json | c4af47cb51169317f52391110e8a0561815fd332acec1b4f5defa2f5060a23e4 |
| ci-retry-py312/1792599829934797774/check-result.json | 08662aeeaf12da737514b9715c91893b5213ded5d3a14806e9fe691eeccb7915 |

Only documentation records changed in this diagnostic/retry turn. The closeout
uses `[skip ci]` for this prose-only record, retaining attempt 2 as failed; it is
not a CI fix or another retry. Documentation/schema/evidence checks passed.
The prepared container was restored to stopped, exit 0. No local test/build task
or remote retry remains running. Stop after the documentation-record push.

## Measured CI timing diagnosis completed — 2026-10-22

The owner requested diagnosis after the unchanged retry. No product/test/harness/
workflow/lock/deadline change or remote operation was made. Local Linux ARM64/
Python 3.12 profiling used retained synthetic CI before/after assessments.
Repeated installed identity/AST analysis accounted for about 1.42/2.39 profiled
comparison seconds; checked-validator construction accounted for about 0.57 seconds.
An existing integration case passed under profile: 18 identity calculations used
6.45/10.30 profiled test seconds and 69 validator constructions used 1.63 seconds.
Profile timings attribute work and are not normal request latency.

A separate unprofiled process-local experiment compared real comparison/export
outputs across four modes, three samples each. Median seconds: baseline 0.9053;
schema compilation reuse 0.7308; one freshly computed identity per operation 0.5605;
both 0.3848. All comparison/evidence values and export file bytes matched. The
experiment modified only transient diagnostic bindings; it is not a production
cache, safety proof or remote CI pass. All 699 retained fixture files match the
original artifact ZIP; source fingerprint remains unchanged. Full details, exact
hashes, scope limits and the correction recommendation are in
`docs/reviews/2026-10-22-ci-timing-diagnosis.md` and ignored
`artifacts/ci-timing-20261022/`.

This identifies avoidable implementation work amplified by CI runtime differences,
not merely an incidental network failure. Recommend preserving full document/
evidence checks while reusing immutable schema compilation and reducing identity/
AST duplication with source/resource/dependency mutation coverage. Do not cache
identity or evidence verdicts forever or raise deadlines before measuring the fix.
No new CI retry or code correction occurred. Linux documentation/evidence checks
passed; the prepared container is stopped again, exit 0. Stop after a local
record-only commit; no remote write is included in this diagnostic task.

## Content-derived work reuse correction: local verification — 2026-10-22

The owner approved correcting the two measured hotspots, retaining all validation
semantics and time limits, then observing CI on a justified new revision. Work
stayed sequential in the existing checkout/Linux ARM64/Python 3.12.15 container.
Only `json_validation.py`, `diagnostics/identity.py` and their two unit-test files
change product/test behavior. No plan scope, dependency, schema, golden, required
case, deadline, image recipe or workflow was changed.

Implementation:

- Generic document validation reuses up to 64 private compiled schema snapshots,
  keyed by complete ordered JSON content. Serialized snapshots own their data;
  caller mutation cannot poison a cached validator. Every document still runs
  iter_errors. External references remain rejected. Declaration order stays in
  the key because it controls same-path diagnostic ordering; this is intentionally
  not a cache that merges differently ordered schemas.
- Installed identity reuses up to 128 source-content-derived AST analyses. Every
  call still reads source text, rebuilds module inventory/closure permissions,
  hashes code/resources and resolves dependencies. Manifest checks run against
  the current manifest even on a content hit. No final identity, file-stat verdict,
  comparison eligibility or evidence verdict is cached.

Regression evidence:

- Initial RED: 2 expected failures / 36 controls passed. Repeated document checks
  compiled three times instead of once, and unchanged source was analyzed twice.
- Initial focused GREEN: 38 passed. Initial fast had one new-test regex lint error;
  the original failed record remains. The regex was corrected, not a product
  assertion or golden. An intermediate full graph passed all thirteen gates.
- Self-review then reproduced altered error ordering from sorted serialization.
  A new order regression was observed RED before removing key sorting. The repeat
  probe now uses a distinct same-order dictionary, because differently ordered
  schemas deliberately retain their distinct diagnostic ordering. Its expected
  single compilation and real invalid-document rejection remain unchanged.
- Final focused suite: 39 passed, no errors/skips. Nine added cases cover real
  document rejection after warming, schema mutation and snapshot isolation,
  external ref/dynamicRef mutation, unchanged-source work reuse, content changes
  with identical size/mtime, manifest permission changes, invalid changed source,
  and declared diagnostic ordering. Existing dependency/resource/module mutation
  coverage also remains in the complete suite.

Final full graph: all 13 gates passed, unchanged source, zero failures/errors/
skips. Python: 831 = 484 unit/harness + 258 integration + 84 acceptance + 5 installed-
package. Node: 20. Chromium: 78. Browser gate took 196.58 seconds, integration
223.44 seconds. The mixed-comparison test took 22.8 seconds. Existing per-test
40-second, browser-child 300-second, outer-browser 420-second and integration
600-second limits remain unchanged. These numbers are not a cross-machine promise.

The final full record observed the uncommitted patch on clean base
`ea614a4e9ad8d0ddabecfd778d9d769194ce8524`, with dirty=true, not a claimed
clean-commit run. Source fingerprint is
`2d7a3e1b454b72f2e38e7b2e36b64432dfd95b832386b8096ab8ad23de7b4fd4`;
new image-context fingerprint is
`e784f413b3ca4322fd911414d550311850a37fa496e81fdb55312e99b5e66bfd`.
Image-context calculation is not an image build or acceptance observation.

A fresh four-case synthetic before/after lineage was generated on the final
implementation. Three alternating samples per mode compared actual optimization
with bypassing only the two new analysis/compilation caches. All identity/evidence
checks remained real, comparisons comparable and complete generated file bytes
identical. Median uncached time 0.9383 seconds; optimized 0.4841 seconds. No absolute
performance threshold was added to tests. This bounded local comparison is not a
remote performance prediction. Earlier diagnostic/provisional samples remain
separate, including their pre-final source fingerprints.

Authoritative ignored root: `artifacts/ci-optimization-20261022/`.

| Record | SHA-256 |
| --- | --- |
| full-final/check-result.json | 692395fdc36f74d706d3418b9ad9d9ce5c7ab0df93b32347bc43b50bec0b6fbd |
| measurement-final/measurement-summary.json | dc02a268bacb4d7dac9403979fc09a9090d24b1c2a81d91456977d722afa32c6 |

The separate evidence verifier checked packaged schema, positive actual JUnit
nodes, RED/GREEN counts, required gates and matching final benchmark/full/current
source fingerprints. Documentation checks passed after handoff edits. Earlier
failed attempts are not erased or merged into a passing record. The prepared
container is stopped again after local closeout, exit 0. Current-source remote CI
is pending the agreed correction push; original failed remote attempts remain
unchanged. No new full image job, endpoint/client test or independent review ran.
