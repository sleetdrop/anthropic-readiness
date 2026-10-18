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

The owner explicitly approved specification revision 1 on 2026-10-18 and asked
to proceed. The next activity is design-only visual alternatives for the run
overview, followed by the remaining workbench/document surfaces in the selected
direction. No implementation plan exists. W2 is not implemented.

## 2026-10-18: first visual alternatives

Three independent Image Gen concepts were displayed, in this order:

| Display order | Layout | Local ignored artifact under `artifacts/w2/visual-20261018/` |
| --- | --- | --- |
| 1 | Group progress with application rail | `exec-4e87de9b-ef7e-4626-ac6e-105bedcae9ed.png` |
| 2 | Full-width operational case table | `exec-52466fd6-dac9-4307-90e3-dee96c98c456.png` |
| 3 | Current-case execution phases | `exec-44be50b7-d60a-4534-bbce-97e024b3a93b.png` |

The existing run-overview screenshot was inspected and attached to each generation
for palette/product grounding. All three use explicitly synthetic four-case data.
The third image incorrectly rendered the current case title as `3 / 5`; this is
a generation defect, not a fifth installed case or accepted copy. The intended
title is the streaming count-from-one-to-five case. The owner was told this before
selection. Selected-direction refinement must replace generated text with exact
fixture-driven copy and verify counts and actual viewport geometry. Images are
layout concepts, not working UI, browser acceptance or endpoint observations.

Status after the first alternatives: waiting for visual direction selection. The issue, comparison and
standalone-report surfaces still need design work in that selected direction.
No prototype server, product implementation, new dependency or live call ran.

## 2026-10-18: selected direction, companion visuals and implementation plan

The owner selected the first displayed overview, then confirmed proceeding with
that direction. Refinements use a smaller target-alias heading, secondary model
metadata and neutral execution completion distinct from successful checks.
Three companion surfaces were generated: issue diagnosis, repair comparison and
standalone report. The [visual handoff](../reviews/2026-10-18-diagnostic-workbench-visual-design.md)
records their exact artifact mapping, consistent synthetic repair story, and
the distinction between static concepts and real layout/interaction acceptance.

The [implementation plan](../superpowers/plans/2026-10-18-diagnostic-workbench-implementation.md)
contains 15 sequential tasks and a W2-01 through W2-14 acceptance map. It preserves
the current checkout/Dev Container execution method and one end-of-stage review.
Source inspection additionally covered CLI dispatch, HTTP security/body limits,
job admission, fresh-directory behavior, report projection and check harnesses.

Author self-review corrected a recipe/context task-order dependency, chose a public
argparse interface, added a separate presentation-3 export-manifest schema rather
than changing legacy consts, and clarified standalone summary versus original-source
archive delivery. It also binds metadata-generation modules into core identity
and makes matrix passing-count denominators explicit. Task checkboxes remain empty.

Current status: companion visual and written implementation-plan review pending.
No product code, new runtime dependency or real endpoint call has been introduced.

The finalized documents passed `scripts/check_docs.py` in the retained Linux
Python 3.12 Dev Container with `UV_OFFLINE=1` / `uv run --frozen`; Git whitespace
checks were clean. The companion PNGs were retained locally and SHA-256 read.
No product unit/integration/browser/image test was run for this documentation-only
change, and no working prototype or real-viewport acceptance is claimed.

## 2026-10-18: Chinese/English and dark-theme amendment

The owner added two-language support and a dark theme before plan approval.
Specification revision 2 and the revised sixteen-task plan incorporate this request;
revision 1 approval and the selected light layout remain recorded. Task 0 defines
checked catalogs and semantic theme tokens. UI/report/CLI-output integration and
the W2-15 through W2-17 acceptance map explicitly cover language/theme behavior.
No product implementation has begun.

One requested dark theme was generated as an English overview using the selected
light reference. Its exact artifact and generated-versus-accepted color distinction
are recorded in the visual handoff. It is a static synthetic mock, not a working
UI or measured contrast result.

Material amendment decisions:

- Workbench locales `zh-CN`/`en`, default `zh-CN`; light/dark/system, default system.
- Persist only checked non-secret presentation choices in a preference cookie;
  do not add browser localStorage/sessionStorage or process-global locale mutation.
- Original requests, raw source data, codes, judgments and semantic identities
  remain unchanged. Translate product-owned explanations and accessible labels.
- Offline HTML embeds both catalogs; no-script initial content is readable;
  Markdown has one language; print uses light appearance in the chosen language.
- CLI flags select report presentation; machine fields and English command-help
  grammar remain stable. Wire the flags with the renderer in Task 13, not earlier
  as nonfunctional options.
