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
