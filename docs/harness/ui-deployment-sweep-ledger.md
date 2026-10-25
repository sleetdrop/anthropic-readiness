# Local UI and deployment verification sweep

Owner authorized controlling the browser to inspect the current application and
fix related UI/deployment defects together (2026-10-25). Presentation follows root
design.md; this is supporting work, not additional endpoint coverage.

User-visible outcomes: consistent usable deployed screens; retained investigation
and form context; a reliable way to load updated UI instead of silently combining
new page fragments with already-loaded old assets.

Sequential scope:
1. Capture installed read-only screens and disposable full-flow synthetic screens
   in both languages/themes and representative desktop/narrow widths.
2. Record reproducible problems with screenshots/rendered checks before fixes.
3. Correct related presentation/update-loading defects without redesigning scope.
4. Verify meaningful regressions, obtain one independent final review, commit
   locally, install the verified image and preserve historical run files.

No real endpoint calls, registry publishing, remote writes or account setup.
Any start/cancel/import/export exercise uses disposable synthetic fixtures. Existing
trial history is read-only except installing the new app on its same data volume.
Evidence and screenshots stay ignored under artifacts/ui-sweep-20261025/.

## Status

Initial repository was clean at 7a2886b. Cached Linux/Python 3.12 environment resumed;
uv sync --locked --offline passed (50 resolved / 48 checked). Capture and repair
are pending. A running development container is not UI acceptance.

## Captured findings and fixes

- Captured 32 installed read-only screens across new/history/import and five run
  views, desktop/narrow and Chinese-light/English-dark. All routes returned 200 and
  had no document-width overflow; screenshot inspection still found a severe
  narrow issue layout failure. Overflow alone was insufficient acceptance.
- The inherited 720px rule made `.issue-list` a horizontal flex container, squeezing
  heading, explanation, toolbar and table into separate columns. Set the accepted
  issue region explicitly to block; preserve horizontal scrolling inside tables.
  Narrow production actions now share one row instead of retaining an obsolete
  header width constraint.
- Other Web tables retained the same outer-zero padding and muted/450 heading
  rules previously repaired only for issue tables. Unified ordinary table insets
  and heading hierarchy while retaining the event table's denser local treatment.
  Standalone report assets are unchanged.
- Added a packaged UI-resource identity computed once per app instance, CSS
  content-version URLs and a health response header. Health JSON and existing API
  contracts remain unchanged. The identity reads only packaged UI/templates,
  locales and shared theme resources, never target configuration or stored runs.
- Visible pages check identity on focus/visibility and every 30 seconds. A valid
  changed identity reveals a neutral manual-refresh notice; it does not reload,
  clear inputs or move focus automatically. Network failure/unknown health identity
  does not establish a deployment change. Browser page-cache return resumes checks.
- Both workbench and other-page presentation updates reject unverifiable or
  mismatched incoming HTML identity before patching, retaining the old document
  until deliberate reload. A legacy service without health identity is unknown;
  attempting to navigate to its identity-less HTML is still blocked safely.

## Evidence and review

- Initial RED: UI-identity backend test failed missing meta; browser tests reproduced
  narrow squeezing and missing update notice. Secondary RED reproduced ordinary
  table insets and page-cache resume failures. All failures are retained.
- First focused backend GREEN: 17 tests passed. First focused browser GREEN:
  15 executions passed, including disposable import, controlled retest/comparison
  and evidence search/return. Visual GREEN: ten executions passed, including two
  accessibility/reflow checks and paired-language/theme narrow regions.
- The Browser plugin control became available again using its current installed
  runtime. Connected to the owner's existing IAB tab; verified current installed
  issue/header insets, navigated problem -> streaming evidence -> close, then new,
  history and import screens, saving current screenshots. No daily Chrome was used.
  Read-only historical captures remain ignored, never committed or published.
- One independent read-only review found P2: a missing incoming HTML identity was
  treated like unknown health identity. A new RED reproduced legacy-meta omission;
  separated strict HTML acceptance from conservative health comparison. Six focused
  GREEN executions cover this fix, valid mismatch, unsaved input/manual reload,
  page cache, unknown health identity and HTTP 503. Reviewer confirmed the fix
  statically; no duplicated full review/test run was requested.
- Final frozen full verification and installed-image acceptance are pending.


## Complete frozen run and final bounded corrections

The first full graph retained source unchanged and observed 496 unit/harness,
30 frontend unit, 103 browser, 281 integration and 84 acceptance tests passing.
Its aggregate result is FAILED: two of five packaging tests rejected a pre-existing
Finder resources/.DS_Store which Hatch intentionally omits. The three other
packaging tests passed. That failed graph and its source identity remain retained;
this is not relabeled as a green full check.

The final narrowly scoped gate correction excludes only the exact .DS_Store file
name from wheel inventory and source identity. New failing controls first proved
the problem; they also require other hidden resources, byte equality and genuine
resource changes to remain checked. No source file, failed attempt or protocol
expectation was deleted. Independent static follow-up confirmed this boundary.

Actual IAB inspection additionally showed a spurious vertical tab scrollbar
(scrollHeight 47 / clientHeight 46). A standalone RED first exposed overflow-y:auto;
then reset the inherited negative margin, prohibit vertical tab scrolling and keep
keyboard focus outlined inside the tab. Horizontal tab access remains. The first
standalone harness attempt had an incorrect working directory and is retained;
the corrected harness reached the actual failing CSS assertion. The regression is
now in the checked-in browser suite. Reviewer confirmed the bounded CSS change.

Final fast graph, all five package checks and 27 focused browser executions cover
these final CSS/gate refinements. All passed. The earlier
full graph applies to its recorded source revision; final verification does not
claim another complete full graph. Endpoint engine/validation code is unchanged.


## Final source checks

Final fast status PASSED with source_unchanged=true, fingerprint
b71bad04d41899c80576d53af98a603255e78be37facd2a65f2ccff29a1bbfc8.
All eight fast gates passed (498 unit/harness and 30 frontend unit checks).
All five package acceptance tests then passed, and 27 final browser executions
passed after the bounded final refinements. The full graph's earlier packaging
failure is retained separately; current-source acceptance is the combination of
these final checks and applicable unchanged Web-backend checks from that graph,
not a claimed second full-graph pass. No tests or protocol assertions were weakened.
Cached final wheel construction passed entirely offline. Installation follows.


## Installed acceptance

Feature `3bfc375` is installed in the existing readiness-trial service on 8765,
using its original persistent volume. All 165 application package files match
source, all four historical runs and 154 run-file hashes remain identical, and
health is OK. Packaged UI identity agrees with the health header and HTML meta;
all three stylesheets carry their resource hashes. Cached trial build only: clean
networked Docker/remote CI/publication was not performed.

Saved and inspected 48 fresh installed screenshots across eight routes and six
locale/theme/width combinations, all 200 with no document-width overflow. Direct
IAB verification at 390px confirmed block stacking, heading width 351px, correct
narrow insets, no vertical tab scroller, English/dark rendering and no false update
notice during language/theme changes. The default viewport and Chinese/light
preferences were restored. No browser console errors were reported in the final
IAB check. A current screenshot/step report is ignored at AUDIT.md in the evidence
folder. The original full failed graph, RED attempts and subsequent GREEN checks
remain available. Historical target content appears only in ignored local evidence.

All scoped steps are complete. No endpoint scenarios were added, no real model
calls were made, and no untested client feature was marked supported. The five
formal scenarios and remaining core coverage/client gaps still apply.