- Same authoritative result/context/recipe with different localized/theme archive
  bytes is an export variant, not an assessment conflict. Keep each archive's
  evidence omissions/eligibility independent; never merge proof across variants.
- Contrast, English expansion, active-run focus preservation and no-request/hash
  invariance require actual browser/fixture checks during implementation.

Current status: amendment, dark visual and updated implementation-plan review
pending. No new endpoint call, runtime dependency or product source change occurred.

Amendment self-review checked defaults, no-script/print behavior, CLI/report task
dependencies, preference versus execution state and export-variant identity.
The revised documents passed the offline/frozen documentation/link/collaboration
check in the retained Linux Python 3.12 Dev Container. The dark PNG was retained
with SHA-256 `94b0133e988aff92220328efd959cbbadc04a0a828c20a689d430f1280c2aed7`.
No runtime/browser/contrast test is claimed for this documentation/design change.

## 2026-10-18: Dark palette refinement

The owner found the first dark design less successful than the light design.
The selected layout is unchanged. One revised English/dark overview uses neutral
graphite surfaces, clearer text/divider hierarchy and smaller semantic accents;
both previous visual references were attached. The visual handoff records the
exact artifact, hash, superseded green-tinted palette and remaining generated
shading/lifecycle-color limitations. The refined palette awaits owner review.
No product code, dependency, live request or browser acceptance changed.
The documentation/link/collaboration check passed offline/frozen in the retained
Linux Python 3.12 Dev Container; the whitespace check was clean. No runtime or
measured theme-contrast acceptance is claimed.

## 2026-10-18: Paired light/dark refinement

The owner requested raising the light design alongside the dark design. One
Chinese light/dark pair now refines the selected overview together, with shared
typography, spacing, title/metadata hierarchy and semantic progress treatment.
The visual handoff records exact images/hashes and remaining generated shading
and light-theme lifecycle-color discrepancies. The pair awaits owner review;
it is not two competing layout options. No product code, browser test or live
request occurred. The specification now explicitly shares geometry and semantics
between themes instead of treating dark appearance as a separate design.
The offline/frozen documentation/link/collaboration check passed in the retained
Linux Python 3.12 Dev Container; whitespace verification was clean. Runtime,
browser and numeric contrast checks were not run for this design-only revision.

## 2026-10-18: Paired visual approval

The owner explicitly confirmed that the paired light/dark treatment meets
expectations. Both exact images in the visual handoff are now accepted overview
targets; earlier dark treatments are superseded. The plan and continuation guide
now resolve to this pair, preserving neutral lifecycle/completion semantics and
shared geometry rather than copying generated shading or incorrect status colors.
This records visual approval only. The written revision-2 amendment, companion
surfaces and sixteen-task plan retain their existing pending-review status.
No W2 product implementation or real endpoint call occurred.
The documentation/link/collaboration check passed offline/frozen in the retained
Linux Python 3.12 Dev Container, and the whitespace check was clean. No runtime,
browser or measured contrast test was run for this approval-record update.

## 2026-10-18: Final written-plan consolidation

After accepting the pair, the owner requested the next step. The existing plan
was consolidated rather than restarting visual exploration or changing execution
method. A five-checkpoint summary maps sixteen sequential tasks to reviewable
deliveries. Self-review checked all seventeen acceptance IDs and cross-task
interfaces; it pinned shared palette/typography starting values, added actual
cross-theme geometry acceptance and made report-figure evidence/denominators
explicit. Archive clock injection now has exact signatures, and parameter escaping
is tested at the rendering boundary rather than claimed by the text catalog.

The continuation guide now states the current decision instead of replaying
superseded design iterations. The revision-2 written amendment, companion surfaces
and plan are presented as one concrete review package. Their approval is pending;
the accepted overview pair and previous sequential execution choice are preserved.
No W2 source implementation, browser acceptance or endpoint request occurred.
The consolidated documents passed the offline/frozen documentation, link and
collaboration check in the retained Linux Python 3.12 Dev Container. Whitespace
verification was clean; no runtime/full/browser/image gate was run for this
documentation-only consolidation.

## 2026-10-18: Execution approval and Task 0 foundation

The owner approved the revision-2 specification, companions and sixteen-task
plan ("确认，请实施"). The current checkout and prepared Linux Python 3.12 Dev
Container are retained, with sequential current-agent implementation and one
independent whole-stage review at the end. No repeated execution-method approval
is needed. Baseline 91544f8 passed all eight fast children and 253 unit/harness tests.

