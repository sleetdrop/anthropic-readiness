# Console interaction study

Current status: none of the visual samples below has been selected. The owner
clarified that Wireshark/Charles are information-organization references, not
visual/layout targets. Start with the
[investigation-flow exercise](investigation-flow.md). It defines task-based detail
disclosure and navigation context before choosing another arrangement or style.

This directory contains standalone, dependency-free HTML/CSS/JavaScript design
samples. They are not part of the installed application, report renderer or
execution engine. The latest bounded navigation sample is [flow.html](flow.html).
The earlier [runner sample](runner.html) followed the report-like layout feedback.
The earlier [overview sample](index.html) remains available for comparison.

The [reference study](../../reviews/2026-10-23-engineering-console-reference-study.md)
explains the external mechanisms and independent visual direction. The existing
application and its preceding desktop walkthrough provided product structure.
The initial exercise used one representative layout. Following feedback on its
generic blue-gray appearance, that layout offered three palette alternatives and
the original as a reference. No sample is an approved visual/layout target.

## Current semantic color direction

Owner clarified that earlier feedback concerned palette quality/coordination,
not a grayscale-only restriction. This direction supersedes the earlier neutral-
text-only trial below, keeping its table hierarchy and interaction structure.
Neutral surfaces and reading text remain dominant; color is applied where its
meaning can be named.

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| Interaction/execution | `#416b7b` | `#93b6c5` | Running status/progress, active filters, focus and selection accents |
| Selection surface | `#eaf0f2` | `#29353b` | Selected occurrence/event and active payload controls |
| Observed deviation | `#984c57` | `#d1949e` | Short protocol-status text and its existing rule, not entire traces |
| Verified pass | `#397052` | `#9bbda9` | Reserved palette role; no new pass UI/result is fabricated in this sample |

Inconclusive/untested conditions remain neutral. Execution completion also uses
neutral heading/progress colors: finishing a run does not establish protocol or
client readiness. Long expected/observed explanations, event names and raw payloads
retain neutral reading colors even when their selected row has a deviation.

Ten targeted isolated-browser light/dark list/detail/evidence/state views passed:
minimum sampled text contrast 5.06:1, focus contrast at least 3:1, neutral completion
and inconclusive presentation, and retained filter/query/raw-tab context across
state changes. Bilingual narrow width was checked; screenshots were compared with
the preceding palette. No page/console/resource error or external request observed.
Evidence: ignored artifacts/flow-semantic-colors-20261023/. Earlier color trials
remain historical. No product/endpoint/complete accessibility acceptance is claimed.

## Current bounded navigation sample

Open http://127.0.0.1:8767/flow.html. This exercises issue -> affected occurrence
-> evidence -> return. Presentation uses sample-local neutral light/dark tokens;
no final style or whole-application layout is selected.

- Filter/search three fictional results: two protocol observations affecting
  three cases and one inconclusive condition. Similar observations do not prove
  a common cause. Inspect either missing-field occurrence's parent JSON without
  inserting an invented missing field into raw data.
- Follow duplicate start to event 58 of 206. View the original start and nearby
  context, expand all events or search the whole capture regardless of expansion.
  Switch among parsed fields, an original-format frame and synthetic full SSE.
- Return using buttons or browser history with filters, query, occurrence,
  evidence selection/tab and main/event-table positions retained. Language, theme
  and simulated run progress stay current. Direct evidence links have a parent
  path within the sample. Timeout evidence remains partial and inconclusive.

Final isolated Chromium checks on 2026-10-23 passed these paths, including searching
outside the initial context and narrow layouts. Main/event-table positions restored
at 20px/900px; a short-viewport list restored the actual click position at 286px.
Documents fit 1280x900 and 390x844 with internal detail scrolling. Screenshots were
visually inspected; no page/console errors or external requests were observed.
An initial check reproduced context-only search, then reverified whole-capture
search after correction. Other failed checks had two fixture assumptions corrected:
loading a hash link in a fresh document and measuring position at the actual click
after automation scrolls its target into view. All attempts remain in ignored
artifacts/investigation-flow-20261023/.

