# Investigation flow before layout selection

Date: 2026-10-23. Status: proposed interaction structure for owner discussion.
This supersedes treating any preceding overview, runner or palette as a selected
direction. Wireshark and Charles are references for managing complex information;
the owner did not request their appearance or window layout to be copied.

## Scope and evidence

This is a desk exercise with fictional observations, not a captured user session,
usability audit or new interface implementation. Checked the current five-case
catalog, retest recipe, comparison facts and diagnostic package schemas. These
existing contracts ground the proposal but do not prove its usability or that
every proposed interaction is already available.

No new colors, component library, pane arrangement or frontend stack is selected.
No product/CLI/report schema changes, real requests, browser control, container
changes or plugin installation are part of this exercise.

## Concrete scenario

Run A selects all five current cases, producing up to six requests:

| Case | Requests | Task | Protocol | Observation |
| --- | --- | --- | --- | --- |
| Plain message | 1 | Pass | Deviation | stop_sequence absent |
| Streamed text | 1 | Pass | Deviation | Duplicate message_start |
| Streamed counting | 1 | Inconclusive | Inconclusive | Read deadline; partial response |
| Forced tool choice | 1 | Pass | Deviation | stop_sequence absent |
| Tool-result round trip | 2 | Pass | Pass | Fresh tool result consumed |

Accounting: four task passes and one inconclusive task; three cases with protocol
deviations, one protocol pass and one inconclusive protocol result. Two distinct
protocol observations affect three cases. One additional case is inconclusive.
Five cases, six requests and two protocol observations are different counts.
Grouping similar observations does not establish a shared internal root cause.

For a complexity exercise, the streamed-text exchange contains 206 fictional
events: 200 text deltas plus lifecycle events, including a second message_start
at event 58. This adds no formal endpoint scenario and makes no UI performance
claim. It tests what information must remain accessible when the evidence is long.
Claude Code is not exercised anywhere in this scenario.

## Task sequence and disclosure

| Moment and user question | Information needed immediately | Open only when needed | Required navigation behavior |
| --- | --- | --- | --- |
| Configure: what am I about to run? | Endpoint/model, selected scope, request/time limits and explicit Start | Versions, case inventory, advanced settings | Keep scope visible; retain validation, live opt-in and frozen-plan admission |
| Running: is it progressing, and do I need to act? | Current activity, finished/selected cases, elapsed/wait state, observed exceptions, Stop | All cases, transport details, captures | New results update counts without replacing the user's current selection |
| Triage: what needs investigation? | Distinct protocol observations and inconclusive conditions, affected case counts, observed impact and client-test limits | Individual assertions and technical identifiers | Open a problem while retaining run identity, filter and return position |
| Investigate: what exactly happened? | Selected problem, affected case and exchange, expected/actual observation | Full ordered events, field structure, headers and raw capture | Select a related case/step without losing the problem context |
| Handoff: what should my colleague inspect? | Reading report versus diagnostic bundle; contents, omissions and evidence availability | Exact file manifest and hashes | Shared artifacts preserve the issue/case/exchange relationships without requiring the local server |
| Verify repair: what changed in comparable checks? | Baseline, rerun scope/versions, then resolved/persistent/new/inconclusive observations | Per-case before/after evidence and configuration differences | New run preserves the original result; incomplete or incomparable work never becomes a repair |

When everything passes, the default surface remains quiet and reports the scope
that passed. It still labels untested client workflows and unselected features.
Pending work, active work and an executed-but-inconclusive result need separate
labels. Completing an execution is not a protocol or client verdict.

## Example investigation, without committing to screen geometry

1. Choose the duplicate-start observation from Run A's exceptions. Show that the
   streamed-text task returned its expected text, with client impact untested.
2. Follow its occurrence to the streamed-text exchange. Open event 58 with nearby
   events and enough earlier lifecycle context to explain the violation. The full
   ordered stream remains available without requiring 206 expanded rows up front.
3. Inspect the parsed fields or original event payload. Every view refers to the
   same recorded exchange; interpretation is visually separate from raw data.
4. Return to exceptions with the prior filter/position. Open the missing-field
   observation and select either of its two affected cases.
5. Show the absent-key expectation next to the observed parent object. Never
   insert an invented missing line into the original JSON, or pretend an absent
   field has an exact byte location. Distinguish absent from explicit null.
