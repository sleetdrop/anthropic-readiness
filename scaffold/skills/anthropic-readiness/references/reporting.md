# Write a compatibility report

The generated `report.html` is a check record. For a shared report, write a short
synthesis in English from the check record, `result.json`, and the
relevant request/response bytes. Reconcile contradictory observations before
summarizing. Cross-run comparisons must name the API header and keep overlapping
case counts separate from request counts.

Identify the tested combination of model, inference software, and API
conversion software, with versions when supplied. Use the existing summary
and findings fields for this context; leave unknown components explicit.
A response model label does not establish backend identity. Preserve unknown
name mappings as findings rather than treating them as configuration mistakes.
When comparing combinations, name the case revisions, API headers, selected
scope, and completed checks. Attribute a difference to an individual layer
only when a controlled comparison distinguishes that layer.

1. **Conclusion.** State what worked, the most consequential verified difference,
   and one important evidence boundary. Name the tested model and versions.
2. **Capability table.** Summarize by tested capability. Distinguish observed
   compatibility, a demonstrated protocol deviation, an explicit capability
   rejection, blocked or inconclusive evidence, and untested scope. Put task
   success next to protocol observations where they diverge. Avoid a total
   compatibility score.
3. **Selected evidence.** For each important finding, give the request condition,
   expected response, observed response, and a brief consequence. Cite the
   applicable contract and link a representative capture. Include case ID,
   exchange number, and JSON Pointer or zero-based SSE index when available.
   Use reviewed snippets only. Leave the complete check matrix and raw records
   in the appendix.
4. **Reproduction and remaining uncertainty.** Give the shortest discriminating
   request or check when it would help. Keep unverified root causes separate from
   observed behavior. State when the SDK or client itself was not exercised.

For an HTTP error, confirm the complete captured body before characterizing it.
A generic 400 or a preset's `BLOCKED` status cannot establish feature
unavailability. A clear capability rejection tied to the tested request can
support that finding. If a follow-up never ran, report the completed step and the
missing step independently of its aggregate status.

## Generate the report

Use [the example input](assessment-example.json) as the shape for a private JSON
file. Supply the English summary, capability observations and findings based on
reviewed evidence. List each run's `result.json` relative to the input file.
Use one requested model per report. Each evidence entry names a run, case and
one-based exchange. Add a reviewed JSON Pointer or zero-based SSE event index
as `location` where it helps locate the evidence. Use `summary.finding` to link
the lead to its supporting finding. A finding can include a comparison table
with a caption, columns, and rows of strings or numbers. Include units in the
caption or headings.

Use Node 24 LTS and `SKILL_DIR` from the
[skill instructions](../SKILL.md) to render the report offline:

```sh
node "$SKILL_DIR/scripts/render-assessment.mts" \
  --input /path/to/assessment.json --out /path/to/assessment.html
```

The renderer reads run metadata, counts distinct selected cases separately from
requests, and resolves evidence links against actual exchanges. It prefers an
existing JSON viewer and links the original JSON when the viewer is unavailable.
The output is a new English HTML file. Keep it and the evidence files in the
same relative layout if moving the report. The input and original attachments
stay local. Inspect the report and evidence before sharing.

Use the renderer for the document layout instead of writing one-off HTML.
The report uses numbered sections, an inline contents list, and a small local
navigation script. Section links remain usable without JavaScript.

## Writing style

Use the wording of an engineering test report. Put the subject and result first.
State which request was sent, what came back, and how it compares with the
documented requirement. Use established protocol terms and exact field names.
Avoid coined terms, promotional language, filler, and repeated conclusions.
Where evidence stops, state which test or exchange was not run.

## Figures and presentation

Use the hierarchy of a short technical paper. Keep the abstract short, use
tables for exact comparisons, and put raw observations in the appendix.
Set the report type above the model name and keep the model identifier easy to
read. Lead with the most important verified result. Give scope its own line.
Number the main sections and link short finding references from the results
table. On narrow screens, give the observation the full width of its row.
Use thin table rules, keep counts right-aligned, and group case IDs, evidence
locations, and response links into separate columns where space allows.
Use figure captions for the reading takeaway and reserve accents for meaning.
Avoid decorative graphics, standalone scores, and charts that restate the text.

Use a figure when the reader needs to see a trend, distribution, or relationship
that is hard to extract from the table. A latency distribution requires repeated
measurements. A before/after chart requires comparable conditions and a shared
scale. Use one panel by default, label units and the number of observations,
and keep missing or blocked data distinct from zero.

For an offline figure, use semantic HTML with an inline SVG if needed, a visible
caption, and the key values or a linked data table. Give the SVG an accessible
name and use labels or shapes alongside color. Figures require no scripts or external assets.