No personal Chrome profile, live endpoint, product/container/CI check or complete
accessibility/performance audit is involved. Repair, export and the full run/case
workspace are outside this sample. It adds zero formal endpoint cases.

### Neutral text/color follow-up

Owner accepted the overall direction but rejected the colored backgrounds and
text, especially in dark mode. All reading text, including status labels, event
names and numbers, now uses neutral tones. Selection uses gray fill and a neutral
edge; protocol status retains a small muted red edge only. Evidence explanations
and inconclusive conditions have no red/amber fill. This sample has its own theme
tokens; earlier palette alternatives are unchanged.

Isolated before/after captures covered light/dark lists, stream evidence and
partial timeout evidence. Sampled text contrast after the change was at least
5.44:1; neutral text, language/theme controls and 390px dark document bounds were
checked. No page/console error or external request was observed. Captures were
visually compared. Evidence: ignored artifacts/flow-tone-20261023/. This is bounded
prototype verification, not complete accessibility or product acceptance.

### Restrained action icons

Owner requested a few clear, visually subordinate icons. Back/search use 14px
neutral Heroicons outline glyphs alongside visible or accessible labels. The owner
later requested icon-only theme switching and EN/中 language captions; both retain
full localized accessible names and native hover titles. Decorative glyphs are
hidden from the accessibility tree, with no icons repeated through event rows. Four upstream SVGs
are local, with provenance and MIT license in icons/. No runtime dependency or
external icon service is introduced.

Owner then annotated the evidence button: its text already communicates the
action, so its icon was redundant. Removed that glyph and unused asset. Use
icons only where they add recognition or directional meaning, not to decorate
every button. This small removal was checked statically; the browser observations
below describe the preceding five-asset iteration.

Targeted isolated-browser checks passed seven rendered views across both themes,
Chinese/English labels, icon-area back clicks, search, evidence navigation and
390px width. All five SVGs loaded locally; no page/console/resource errors or
external requests were observed. Screenshots were inspected. Evidence is ignored
in artifacts/flow-icons-20261023/. Product source and endpoint coverage are unchanged.

### Compact status labels (rejected)

Owner questioned the full-cell colored rule and welcomed a more meaningful
visual treatment. An experiment replaced isolated status edges with compact non-interactive
labels in the list, issue heading and duplicate-event observation. Protocol
labels use a muted outline; inconclusive labels use a neutral dashed outline.
Both keep neutral text/fill; selection retains its independent gray row treatment.
This adds no severity or root-cause inference.

Isolated browser checks covered both themes, list/stream/timeout evidence,
issue/evidence return paths, bilingual controls and narrow width. Sampled text
contrast minimum was 5.44:1; labels have no button role/tab stop and no cell-height
colored rule remains. Screenshots were inspected. Evidence is ignored in
artifacts/flow-status-labels-20261023/. No product or full accessibility acceptance.

The owner rejected the boxed appearance and preferred the preceding table style,
like tables in technical articles. Restored CSS/JS exactly to `852ef59`, preserving
the neutral themes, limited supporting icons and text-only evidence buttons.
Syntax, whitespace and exact-restoration checks passed; no fresh browser run was
needed for this visual rollback. The experiment and its observations remain
historical evidence, not a selected design.

### Table hierarchy and short status marks

Owner questioned headers being weaker than primary first-column content, and
requested refinement of the original status line. Issue-table headers and primary
names share 12px; header weight is 600 and name weight 500, with secondary notes
still 11px/400. The status mark is a 24px vertical rule beside plain neutral text,
with consistent placement across list/detail/event observations. No boxes return.

Isolated-browser checks passed light/dark views, equal header/name sizing,
header weight, short-rule bounds, navigation, bilingual controls and narrow width.
Sampled text contrast minimum remains 5.44:1. The owner's 736x769 annotated viewport
and dark list were visually inspected. Evidence is ignored in
artifacts/flow-table-balance-20261023/. This changes the sample CSS only, plus
its cache version; no product or complete accessibility acceptance is claimed.

