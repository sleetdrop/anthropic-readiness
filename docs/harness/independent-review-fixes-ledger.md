# Independent review correction ledger

## Scope and stopping rule

The owner authorized one complete correction per turn on 2026-10-20, followed by
a pause rather than starting another finding with an uncertain usage allowance.
Work stays on the existing checkout and prepared Linux/Python 3.12 Dev Container.
Local commits are required; no remote write, live endpoint call or new whole-stage
review is part of this correction. The completed W2 plan and its historical
acceptance records remain unchanged.

Review source: `0ac72c6be5ac3d16ea76abf487026e3efb55c2be`.
Original review and synthetic probes are retained, without modification, under
ignored `artifacts/independent-review-20261020/`. The report records four reproduced
findings; each still requires author verification before its own correction.

| Finding | Priority | Current state | Next action |
| --- | --- | --- | --- |
| F01: malformed intermediate message delta is overwritten | P1 | Fixed and locally verified in 6ea328d | Complete |
| F02: missing response evidence can still support recovery claims | P1 | Fixed and locally verified | Stop after local commit |
| F03: replay trusts contradictory cached tail metadata | P2 | Pending; no correction in this turn | Verify byte-derived framing against metadata |
| F04: imported dimensions and request counts contradict facts | P2 | Pending; no correction in this turn | Verify result semantic validation and projections |

## F01: retain malformed stop-field failures

Root cause: `StreamValidator.consume` merged `stop_reason` and `stop_sequence`
directly into the reconstructed message. Later valid values erased the only
observable malformed values before final-message validation. Existing `_record`
already preserves failures once they have actually been recorded.

Correction: inspect each present stop field before merging it. A non-null value
must be a string; otherwise record `STR-JSON=FAIL` with the event sequence. Reuse
the existing failure-retention mechanism and final-message checks. Missing keys,
null/string values, legal multiple deltas and unknown extension fields retain
their existing behavior. No enum, catalog, schema, golden or required-case change
is introduced. The execution implementation identity covers the changed validator;
old source acceptance is not rebound to this patch.

The regression catches removal of the event-level type check: integer, Boolean,
object and array values for either field must remain FAIL after a legal terminal
delta. It checks the offending event identity and confirms final stop checks are
PASS, proving that the preserved failure comes from the intermediate event.
Four legal controls cover omitted fields, null fields, string stop reason and an
unknown extension field.

### Observed checks

All product execution used the existing Linux ARM64/Python 3.12.15 Dev Container
with `UV_OFFLINE=1` and locked dependencies. Evidence root:
`artifacts/review-fixes-20261020/f01/`.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Regression before implementation | 8 expected failures, 4 legal controls passed | `red.xml` |
| Original reviewer runner probe before implementation | Malformed and valid controls both incorrectly returned exit 0 / passed | `probe-red/delta-summary.json` |
| Stream and final-message regression suite after implementation | 59 passed; zero failures/errors/skips | `green.xml` |
| Same reviewer runner probe after implementation | Malformed stream exit 1 / not_ready; valid control exit 0 / passed; all three planned cases remain accounted | `probe-green/delta-summary.json` |
| Runner, historical review regressions and comparison service | 26 passed; zero failures/errors/skips | `runner-comparison.xml` |
| Fast verification | All 8 gates passed, unchanged source; 475 Python unit/harness tests passed | `fast/check-result.json`, `fast/unit.xml`, `fast/frontend-static/` |

The fast run observed the uncommitted patch on base `0ac72c6`, not a clean-source
whole-stage release. Its source fingerprint was
`9f1c8454141c19bc512e90a7b9f5444882fc1195bf3cc2d7c7a1a2b3c868252e`.
Focused suite counts overlap the fast suite and are not summed as unique tests.
The standalone runner probe uses synthetic transport, not a real endpoint.

### Limits and handoff

No full browser graph, installation/multi-architecture image rebuild, remote CI
or real endpoint/client workflow was run for this two-line validator patch.
Existing runtime images and retained preview data have not been updated or
migrated. The prior W2 image/full records certify their old source only.
No existing evidence or failed attempt was deleted or rewritten.

