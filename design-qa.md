# W2 operational workbench design QA

Historical W2 verification record. The current owner-approved presentation
baseline is [design.md](design.md); it supersedes conflicting visual compositions
here without erasing these observed checks or claiming a completed UI migration.

Scope: Task 12 operational Web UI. Independent presentation-3 documents are a
separate Task 13 deliverable and are not accepted by this record. This is author
visual/interaction QA; the independent whole-W2 review remains Task 15.

## Source visual truth

The owner-approved pair and companion compositions are recorded in
`docs/reviews/2026-10-18-diagnostic-workbench-visual-design.md`:

- Light: `artifacts/w2/visual-20261018/exec-1775e6e7-1d1e-4f9f-a2c3-28ca19665826.png`.
- Dark: `artifacts/w2/visual-20261018/exec-771e5e11-ce7f-493f-bae8-d81bbbc96698.png`.
- Issues: `artifacts/w2/visual-20261018/exec-4767842e-fafb-40a7-bcc3-39a79003f8a4.png`.
- Compare: `artifacts/w2/visual-20261018/exec-e4d40757-6653-4df6-9f78-122fbcf3b047.png`.

The generated references are 1586x992 pixels and declare no authoritative CSS
viewport or density. The written 1280x800/1440x900 acceptance and neutral lifecycle
rules override incidental generated geometry, color and sample numbers.

## Rendered evidence and normalization

Latest full browser evidence is under `artifacts/w2/task12/browser-all7/`:

- `browser-artifacts/workbench-approved-active--e50e1--and-three-request-evidence/active-light.png`
  and `active-dark.png`: 1280x800 CSS pixels, deviceScaleFactor 1.24, approximately
  1587x992 output pixels. This normalizes the approved image's aspect/density to
  the written viewport; the one-pixel raster-width difference is not a defect.
- `browser-artifacts/workbench-paired-inspector-6b5a8--verified-field-composition/inspector-light.png`
  and `inspector-dark.png`: same CSS viewport/density, full document capture.
  `fields-light.png` and `fields-dark.png` are focused captures of verified fields.
- `browser-artifacts/diagnostics-comparison-kee-acd73-gressions-and-gaps-together/`:
  `mixed-comparison-viewport.png` and `mixed-counts.png` show the primary hierarchy
  and count semantics; `mixed-comparison-light.png`/`mixed-comparison-dark.png`
  preserve the complete page. Comparison uses 1280x900 CSS pixels at density 1;
  it is a structural comparison, not a pixel-perfect match to the generated art.
- The same browser output contains 390px and 640px reflow, 1440x900, long-name,
  empty, interrupted, evidence-dialog and no-script captures. The 200-percent
  equivalent test uses 640x400 CSS pixels at density 2, matching a 1280x800
  physical surface; native browser-chrome zoom controls were not exercised.

References and implementation captures were opened together in the same
comparison inputs, including paired appearances and focused field comparisons.
The active fixture has an actual owned worker, two committed cases, three started
requests and a third request waiting for headers. Its elapsed time and alias are
actual synthetic records, not copied design numbers. The mixed comparison comes
from two complete four-case executions with identical conditions and changed
synthetic peer responses. Group counts are checks, not assumed issue families.

The local browser preview uses only synthetic records on port 8766; the prior
8765 service is preserved. Manual browser checks covered language/theme changes,
issue navigation and the rendered field inspector. Captured browser error/warning
logs were empty. Automated checks also cover execution, stop/reconnect, import,
original-scope retest, comparison, export review and evidence access.

## Findings and comparison history

All actionable P0/P1/P2 findings below are closed.

