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
