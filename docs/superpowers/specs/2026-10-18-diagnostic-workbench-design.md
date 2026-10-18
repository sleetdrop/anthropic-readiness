# Anthropic compatibility diagnostic workbench and repair handoff

Date: 2026-10-18. Revision: 1. Status: draft for owner review.

The owner approved the conversational direction: a focused diagnostic workbench
for Anthropic-compatible endpoints used by Claude Code, a separate assessment
document, and portable handoff followed by repair verification. The owner asked
that this be practical and evidence-backed. This written specification is not yet
approved. Product implementation, implementation planning and new endpoint calls
have not started. Visual layouts still require review before implementation.

## 1. Purpose and users

An inference server, protocol translator or API gateway changes. Claude Code then
behaves unexpectedly. An endpoint user needs to expose observable incompatibilities
and send useful evidence to the colleague who maintains that chain. That colleague
and their coding agent investigate, change their system, and use this tool to
check the result. A person maintaining their own inference stack has the same need.

The product specializes in Anthropic Messages compatibility and the observable
conditions needed by Claude Code. Supporting self-hosted DeepSeek, GLM or another
model behind this interface fits that specialization. Adding OpenAI protocols,
general model-quality ranking, load testing, shared hosted collaboration, user
accounts or a notebook authoring environment is outside this design.

Success means that a user can monitor a run without reading a document, find a
specific difference with its evidence, hand it off without copying terminal logs,
and distinguish observed recovery from missing or incomparable verification.
The owner values test depth over API expense. Optional cost control must not
dominate the primary flow or reduce the selected scope silently.

## 2. Relationship to current delivery

W1 is locally delivered; its specification, verification records and original
results remain historical facts. This is a proposed W2 follow-up. If approved,
it supersedes W1's embedded long-report interaction for new Web pages and new
presentation exports. It does not rewrite W1 acceptance or frozen Stage A files.

Observed current implementation:

- `resources/web/run.html` places execution progress, the full rendered report
  and export controls in a single document.
- `cases.py` provides four fixed cases selected by profiles. `RunPlan.to_json()`
  fixes repeat to one and retry to zero. Arbitrary case selection is not present.
- `exports.py` preserves result bytes and selected verified evidence. Export
  manifest 1.0 describes delivery, not a portable executable test recipe.
- Existing configuration fingerprints include local target details. Existing
  test fingerprints do not establish a complete cross-release validator identity.
  Neither alone is an adequate repair-comparison key.

W2 delivers the closed loop using the installed formal catalog. Its default action
is labeled "Run installed suite" with the actual case count and coverage shown.
It must not advertise four cases as comprehensive Claude Code verification.
Broader API cases, repeated sampling, full tool loops, multi-version execution,
Claude Code workflows and protocol-update tooling retain separate B/C/D scopes.
The private comprehensive assessment is not imported as a supported test catalog.

## 3. Delivery slices and explicit limits

Use one written W2 contract, with sequential implementation slices:

1. Separate operational workbench views from exported assessment documents.
2. Deliver a versioned diagnostic package and read-only baseline import.
3. Generate a local retest preview and compare fresh results with the baseline.

W2 is useful only when the entire handoff/retest loop works; completing the first
slice is not whole-W2 acceptance. Each slice must leave the CLI usable.

The first retest executes the entire original selected profile scope, including
previously passing and unresolved cases. This deliberately narrows the previously
discussed targeted-retest idea: four cases do not justify weakening existing
required-profile accounting. Failed-case-only execution, custom subsets and
automatic related-case selection are deferred until their selection and coverage
contracts are separately defined. Displaying or filtering failures never changes
execution scope. No retry or repeated-sampling control is offered before support
exists in the engine and schemas.

## 4. Information architecture

Application navigation contains Runs, New test and Import diagnostic package.
Presets remain part of configuration; no new administration area is needed.

