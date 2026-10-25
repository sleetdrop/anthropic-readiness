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

## Sequential ledger

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

## Observed verification

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
