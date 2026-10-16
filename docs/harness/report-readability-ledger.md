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
