# Engineering console reference study

Date: 2026-10-23. Audience: local endpoint users and inference-stack maintainers
running checks, investigating exceptions, sharing evidence and verifying repairs.
The owner requested external grounding and an identity independent of Anthropic.

Later owner feedback supersedes any implied fixed arrangement or palette below.
Use the [investigation-flow exercise](../design/console-study/investigation-flow.md)
for the current task-based direction; no preceding visual sample was selected.

## Evidence and limits

Reviewed official documentation and published interface examples linked below.
These establish documented mechanisms, not independent usability outcomes.
Competitor applications were not installed or tested. Recommendations are our
interpretation for this product, informed by the preceding desktop walkthrough
with synthetic responses. No product implementation, new endpoint coverage or
real endpoint execution is part of this study. Public documentation can change.

## Reference mechanisms and proposed adaptations

| Reference | Documented mechanism | Proposed adaptation and boundary |
| --- | --- | --- |
| [Postman Collection Runner](https://learning.postman.com/docs/tests-and-scripts/running-collections/intro-to-collection-runs) | Real-time results; runtime errors distinguished from assertion failures; rerun with the same settings. | Compact runner with concrete case status and clear rerun action. Separate transport failures from observed protocol deviations. Retain explicit opt-in and budgets; avoid a general request editor. |
| [Playwright Trace Viewer](https://playwright.dev/docs/trace-viewer) | Actions and timeline link to contextual logs and network request/response details. | Case/step list beside an evidence inspector. Show tool round trips as linked exchanges and streaming events in order. Stream validation still needs our protocol-specific rules. |
| [Allure assertion differences](https://allurereport.org/docs/assertion-diff/) | Assertion messages expand into details; expected/actual differences support side-by-side inspection. | Lead issue details with expectation and observation, then affected cases and evidence. Distinguish absent from null, and protocol deviation from demonstrated client impact. |
| [ReportPortal history](https://reportportal.io/docs/work-with-reports/HistoryOfLaunches/) | Test-case history table across executions with status-based navigation. | Repair comparison with fixed, persistent, new and unverified issues. Match suite/rule versions and scope; missing observations cannot count as repairs. Avoid enterprise project/role management. |
| [Promptfoo web viewer](https://www.promptfoo.dev/docs/usage/web-ui/) | Tabular results with failure/error/difference filters, cell details and evaluation comparisons. | Compact coverage matrix opening the relevant case/issue. Use compatibility dimensions rather than rankings; deterministic results must not become manually editable scores. |

[Allure Agent Mode](https://allurereport.org/docs/agent-mode/) separately documents
human visual reports and Agent-oriented Markdown/metadata, with an index leading
to supporting evidence. Borrow that organization for colleague-and-Agent handoff,
without installing Allure: readable report, concise Agent entry document,
structured facts and sanitized captures referring to the same run and issues.

## Recommended workflow, pending visual validation

1. **Configure:** simple endpoint/model entry with optional credentials. Show
   scope, maximum request count and time limit beside the primary action.
   Full plan details expand on demand.
2. **Run:** one overview with current case, completed/selected count, elapsed
   time, exceptions and stop control. Keep stable access to all cases/evidence.
3. **Investigate:** issue/case list beside details, instead of inserting an entire
   report into the dashboard. Expectation, observation, affected step, plausible
   consequence and limits precede raw payloads.
4. **Verify or share:** rerun original scope against a baseline, or export a
   readable report/diagnostic bundle. Choose purpose before file-format details;
   summarize manifests before expanding individual paths.

The earlier recommendation to compact the separate confirmation page is revised:
explore whether an inline summary and explicit Start can remove that extra page.
This proposal must preserve preflight validation, frozen-plan admission,
request/time limits and live opt-in. Current preview/start behavior remains
implemented until a bounded change is chosen.

Completion is a process state, not a compatibility verdict. Foreground
passed/failed/unassessed scope and whether client behavior was tested, rather
than a celebratory 100% indicator or unsupported overall score. Protocol
differences must not be presented as a proven Claude Code failure.

Charts should answer diagnostic questions: coverage/status matrix, repair
comparison and ordered stream/step timeline. At five cases a clear table may
serve better than multiple charts. Never manufacture trends or fill untested cells.

## Independent visual direction, pending sample review

[Primer color guidance](https://primer.style/product/getting-started/foundations/color-usage/)
demonstrates neutral surfaces and semantic color roles in light/dark modes.
Borrow that discipline, not GitHub branding. Proposed direction:

- Light: white/neutral-gray surfaces, clear text hierarchy and restrained borders.
- Dark: graphite surfaces with distinct panel levels and readable secondary text;
  tune contrast separately rather than mechanically inverting the light theme.
- One restrained blue interaction accent; green/red/amber for labeled statuses.
  Completion, missing coverage and transport uncertainty need distinct text/icon
  semantics, not color alone.
- Sans-serif navigation/body; monospace for identifiers and evidence. Prefer
  alignment, spacing and table structure over oversized cards or decorative effects.
- Share typography/status meanings between Web and exports; Web uses a compact
  working layout while offline reports provide a self-contained narrative.

## Bounded next step

Before implementation, inspect one representative overview/issue-detail sample
with realistic long names, mixed outcomes and both themes against these sources.
This research adds zero formal cases. Do not reopen a whole-product specification
or introduce a new frontend stack.
