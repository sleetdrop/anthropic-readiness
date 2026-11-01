## Outcome

What concrete diagnostic capability or usability defect does this change address?

## Validation

- TypeScript check entry point: command and actual outcome
- Relevant fault/control tests: what they establish
- Browser or real endpoint checks, when applicable: scope and outcome, or not_run

Keep endpoint scenarios, assertions and tool self-test counts separate. For
supporting-only work, explicitly say endpoint coverage did not increase.

## Limits and review focus

Remaining gaps, changed contracts and known failures. Use public IDs and synthetic
reproduction only; never attach credentials, private endpoints or original logs.
The active guide is AGENTS.md. Historical Python/container acceptance is not a
rewrite prerequisite. No new stage plan or approval loop is needed for a small fix.