A run has a persistent compact header containing target alias, requested model,
API date, beta set, rule revision, run lifecycle and the applicable action.
Actions include cancel while active, export after termination, and prepare retest
for a usable baseline. Completed runs do not retain a disabled primary cancel
button. Full URL, identities and hashes are available through details.

Below the header, use distinct run views:

| View | Main question | Main content |
| --- | --- | --- |
| Overview | Is this run progressing, and does anything need attention? | Progress, current activity, attention summary, compact group status. |
| Issues | What difference was observed and why does it matter? | Filtered issue list and a selected issue inspector. |
| Cases | What ran and what did each check establish? | Case table and selected case details. |
| Compare | What changed relative to the selected baseline? | Conditions, paired results, observed recoveries, remaining failures and gaps. |
| Activity | What happened during execution? | Recorded phases/events and optional timing view. |

Compare explains how to choose/import a baseline when none is selected; it does
not invent an empty comparison. Imported assessments use a read-only baseline
page with source identity and import quality, rather than pretending to be local
jobs with a worker, heartbeat or local completion timestamp.

Views and selected objects have stable URLs. Refresh, browser Back and closing an
inspector restore the filter, selected row and scroll position where applicable.
Incoming progress must not replace the focused inspector or move keyboard focus.

## 5. Quiet, single-screen run overview

The overview is an operational surface, not a report introduction. Its normal
desktop composition contains:

1. Persistent run header and view navigation.
2. Completed/evaluated versus planned cases, execution state, elapsed time, actual
   requests versus the admitted cap, and unresolved/failed result counts.
3. Current case and last recorded upstream phase/activity.
4. A compact group-progress display and at most three issue summaries with an
   explicit link/count for the rest. If there are none, show a calm empty state.

Normal passes update counters quietly. Newly observed issues update a badge and
the attention region; they do not open a modal, change views or reorder a selected
row. Completion gives one concise status change. No raw token stream, auto-scrolling
log or permanent stack of dismissible success notifications appears here.

Keep three facts separate: browser connection to the local service, worker/job
liveness, and last upstream data received. A local SSE connection or server
heartbeat does not prove upstream activity. Derive any stale-activity indicator
from known timestamps and configured timeouts; show "no new upstream activity"
with elapsed time rather than declaring a hang. Reconnecting does not resend.

Waiting for headers, receiving a response, protocol completion and capture end
retain their actual meanings. Do not label arbitrary bytes as first-token latency,
invent estimated completion times, or infer completed tests from elapsed time.

At 1280x800 and 1440x900 CSS pixels with 100% zoom, global run state and the
overview's attention/action area must be visible without document scrolling.
Use the compact composition for these sizes. The complete catalog and long text
live in other views. At narrower widths or 200% zoom, readable reflow and keyboard
access take precedence over the one-screen target. Avoid multiple competing
scroll containers; a long case/issue list may scroll within its clearly labeled
region while its inspector stays accessible. Use a dedicated detail view when
the split layout cannot fit.

## 6. Investigation and visual expression

Issues use a master/detail layout on wide screens and a list/detail navigation
on narrow screens. Each issue inspector presents, in order:

- A plain-language observed difference, its check category and affected cases.
- Demonstrated consequence, or a clearly labeled potential impact when client
  behavior was not tested. Never imply an unobserved Claude Code failure.
- Expected versus observed structured fields or event order.
- Case, attempt, assertion and exact evidence references.
- Rule basis and a concise next verification step.

Issue grouping indicates a shared observation, not a proven common root cause.
Do not identify the gateway or inference server as responsible without an
observable comparison at those boundaries. Deployment/build labels may be entered
as user-supplied context and are labeled accordingly; no topology editor or
automatic internal-component discovery is introduced.

Use shared facts with distinct presentation responsibilities:

| Visual | Operational role | Export role |
| --- | --- | --- |
| Capability matrix | A cell applies a case/issue filter and opens matching details. | Summarizes assessed dimensions and unassessed areas, with labels and denominators. |
| Issue impact bars | Select an observation and inspect affected cases. | Explain scope; overlapping issue counts are not added as unique failures. |
| Execution timeline | Investigate recorded waits, ordering and incomplete capture. | Include only when it explains a finding; describe measured boundaries. |
| Baseline difference matrix | Locate recoveries, regressions and verification gaps. | Summarize repair verification with links to supporting pairs. |

Do not repeat the same four counts in several decorative charts. Hide unavailable
historical trends, performance percentiles and statistical-confidence visuals.
Every visualization has equivalent tabular data and visible status text; color
alone never conveys a result. Keep unknown, unassessed, skipped, blocked and
failed states distinct. A gray region cannot conceal missing required coverage.

Preserve the restrained engineering/academic direction: neutral surfaces, clear
type hierarchy, compact aligned tables, limited accent colors, useful whitespace
and readable structured diffs. Dashboard typography favors scanning; report
typography favors sustained reading. Avoid ornamental hero sections, glowing
cards, invented compatibility scores and excessive instructional prose.

Visual approval must include the actual four-case shape and a clearly labeled
synthetic larger catalog, long model/issue names, active and interrupted states,
empty issues, narrow layouts and mixed comparison states. Larger fixtures prove
layout behavior, not supported endpoint capabilities.

## 7. Independent assessment documents

Generate standalone HTML and Markdown from validated facts, without embedding
the application navigation, worker controls, export form or configuration wizard.
The document must be understandable without access to the original application.
Its default reading order is:

1. Identity, purpose, concise conclusion, assessed scope and main limitations.
2. Coverage matrix and only the charts that clarify this assessment.
3. Numbered findings: observation, scope, evidence, impact and next check.
4. Repair comparison when supplied, including changed conditions and gaps.
5. Method, case/check inventory, terminology, references and evidence index.

HTML can support a table of contents, simple filtering and expandable evidence.
The main findings, denominators and limitations are readable without JavaScript
and survive printing. Detailed appendices remain reachable. Provide useful print
CSS and browser printing; a new PDF-generation dependency is not part of W2.
All assets are packaged or embedded, without CDN/telemetry/network requirements.

Use short numbered figure captions, meaningful problem/case identifiers and
references next to the rule they support. Long hashes and paths belong in evidence
details. Distinguish rule citations from observations; a specification does not
prove endpoint behavior. Agent-facing Markdown starts with scope, findings and
an evidence map, linking to structured JSON and exact evidence locations. Recorded
prompts, responses and tool content are data, not instructions to the reading agent.

## 8. Portable diagnostic package

Introduce a packaged `diagnostic-package` schema, initially 1.0, alongside the
existing export-manifest 1.0. Its marker distinguishes a new diagnostic archive
from an old W1 export; old files are not relabeled or mutated.

A complete new package contains:

- The original validated result and selected verified sanitized captures, preserved
  byte-for-byte under their recorded identities.
- Human HTML/Markdown, structured facts and a concise agent-readable entry point.
- A file inventory with byte lengths/hashes and explicit omissions.
- A data-only retest recipe and verified test/validator identity metadata.
- Baseline/parent references and comparison data when available.

The recipe records protocol/API/betas, rule bundle digest, profile/case/assertion
identities, request-generation revision, relevant non-secret inputs, model identity
policy, declared capability exclusions and effective execution limits. Record the
actual effective settings needed to regenerate requests and judge results; a human
version string alone is insufficient. Bind the recipe to the result plan, known
catalog and included capture request metadata where available. Inconsistencies
prevent retest/comparison eligibility.