| Finding | Evidence and impact | Fix and post-fix observation |
| --- | --- | --- |
| P2: overview overflow | Initial 1280x800 captures measured 819px document height; a wrapping count header and later an in-progress partial notice pushed the footer down. | Keep the count header on one line, tighten spacing, and show the partial-record notice after termination. `visual-green2` passed nine paired/active checks; full `browser-all7` passed desktop height and unclipped-action checks. |
| P2: weak operational type hierarchy | The first normalized comparison showed small group/attention text relative to the approved pair. | Raise group headings to 22px and group/attention text to 15px, with tighter table padding. Reopened both source/implementation pairs; data remained readable and the active overview fit the written viewport. |
| P2: repeated issue blocks recreated a report | The first four-case inspector stacked every field variant and showed protocol identifiers in the list. | Show one explicitly selected case, retain four member controls and all evidence, and move raw identifiers/paths into technical disclosure. `inspector-green1` and full `browser-all7` retain scope, focus, text selection, native disclosure and source hashes. |
| P2: raw comparison buried the changes | The initial mixed view displayed 52 raw pair rows before the meaningful changes could be scanned. | Add a pure five-group observation matrix for the real fixture, retaining all 52 original pairs in a native disclosure. `group-browser-green1` passed original-scope/mixed checks; full `browser-all7` also verified keyboard expansion, localization retention and narrow layout. |
| P2: duplicate unnamed landmarks | Axe reported duplicate complementary landmarks. | Name the application rail; both viewport accessibility checks pass across configuration, history, import, overview, issues and cases. |
| P2: one-pixel vertical tab scrolling | Manual narrow-browser measurement found 49px content in a 48px horizontal tab rail. | Remove the negative narrow-tab bottom margin. Narrow automated layouts retain reachable controls and no document-width overflow. Manual post-fix desktop measurement had visible vertical overflow and fractional 49.5px geometry (integer scrollHeight/clientHeight round differently); it is not evidence of a remaining vertical scrollbar. |
| P2: evidence failure hidden behind modal | A failed evidence request left the dialog loading while an error appeared behind it. | Render failure inside the dialog, bound streamed display bytes, cancel closed reads and recover a read session once. Both faults were observed RED/GREEN, with no repeated model request. |

A separate inspector geometry failure was a capture calibration issue: the
focused element screenshot scrolled the document before the next measurement.
Both measurements now use the same scroll position, keeping the original one-pixel
tolerance. It was not a theme-token layout difference.

## Required fidelity surfaces

- Fonts and typography: system UI/Noto CJK and monospace fallbacks follow the
  checked shared tokens. Header hierarchy, line height, weight and wrapping were
  inspected in both languages. OS glyph rendering is intentionally not a raster
  golden; no external font dependency is introduced. Long aliases retain titles
  and primary actions, and raw field data keeps its original spelling.
- Spacing and layout rhythm: the rail/header/tabs/metrics/groups/attention
  hierarchy follows the accepted pair. App views share one operational header.
  Desktop overview fits one screen; secondary inspectors and raw disclosures may
  scroll. Theme changes preserve header, navigation, metrics and inspector boxes
  within one CSS pixel. Narrow tables scroll within labeled keyboard regions.
- Colors and tokens: flat paired surfaces replace generated shading. Lifecycle
  completion is neutral; successful checks/recoveries alone carry PASS semantics.
  Native progress is completion, not a compatibility score. Measured text/code
  combinations meet 4.5:1 and meaningful controls/focus/progress/selection meet 3:1
  in both appearances. System appearance and explicit overrides are exercised.
- Image quality and asset fidelity: this is a data UI with no raster illustration.
  The packaged, unmodified Heroicons outline assets are consistently sized and
  sharp. Native progress and tables encode actual counts. No generated screenshot,
  custom SVG artwork, emoji or decorative substitute is shipped as UI content.
- Copy and content: bilingual copy, accessible labels and dynamic execution
  previews update without changing source data or clearing credentials. Empty,
  interrupted, unknown-lineage and unavailable-evidence states remain distinct.
  Comparison explicitly names check units, overlapping case scope and missing
  verification. A single sample never asserts causality, stability or untested
  Claude Code compatibility.

## Implementation checklist

- [x] Compare the source pair and actual active overview together.
- [x] Compare issue and comparison hierarchy with their companion sources.
- [x] Inspect focused field captures and both appearance variants.
- [x] Close actionable layout, hierarchy, accessibility and evidence-state issues.
- [x] Verify global controls, keyboard navigation and context-preserving updates.
- [x] Retain all raw facts and pairing members behind accessible disclosures.
- [x] Finish the post-lint fast gate and Task 12 completion record (443 Python, 20 Node, 61 browser tests).
- [ ] Perform separate document QA in Task 13 and whole-stage acceptance/review.

