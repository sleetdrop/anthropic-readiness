# Evidence token-marker refinement QA

final result: passed

## Comparison truth and scope

Source: `e85ddea` synthetic sample with gutter marker, captured at
`artifacts/evidence-bubble-20261025/iab-final-light.png`.
Owner-directed change: place the indicator beside the relevant key/value without
covering characters, consuming text space or changing JSON indentation. Missing
fields must still locate their real parent. This is a scoped prototype refinement;
the owner subsequently accepted `446d695` on 2026-10-25. Production binding remains
the next bounded implementation task.

Implementation: `evidence-annotation.html?rev=8`, missing-field, Chinese/light,
popover open. Capture: `artifacts/evidence-token-marker-20261025/iab-final-light.png`.
Both captures are 1280x720 pixels at 1280x720 CSS pixels, density 1. Full pair:
`compare-final.png` in the latter artifact directory. Focused pair:
`compare-detail.png`, using equal 650x300 regions at x24/y245. Both pairs were
opened and compared; no density normalization was needed. The comparison restores
the original line-number/fold/text grid deliberately, rather than matching the
superseded extra gutter. No remaining actionable P0/P1/P2 mismatch was observed.

## Fidelity surfaces

- Typography: system/CJK UI and monospace JSON families, compact weights/sizes and
  neutral token text retained. No new syntax coloring or font dependency.
- Spacing/layout: absolute marker beside the actual value (`"8"`,
  `"message_start"`) or parent `{`. It clears the trailing comma/collapsed suffix;
  JSON characters and row positions do not move when markers/popovers toggle.
  Constant end padding makes room in the reader's own horizontal scroll area.
  Popover geometry and spare-space/target-avoidance behavior are retained.
- Colors: accepted gray-blue location, rose fault, neutral related context and
  paired surfaces retained. No new semantic colors or inferred pass state.
- Assets: existing unmodified local Heroicons 2.2.0 outline glyphs and MIT license,
  now in an absolute token-adjacent button. No added or approximated imagery.
- Copy/content: same expected/observed facts; diagnostic notes remain separate
  from JSON. Source copy/download and missing-parent/SSE-context meaning unchanged.

## Verification and history

The new token-location check was observed RED against the old gutter version.
After implementation, targeted Linux Dev Container checks passed all 36
width/theme/language/scenario combinations. They assert near-token positioning,
no character overlap, viewport fit, target avoidance, identical JSON geometry
before/during/after popovers and when marker visibility changes. Prior marker
repeat-click, outside/Close/Escape, keyboard focus, folding/Locate, source-copy
byte equality, full download and related-context checks remain green. No page
errors or API/model requests. One independent static review found no clear
regression; it did not repeat the browser run.

Direct IAB additionally inspected the value marker at the owner's current desktop
width, the comparable 1280x720 light state and 390x844 dark. Narrow capture:
`artifacts/evidence-token-marker-20261025/iab-final-narrow-dark.png`.
Normal viewport and Chinese/light were restored for the owner's trial, which
subsequently accepted this version.

Earlier gutter/inline findings and their corrections remain historical in the
study ledger and ignored artifact directories. Full accessibility, screen-reader,
cross-browser, very long/invalid capture and multiple-finding acceptance are not
claimed. Product/Activity integration is unchanged; root design.md now records
the owner's acceptance separately from this verification report.
