# W1 independent review — 2026-10-18

## Scope and verdict

One independent reviewer inspected `ad83593812f18f61feea0b53cd19d7a2f8fb1dbc`
through `0d1191ee6e25b5d32bc176ce07ae1d155644dce4`, against the approved
[specification](../superpowers/specs/2026-10-16-local-web-console-design.md) and
[plan](../superpowers/plans/2026-10-16-local-web-console-implementation.md).
The same reviewer context resumed after a quota interruption; this was not a
second review. The checkout stayed clean and unchanged throughout review.

Independent verdict: **With fixes**. Five Important findings, two Minor findings,
no verified Critical finding. Candidate W1 completion is not accepted yet.
The reviewer additionally ran eight Focus-related regressions: eight passed in
6.51 seconds. These do not cover the missing scenarios below and do not replace
whole-stage acceptance. The author will perform one RED/GREEN fix pass; no re-review.

## Strengths observed

Transactional idempotent admission precedes preview expiry checks. Worker ACKs
prevent subsequent dispatch after parent loss. Exports rehash copied bytes and
publish discoverability last. Original assertion semantics remain intact, CLI/Web
share the execution engine, optional Web resources are packaged, and environment/
endpoint/publication limits are represented honestly.

## Findings as reported

| ID | Reviewer grade | Finding and reproduction |
| --- | --- | --- |
| I1 | Important | `report_sources.py` only reads parent-advertised checkpoints; manager restart marks missing-result jobs interrupted without exposing valid unindexed checkpoints. Actual parent kill at the `pending_ack` barrier retained one valid checkpoint and one request, but report cases and ZIP evidence were empty with no warning. A two-checkpoint fixture retained only one in reports/exports. Preserve active publication gating; expose explicitly recovered verified partial records after interruption, without resend, invented timing or final results. |
| I2 | Important | `result.json` absence is checked before the execution snapshot. Publishing the result and terminal state after that absence check yields completed job/execution but a stable partial report with null source hash. Detect inconsistent source generations and retry; retain honest diagnostics for genuinely missing/corrupt results. |
| I3 | Important | Partial projections have empty report context; HTML/Markdown treat every non-`live_endpoint` context as synthetic/replay. A live partial with one request is incorrectly labeled offline synthetic. Preserve explicit origin or show an honest unknown origin; mode alone does not prove live versus synthetic. |
| I4 | Important | Narrow matrix outcome cells each reserve six rem while the first column collapses. Actual 573px GUI screenshot and Chromium measurements: first column27.31px/row425.86px at390px;34.77px/310.34px at573px;261.16px/80.11px at1280px. Preserve readable column width, bounded accessible keyboard scrolling, and Web/offline/print checks. |
| I5 | Important | Every matrix aggregate links to the group's first case. In a streaming protocol cell containing FAIL and PASS, clicking PASS opens the first FAIL case. Link each status to its actual matching members, or open the correct member list; preserve no-script access and focus behavior. |
| M1 | Minor | `junit_result()` accepts one executed plus one skipped testcase as passed. Existing observed436Python/10Node/15Chromium artifacts have zero skips, so those observations remain valid. Unexpected skips should fail the selected-test gate. |
| M2 | Minor | Capability filtering only offers all/needs-attention, merging failures and unresolved states. The four-case scope remains readable, but explicit separate filters are absent. |

## Review Focus results

1. Lost reply/two tabs/preview expiry: admission ordering and uniqueness were
   sound; related three regressions passed.
2. Parent loss between checkpoint and indexing: actual worker termination and
   no-resend passed, but evidence visibility/export failed (I1).
3. Hostile markup and paths: no reproducible execution/outside-read defect found;
   escaping, CSP, opaque IDs, path/symlink handling and download headers checked.
4. Replacement after verification before copy: actual copied bytes are checked;
   failure leaves no published record. Related regression passed.
5. Expired session/ahead cursor: session/read recovery, reset handling and no
   mutation resend were sound. Separate final-publication race remains I2.