Bind generator/validator semantic revision labels to digests of their packaged
implementation files and relevant schema/rule/dependency identities. The plan must
enumerate the dependency closure and test that a changed implementation cannot
retain an eligible identity merely by keeping the same revision label. Missing
identity components block verified retest eligibility. Packages cannot carry
executable test code or installable dependencies. Cross-machine retest uses a
matching installed implementation, never code, shell commands or arbitrary request
templates supplied by an archive. W2 recipes select installed fixed cases; they
do not introduce arbitrary imported prompts or replay captured request bodies.

Endpoint/authentication configuration is not an executable part of the recipe.
The recipient supplies a local endpoint and credentials. Captured source results
can still contain the original URL/model or business text: the export preview
must identify that retained content plainly. Credential redaction is not general
anonymization. Do not claim an original-evidence package is anonymized. An alias-only
summary can be shared without original evidence, but is explicitly insufficient
for independent evidence verification or a verified portable baseline. W2 does
not implement arbitrary user-edited evidence redaction under the original hashes.

Exporting does not send requests, modify original results, or verify that a service
still behaves the same way. Hash validation proves internal byte consistency, not
the truth of an external assessment or the identity of its author.

## 9. Read-only import and eligibility

Accept a diagnostic ZIP or legacy W1 ZIP. A standalone HTML/Markdown report is a
reading artifact, not a recoverable baseline. CLI import uses the same service.
Show eligibility and reasons before persisting the baseline:

| Condition | Available operations |
| --- | --- |
| New package, valid complete result, valid recipe, verified identities and required evidence | Read, prepare retest and conditionally compare. |
| Valid metadata/result but evidence intentionally omitted | Read declared results; mark evidence unavailable. No evidence-verified repair claim. |
| Valid legacy W1 export without portable identities | Read as legacy; manually prepare a current test. No verified same-test repair comparison. |
| Partial/interrupted package | Read retained observations; missing baseline checks stay missing. No complete-baseline claim. |
| Missing local matching generator/validator/rule identity | Read; retest blocked with the exact mismatch. No silent upgrade or installation. |
| Corrupt inventory, conflicting identities or invalid required documents | Reject activation with specific errors; retain the original uploaded bytes only under bounded local quarantine if needed. |

Evidence-verified comparisons require the complete new baseline above. Lesser
inputs can be viewed side by side with explicit limitations, without recovery or
regression badges that imply a controlled comparison. Optional presentation files
are not authoritative: regenerate local views from validated structured facts.

Assign each imported baseline a local ID and retain its external assessment ID
and archive digest. Identical imports deduplicate by archive digest; matching
external IDs with different bytes remain separate and visibly conflict. Imports
do not create local job-completed events or overwrite a local run with that ID.

Treat archives as untrusted data. Validate bounded upload/member count, compressed
and expanded sizes, total expansion, paths and member types before extraction;
reject traversal, absolute paths, duplicate/ambiguous names and links. Parse JSON
strictly and validate schemas, cross-file relationships and hashes. Bound parsing
and storage work. Never execute or serve uploaded HTML/JS as application content,
dereference external resources or make endpoint requests during import. Rendering
uses the existing escaping and local security boundaries. Concrete finite limits
are fixed in the implementation plan and tested at their boundaries.

## 10. Preparing a retest

The baseline action opens a new local configuration preview. The endpoint starts
empty even if the original result records a URL; a user can explicitly select a
local preset. Credentials are always supplied or selected locally. Preserve the
source model and test conditions as visible reference values, not hidden defaults
that override user input. Local Docker addressing remains explicit.

Resolve the installed matching catalog, regenerate the whole original scope and
compare the generated plan against the recipe before admission. Show a concise
conditions-difference summary: endpoint/build label, model, API/betas, identity
policy, exclusions, rule/generator/validator identities, selected profiles and
effective limits. Starting requires the same explicit local preview/live opt-in
as W1; import, viewing and preparing a retest make zero upstream requests.

New results carry lineage in a separate versioned assessment-context record:
local baseline ID, original assessment/result digest, recipe identity and declared
changes. Preserve existing result 1.0 bytes and required-profile semantics. Never
insert comparison facts into the original result or modify its assertions.

