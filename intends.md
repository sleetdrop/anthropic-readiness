# Project intent

## Purpose and primary users

Help an endpoint user or inference-stack maintainer diagnose observable Anthropic
Messages incompatibilities across inference servers, protocol translators and API
gateways, particularly those that disrupt Claude Code. Self-hosted DeepSeek, GLM
and other models exposed through this interface are valid targets.

The defining workflow is: a chain changes, an agent behaves unexpectedly, the
user runs relevant checks, shares reproducible evidence with a colleague and their
coding agent, and repeats the checks after a repair to distinguish recovery from
remaining failures and missing coverage.

## What the product must deliver

- A substantial, explicit, versioned catalog covering ordinary messages, streaming
  lifecycle and content assembly, tool arguments and complete result round trips,
  multi-turn state, request validation and error responses. Test optional features
  separately and expose their prerequisites and coverage limits.
- Checks that identify concrete faults. Every supported scenario has a documented
  expected outcome and suitable valid/faulty offline controls. A rejected invalid
  request can be a success; a timeout cannot establish a protocol violation.
- Real client checks for SDK and Claude Code workflows, with exact tested client,
  platform and task scope. API-only success does not establish client readiness.
- Repeatable execution against an explicitly selected protocol snapshot: API
  headers, beta set, rules and suite revision. Maintain official source references
  and a repository Agent command for periodically reviewing protocol changes.
  Provide version comparisons and locking guidance only to the extent tested;
  an API date alone does not pin model behavior or guarantee workflow stability.
- One execution engine usable through a local Docker Web application and CLI.
  The Web view emphasizes global progress and actionable exceptions; details are
  available without turning the overview into a long report. CLI runs also write
  reports. Exported reports work independently of the running application.
- Concise, professional Chinese/English reports and interfaces, useful charts and
  matrices, light/dark themes, structured Agent-readable facts, references,
  expected/actual differences and enough sanitized evidence to reproduce issues.
  Handoff and repair verification preserve original results and expose omissions.
- An independent, restrained engineering-tool identity. Supporting Anthropic's
  protocol does not imply adopting its website/application branding or palette.
  Ground interactions in comparable diagnostic/test tools and observed usage;
  use deliberate information hierarchy in both light/dark themes.

## How to choose and finish work

1. Start with the user-visible diagnostic capability being added or the concrete
   defect blocking use. Explain supporting infrastructure work in those terms.
2. Prioritize reliable fault detection and hands-on use. Deep testing is the
   owner's priority; optional budgets must not silently reduce selected coverage.
   Real calls still require explicit opt-in and recorded request/time limits.
3. Each delivery states the formal endpoint scenarios added or changed, faults
   they can detect, how the user can run them, and important remaining gaps. For
   supporting-only work, say explicitly that endpoint coverage did not increase.
4. Keep remaining core coverage visible in [the current handoff](docs/CONTINUE.md).
   A narrow milestone limits that task; it does not remove the unfinished product
   goals here. Do not repeatedly defer them behind presentation or release work.
5. Count endpoint scenarios, assertions, tool self-tests, sampled repetitions and
   client workflows separately. Large self-test counts and green CI are evidence
   of implementation quality, not comprehensive endpoint compatibility.
6. Use checks appropriate to changed behavior and meaningful regressions. Reuse
   verified unchanged-source evidence where applicable, state its identity and
   limits, and retain failures. Broaden checks for concrete risks or release needs.

## Boundaries and maintenance

This is a specialized compatibility diagnostic tool. General OpenAI-protocol
testing, model ranking, load testing and hosted multi-user collaboration are
outside its current intent. Do not infer endpoint internals, certify untested
features, or claim complete coverage of a changing protocol.

Use the checked-in Dev Container, modern typed Python, appropriate GitHub CI,
human/Agent-friendly contribution guidance and Docker delivery to support this
purpose. Keep private targets, secrets and original service logs out of source
and public artifacts. Preserve the repository's evidence and engineering rules.

This file records durable intent, not delivered status or a release checklist.
The owner's current instructions govern changes in direction. Update this file
when that intent changes; do not rewrite it to justify an implementation after
the fact. Resolve conflicting milestone assumptions explicitly and record gaps.
