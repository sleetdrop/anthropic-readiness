# Worker exit probe correction

After PR 2 merged as `f94ed1d`, its post-merge main CI run 41195337568 failed
the Python 3.11 integration gate: 257 tests passed and one failed. The owned
worker's `/proc/<pid>/stat` existed at the first check but raised
`ProcessLookupError` when read after parent termination. The other main jobs,
including Python 3.12 and the Dev Container, passed; the required aggregator
correctly failed. Original logs and JUnit were downloaded to ignored
`artifacts/ci-41195337568-py311/` in the isolated workspace.

The existing Linux test now reads the process state once and recognizes missing
or disappearing procfs entries as exit. It still waits for either exit or zombie
state and retains the pidfd cleanup, original deadline and no-additional-request
assertions. Unrelated read errors do not count as exit. This is supporting-only
test infrastructure: it adds no endpoint scenario or product behavior.

Four synthetic cases cover `FileNotFoundError`, `ProcessLookupError`, live versus
zombie state, and permission errors. Before the helper was implemented the new
test module could not import it; afterward all four cases, Ruff and strict mypy
passed on Mac. The historical CI failure remains failed; it is not replaced by
these local checks. Linux execution and fresh remote CI need separate evidence.

The final Mac fast graph passed all eight gates on unchanged source fingerprint
`207e803cece30e7b398559d0c9044553ad26ed56724729e9b50048b1e8b5c5fb`:
504 Python unit/harness and 20 frontend unit checks. Its record remains in ignored
`artifacts/checks/1793445909528911000/`. One independent whole-stage review found
no material issue; the Linux-only integration case has not yet been re-executed.

## Existing browser test synchronization

PR 3's initial GitHub CI passed both Linux Python full jobs, including the worker
integration case, and amd64 image smoke. Dev Container again failed the same
existing browser case as PR 2's first attempt; 77 of 78 cases passed and the
required aggregator failed. Its trace again shows a `running` workbench snapshot
before a completed HTML render, so the expected synthetic HTML failure was never
injected. The first failed Dev Container reports for both PRs remain under ignored
`artifacts/ci-41192868578-devcontainer/` and `artifacts/ci-41196893524-devcontainer/`.

The browser test now installs its snapshot route before starting the job, waits
for a real completed snapshot before fulfilling it, and independently verifies
the server is running before releasing it. It still requires exactly one injected
503, a later successful read, the completed UI and the original request counts.
The existing running-UI assertion moved to the existing active-composition case,
which holds a real job in progress; no serial browser case was added. Independent
review found and resolved a possible pre-release waiting cycle, and confirmed the
final test retains these assertions. The original 12- and 40-second limits remain.

On Mac, both final browser cases passed twice using the existing Chromium headless
shell 143.0.7499.4; fixture PID and listener cleanup passed. The synthetic peer
logged connection resets during teardown. This is supplemental evidence: the
project locks Chromium 156, which must still run in Linux CI. An attempted locked
Mac browser download was interrupted while slow; the first fallback configuration
could not start its server, and a second used an incomplete browser installation
and failed before executing test bodies. Those attempts are not passes. Existing
full Linux browser duration was close to its unchanged 300-second gate budget;
the final test must be observed in CI.

With both corrections present, all eight Mac fast gates passed on unchanged
source fingerprint `c2e4d4c15de019f07dbcf02563336da535dc86ddff0832cf3ba59bf6a0dc4df0`.
The ignored record is `artifacts/checks/1793448827012777000/`. The earlier Mac
fast result above applies to the worker correction before the browser change.