The Web and CLI use the same import, eligibility, retest-plan and comparison
services. CLI retains standalone execution and automatic output. Provide CLI
operations for import/inspection, preparing a retest, and comparing two locally
available assessments; exact option names are implementation-plan decisions.

## 11. Comparison and honest repair statements

Compare cases and assertions by verified semantic identity, not displayed row
number, finding label F01, timestamps or the existing whole-target fingerprint.
The comparison identity includes case/generator identity, deterministic request
parameters, validator/rule identity and expected-value policy. Exclude endpoint,
credentials, run IDs and display labels; show these separately as changed context.

W2 verifies paired rule-check transitions under unchanged non-transport test and
judgment settings. A changed model, API/beta set, alias policy, selected scope or
semantic implementation is shown side by side as changed conditions, without
automatically calling a transition a repair. If effective time/size limits differ,
mark affected execution/capture-dependent comparisons incomparable; preserve raw
protocol observations without inferring improvement from truncated evidence.
Conservatively mark the whole pair incomparable when affected checks cannot be
identified reliably. Endpoint changes are allowed for retesting a locally deployed
fix, but are declared prominently and do not establish causation.

| Original check | New check | W2 interpretation when conditions are comparable |
| --- | --- | --- |
| FAIL | PASS | Previously violated check passed this sample; observed recovery. |
| FAIL | FAIL | Still failing; show whether the observed details changed. |
| PASS | FAIL | Newly observed failure relative to this baseline. |
| PASS | PASS | Passed in both samples. |
| Any | Missing, blocked, skipped, indeterminate or incomplete evidence | Verification gap; never recovery. |
| Missing or unresolved | PASS or FAIL | Newly evaluated result, not a proven improvement/regression. |

Also enumerate unmatched/added/removed cases and checks. Report baseline scope,
new scope, matched coverage and missing required checks separately; do not hide
unpaired checks in a percentage denominator. The headline "all previous failures
passed this retest" requires every original failing check to have a comparable
PASS with sufficient evidence. It does not assert that the whole protocol, all
Claude Code workflows or an intermittent fault has been fixed. Display any new
failures and gaps beside that headline.

One original sample and one retest sample cannot establish stability. W2 says
"not observed in this sample" where appropriate. Future repeat support must
preserve every attempt, state case versus request versus trial denominators and
avoid a last-pass-wins or hidden automatic-retry policy.

## 12. Execution controls and test depth

Retain W1 finite request, timeout, response-size and event bounds. An optional
monetary cap is not currently implemented and is not added by W2. The UI must not
pretend to estimate provider cost. For the owner's unrestricted-cost use, selecting
the entire installed scope computes a finite admission request allowance without
forcing a pricing workflow. Effective controls remain visible in details.

Do not silently drop cases to fit limits or stop at the first compatibility
failure. Preserve required-case accounting and fail explicit plan validation if
the configured cap cannot cover the scope. Cancellation and transport/storage
failure preserve partial results. More complete catalogs and repeated sampling
can later use these workbench views without inventing currently absent tests.

## 13. Architecture and contracts

Keep one execution engine and validated evidence/result reader. Add pure
comparison/eligibility projections; put archive I/O, storage and endpoint access
in adapters. The workbench consumes operational/fact projections and renders its
own templates; it does not embed the standalone report body. Standalone documents
consume the same checked facts with their own document composition.

Add packaged versioned schemas for diagnostic package, retest recipe,
assessment context, imported baseline metadata and comparison. New presentation
uses version 3.0; report-view projection changes are explicitly versioned, with
old readers/exports remaining identifiable. The plan must enumerate every affected
consumer and backwards-compatibility fixture. Do not change frozen result 1.0,
original captures, historic manifests or golden outcomes to fit the new UI.

