# Visual expression and interaction proposal

Status: design discussion, not an approved product implementation specification.
This extends the [local Web console proposal](2026-10-16-web-console-reference-study.md).
The owner requires restrained, professional styling with substantially better
visual explanation, rather than a predominantly textual report.

## Primary references and interpretation

- [Promptfoo Web viewer](https://www.promptfoo.dev/docs/usage/web-ui/) documents
  result tables, filters, output details and charts. Borrow the connected
  comparison/detail workflow. Do not import its grading scores as compatibility.
- [Allure timeline](https://allurereport.org/docs/timeline/) connects execution
  order/duration with test details. Borrow this as an investigation tool, not a
  decorative chart or an unsupported performance benchmark.
- [Inspect viewer](https://inspect.aisi.org.uk/log-viewer.html) separates live
  evaluation status, individual samples, messages and metadata. Preserve these
  distinctions when progressing from overview to evidence.

These are official-document observations. The local mockup is original and uses
synthetic data; it does not reproduce third-party source or styling.

## Reading structure

The same assessment identity connects configuration, execution and final reading.
The first screen answers: what was tested, what happened, where the gaps are, and
what to inspect next. Details follow a short path:

`Conclusion -> capability matrix or chart -> cases -> finding -> evidence/source`.

Use compact metadata, a short scoped conclusion and a meaningful matrix near the
top. Avoid repeating the same counts in several oversized visual components.
Dense details belong in accessible expandable panels, without losing filter state.

## Visual vocabulary

| Visual | Question it answers | Data and interaction contract |
| --- | --- | --- |
| Capability matrix | Which capability works, and in what sense? | Rows are declared capability groups; columns separate behavior, protocol and execution conditions. Cells show exact counts/statuses, with case details on activation. |
| Status distribution | How is the declared scope accounted for? | Distinguish PASS, FAIL, INDETERMINATE, BLOCKED and SKIP. During execution also show pending/running separately. State the counting unit and denominator; never label this a universal compatibility percentage. |
| Finding impact bars | Which observed issues affect more tests? | Count distinct affected cases, not assertion repetitions. One case may belong to multiple findings; bars are not additive coverage or inferred severity. |
| Execution timeline | Where did the run spend time or stop progressing? | Use actual recorded start/end/phase times and distinguish live from completed spans. Activation enters corresponding cases. Missing timestamps do not justify fabricated chronology. |
| Expected/actual comparison | What specifically differs? | Show verified local fields, missing versus null, event context and provenance. Label excerpts and omissions; do not silently normalize raw responses into compliant-looking output. |
| Version/run comparison matrix | Which tested configuration is suitable to pin? | Use explicit model/API-date/beta/rule-snapshot identities and evidence-backed results. Distinguish untested cells, changed rules and changed clients. Compare matching assertions or label non-comparability. |

The initial screen needs a small coherent selection: capability matrix, status
distribution, finding impact and timeline when timestamps exist. Version/run
comparison belongs in a separate comparison view once formal catalogs and history
support it. It must not invent newer API dates or turn header acceptance into
version negotiation proof. Performance plots require suitable measurements;
do not derive token speed from bytes, call the first event a first output token,
or claim useful tail-latency statistics from isolated tests.

## Visual style and interaction

Use a light paper-like canvas, a clear typographic hierarchy, restrained semantic
colors and aligned numerical values. Color always has a textual/symbol counterpart.
Use spacing, captions, axis labels, units and source notes as part of the design.
No 3D charts, neon decoration, speculative radar scores or dominant pass-rate dial.

Matrix cells and timeline segments support mouse and keyboard activation. Offer
filters for failures and unresolved results. Details retain a route back to the
same context. Hover can add information, but cannot be the sole way to read it.
Running views distinguish observed activity from estimated completion. A real
slow endpoint must not be represented by a fake steadily increasing progress bar.

## Export and agent interpretation

The Web UI and export share a versioned report view model derived from authoritative
results. The export is a composed report, not a screenshot of the running app.
Offline HTML keeps useful charts, matrix filtering, details and local navigation,
with all required assets/data packaged and no server, CDN or telemetry requirement.
This proposal permits packaged optional browser scripts for the new export;
it does not retroactively change the historical script-free Stage A acceptance.

Essential conclusions, matrices and chart data must remain readable when scripts
are unavailable. Use static HTML/SVG plus progressive enhancement. Printing should
retain essential figures, captions and evidence references while removing live
controls. Markdown provides chart-equivalent tables and explicit interpretations;
JSON preserves machine-readable values, identities, denominators and evidence links.
Every figure has a stable identifier, a short caption and a route to its data.

Neither a visualization nor a presentation migration may alter source verdicts,
hide unresolved required cases, erase attempts or rewrite original evidence.

## Data availability and verification

Current source has case dimensions, attempts, assertion/evidence references and
attempt durations. These can support count matrices, issue groups and duration
comparisons within the actual shipped four-case scope. Persistent progress events,
per-case wall-clock spans, expanded capability catalogs, comparable multi-version
history and client workflows require new implementation. Do not backfill a timeline
by assuming that the sum of request durations equals elapsed execution time.

The owner approved a browser visual companion. Its ignored local mockup shows
running and completed views with 24 explicitly fictional cases, original SVG charts,
matrix filters, case/finding drawers and an export-content preview. It does not run
tests, export real reports or establish support for the demonstrated capabilities.

Observed browser checks covered view switching, matrix-to-case-to-finding navigation,
expected/actual display and export-preview opening. Captured screenshots remain in
the ignored companion session. This is design feedback material; production browser
accessibility, offline-export behavior, print/narrow-layout acceptance, data integrity
and Docker acceptance remain unrun and belong to the future implementation plan.
