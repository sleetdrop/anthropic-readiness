# Approved console baseline implementation

Owner authorization: implement the accepted flow sample in the product in the
current conversation (2026-10-23). Root `design.md` governs presentation.

Scope: existing five formal cases; actual persisted progress; searchable issue
table; selected occurrence and verified evidence inspection; retained navigation,
retest and export. No live endpoint calls, new scenarios or report redesign.

Sequential delivery:

1. Record failing checks for list/detail/search and evidence navigation.
2. Connect checked projections to the approved layout and paired themes.
3. Implement bounded evidence reading and context-preserving navigation.
4. Run offline backend/frontend/browser checks and inspect paired screenshots.
5. Obtain one independent review, resolve findings, commit locally and make the
   verified build available for owner trial without replacing stored runs.

## Observations

- Existing development container resumed; cached `uv sync --locked --offline`
  passed (50 resolved packages, 48 checked). Source tree initially clean.
- Product service on 8765 and its persistent volume remain intact. Static sample
  on 8767 remains a reference, separate from the running product.
- Implementation and verification are pending; container startup is not acceptance.

## Implemented behavior and contract boundaries

- Steps 1-3 are implemented. Real persisted case/request progress stays visible;
  running and finished lifecycle styling is separate from protocol outcomes.
- Overview/issues use the approved compact table and filters. Search includes
  localized case names and observed fields. List/detail navigation preserves the
  query, selected occurrence and browser history/scroll context.
- Verified evidence opens in a bounded reader: contextual/all loaded event lists,
  search, parsed/source views, JSON pointer or existing-parent location, retained
  reading state and original-file download. Event records are explicitly labeled
  as parsed SSE records, not original network bytes. Display projections never
  validate or rescore the stored facts.
- Reading remains capped at 256 KiB and event rows at 100 per expansion. Search
  covers loaded events only. An event outside that prefix retains its referenced
  number and is explicitly unavailable; no substitute event or missing-field
  verdict is shown. Invalid JSON also cannot yield a missing-field statement.
- HTML workbench presentation is version 2.0. Machine WorkbenchView/fact/schema
  versions and existing endpoint verdicts remain unchanged. Export/report assets,
  CLI engine and formal five-case catalog are unchanged.
- Paired web-only tokens follow design.md. Intentional accessibility refinement:
  dark control outline #666666 -> #686868 (the former sampled below 3:1).
- Fixed a related existing input-history layout race exposed by retest tests:
  blur-time history controls could move the preview button before pointer-up.
  Reserving their visibility during input keeps clicks reliable, including
  blocked/quota-limited storage. No new stored credentials or configuration keys.

## Verification record

Evidence directory: ignored `artifacts/console-baseline/`.

- RED: backend list/detail/search assertion failed before implementation; new
  reading-projection tests failed on the missing module. These attempts remain.
- Intermediate runs exposed type/format issues, accessible toggle naming, missing
  page headings, theme-helper system-mode handling and the input-history race.
  Those failures remain as evidence; they are not acceptance.
- One attempted full graph collided with an independently running browser fixture
  on port 18765 and overlapped source edits. Its `source_unchanged=false` and red
  status are retained; neither is reported as a passing full graph.
- That graph separately observed 495 unit/harness tests, 84 acceptance tests and
  five installed-package tests passing. Integration was 279 passed / one failed:
  a pre-existing literal expected the old preview caption. Updated that assertion
  to require the same preview control and its current approved caption; no
  endpoint assertion or golden protocol expectation was changed.
- An initial 87-test browser pass was 84 passed / three failed (two missing H1
  semantics, one old heading locator). Added the semantic run heading and retained
  visible no-script heading coverage. All nine focused browser checks then passed,
  including 390/1280px accessibility, no-script pages and direct-file reports.
- Independent read-only review found one P2: an unloaded referenced event could
  silently become event zero. A new >256 KiB / event-299 browser test reproduced
  it (RED), then passed after explicit unavailable handling. The reviewer confirmed
  the correction and event-button focus restoration by static follow-up. The
  nine-test focused GREEN includes this regression.
- Inspected actual-product light evidence and paired dark issue-list screenshots;
  waited for the translated server projection before assessing the English view.
  Synthetic fixtures do not establish any additional endpoint compatibility.
- Final frozen full graph, installation and local delivery are pending below.

## Frozen source acceptance

The final `verified/check-result.json` reports `status=passed` and
`source_unchanged=true`, fingerprint
`27a45f671a9c8c19323ebc669be066478f78397e0b35f6a90ddbae27e60875ce`.
All 13 local gates passed: lock, format, Ruff, strict types, architecture, schemas,
unit, frontend static/browser, integration, acceptance, packaging and docs.
Observed executed counts: 495 unit/harness, 29 frontend unit, 88 browser,
280 integration, 84 acceptance and five installed-package tests; zero failures or
skips. These are offline controls, not endpoint coverage. The aggregate harness
still marks product stage readiness incomplete; unfinished core coverage remains.

A standard `--network=none` Docker build could not download an uncached dependency;
that failed attempt is retained. Building the wheel on the existing cached build
image then passed entirely offline. This is local trial preparation, not clean
networked Docker or remote-CI acceptance. Installed-container verification follows.
