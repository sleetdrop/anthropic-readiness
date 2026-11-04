## Outcome

What concrete diagnostic capability or usability defect does this change address?

## Validation

- TypeScript check entry point: command and actual outcome
- Relevant fault/control tests: what they establish
- Real endpoint checks, when applicable: scope and outcome, or not_run

Keep endpoint scenarios, assertions and tool self-test counts separate. For
supporting-only work, explicitly say endpoint coverage did not increase.

## Limits and review focus

Remaining gaps, changed contracts and known failures. Use public IDs and synthetic
reproduction only; never attach credentials, private endpoints or original logs.
See AGENTS.md for current development instructions.
