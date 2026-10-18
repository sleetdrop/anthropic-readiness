# Diagnostic workbench design ledger

## 2026-10-18: W2 design proposal

The owner clarified the intended users and workflow: diagnose an Anthropic-facing
inference/translation/gateway chain used by Claude Code, share the report with
the chain maintainer and their agent, then verify the repair. The owner approved
the conversational workbench/document split and portable import/retest direction,
asking for practical and truthful behavior. No product implementation was requested
in this discussion. The current proposal is
[specification revision 1](../superpowers/specs/2026-10-18-diagnostic-workbench-design.md).

Observed source inspection covered the run template, four-case catalog, run plan,
configuration fingerprints, report models, exporter and packaged plan/export schemas.
It confirmed that W1 embeds the report body, arbitrary case selection and repeat
execution are absent, and export manifest 1.0 is not a portable retest contract.
No new endpoint call, product dependency, product source change or test execution
occurred. W1 acceptance and its completed plan remain unchanged.

Material design rulings:

- One-screen quiet overview; issue/case/compare/activity views own detailed analysis.
- Separate operational templates and exported documents share validated facts.
- First retest preserves the entire original selected profile scope; targeted
  subsets, repeats and expanded catalogs remain separately scoped work.
- New portable metadata must bind the result to installed request/validator
  implementations; version labels and existing fingerprints alone are insufficient.
- Legacy, partial and evidence-omitted packages remain explicitly limited.
- New import is read-only and makes no outbound request. A local target and live
  preview are required for a new assessment; old attempts remain immutable.
- Comparison distinguishes observations, verification gaps and changed conditions;
  one passing sample does not establish stability or internal root cause.
- Monetary controls are absent in the current engine and not added by this UI work.
- Cross-machine synthetic handoff/repair/new-regression acceptance is mandatory.

Author self-review checked placeholders, scope consistency, provenance, identities,
comparison denominators and backwards compatibility. It strengthened implementation
identity requirements so unchanged human revision labels cannot conceal changed
generator/validator code. This is document review, not independent stage review,
runtime verification, visual acceptance or endpoint evidence.

Current status: written specification awaits owner review; new visual layouts are
not produced or approved. No implementation plan exists. W2 is not implemented.
