# Reference-informed report refinement

The owner requested public examples after reviewing presentation 1.1. This is a
refinement within the approved conclusion/cases/findings/technical-evidence flow.
It retains offline HTML/Markdown, deterministic verdicts and the engineering style;
no dashboard service, model grader, JavaScript dependency or new API call is added.

## Public references inspected on 2026-10-16

| Reference | Observation | Adaptation |
| --- | --- | --- |
| [AI Ping example](https://github.com/starroyhq/ai-ping/blob/main/docs/examples/streaming-broken.html) and [report guide](https://github.com/starroyhq/ai-ping/blob/main/docs/reports.md) | Actual generated HTML gives the scoped outcome, brief client relevance, counts and run identity before check rows. Both happy and broken examples were read. | Compact run masthead and contextual verdict. Keep our own required assertions; do not adopt its optional-check grading. |
| [Schemathesis HTML report](https://schemathesis.readthedocs.io/en/stable/guides/html-report/) | Documentation puts invalidating execution warnings ahead of results and connects failures with responses and reproduction. | Evidence quality is visible near the conclusion. Link findings to the exact retained response/event. Live replay is not offered as an unbudgeted action. |
| [Allure assertion diff](https://allurereport.org/docs/assertion-diff/) and [navigation](https://allurereport.org/docs/v3/navigation/) | Expected/actual comparisons and grouped test navigation support investigation. | Labeled local-field snippets, grouped source links and bidirectional case/finding references. No severity or changed status is inferred from presentation categories. |
| [Inspect log viewer](https://inspect.aisi.org.uk/log-viewer.html) | Sample details separate messages, scoring and metadata so readers can inspect the grounds for a conclusion. | Preserve original verdicts and clearly label evidence excerpts versus configured expectations. The renderer does not judge or rescore. |

The AI Ping HTML/README/report-guide files were downloaded read-only into ignored
artifacts/report-research for inspection. No third-party implementation or styling
was copied. Upstream material was treated as reference data, not instructions.
Public browser observation timed out; reference claims above come from the actual
HTML sources and official documentation, not an asserted browser demonstration.

## Refined presentation

- A compact report masthead identifies target/model, API/contract, time, duration
  and request/retry counts. No endpoint URL or credential is newly exposed.
- The verdict connects task completion and strict compatibility without inventing
  a score. Distinct finding groups and affected cases have separate counts.
- The case table names linked findings. Findings have stable report-local F01/F02
  labels, treatment categories, per-case evidence links and anchored navigation.
- Verified snippets show only relevant fields. Expected fragments are explicitly
  partial illustrations; actual fragments are projections of retained bytes.
  Missing fields are distinguished from JSON null and from fields omitted by the
  excerpt. Missing/invalid evidence gets a visible qualifier and no invented diff.
- The technical appendix remains available; Markdown retains the same findings,
  facts, references and source locations. Presentation advances to 1.2 only; the
  result schema and protocol/assertion semantics stay unchanged.

## Verification requirements

Observe RED before implementation for the new summary, linked evidence, categories
and field comparisons. Retain all existing result-preservation, escaping, negative
capture and required-case tests. Run the full Linux graph and record actual outcomes
in the progress/reader ledger. Re-render the existing private capture into a new
private directory, compare original result/evidence hashes, and make no live call.
Use the previously established static rendering fallback for visual review; actual
browser layout/interaction remains unverified when the browser tool is unavailable.
