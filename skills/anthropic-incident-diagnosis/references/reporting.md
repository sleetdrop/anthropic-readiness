# Write a compatibility report

The generated `report.md` is a check record. For a shared report, write a short
synthesis in the user's language from the check record, `result.json`, and the
relevant request/response bytes. Reconcile contradictory observations before
summarizing. Cross-run comparisons must name the API header and keep overlapping
case counts separate from request counts.

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

Use Markdown as the shareable and agent-readable source. An offline HTML view
can use plain typography, restrained status colors and a compact capability
table. Every label should remain meaningful without color. Keep navigation to the
evidence and omit private URLs, credentials, and unnecessary raw text in any
shared version.