Task 0 adds pure checked presentation choices, strict preference-cookie parsing,
packaged Chinese/English catalogs, safe named-parameter substitution, schemas and
shared semantic color/typography tokens. Catalog parity/count forms and malformed
placeholders fail validation; original source parameters remain plain text.
Presentation does not enter core values/validators. The existing frontend format
gate now includes the new catalog and theme resources. Rendering/UI integration
remains in later tasks; no new interface is claimed here.

Observed RED/GREEN and checks under ignored `artifacts/w2/task0/`:

- Foundation absence was observed before implementation; 37 focused tests now pass.
- First fast gate retained three strict-type findings; these were fixed without
  suppression. Final `fast-3` passed all eight children and 290 unit/harness tests.
- Full Python regression: 491 passed, zero failures/errors/skips, using
  `uv run --frozen python -m pytest`. The earlier bare executable invocation
  failed nine `scripts` imports during collection and remains preserved separately.
- Browser cascade RED: two new probes found system-dark selectors defeating
  print-light tokens; all 22 original browser tests passed in that run. Lowering
  only the system selector specificity fixed the defect. Browser GREEN: 25 passed,
  and prerequisite/cleanup children passed.

Ruling: use the module pytest entry point for whole-repository tests, matching
the checked-in harness — otherwise the root `scripts` namespace is missing —
cost if wrong: an alternative invocation could expose import-path assumptions.
Ruling: verify the isolated system/print token cascade in Task 0 rather than
waiting for full UI acceptance — this caught a real priority defect — cost if
wrong: one extra browser startup for a narrow foundation boundary.

Tasks 1–15 remain pending. These observations do not establish finished bilingual
pages, numeric contrast, offline-document behavior, image acceptance, remote CI
or real endpoint compatibility. No network target or external publication was used.

## 2026-10-18: Task 1 versioned diagnostic contracts

Task 0 delivery commit is `43326db`. Task 1 adds eight data-only frozen wrappers
and nine self-contained packaged schemas, including the independent export-manifest
2.0 / presentation-3.0 boundary. Existing result 1.0, report-view 1.0/presentation
2.0 and export-manifest 1.0 resources are unchanged. Schema validation is closed
to known packaged names and rejects nonfinite JSON, absent recipe/check/file
identities, unknown versions/fields and unsafe inventory paths. Structural
validation does not certify source/recipe/evidence relationships or eligibility.

Ruling: the new workbench/document schemas embed the existing frozen report-view
facts shape under `facts`, with separate composition/version metadata — reuse
checked counts and evidence without rejudging or embedding report HTML — cost if
wrong: old controlled prose/provenance could leak into new presentation. Tasks
11/13 must select/localize controlled labels and sanitize document-only endpoint/
auth-reference context while preserving original source bytes. This boundary and
explicit case/check denominators are recorded in the plan.

Observed checks at `artifacts/w2/task1/`: missing package RED was retained; 27
focused diagnostic/schema/architecture tests passed. The first fast attempt found
one overbroad exception assertion; the test now specifically exercises nonfinite
data inside an otherwise arbitrary protocol body. The final fast graph passed
all eight children with 313 unit/harness tests; full Python regression passed
514 tests, zero failures/errors/skips. No browser/image rerun was needed for
these data-only changes. Whole-W2 UI/portable-flow acceptance remains pending;
no real endpoint or external publication occurred. Task 2 is next.

## 2026-10-18: Task 2 execution implementation identity

Task 1 delivery commit is `f1a1d04`. Task 2 implements canonical identity from
declared package files, core resources, active transitive dependency versions
and Python implementation/major.minor. The packaged manifest/schema are themselves
checked and hashed. New reachable modules/resources, undeclared dynamic local
imports, missing metadata and forged identity digests block verification. Only
explicitly declared standard-library dynamic imports are permitted. Unrebound
type-only imports do not drag presentation into the runtime closure.

Ruling: split core metadata validation into `diagnostics/core_contracts.py` while
retaining the public diagnostic validator — the shared loader would otherwise
couple execution identity to view schemas — cost if wrong: loader dispatch drift.
Existing nine-contract regressions cover that delegation. Later context/recipe
modules must use the core adapter; their presentation annotations are type-only.

Ruling: promote already-locked packaging 26.3 from build tooling to a runtime
dependency — standards-compliant Requires-Dist markers and extras are needed to
record actual dependencies rather than inactive extras — cost if wrong: one
additional runtime/image library. Offline lock/sync changed only the project's
dependency declaration; no package version upgrade or network preparation occurred.

