# Local development policy and verification ledger

## Scope and decision

On 2026-10-31 the owner accepted host development with the Dev Container retained
as an optional reproducible Linux environment. This is supporting-only work: no
endpoint scenarios, fault detection, runtime behavior or CI job requirements
changed. Existing Linux, container, image and remote results retain their original
source identities and do not prove this documentation revision passed those gates.

## Mac preparation observations

The host has Python 3.12.15, uv 0.13.1 and Node 24.22.0/npm 11.19.1. Node 26 was
first on the initial PATH; selecting Node 24 made the frontend static prerequisite
pass. The locked Chromium prerequisite returned blocked because the matching
browser was not present. The npm tree was already present; a fresh npm install
and browser download were not tested.

An offline `uv sync --locked` with an empty disposable cache failed for missing
dependencies. With the host's default package index, networked `uv sync --locked`
reported a lock mismatch. A disposable lock comparison showed index URL changes;
with `UV_DEFAULT_INDEX=https://pypi.org/simple`, offline `uv lock --check` and
networked `uv sync --locked` succeeded in a temporary environment. A diagnostic
`uv lock --offline` was inadvertently run in the checkout and rewrote registry
URLs; the clean original lock was immediately restored from HEAD. No dependency
change is included. The interrupted frozen install attempt is not a pass.

The browser fixture and some harness tests use Linux `/proc`; complete macOS fast
and browser checks cannot be claimed supported on the basis of the host setup.

## Verification

- Mac offline focused unit suite: 410 passed. Node static prerequisite and the
  fast graph's frontend-static, lock, format, lint, architecture and schema gates
  passed. The Python/npm/Chromium fresh-setup path is not fully verified.
- On the prepared Mac environment, CLI validation, synthetic dry-run and valid
  capture replay exited successfully. Dry-run and replay each reported zero
  actual requests; replay's selected synthetic case reported passed. These do
  not establish live endpoint compatibility.
- Mac fast graph failed in two gates. The type gate reported two missing macOS
  `pidfd` attributes. The first run had seven test failures, including three
  local-listener permission failures; with local listener permission, the rerun
  had 494 passes and four failures: three `/proc`-dependent cases and a timeout
  harness case. Logs and JUnit are in ignored `artifacts/checks/1793430349959490000/`
  and `artifacts/checks/1793430404341570000/`. Both runs recorded source changes
  during execution as documentation was edited; neither is a final-source pass.
- Documentation link check passed after adding this ledger; an earlier link check
  failed while the ledger had not yet been created. The lock's final bytes match
  HEAD. Linux full checks, Dev Container/image acceptance, remote CI, and real
  endpoint calls were not run for this documentation increment.

## Independent review

One independent whole-stage review identified that the README and development
guide placed full fast-check commands in a potentially misleading macOS context.
Both now explicitly direct full checks to prepared Linux environments. The review
also suggested exercising the local CLI; the three synthetic checks above passed.
No re-review was requested.

## macOS fast graph portability follow-up

The owner selected a follow-up to make the complete fast graph usable on macOS.
This is supporting-only work; it adds no endpoint scenarios or fault detection.
The plan is to preserve timeout and fixture cleanup guarantees, verify the same
required fast gates on macOS, and independently review the complete change.
Full-graph macOS, container images and real endpoints remain separate scopes.

Before implementation, two new regression cases failed: a transient permission
error during a timed-out process-group probe prevented a result record, and a
live fixture PID was not rejected on a host without `/proc`. The original macOS
fast failures above remain part of the record. The implementation treats an
indeterminate process-group probe conservatively, verifies any still-live fixture
PID rather than claiming success on a reused PID, and checks descendant cleanup
with an owned FIFO held open by the synthetic child. The Linux-only `pidfd` test
keeps its runtime behavior while exposing typed function signatures to macOS mypy.

The final Mac fast graph passed all eight required gates on unchanged source
fingerprint `3c335b57b0703d7eb7de622d9b1b1dbcaeb02a8eaa511f86a95771cb148b00a8`:
503 Python unit/harness cases and 33 frontend unit cases, with no failures or
skips. Evidence: ignored `artifacts/checks/1793441737571281000/`. Python 3.12.15,
uv 0.13.1, Node 24.22.0 and the project-local `.venv` were used with an explicitly
selected project index and disposable uv cache. Documentation checks passed.

An earlier fast run passed on unchanged source at
`artifacts/checks/1793431620159143000/`, before the independent review correction.
Two subsequent attempts had all gates pass but recorded a changing source tree;
their overall result was failed, not a final pass. See
`artifacts/checks/1793441343650485000/` and `1793441424782659000/`.

A real synthetic Mac fixture lifecycle started, terminated and verified release of
the owner PID and both listeners. Its first attempt failed because its output root
already existed; a fresh child directory corrected that invocation. No browser was
launched. One independent whole-stage review identified a test cleanup leak on
early failure. A focused re-review found a further open-before-close race; the
no-reader variant first timed out, then passed after nonblocking open. Both reader
closure orderings and the still-open descendant check pass; the reviewer found no
remaining actionable issue in that correction. The focused harness suite passed
28 tests.

Linux full/fast verification, browser tests, fresh Chromium installation, image
acceptance, remote CI and real endpoint calls were not run. A sandboxed Docker
status query could not access its socket; an elevated retry was interrupted after
waiting and did not establish server availability. The fixture PID check is now
deliberately conservative: a live reused PID blocks cleanup acceptance, and an
inaccessible PID remains unverifiable rather than silently passing.
