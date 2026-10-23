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
- Initial implementation and verification were pending; container startup alone
  was not acceptance. Final outcomes follow below.

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
- Final frozen full graph, installation and local delivery are recorded below.

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

## Local delivery and remaining limits

All five sequential delivery steps are complete. Feature commit `315f23f` is
installed in the existing `readiness-trial` service on port 8765, using the same
persistent volume. New image manifest:
`sha256:9ffc1b65a5996e4cbd535faad6712628001429ceec2744da91b10f4bd2769776`.
The prior image remains tagged `anthropic-readiness-web:before-console-baseline`.
The local trial recipe reuses cached dependencies; image-context identity remains
unknown, so it is not a release/publishing proof.

Post-install read-only acceptance passed: health OK, workbench HTML version 2.0,
actual issue table present, all four run IDs visible, all 154 historical run-file
hashes unchanged, and every one of 163 installed package files identical to source.
Detailed snapshots/hashes remain ignored in `artifacts/console-baseline/`; no real
targets, credentials or captured source records were added to the repository.
Requested the existing run's Issues page in Codex's built-in browser; the app
returned queued, so that request alone is not evidence of human visual approval.
The static sample on 8767 is preserved. No user Chrome automation was used.

This increment adds zero endpoint scenarios and makes no new protocol/client
support claim. The catalog remains five formal cases. Streaming tool loops,
broader multi-turn/request-error coverage and real SDK/Claude Code tests remain
unfinished core goals. No live endpoint calls or remote writes occurred. Reports
retain their existing independently exported presentation. Owner hands-on feedback
is next; evidence display remains bounded and full files remain downloadable.


## Owner-triggered presentation conformance correction

Owner questioned the gray progress bar and fidelity of the installed page. Actual
read-only capture confirmed the opened run was completed: neutral progress agrees
with the accepted baseline; running remains blue. The comparison also found real
cascade defects: issue headers rendered weight 450 / muted instead of 600 / primary;
first/last cell padding rendered zero; native progress retained old rounded corners.
The 850px product breakpoint also moved progress below identity earlier than the
sample's 650px breakpoint. Fixed those selectors and progress state styling;
placed production actions alongside view tabs to retain the reference header layout.
Updated root design.md with this bounded refinement; no palette redesign.

User explicitly approved isolated Dev Container browser capture because the Browser
runtime did not expose `iab` (discovery only offered the owner's daily Chrome).
No daily Chrome control was used. Fresh installed light/dark captures preceded
implementation; paired synthetic source captures exercised real persisted 2/4-case,
3/4-request execution, followed by actual terminal transition, in both languages
and themes. No production lifecycle, counters or findings were fabricated.

Evidence is ignored under `artifacts/presentation-audit-20261023/`. New rendered-
style regression reproduced the 450-weight heading before the fix (RED). Initial
fast check caught nullable test geometry; retained that failure and corrected the
checks. Final fast graph passed all eight gates with source unchanged. Ten focused
browser executions passed, then 18 executions passed including nonzero running
progress, paired geometry (390/640/1280/1440), long target names, 200% reflow,
contrast, export invalidation and existing investigation/evidence paths. Four new
presentation cases overlap the two runs; these are not 28 unique cases or added
endpoint coverage. Independent static follow-up found no concrete two-file
regression. The previous full source graph remains evidence for its own revision;
a full graph/remote CI/live endpoint run was not repeated for this bounded fix.
Installation acceptance follows below.
