# Evidence annotation interaction study

## Purpose and authorized boundary

User-visible outcome: assess whether a reader can find the relevant JSON object,
value or SSE event and understand a diagnostic note without confusing it with
captured data. The owner approved proceeding with a small interactive sample.
The preceding clarification reserves annotations for evidence inspection;
Activity/run records only need inspectable interaction details in a separate
increment. No production migration is included in this study.

Initial checkout: clean `d2369f8` on `codex/tool-result-round-trip`.
Source: `docs/design/console-study/evidence-annotation.{html,css,js}`, extending
root design.md and the existing flow sample's local fonts, icons and color tokens.
The new interactions await owner review. Root design.md remains unchanged.

## Current revision: gutter marker and popover

After trying `a057d2c`, the owner requested keeping JSON layout intact and opening
details from a small indicator instead of inserting explanatory rows. The owner
approved this bounded revision. It remains a standalone sample awaiting visual
feedback, not a production migration or root design.md baseline change.

DONE sequentially: observe old behavior; add failing marker test; replace inserted
notes with a fixed native non-modal popover; check layout and source fidelity;
inspect paired images and direct IAB; complete one independent static review;
correct its actionable finding and verify the final sample; update handoff and
commit locally. Fixed-width gutter space remains present even with markers hidden.
Fault/context use unmodified Heroicons 2.2.0 exclamation/information circle assets.

The panel uses spare desktop space after visible JSON content when possible;
otherwise it fits above/below the target, or at the narrow screen's bottom edge
when that leaves the target visible. It never inserts data/annotation rows.
Clicking the marker again, clicking outside, Close and Escape dismiss it;
Close/Escape restore marker focus. Navigation, external scroll and resize dismiss
temporary details without resetting JSON folding/reading state.

Final Linux Dev Container browser check passed 36 combinations of three widths
(1280/737/390px), two themes, two languages and three synthetic scenarios. Assertions
compare every JSON text row's content/position/size before opening, while open and
after dismissal; popovers must fit the viewport and avoid the target text. Checked
repeated marker toggling, keyboard activation/focus, outside dismissal, parent and
exact-node locations, related SSE neutrality, retained folding, raw clipboard byte
equality, seven-record download and icon color inheritance. No page errors or
API/model requests occurred. Direct IAB additionally inspected 1280x720 light and
390x844 dark, with the same final appearance left at normal size/Chinese/light.

Retained REDs cover the initially absent marker, desktop panel obscuring nearby
JSON despite spare space, and repeated marker click reopening after native light
dismiss. An independent static review found muted inherited icon color and
suggested the repeated-click check; the latter was reproduced before correction.
Icons now inherit semantic parent color; explicit native invoker association plus
controlled activation fixes repeated clicking. All final targeted checks passed.
Syntax, explicit formatting and repository documentation checks passed; no full
product graph was rerun. Source data, endpoint cases, reports and installed 8765
remain unchanged. Activity interaction details are still a separate pending task.

Detailed evidence: ignored `artifacts/evidence-bubble-20261025/`; original inline
evidence remains below. [Visual QA](../design/console-study/design-qa.md) records
the intentionally changed presentation and paired screenshot comparison.

## Original sequential ledger, a057d2c (historical)

1. DONE: read intent, handoff and presentation baseline; inspect actual installed
   issue view in the in-app browser; establish synthetic-only scope.
2. DONE: create failing browser contract check before sample implementation.
   Initial RED was the expected HTTP 404 for the absent sample, not a browser or
   dependency failure. Retained under ignored artifacts.
3. DONE: implement three synthetic cases: absent stop_sequence at root parent,
   string output_tokens at its JSON Pointer and repeated message_start at event
   #5 with event #0 as neutral related context. Data text stays neutral; current
   location is gray-blue and a short rose mark identifies the example fault.
4. DONE: support folding/ancestor expansion, expected/observed disclosure,
   annotation visibility, original source/copy/download and issue/evidence return.
   Copy/download read fixed source strings, never the annotated DOM. SSE download
   is seven JSONL capture records, not an unmodified wire stream.
5. DONE: bounded automated and direct in-app browser verification, followed by
   one independent static read-only review. Its keyboard-focus finding was
   reproduced RED and corrected; event-list focus and scrolling are retained.
6. DONE: document the sample and scope, check syntax/format/documentation and
   make a local delivery commit. No remote write or installed-product update.

## Original inline-study verification (historical)

Environment: checked-in cached Linux/Python 3.12 Dev Container, offline uv runner
and its existing Chromium/Playwright. No new dependencies were installed.
Static preview runs read-only on host loopback port 8768 with only the synthetic
study directory mounted. Product port 8765 and its data volume were not replaced.

Final targeted browser check passed: parent-only missing-field target, exact
wrong-type target, collapsed-ancestor Locate behavior, show/hide notes, retained
disclosure/folding on return, related-event context, keyboard event focus, source
copy byte equality and a complete seven-record JSONL download. Eighteen screenshot
samples cover three scenarios at 1280/737/390px in light/dark; English reflow was
also checked at each combination. No page errors or model/API requests observed.
The screenshot loop uses full navigation to avoid falsely treating hash-only
navigation as a fresh language/theme initialization.

Direct IAB inspection covered desktop missing-field/light, repeated SSE/dark
and 390px repeated SSE/dark. Final return state is Chinese/light at normal
viewport. This is a bounded visual/interaction check, not full accessibility,
screen-reader or cross-browser acceptance. Source syntax, explicit Prettier check
and repository documentation check passed. Full product checks were not repeated
for this standalone study.

Detailed scripts, REDs, GREENs, download and screenshots remain ignored under
`artifacts/evidence-annotation-20261025/`. Independent review was static, not a
second browser pass. Its sole actionable finding was verified by the new failing
keyboard test and the final GREEN. No duplicate whole-stage review ran.

## Delivery and gaps

This is supporting-only prototype work: zero endpoint scenarios added or changed,
zero new detectable endpoint faults, zero live calls, no report/CLI/engine changes
and no remote CI or publication. Formal coverage remains five cases.

Use the separate preview and its footer scenario selector to try localization,
folding, source fidelity and return behavior. After owner feedback, production
integration must use validated evidence identities and conservative location
fallbacks; it must not guess a JSON node/event when evidence cannot support one.
Large/truncated/invalid captures, multiple findings on one node, production
deep links and complete-capture search remain outside this sample. Activity's
interaction-details entry is still pending and must not gain issue annotations.
