# Report readability follow-up

Approved bounded design: explain the conclusion and task/protocol distinction first,
name the four cases in Chinese, group repeated findings, show expected/observed
fields with impact and next steps, and retain full technical records in an appendix.
The owner approved this design in the current chat after reviewing the real report.
This is a presentation follow-up to Stage A, not Stage B or a new endpoint assessment.

## Implementation and evidence

- A pure report_reading module builds names, dimension counts and grouped explanations.
  It is covered by the same dependency-direction/purity gates as the existing pure code.
- The reporting adapter extracts stop-field/model excerpts only from verified referenced
  body/event files, rechecks their read bytes, bounds extraction and falls back when
  evidence is missing, invalid, unparseable or unsuitable. It does not re-score cases.
- HTML places the reader overview before a collapsed technical appendix. Markdown
  preserves the same overview, findings, limitations and complete appendix. Captured
  strings remain escaped data; no script, font or stylesheet is loaded remotely.
- report-manifest.json records presentation_version 1.1. Result schema, API bundle,
  request templates, assertion semantics and original verdicts are unchanged.
- Initial reader regressions observed four failures before implementation. The synthetic
  transport setup was corrected to select count responses by request rather than a
  shared transport call index. Text assertions account for existing Markdown escaping;
  no golden verdict was relaxed. Empty-alias wording separately observed RED before fix.
- Five new acceptance tests cover ordering/task names, grouped verified field/alias
  explanations, exact result preservation, invalid/missing evidence and markup injection.
  Focused report tests passed 11/11 before final full verification.

## Private report and visual scope

The existing private assessment was re-rendered offline into a new private directory.
No new API request, proxy modification, alias allowlist or source-result rewrite occurred.
Its original report/result/evidence remain intact. Private identifiers, configuration,
response bytes and rendered examples remain outside Git/build contexts.

The in-app browser automation rejected file:// under its URL security policy; no
alternative browser surface, HTTP-serving workaround or raw browser command was used.
An existing WeasyPrint 70.0 static document renderer with all URL fetching disabled
was used instead. Desktop-width, 390px narrow layout values and all seven A4 pages
were inspected as static images. Narrow CSS values were supplied explicitly because
this static engine does not execute browser viewport queries. This is not browser
responsive/interaction or browser print acceptance; those checks remain unrun.

The prior Stage A image/visual evidence and frozen handoff manifest are historical
records for their original source baseline. Runtime images, remote CI and native
platform acceptance have not been repeated for this presentation follow-up.

## Final verification

All 11 full Linux/Python 3.12 gates passed; 171 tests (107 unit/harness, 22
integration, 41 acceptance, one installed-package), zero failures/errors/skips.
Check manifest: artifacts/checks/1792138109363923672/check-result.json. Source fingerprint: 8093e7e9d327a7364c5677d7b74803a5480a17a885cd661cb49013e1d73a2f2f.
The source remained unchanged during verification; the lock file remains unchanged.
An ignored machine index is saved at artifacts/report-readability/verification.json.

## Reference-informed refinement (presentation 1.2)

The owner requested comparison with reports from similar tools. See the
[reference study](../reviews/2026-10-16-report-reference-study.md) for primary
examples, observations and adaptations. The approved reading flow remains the same.

- Added a compact run masthead, contextual verdict, distinct finding/affected-case
  counts, visible evidence quality, report-local finding IDs and case/finding links.
- Partial expected/actual JSON excerpts link to retained responses or SSE events.
  Identity configuration is labeled separately from protocol format; original FAIL
  states remain visible. Different observed field values retain distinct excerpts.
- HTML uses restrained typography, semantic navigation, comparison columns and
  narrow-layout stacking. Markdown includes the same facts and evidence locations.
  No external asset, script or service is required.
- The presentation contract advances from 1.1 to 1.2; the manifest regression was
  intentionally updated for this version change. Result schema, API bundle, golden
  verdicts and original result bytes are unchanged.
- Initial summary/evidence tests observed two failures and one passing negative
  control before implementation (artifacts/report-research/red.log). Existing markup
  injection coverage caught a Markdown snippet regression; string brackets are now
  represented with JSON unicode escapes, retaining their decoded values.
- Content review identified different final stop values being combined under the
  same missing-field description. A new test failed before the grouping key included
  the actual/expected excerpts (distinct-values-red.log). Focused reports then passed
  15 tests (green-final.log); no assertion or recorded verdict was weakened.

Final Linux/Python 3.12 graph: all 11 gates passed, 175 tests (107 unit/harness,
22 integration, 45 acceptance, one installed-package), zero failures/errors/skips.
Check manifest: artifacts/checks/1792140545162506299/check-result.json.
Source fingerprint: 2dea2be76048d18ddd832edca142d46290af90a0de0b7c4b5384d50df130959b.
Source remained unchanged during verification; the lock hash remains unchanged.
The ignored index artifacts/report-research/verification.json records the checks.

Static document QA inspected desktop/narrow layouts, the narrow stacked comparisons
and all eight A4 pages. URL fetching was disabled. The local-field values and source
links were also inspected in the rendered output. Browser interaction/responsive
acceptance remains unrun; the public example tab timed out, and the previously
blocked local file was not accessed through another browser surface.

The private re-render preserved result.json and all 20 evidence files byte for byte;
the generated evidence status is verified with no errors.
The existing capture is re-rendered offline to a new private output directory; no
new endpoint request is made. Frozen Stage A and presentation 1.1 observations above
remain historical, rather than acceptance for this renderer.