The development container was stopped before this turn and was restored to that
same stopped state after all checks completed. The final Docker state is recorded
in `container-final-state.json` (`exited`, `running=false`, exit code 0). No check
or build process remains running in it. No replacement container, network or volume
was created. This F01 turn stopped without starting another finding. The owner
subsequently authorized the separate F02 turn recorded below.

## F02: require complete, attempt-bound response proof

Base: `6ea328d` after F01. The owner authorized proceeding with F02 only if it
could finish within the remaining allowance, retaining the one-fix stopping rule.
No F03/F04 correction or new independent review is included.

Root cause: report-source quality verified only the declared top-level references.
It did not check the capture's own file inventory, and required nonempty assertion
references only for FAIL. A self-consistent enclosing package could therefore omit
response files, retain PASS claims, and regain comparison/retest eligibility.

Correction: share the existing capture-schema/exact-four-file inventory check
between the replay loader and report-source reader. For each captured attempt,
require its response metadata and all four inventoried files in the verified
top-level inventory, with the same hashes. Observed PASS assertions require a
reference; attempt assertions cannot borrow proof from another attempt. An
interrupted/internal attempt that never produced a capture remains readable with
its existing indeterminate execution assertion. No source bytes are rewritten,
no schema/golden/catalog changes are made, and replay framing behavior is not
changed as part of this extraction. Existing implementation identity accounts for
the changed evidence module; historical acceptance is not rebound to this patch.

All adapters consume the shared quality result. A malformed source stays readable
as `missing_or_invalid`, loses retest/compare eligibility, produces incomparable
pairs instead of recovery claims, and cannot be exported with evidence included.
An independently assembled incoming ZIP is also retained only for limited reading;
activation, revalidation and source-fact recomputation cannot restore eligibility.
Complete valid before/after proof still yields the legitimate recovery conclusion.

### Observed checks

All product execution used the existing Linux ARM64/Python 3.12.15 Dev Container,
offline with locked dependencies. Evidence root:
`artifacts/review-fixes-20261020/f02/`.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Initial regression construction | 4 failed, 3 passed; nested mutation helper needed correction because production JSON conversion copies objects | `red.xml` |
| Corrected independent mutations, before implementation | All 6 negative variants failed because quality was incorrectly verified; healthy recovery control passed | `red-2.xml` |
| Core closure/source/comparison tests | 26 passed; zero failures/errors/skips | `green.xml` |
| Related import/export/recovered-report/review/CLI/handoff tests | 60 passed; zero failures/errors/skips | `related.xml` |
| Fast verification | All 8 gates passed, unchanged source; 475 Python unit/harness tests passed | `fast/check-result.json`, `fast/unit.xml`, `fast/frontend-static/` |

The six independent mutations remove body, event or response files, contradict a
capture's declared file hash, remove a PASS assertion's reference, or substitute
another case's proof. Tests bind all enclosing result/context hashes after the
intentional mutation, so rejection cannot rely on an accidentally stale envelope.
They exercise real execution, source reading, comparison, guarded export,
independently assembled ZIP import/activation, repeated baseline reads and comparison
against the imported source. Original delivery bytes remain unchanged throughout.
The first test-construction attempt remains retained and is not counted as the
complete six-variant RED result. Expectations were not weakened.

Fast observed the uncommitted patch on base `6ea328d`, with source fingerprint
`db07c022a13e94c4b03607ddce07bc1046d9239f9b1e6b952580892896ad2e9e`.
This is local correction verification, not clean-source whole-stage acceptance.
No full browser graph, installation/multi-architecture image rebuild, remote CI
or live model/client workflow was run. Existing runtime images and preview data
were not updated. F03 and F04 remain pending for separately resumed turns.

After all checks completed, the existing development container was restored to its
original stopped state. `container-final-state.json` records `exited`,
`running=false`, exit code 0. No test/build task remains running; no replacement
container, network or volume was created. Pause after the local F02 commit.
