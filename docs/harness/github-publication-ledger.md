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