## Behaviors the reviewer declined to judge

- Stage B/C/D, tool loops, SDK/Claude Code and newer version matrices: outside W1.
- Real endpoint compatibility and the historical local service: no W1 live opt-in.
- Remote CI/registry publication/native AMD64 developer environment and unrun
  platforms: not observed; emulated runtime evidence is not extrapolated.
- Policy-denied actual IAB host-file navigation: no bypass; in-memory Chromium
  measurements and approved synthetic offline QA do not establish that manual path.
- Public multi-user deployment and a same-privilege local writer's complete
  concurrent filesystem attack model: outside this personal local-service scope;
  path/copy checks do not certify those expanded deployments.

## Author disposition

All five Important findings are accepted for reproduction and one author fix pass.
M1 is **regraded Important**: a partially skipped selected suite could otherwise
certify incomplete required checks. This does not change prior zero-skip results.
M2 is **Minor, deferred**: all raw statuses remain visible; at four cases the missing
filter is a navigation inconvenience rather than a false result or blocked task.
Author fixes, failing regressions and final evidence will be recorded separately
below. This report will not be rewritten as an independent approval of later code.

## Author fix pass (not a second independent review)

- I1: the real pending-ACK parent-loss test now reads the report, follows opaque
  HTTP evidence links and verifies ZIP checkpoint/capture hashes. Separate active/
  interrupted tests preserve publication gating. Corrupt evidence, foreign run
  identity, unstarted cases and excess request counts are rejected. Recovery uses
  a verified internal checkpoint inventory; original execution/journal timing and
  checkpoint bytes remain unchanged, with explicit recovery notices.
- I2: deterministic absence-check/publication/snapshot and terminal-partial tests
  failed before the fix. A sidecar binding a final result cannot certify an unread
  result; HTTP acceptance checks result status/hash together with execution. A
  genuinely missing bound result is unavailable, not an ordinary clean partial.
  The partial-replay fixture now explicitly represents interruption without a final
  receipt; its zero-request assertions were preserved.
- I3: partial origin is explicitly unknown when it was not persisted. HTML and
  Markdown distinguish known live, known synthetic/replay and unknown JSON context
  values. Neither live mode nor missing context establishes real endpoint origin.
- I4: first-column width, named keyboard scrolling, bounded page layout and print
  behavior passed actual Web/offline Chromium checks at390/573px. The first fix
  exposed standalone Grid expansion; that failure was retained and corrected.
- I5: state actions select matching cases; multiple matches use native disclosures
  with stable IDs and member links. Mixed PASS/FAIL navigation passed with scripts
  enabled and disabled; Web refresh preserves expanded members and keyboard focus.
- M1, author grade Important: both actual JUnit nodes and pytest suite counts now
  reject partially skipped selected suites. Two explicit return-code assertions
  failed before the fix. Existing all-skipped/zero-test/failure classifications remain.

Focused verification observed: I1 nineteen checks, then six recovery/accounting/
barrier checks; I2 twenty-eight API/source checks; I3 twenty-eight report checks;
I4 nineteen browser cases; I5 thirteen static report cases and twenty-two browser
cases; M1 twenty-nine harness checks. All meaningful failures and later outputs are
retained in ignored local artifacts. Ruff/lint and strict mypy passed126 source
files after explicit JSON type narrowing. Whole updated source/image acceptance
is recorded in the W1 handoff after completion; these focused results alone are not
whole-W1 acceptance. M2 remains deferred as recorded above.

The complete author verification graph subsequently passed all13 required gates:
454 Python tests (253 unit/harness,135 integration,62 acceptance,4 installed),
10 Node cases and22 Chromium cases, with zero failures/errors/skips. The initial
full attempt retained one test-only TypeScript URL-resolution failure; it was fixed
without suppressing types and the full graph rerun passed. Rebuilt-image acceptance
remains separate and is bound to the clean source commit in the final W1 handoff.