Residual scope: this record does not claim a real endpoint test, an image build,
remote CI, native zoom-control integration or independent review. There is no
remaining actionable visual P0/P1/P2 in the inspected operational surfaces.

final result: passed

## W2 independent document QA — Task 13

Source: the approved editorial companion
`artifacts/w2/visual-20261018/exec-f7a2a61a-532a-4816-968d-59f18b89f94f.png`.
It was opened alongside the actual paired document captures. The document keeps
its own contents rail, serif title/section hierarchy, numbered matrix/findings,
rule citations and evidence index. It includes all four recorded dimensions rather
than omitting execution conditions to match the concept's sample. Comparison is
optional and follows findings per the written specification. Actual sample counts
replace concept numbers; no illustration or synthetic chart image is shipped.

Actual paired comparison captures are in
`artifacts/w2/task13/browser-all2/browser-artifacts/diagnostics-comparison-kee-acd73-gressions-and-gaps-together/`:
`report-light-viewport.png`, `report-dark-viewport.png`, full-page equivalents and
`mixed-assessment.html`. These come from actual two-run synthetic requests and
exported files, with recovery/persistent/new-failure/gap groups retained together.
The later footer wrapping changes no first-viewport geometry. Final narrow and
print evidence is under `artifacts/w2/task13/browser-doc-final/captures/`.

Fonts use the shared system/CJK and document-serif stacks; there is no remote
font request. Both themes use identical type/spacing with the shared flat semantic
tokens. Main matrix states are localized reader labels; exact machine states
remain in the original-check appendix and embedded factual dataset. Identical
field excerpts share a block, retaining every affected case and original evidence
member. Native impact bars encode distinct affected cases, not a compatibility
score, and have captions and equivalent tables. Overlapping findings are never
summed as unique cases. Timing-only figures are omitted because no current finding
is explained by their boundaries; actual summary/attempt durations remain data.

Closed findings:

- Final-asset CSP hashes now include template whitespace/semicolon bytes; 12 initial
  direct-file failures were observed before correction. The restrictive policy
  remains, with no network/telemetry dependency.
- Theme option text and region accessible names now follow in-file language changes;
  a language-switch failure was observed before correction. Initial language remains
  readable without scripts; unavailable controls are hidden.
- A 390px document-width failure was measured as MAIN 479px / FOOTER 457px against
  a 390px viewport and 346px content area. Long footer digests now wrap. All four
  locale/appearance narrow cases pass without document overflow; matrix tables
  retain named, keyboard-scrollable regions.
- Main tables no longer repeat raw state identifiers such as not_evaluated. These
  remain available in technical data; the readability check observed RED first.
- Markdown matrices have contiguous CommonMark rows. Version-3 JSON downloads use
  document-view.json while the old export path retains report-view.json.
- Privacy omission no longer performs global replacement of credential-reference
  words that can equal verdict/model strings. Both collisions observed RED/GREEN.
  Routing/configuration omission is distinct from changing source evidence.

Observed author QA: browser-all1 passed 73; browser-all2 passed 73 with four new
narrow failures; after the measured fix, browser-doc-final passed 16. These include
both locales, three initial appearances, scripts on/off, zero attempted HTTP reads,
unchanged embedded data, selected-language light printing, code/status/control/
progress contrast, and narrow keyboard table navigation. Fast-4 passed all eight
children (453 Python and 20 Node); focused-final passed 32. A separate six-request
synthetic CLI comparison confirms identical request bodies/API headers and verdicts
across presentation choices; it is now a formal acceptance test.

Manual browser verification of the refreshed 8766 synthetic service retained the
same selected issue/case and produced a version-3 export through the actual dialog.
The preview showed its en/dark choice, document-view.json and explicit omissions;
ZIP/HTML/Markdown/JSON download links appeared. No model request was started.

Task 13 post-commit task-done passed all 77 browser tests in 3.8 minutes on unchanged source, with prerequisite/cleanup checks passed. Whole-W2 image,
remote CI, real endpoint and independent review acceptance are outside this record.

Task 13 document author QA final result: passed. Independent whole-W2 review remains pending.