Reuse the existing local FastAPI/templates/packaged browser modules, single
scheduler, worker isolation, Docker volumes and CLI. Tabs or split views alone do
not justify a new SPA framework. Add tooling only for an evidenced implementation
need. Retain no-CDN/offline exports, strict typing/schema checks, architectural
dependency gates, Dev Container execution and synthetic CI.

## 14. Required acceptance evidence

The implementation plan maps each item to meaningful failing-before-fix tests,
retained artifacts and observed results. No current test outcome is claimed here.

| ID | Acceptance condition |
| --- | --- |
| W2-01 | Same synthetic run produces equal authoritative facts through CLI, workbench and standalone documents; original result/evidence hashes are unchanged. |
| W2-02 | Both target desktop viewports show global progress and attention/action state without document scrolling; narrow and 200% zoom layouts remain usable. |
| W2-03 | A deliberately slow synthetic peer distinguishes local service connection, worker liveness and absent upstream activity; reconnection sends no duplicate request. |
| W2-04 | New issue/completion updates preserve focus, selected detail and reading position; keyboard users can operate tabs, filters, inspectors and Back navigation. |
| W2-05 | Issue/case/matrix navigation identifies the matching observations, exact evidence and rule basis; missing client checks never become demonstrated client impact. |
| W2-06 | HTML opens offline without a service; its main conclusion, coverage, findings and limitations remain readable without JavaScript and in print. |
| W2-07 | Export at machine A, import into a fresh machine-B data root, supply a different local synthetic endpoint, preview and run the entire original scope, then export the paired assessment. No source checkout, A endpoint or credentials are required at B. |
| W2-08 | Changed generator/validator identity with the same human case label is detected. Missing installed revisions, altered judgment policy and incompatible inputs do not receive verified repair badges. |
| W2-09 | Synthetic paired runs exercise recovery, persistent failure, newly observed failure, unresolved/missing checks and changed scope/limits; denominators and headline rules retain every gap. |
| W2-10 | Legacy, evidence-omitted, partial, duplicate and conflicting imports receive their specified eligibility; malformed archives and forged references are rejected without execution or outbound I/O. |
| W2-11 | Original source facts, imported facts and local retests have separate immutable identities and provenance; view/export/import never mutate old assertions or erase failed attempts. |
| W2-12 | CLI import/retest/compare works without Web dependencies or a running service; both shipped images and persistence survive the supported local restart path. |
| W2-13 | Fast/full quality gates, browser coverage, installed resources and container checks pass in the checked-in Linux Dev Container; remote CI and real endpoints are reported separately. |
| W2-14 | One independent whole-stage review is completed after sequential implementation, followed by an evidence-recorded author correction pass if required. |

Use disposable synthetic peers for cross-machine tests, including a baseline
failure that the changed peer resolves and an independent defect introduced by
that change. This proves the actual handoff loop rather than only screenshot
appearance. Test larger synthetic lists as layout stress data, clearly labeled.
Real endpoint/client validation needs its own explicit live scope and budget.

## 15. Reference rationale and next review

The prior discussion reviewed official documentation for
[Promptfoo's viewer](https://www.promptfoo.dev/docs/usage/web-ui/),
[Inspect's log viewer](https://inspect.aisi.org.uk/log-viewer.html),
[Allure features](https://allurereport.org/docs/features-overview/) and
[Allure Agent Mode](https://allurereport.org/docs/agent-mode/).
The adopted principles are filter/drill-down analysis, continuous live-to-result
navigation, structured evidence/diffs and a distinct agent-readable entry point.
This specification is project-specific; it does not claim an interactive audit
of those products or copy their scoring/hosting models.

Before implementation planning, review this written scope and the visual layouts
for overview, issue inspection, comparison and the separate report. Visual work
is design-only and needs a selected direction before product implementation.
Broader suite design remains a subsequent explicit milestone; W2 completion alone
does not satisfy the owner's eventual comprehensive diagnostic coverage goal.