6. Open the tool-round-trip case and see both exchanges under that one case.
   Switching steps keeps the case's overall state visible. A successful step must
   not conceal a failed or unexecuted prerequisite.

The content hierarchy is run -> case -> step/exchange -> captured evidence.
Problems cross-reference occurrences within that hierarchy; they are not a second,
disconnected copy of the data. Rule identity/version and evidence references link
expectations to observations. No fixed three-column, upper/lower, tab or drawer
arrangement is implied by these relationships.

## Repair verification and handoff exercise

The default verification action reruns the original selected scope as a new run,
with its recipe, versions, prerequisites and fresh tool-result data. Keep the
explicit request/time budget. Do not replay only the final tool-result request.
A targeted problem-verification action is a proposal requiring separate scope and
contract work, not a newly delivered feature.

In fictional Run B, both missing-field occurrences pass, duplicate start persists
and streamed counting remains inconclusive. Present: the missing-field observation
did not recur in these two comparable cases; duplicate start still occurs; counting
still lacks a conclusion. Do not claim stable workflow compatibility or describe
the inconclusive case as fixed. Changed versions, omitted cases or missing evidence
must be visible before any before/after conclusion.

Reading reports explain results and limits independently. A diagnostic bundle
also provides an Agent entry summary, structured facts, sanitized supporting
captures, references and enough recipe/context information to rerun the scope.
Reuse the existing package/recipe/evidence-integrity contracts; new content or
cross-assertion grouping must be mapped or versioned explicitly during implementation.
Runtime credentials and source evidence must never be conflated in export previews.

## Decisions and next bounded artifact

Keep global run status accessible, group by observed phenomenon rather than claimed
root cause, reveal evidence progressively and preserve context across navigation.
Normal operation should not require reading a protocol trace or a full report.
Problem/evidence views must let maintainers reach the exact observation and return.

The next design artifact should demonstrate one issue-to-evidence-and-back journey
with these mixed outcomes and long stream. Decide presentation from those tasks;
do not start another complete application skin or assume a Charles/Wireshark clone.
The preceding static samples remain discussion material, not approved designs.

## Bounded artifact ledger: 2026-10-23

Owner authorized the issue/evidence/return sample, now delivered as flow.html.
Its synthetic affected-occurrence selection, 206-event navigation and retained
context passed final isolated-browser checks. Context-only search was reproduced
before correction to whole-capture search. README.md records observed positions,
bounds and test-fixture corrections; all attempts remain in ignored
artifacts/investigation-flow-20261023/. The broader configuration/repair/export
exercise above is not implemented here. No layout/palette is selected or product
coverage added. Stop for owner feedback before another increment.

Owner follow-up accepted the overall sample direction but requested less color in
both blocks and text, especially dark mode. The sample now uses neutral reading
text and selection, with muted status edges only. Sample-local light/dark tokens
replace its dependency on the earlier palettes. Targeted isolated-browser visual
and sampled contrast checks passed; README.md records limits. Final styling still
awaits owner feedback. Navigation, product source and coverage are unchanged.

Owner then requested restrained supporting icons. Added small neutral licensed
Heroicons alongside back/search/evidence/theme labels. Targeted isolated-browser
checks passed seven views, icon-area clicks, bilingual themes and narrow width;
all assets loaded locally. See README.md and ignored artifacts/flow-icons-20261023/.
No production behavior or endpoint scope changed.
Owner's next annotation removed the redundant evidence-button icon; remaining
icons must add recognition/direction. Static checks only for this small removal.
Owner then welcomed an alternative to ambiguous full-cell status rules. Compact
status labels now unify list/detail/event observations, retaining neutral text and
independent gray selection. Targeted browser checks passed; see README.md and
ignored artifacts/flow-status-labels-20261023/. No product behavior changed.
The owner rejected boxed status labels in favor of the preceding technical-article
table style. CSS/JS were restored exactly to `852ef59`; static checks passed.
Keep the experiment as historical evidence, not the current design target.
Owner next requested stronger table-header hierarchy and refinement of the rule.
Matched header/name font size, strengthened headers and shortened status rules
to 10px beside text. Targeted browser checks passed; see the sample README.
Owner found 10px letter-like; lengthened the mark to 24px. Six light/dark
list/detail/event checks passed with space remaining around the mark.