The initial 10px rule looked like a letter to the owner. Lengthened it to 24px;
six targeted light/dark list/detail/event captures at 736x769 confirmed that the
mark exceeds text height while retaining space within each row/title region.
Screenshots were inspected; no page/console errors. Evidence is ignored in
artifacts/flow-rule-height-20261023/.

### Toolbar and explicit running/finished presentation

Owner annotated three hierarchy problems: labels and inputs felt disjointed, run
status was hard to distinguish from final results, and the demo dropdown mixed
simulation controls into run information. The issue toolbar now uses inline
exclusive text-filter buttons with selection underlines, an integrated search
icon/input with a retained accessible label, and a separate result count. Event
search uses the same field pattern. Selected filters and search align at 32px.

The persistent run section now emphasizes Running/Run finished and a native case
progress bar, with finished-case counts separate from sent-request counts. List
headings distinguish issues found so far from run results. Finished status retains
deviation/inconclusive reminders and the client-not-tested qualification. It does
not mean that every case passed. Footer buttons clearly labeled Prototype state
replace the demo dropdown. Both states remain manually simulated, with no automatic
progress, actual execution or new network calls behind these controls.

A pre-change browser check reproduced the missing progress representation. Final
isolated-browser checks passed all eight language/theme/state combinations at
736x769; filter/search fields align with zero center difference. Exercised keyboard
filter/state controls, whole-stream search, retained raw tab/query/selection on
state changes and return/history navigation, empty-result recovery and 390px width.
Screenshots were inspected; no page/console/resource error or external request.
Evidence: ignored artifacts/flow-controls-20261023/, including the original failure.
These are synthetic prototype checks, not product or full accessibility acceptance.

The header simplification passed four language/theme keyboard-switch combinations
at 737x694, retaining event search/raw-tab/run context; 390px width was checked.
Screenshots were inspected after local mask assets settled, retaining earlier
captures. Evidence: ignored artifacts/flow-header-controls-20261023/. This adds no
endpoint coverage or product behavior.

## Earlier runner sample (unselected)