Retained RED/GREEN under `artifacts/w2/task2/`: missing identity/wheel functionality,
then an AST false positive on `re.compile`, and later a real dependency-scope bug
where an application-wide presentation dependency entered the core graph. Fixes
distinguish builtin execution from regex compilation and traverse dependencies
only from actual core external imports. The latter has a specific mutation test.
The first fast attempt also exposed a strict TypedDict/environment mismatch;
explicit validation fixed it without type suppression.

Final `fast-3` passed all eight children with 342 unit/harness tests. Fifty-four
focused identity/contract/architecture/actual-wheel checks passed, including a
fresh process without `.git`, wheel/editable equality, selected/inactive extras,
resource changes and real reverse-dependency rejection. Final full Python run
passed 543 tests with zero failures/errors/skips. Earlier failures and the prior
542-test run remain separate. Documentation/whitespace checks accompany delivery.
No new browser/image acceptance or real endpoint outcome is claimed. Task 3 is next.

## 2026-10-18: Task 3 pre-request provenance

Task 2 delivery commit is `a79102c`. Additive database migration 3 stores checked
plan contexts transactionally without modifying frozen plans or backfilling old
history. Admission binds the actual run ID before queue publication; the child
verifies the stored digest and context before sending requests. Standalone
application execution writes its context after fresh-directory creation and
before the first send. Original result/capture schemas and bytes remain unchanged.

Ruling: preserve the pre-request header and write a separate final
`assessment-context-verification.json` — drift must remain visible even if files
are later restored — cost if wrong: one extra metadata artifact/schema. Import/
export tasks require an unchanged final check bound to exact context/result bytes
for controlled eligibility. Missing or changed verification never certifies it.

Ruling: admission validation runs inside the store transaction after existing-job
idempotency branches — lost-reply retries must return the original admission even
after the installation changes — cost if wrong: a short identity scan holds the
SQLite admission lock. Parent initialization supplies the original context digest;
the child and application independently revalidate before networking.

Ruling: enrich only diagnostic recipes with an explicit pure assertion-category
mapping — frozen plans have no category field, while the new recipe requires it
— cost if wrong: mapping maintenance for future assertions. Unknown IDs fail;
neither old plans nor the stronger new schema are changed to hide the difference.

The synthetic worker test caught completion being visible before the final
verification file existed. Finalization now precedes forwarding result_committed;
the application finally block still records interrupted execution when possible.
The focused provenance/store/worker/migration/application set passed 43 tests.
Initial missing-module, category binding, manifest registration and completion
race failures remain under `artifacts/w2/task3/`. Strict typing found fixture-only
list variance and a test import issue; fixes preserve assertions. Final fast/full
regression passed 555 tests, zero failures/errors/skips. The final fast-6 graph
passed all eight children with 344 unit/harness tests after a fixture-only
lint/type compatibility fix. Documentation/link checks and whitespace checks
passed. No completed W2 UI,
image, remote CI or live result is claimed from this foundation work.

## 2026-10-18: Task 4 installed recipes and full-scope preparation

Task 3 delivery commit is `458c464`. Recipes use installed generators for every
selected case, fixed request parameters, rule/check inventory and effective limits,
excluding endpoint/auth references. Retest preparation regenerates the complete
original profile scope, including previously passed/skipped cases; insufficient
budgets reject rather than dropping cases. Unknown rule revisions or mismatched
execution identities never silently select a current replacement. Changed model,
aliases, capability declarations or limits are explicit semantic changes, and
cannot earn controlled repair badges. Ordinary Web previews now persist generated
contexts without changing their existing HTTP response contract or making calls.

Ruling: keep recipe/source plan validation and add the I/O adapter
`validate_recipe_evidence(recipe, source, root)` — ReportSource contains references
but not a root/raw request bytes, so the planned argument alone cannot establish
capture binding — cost if wrong: one extra adapter call in import/export. Tasks
6/7 must require both. A failing mutation exposed equal-count inventory substitution;
validation now requires the exact recorded case/attempt paths as well as hashes
and semantic request content. Redacted semantic requests cannot claim exact retest.

Eligibility is pure and requires explicit positive source/completeness/recipe/
context/evidence facts and checked identity reasons. Missing proof stays limited.
Missing-feature, forged-request, context-binding and substituted-attempt RED
evidence is retained in `artifacts/w2/task4/`. The focused recipes/cases/runner
checks passed 32 tests before the final inventory test; the Web adapter regression
set passed 43. Latest fast-1 passed all eight children with 360 unit/harness tests.
The final complete Python regression passed 571 tests, zero failures/errors/skips;
documentation/link and whitespace checks passed. Whole-W2 handoff/UI/image checks,
remote CI and live endpoint outcomes remain unobserved.