Open http://127.0.0.1:8767/runner.html. The working structure follows the selected
case and its captured exchanges: compact run controls, a grouped case navigator,
an evidence workspace, an adjacent check inspector and a collapsible run log.
Run state/accounting remain in a fixed status bar. Panes scroll independently;
there is no large title, narrative summary or metric-card row in this sample.
References: [Playwright Trace Viewer](https://playwright.dev/docs/trace-viewer)
for action/evidence linkage and
[Postman Collection Runner](https://learning.postman.com/docs/tests-and-scripts/running-collections/intro-to-collection-runs)
for execution controls and per-request inspection. This is an adaptation, not a
clone or an independently validated competitor usability comparison.

- Select cases and the two tool-loop exchanges; use Request/Response/Stream
  events/Headers to inspect their fictional captures.
- Select an event to inspect its payload; select a check and Locate evidence
  to navigate to the appropriate header, response or event view.
- Filter case attention, scope the run log, select log entries and adjust the
  pane splitters by dragging or arrow keys. The mobile view switches panes.
- Rerun/stop are explicit simulations. An unfinished exchange does not reveal
  the completed response or count as passed. Export provides purpose previews
  and a clearly labeled synthetic JSON only.
- Chinese/English, three palettes and light/dark remain available. The six checks
  shown per case are examples for interface discussion, not a complete assertion
  catalog or additional shipped test coverage.

Final isolated-browser verification on 2026-10-23 exercised those interactions,
tool-result steps, both languages, light/dark and narrow pane navigation. The
1280x900 and 390x844 documents fit their viewports; content scrolls within panes.
No console/page error or external request was observed. Screenshots were visually
inspected. No full mobile/accessibility, production, container, endpoint or remote
CI acceptance is claimed. Evidence: ignored artifacts/runner-study-20261023/.
The owner's everyday Chrome profile was not used. Do not investigate app browser
integration merely to continue this design discussion.

## Earlier overview sample

Serve this directory with any static file server. The local design preview uses
http://127.0.0.1:8767/ independently of the actual application on port 8765.
No build, dependency installation or backend is required; index.html also works
as a local file where browser history APIs permit file URLs.

- Toggle Chinese/English and light/dark using the header controls.
- Use Palette to compare Graphite (neutral gray with charcoal controls), Slate
  (cool gray with subdued steel accents), and Ink (warm gray with ink controls).
  Original blue remains available for comparison. Graphite is the proposed
  default for review, not an approved production identity. Palette selection is
  retained in the local page URL, including after theme/language changes.
- The Overview displays five cases and six requests with separate task/protocol
  judgments. These numbers match the current catalog, not newly implemented tests.
- Select a case or grouped issue to inspect differences, stream ordering, raw
  synthetic payloads, affected cases and impact limitations.
- Switch Demo state or simulate a rerun/stop. There is no automatic progression
  and no queued task, real cancellation or API request behind these controls.
- Export previews distinguish reading and diagnostic handoff. Only a clearly
  labeled synthetic summary JSON can be downloaded. No production HTML report,
  evidence archive, ZIP bundle or repair comparison is generated by this sample.

All identities and observations are fictional; the example.test endpoint does
not identify a user service. No credentials, original logs or private trial data
are embedded. The prototype does not fetch data or use browser storage.

## Earlier overview verification and limits

On 2026-10-23, the standalone sample was inspected in Chromium at 1280x900 and
390x844. The completed Chinese desktop overview fits one 900px screen. Narrow
overview/issue layouts have no document-level horizontal overflow; the mobile
issue selector scrolls within its own region. Detail pages may scroll vertically.

The local browser walkthrough exercised navigation, filters, affected-case
selection, evidence tabs, bilingual/theme switching, configuration/rerun/stop,
export-purpose previews and the synthetic JSON download. Final verification
recorded no console/page errors and no external requests. These are prototype
checks, not acceptance of equivalent behavior in the installed application.

Visual inspection caught a theme-switch transition temporarily pairing light
background with dark-theme button text. Removing the generic background-only
transition fixed it; final measured export-button text contrast was 13.21:1.
The initial 925px completed overview was compacted to fit 900px without removing
case results. Original failed observations/screenshots remain in ignored
artifacts/console-study-20261023/ alongside final captures and observations.json.

The in-app browser control surface was not exposed. Chrome could capture the
initial sample, but viewport/evaluation calls later timed out. Existing authorized
independent-browser fallback was used to complete checks. No complete accessibility,
screen-reader, browser matrix or arbitrary long-content acceptance is claimed.
No product/container/remote CI or real endpoint check accompanied this work.

## Palette follow-up: 2026-10-23

The owner rejected the previous generic blue-gray appearance and requested a
professional direction. The alternatives use neutral surface layers and preserve
the same diagnostic color roles and layout, allowing a fair comparison. The
[Carbon color guidance](https://www.carbondesignsystem.com/building-blocks/foundations/color/overview)
informed neutral layering and role separation; its brand blue is not adopted by
the three alternatives. No palette has yet been selected by the owner.

An isolated temporary test browser rendered all eight palette/theme combinations;
the owner's everyday Chrome profile was not connected or inspected. Final checks
recorded no page/console errors, no external requests, and a minimum 4.72:1 contrast
among sampled body/secondary text, primary/secondary buttons and status badges.
The 1280x900 completed overview still fits one screen. English labels, selector
behavior, URL restoration and 390px overview/issue width were checked. These are
bounded prototype observations, not complete accessibility conformance or product
acceptance. Captures and observations are in ignored artifacts/console-palettes-20261023/.

## Handoff

Review this sample before choosing a bounded production change. Do not infer
approval of implementation, a new frontend stack or another whole-product stage.
The existing application and its stored runs remain unchanged. Product source
still provides five formal endpoint cases; this prototype adds zero coverage.
