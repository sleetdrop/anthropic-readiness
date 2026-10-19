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

## 2026-10-18: Task 5 bounded classic-ZIP handling

Task 4 delivery commit is `c8e6274`. Archive handling preflights the classic footer
and actual central-record count before allocating ZipFile metadata. Only stored/
deflated regular files with unambiguous ASCII relative paths are accepted. ZIP64,
encryption, split archives, links/devices and path collisions are rejected. Every
compressed/expanded/member/JSON/count/directory limit and monotonic deadline has
finite defaults; tests inject small limits and include exact inclusive boundaries.

Raw bounded decompression verifies actual expansion, size, CRC and SHA-256 without
trusting declared expanded sizes. Extraction rechecks the archive and inventory,
publishes each member only after verification, and removes only its newly owned
destination on failure. Existing destinations are never reused or removed. Data
descriptors and empty/chunk-boundary payloads are supported; no code or sockets
are invoked by archive contents. This does not establish a valid assessment;
schema/source/recipe verification belongs to the next import task.

Retained missing-module RED is in `artifacts/w2/task5/red.log`. A nested-directory
permission regression failed at edge-red.log (44 passed/one failure); explicit
0700 creation at each level fixed it, with 45 focused checks passing afterward.
The final 46-test set includes forward-only classic data descriptors. Fast-1
passed all eight children (406 unit/harness tests); full Python regression passed
617 tests, zero failures/errors/skips. Documentation/link and whitespace checks
passed. No new endpoint, remote CI or image result is claimed.

## 2026-10-18: Task 6 read-only import and baseline activation

Task 5 delivery commit is `fcb9502`. Imports copy the original archive into owned
15-minute, session-bound previews, capped at two active previews. Archive and
extracted-file inventories, packaged schemas, source IDs, plan/context/recipe
bindings, final implementation verification and captured request semantics are
checked before granting operations. Old/partial/omitted inputs remain limited.
Preview, activation and read perform no upstream call and create no live job.
Current dependency/code mismatches revoke retest/comparison without rewriting
original bytes. Reopening detects changed archives or extracted evidence.

Identical archives deduplicate by digest. Byte-distinct localized or evidence
delivery variants keep separate records and eligibility; shared external IDs with
different authoritative identities are conflicts. An omitted variant never borrows
the full variant's evidence. Uploaded HTML is data only and is never rendered as
local application content. New view composition remains in Tasks 11/13.

Ruling: add `load_report_source(..., frozen_operations=True)` for imported snapshots
— normal journal reads create a writer lock and require the deliberately omitted
mutable journal — cost if wrong: two read modes require consistent schema/plan/
checkpoint validation. The frozen branch preserves those checks and creates no
local event, timestamp or worker state. RED/GREEN and exact unchanged-file tests
cover imported partial snapshots.

Ruling: use final `committed.json` as activation boundary and SQLite as rebuildable
lookup — checked source and hashed baseline metadata precede marker publication
— cost if wrong: unmarked private staging may remain after a hard crash. Before-
marker failures are inert; after-marker restart may recover a completed commit
whose reply was lost. Tests cover injected publication failure and index rebuild;
no committed baseline files are automatically deleted. Private preview and commit
formats have packaged schemas separate from the public diagnostic allowlist and
execution identity.

Initial focused checks passed 38. Cross-document mutations exposed two accepted
contradictions (undeclared evidence files and inconsistent execution snapshot);
both now reject with specific codes. Missing storage-contract RED and initial
consumer-name correction are retained. A real FIFO input blocked a disposable
subprocess RED; nonblocking descriptor open plus regular-file validation fixes
the input boundary before copying. All logs remain under `artifacts/w2/task6/`.
The first full regression passed 639; subsequent packaged storage checks passed
55 focused cases. Latest fast-2 passed all eight children (408 unit/harness tests).
Full-2 passed 642 tests. A subsequent deadline RED proved that expiration during
metadata validation could still publish a preview; final deadline checks now
guard preview, commit and baseline read. Its two focused late-boundary tests pass.
Full-3 passed 643 tests, zero failures/errors/skips; final fast-4 passed all eight
children with 408 unit/harness tests, including the fixture-only explicit-import
typing correction. Documentation/link and whitespace checks passed. No new image,
remote CI or real endpoint result is claimed.

## W2 Task 7 — portable exports

CLI-facing diagnostic sources and Web exports now share package composition and
the same bounded classic-ZIP writer accepted by import. New context-bearing
exports carry the diagnostic marker, exact source/context/checkpoint/capture
bytes, recipe and a small untrusted-data reading guide. Legacy sources retain
legacy eligibility. Fresh reports are generated from checked facts; uploaded
HTML is never reused. Previews disclose retained target context, and archives
are explicitly not described as anonymized.

Ruling: require `raw_files` in the package composer — parsed ReportSource values
and digests cannot recover exact original result/capture bytes — cost if wrong:
one additional adapter input and binding checks at each caller. The adapters
collect verified artifacts; the composer does not add filesystem paths to the
ReportSource contract.

Ruling: provide an explicit declared-only checkpoint reader for frozen,
evidence-omitted imports — dropping valid retained records when captures were
deliberately excluded breaks partial-source identity and coverage — cost if
wrong: two reader modes must preserve the same structural/accounting checks.
Strict writer/default reads still require actual evidence; the declared reader
does not grant proof or comparison eligibility. Its use requires a frozen
snapshot and an explicit manifest policy. Changing the checkpoint module also
conservatively changes execution identity under the existing file-hash contract.

The missing package module and Web diagnostic marker were observed RED. The
partial/omitted round-trip exposed a dropped checkpoint and was fixed without
changing its bytes or status. Boundary tests cover noncanonical legacy result
bytes, partial/omitted re-export and unchanged source files. An added accounting
test initially mutated only an object_value copy; assigning that copy back
corrected the test input. Logs remain under `artifacts/w2/task7/`. Before resume,
an automatic approval usage-limit rejection prevented a run; after reset the
stopped Dev Container was restored and focused green-4 passed 25 tests. Fast-1
passed all eight children but source edits during that run invalidated its
overall fingerprint; it is not recorded as acceptance.

Final focused-1 passed 67 tests. Fast-2 passed all eight children (408 unit/harness
tests) with an unchanged source fingerprint. Full Python regression passed 654
tests, zero failures/errors/skips. Documentation collaboration and whitespace
checks passed. No new image, remote CI, or real endpoint acceptance is claimed.

## W2 Task 8 — paired check comparison

Task 7 delivery commit is `c98fb68`. The comparison service reads the same
validated local/imported artifacts as export, without executing or reusing
uploaded HTML. Its pure projection joins by case/version, deterministic request,
implementation/rule and assertion/version/category/required identities. Target
endpoint, delivery label and auth references are declared context differences;
changed semantic settings or effective limits remove controlled recovery claims.
All planned cases/checks remain in normalized facts, including missing records.
Paired assertions retain statuses, reasons, expected/actual details and both
evidence reference sets. Unmatched identities and both original denominators are
explicit; neither a missing required item nor an unresolved new check is a pass.

Ruling: package a separate internal comparison-facts schema — the plan specifies
checked normalized facts but leaves their internal JSON shape to implementation
— cost if wrong: common source/evidence definitions must remain consistent with
the frozen public comparison contract. Public diagnostic schema names and core
execution identity are unchanged. Adapter validation precedes pure comparison;
architecture checks now explicitly forbid comparison-to-adapter dependencies.

Ruling: suppress the clean previous-failures headline when a new failure or any
unmatched/gap item remains — the recovery count and its member pairs still show
observed recoveries alongside regressions — cost if wrong: a literally narrower
statement about old failures may be withheld; no observed result is hidden.
Repeated identical check identities are explicitly rejected rather than adopting
last-pass-wins; W2 remains one sample and no retries.

Missing module/service operations were observed RED. The first transition set
passed 21 cases. Later RED exposed borrowing an old `verified` status despite
omitted delivery, and classifying a new BLOCKED check as newly evaluated; both
were fixed. Full synthetic source/imported-source service comparisons preserve
all four planned cases for a one-checkpoint, evidence-omitted baseline. Static
type narrowing and an unused loop variable were corrected after the retained
first fast run. Logs remain under `artifacts/w2/task8/`.

Final focused-2 passed 66 tests. Fast-2 passed all eight children (433 unit/harness
tests) on an unchanged source fingerprint; full Python passed 681 tests, zero
failures/errors/skips. No real endpoint, remote CI or new image acceptance ran.

## W2 Task 9 — standalone CLI operations

Task 8 delivery commit is `bad1b8e`. New `diagnostics import`, `inspect`, `export`,
`retest` and `compare` commands delegate to the shared service. They emit JSON on
stdout, explanatory text on stderr, and preserve operation/run exit meanings.
Successful representation of an incomparable comparison returns zero with an
explicit `comparable: false`; zero is never a compatibility assertion.

Retest requires either `--dry-run` or `--allow-live` before output/source work.
Dry-run creates only `retest-preview.json` in a fresh output directory, with its
own packaged internal schema. The shared `prepare_retest` service regenerates the
entire original selected scope, creates new pre-request context and baseline
lineage, and fills transport-context differences from the checked original target
and explicit local target. Credentials are selected locally. It never executes
an uploaded request. Legacy/unverified sources explain how to configure a separate
current test. CLI export uses disposable private service state and the shared
bounded writer; it does not add an undocumented persistent data directory.

Normal live CLI planning now calls the Task 3/4 preparation path and supplies its
context to the existing application execution hook. No duplicate application
execution path was needed. Replay remains a captured offline observation, not a
new live provenance claim. Presentation flags remain deferred to Task 13.

All seven new/extended acceptance checks were observed RED (unknown commands and
missing normal-run context), then GREEN. The existing actual wheel/no-dev install
test now also denies imports of FastAPI/Jinja/Uvicorn while exporting a diagnostic
ZIP away from the repository; no Web extras are installed in that environment.
An explicitly opted-in disposable loopback peer received exactly four retest
requests. Its unsupported tool response remains a real FAIL/exit 1; it was not
altered to make the live synthetic result green. Baseline/source bytes remain
unchanged. Focused-1 passed 18 new/legacy CLI, replay, serve and installation checks.
Logs remain under `artifacts/w2/task9/`.

Final fast-1 passed all eight children (433 unit/harness tests), unchanged source
fingerprint. At delivery commit `a1ba449`, supplemental full Python regression was
still running. It subsequently passed 687 tests, zero failures/errors/skips,
before any subsequent source changes. No new image,
remote CI, or real endpoint acceptance is claimed.

## W2 Task 10 — authenticated Web diagnosis and preferences

Task 9 delivery is `a1ba449`, with final full-regression documentation in
`d1dbfb2`. The Web now offers one exact POST ZIP-upload route, session-owned
import activation, regenerated baseline facts, original-scope retest previews
through the normal frozen-plan/start path, typed run/baseline comparison and
checked language/theme preference cookies. Import/preview/view/compare do not
send model requests. A disposable loopback retest used the existing start API and
sent exactly four requests; imported HTML was never rendered.

The binary branch retains Host/Origin/session/CSRF checks before reading bytes.
All other mutations remain strict JSON with the existing 65536-byte cap. Uploads
use private owned staging, streamed size/Content-Length checks, one shared
monotonic receipt/validation deadline, two in-flight slots and cleanup on timeout,
disconnect and failure. Slow inspection and file operations run in the threadpool;
the health route stays responsive while two imports await processing.

Ruling: extend shared preview methods with an optional earlier deadline — a Web
upload must not receive a fresh full budget when archive validation begins —
cost if wrong: one optional adapter parameter must remain consistent across CLI,
Web and storage. Existing callers retain their bounded default. A real RED showed
HTTP 200 after expiry; carrying the same deadline yields 408 and no ready preview.
A second RED advanced time during private-preview encoding; the final check now
runs inside the publication transaction before setting state to ready.

Ruling: expose ExportService.verified_source for typed local-run comparisons —
valid artifacts alone do not bind a source to its admitted job/plan — cost if
wrong: duplicate local source reads before comparison. A disposable substitution
of another valid assessment is rejected, rather than compared under the local
run ID. No Web body accepts a filesystem path.

Ruling: add the closed version-2 diagnostic export request contract now and expose
its HTTP rendering path in Task 13 — presentation choices cannot be accepted and
silently ignored before those renderers exist — cost if wrong: new export-option
interaction remains pending until Task 13. Existing export request variants and
all earlier Web schema definitions were structurally compared against the Task 9
commit and remain unchanged. Task 13 must implement the versioned request/response
path; the legacy endpoint currently rejects these extra fields.

Errors use request-local checked catalogs, keeping machine codes unchanged.
Preference cookies are HttpOnly/SameSite=Strict/path=/ with a one-year max-age;
malformed values fall back, and invalid explicit updates reject. No global locale
or browser storage is used. OpenAPI declares binary ZIP input, and TypeScript
contracts name the new data boundaries. Source/recipe judgment identity does not
depend on these UI preferences or Web schemas.

Initial checks retained five feature failures and ten guard passes; the separate
disconnect RED required actual stream consumption. The first green run exposed a
test request missing its JSON media type; correcting that test input retained the
65536-byte expectation. Green-2 passed 18, green-3 passed 19 before the final
publication check. Focused-2 passed 71 Web/security/API/events/import regressions.
Fast-2 found a test-only explicit module-export typing issue; it was corrected
without changing runtime behavior. Logs remain under `artifacts/w2/task10/`.

Final fast-3 passed all eight children (433 unit/harness tests), unchanged source
fingerprint. The 71 focused regressions include both shared-deadline fixes and
the pre-publication expiry guard. The prior full Python baseline remains Task 9's
687 tests; no new full-stage, browser, image, remote CI or real endpoint result is
claimed by this API task.

## W2 Task 11 — independent operational workbench

The workbench now composes operational facts independently of report documents,
with overview, issue, case, comparison and recorded-activity views. It preserves
original dimensions, pending records and unassessed client coverage. Completion
and worker lifecycle remain neutral. Imported baselines are read-only; new retest
configuration retains original profiles while requiring a new local endpoint and
credentials. Actual expected/observed field excerpts come only from verified
observations. Hostile model metadata is escaped once at the real template boundary.

Worker observation checks the owned OS process under the manager lock and records
its own observation time. Recorded upstream activity keeps its original clock.
A terminal publication race is tested against one coherent result generation.
Legacy fragments map to checked case/finding IDs and canonical query links;
ordinary query navigation also works without JavaScript.

Ruling: compose queued workbench facts from the frozen plan with pending states
and absent execution timestamps — no execution record exists yet — cost if wrong:
a second projection path must retain the same group and dimension accounting.
Projection functions perform no resource or filesystem I/O during calls; the
existing report-view schema is cached at module import.

Ruling: list stored baseline metadata without granting proof, then revalidate
source data for inspection, comparison and retest — browsing labels must not
activate stale evidence — cost if wrong: extra reads and unavailable labels for
a damaged local source. Stored metadata alone never grants an eligibility badge.

Ruling: implement the approved existing project rather than scaffold a separate
Product Design prototype — the accepted specification binds the production
repository and shared themes — cost if wrong: visual fixes must fit the existing
server-rendered architecture. Official Heroicons 2.2.0 outline assets and their
MIT license are packaged locally; this data UI needs no raster illustration.
Actual browser fidelity and interaction acceptance belong to Task 12.

Initial feature checks observed missing projection/routes and legacy-link code.
The first page fixture incorrectly tried to acquire a second service owner lock;
fixture ordering was corrected without weakening that lock. Genuine failures
then exposed a reserved catalog count-form suffix, missing template endfor and
English copy mismatch; each was corrected. Focused-1 passed 54 tests, and fast-1
passed all eight children before the final legacy-link addition. Final focused
and fast results are recorded below before delivery. No browser/image or live
endpoint acceptance is claimed by these server-rendered checks.

Final focused-2 passed 54 tests; both legacy-link Node tests passed. Fast-2 exposed
missing strict JSDoc annotations in that new module. After adding checked JSON
access and explicit parameter/tuple types, final fast-3 passed all eight children
with 442 unit/harness tests on unchanged source. No assertions or fixture outcomes
were weakened. Logs remain under `artifacts/w2/task11/`.

## W2 Task 12 — interaction and browser acceptance in progress

Task 11 delivery is `fff8e41`. Its final task-done run passed 41 named
projection/page/recovery/source checks. Task 12 retains the existing DOM controls,
inspectors, disclosure state, selected source text and keyboard focus through
keyed patches of escaped server templates. Local reads never start model work.
The frozen execution preview survives locale/theme changes; export review is
invalidated. Import uses the selected File as a bounded binary body, without
base64 or uploaded-HTML execution. Retest preview uses the shared original-scope
service and normal explicit admission path.

Initial static checks observed the missing state module; six pure state/activity
checks then passed. Initial browser checks observed three missing preference/live
interaction failures and one ordinary-link pass. Actual iteration found and fixed
a navigation/Back race, 1280x800 overview overflow, dynamic preview localization,
a non-scrolling 96-row list, duplicate unnamed complementary landmarks, and a
terminal activity-age display frozen at page load. The first clock test was a
false positive because the initial read had not settled; after waiting for that
read it observed RED, and a local display timer fixed the issue without changing
recorded activity or adding requests. Theme geometry and semantic contrast checks
passed in both locales/appearances; this is not yet whole-task acceptance.

Ruling: continue using server-escaped operational templates for keyed patches,
never replace the workbench/inspector root or render uploaded HTML — one renderer
avoids divergent fact formatting — cost if wrong: extra local read bandwidth and
a bounded five-second persisted-fact refresh. SSE signals changes; persisted
snapshots remain authoritative, with ordered read/sequence/terminal guards.
Worker observation is separate from upstream activity and the local age timer.

Ruling: represent 200-percent browser reflow with a 640x400 CSS viewport at device
scale factor 2, producing the 1280x800 physical-pixel surface — this reproduces
layout viewport and density without changing host browser settings — cost if
wrong: native browser-chrome zoom integration is not exercised. This is an explicit
reflow/scale test, not a claimed observation of native zoom controls.

Ruling: the 96-row scaling test expands only labeled synthetic DOM data through
the real keyed renderer — four formal installed cases remain unchanged — cost if
wrong: this stresses layout/identity retention rather than a future 96-case engine
or schema catalog. No generated row grants a capability or extra coverage.

The first full browser iteration passed 34 and failed 12. The second passed 48
and failed three, including stale legacy copy expectations and missing display of
an interrupted case's last operational state alongside retained checks. Assertions
on request counts, credentials, evidence, original report files and source hashes
remain. Legacy presentation-2 direct-file/matrix/print fixtures are retained; only
Web expectations intentionally move from embedded reports to operational views.
Session errors now use stable internal codes and request-local UI translation;
Node tests still prove bounded read recovery and no automatic mutation resend.
Final browser, visual and quality-gate results remain pending below.

Further visual/interaction verification found a real active-overview overflow:
a natural in-progress partial source was shown as a partial-record warning. The
warning now appears after termination, with active progress retained in counters.
Group/attention typography was raised and table padding tightened against the
accepted pair. Active 2/4 checkpoints and 3/4 requests are produced by a real
owned worker waiting at a controllable synthetic peer, not assigned UI statuses.
The admitted request cap is now the counter denominator: a separate 3-case,
7-request-cap RED/GREEN guards against the equal-default-count masking this bug.

Ruling: encode matrix drill-down as a closed `matrix:group:dimension:state` variant
of the existing filter query — preserve the approved five query parameter names
and select actual matching members — cost if wrong: an additional finite filter
grammar must remain synchronized with matrix navigation. Invalid groups/dimensions/
states reject, and browser Back restores the full list and control value.

Ruling: show one explicitly selected case's field comparison within an issue while
retaining all affected members and evidence — repeated full field blocks recreated
the report-like scroll the redesign removes — cost if wrong: reviewing another
variant needs a case-selection click. The default selection is pinned before live
updates; original facts and assertions are unchanged. Protocol/reason identifiers,
full evidence paths and rule references remain in the technical disclosure.

The third full browser iteration passed 56 and failed one new inspector geometry
check. Its crop capture scrolled the document between measurements; resetting the
same scroll position retained the one-pixel tolerance and passed. Four targeted
inspector/selection checks passed. The two-case matrix filter and 7-request-cap
integration checks passed; focused-1 passed 55 backend regressions before the last
inspector refinement. Fast-1 passed seven children but failed strict Python typing
on repeated nested JSON indexing; binding the checked group member list fixes the
type issue without suppressions. Final fast-2 and browser-all4 remain in progress.

Final browser-all4 passed 58 tests with unchanged source. A subsequent explicit
evidence-failure check observed a loading message left visible while the error
was behind the modal. The dialog now shows failure locally, bounds streamed
display to 256 KiB without splitting a UTF-8 prefix, cancels unread/closed streams,
and recovers a 401 read session once. Both browser faults were observed RED then
GREEN; two new Node reader tests pass. Original evidence bytes are unchanged.
Fast-3 passed all eight children with 442 Python and 20 Node tests.

Browser-all5 passed 59 and failed one terminal-state wait. The retained trace
shows admission at 09:51:33, actual worker start at 09:51:38, completion at
09:51:44.669, and the five-second local read started at 09:51:43 still in flight
when the old 12-second assertion ended. Execution sent exactly four requests.
Ruling: give controlled execution-completion assertions a 30-second wait within
the existing 40-second browser-test budget — process startup plus the approved
five-second observation cadence can exceed 12 seconds under concurrent checks —
cost if wrong: a genuine terminal-display stall can take up to 30 seconds to fail.
No retry, verdict, request-count, evidence or source-hash assertion was weakened.
This is an explicit test observation budget, not an increased endpoint budget.

A further mixed-comparison visual fixture changes only the synthetic peer phase:
stop fields recover, model mismatch persists, a duplicate stop appears, and a
tool request receives HTTP 503. Both executions retain identical configuration
and four-case scope. An initial malformed 200 response produced resolved failures
rather than a verification gap; the fixture now expresses the intended unavailable
verification through an actual 503, without editing runner outcomes or captures.
Final mixed-state, full browser and task-done observations remain pending.

Browser-all6 passed all 61 tests on unchanged source, including the real mixed
comparison. Visual comparison then identified a remaining presentation defect:
52 raw check rows buried the meaningful differences. The new pure grouping
projection presents observation types with separate transition/check counts and
unique affected-case scope, while retaining all 52 original pairs in a native
technical disclosure. Missing checks stay visibly missing; gaps are grouped by
case, rather than assigned a common cause. Group keys and disclosure state survive
language/theme updates. Original assertions and comparison JSON are unchanged.
The grouping test was observed RED then GREEN and verifies input immutability,
member/check accounting, overlap and order independence. The browser grouping
check also observed RED; original-scope and mixed-sample targeted checks passed.

Ruling: group the primary comparison by observation family/transition and group
verification gaps by affected case — the accepted companion calls for a scannable
repair matrix, not a report-sized raw-check table — cost if wrong: distinct variants
need expansion. Every raw member and both record links remain available; this is
presentation grouping, not a root-cause claim or a new compatibility judgment.

Browser-all7 passed all 61 tests on unchanged source, including keyboard group
expansion, preserved disclosure after localization, complete raw pairs and narrow
comparison layout. Focused-2 passed 56 backend regressions. Fast-4 exposed strict
JSON list variance and a reused tuple/string variable; fast-5 passed typing but
caught unnecessary comprehensions. Typed list extension preserves the same output
without suppressions; final fast-6 is running. The previous full Python baseline
remains Task 9's 687 tests; whole-W2 packaging, images and final review are pending.

Task 12 final acceptance: fast-6 passed all eight children, 443 Python tests and
20 Node tests; focused-2 passed 56 backend regressions. After the lint-only typed
list rewrite and local commit 0abc160, taskdone-browser passed all 61 Chromium
checks in 3.3 minutes on unchanged source; prerequisite and cleanup checks passed.
The operational visual record is design-qa.md. Tasks 13–15 remain unaccepted;
no full-W2 Python/image/remote CI or real endpoint result is implied.

### Task 13 — standalone documents (in progress)

BASE 30d8696. Initial 14 document/CLI checks observed RED. The first implementation
passed seven projection/render checks; a file-edit boundary accidentally omitted
reporting entry points and was restored from the preceding committed version.
Green-2 passed 14; export RED then Green-4 passed 17. A foreign-comparison binding
check observed RED and now rejects a comparison whose after source differs from
this document's run/result/checkpoint identity. Green-5 passed 18.

The first 12 direct-file browser checks failed because template formatting added
whitespace/semicolon bytes around inline assets, invalidating pre-template CSP
hashes. Hashing the final trusted asset text retained the restrictive policy;
browser-doc2 passed all 12 combinations of locale, initial theme and script mode,
with zero attempted network calls/errors and light printing in the selected
language. Strict typing passed 174 files after the first typing corrections.

Comparison export checks observed RED in CLI/shared service and HTTP. New explicit
comparison inputs bind to the current source, and the workbench's chosen baseline
uses the same owned-source resolver as comparison. The first browser-comparison
attempt assumed a nonexistent ZIP checkbox; the existing form selects HTML/MD/JSON
and always delivers the bundle. Correcting that fixture assumption produced one
passing actual two-run mixed-comparison export, eight synthetic model requests
unchanged, five report groups and all original pairs. A legacy self-comparison
correctly remains incomparable; the HTTP test now asserts that rather than
expecting a fabricated persistent-failure count. Green-7 passed 21 checks.

Markdown table separation and the presentation-3 JSON Content-Disposition name
were observed RED and fixed. A subsequent locale switch check observed untranslated
theme options; its correction is awaiting rerun. Identical excerpt grouping also
observed RED; it retains every original case/evidence member. A packaged version-2
document-manifest contract is being added after an unknown-contract RED; the
frozen report-view/result/export-manifest-1 contracts remain unchanged.

Ruling: omit the operational execution object and timing-only figures from the
presentation-3 document facts, retaining actual summary/attempt durations and all
case/check facts — the embedded operational target has required private routing
fields, and no current finding is explained by its timing boundaries — cost if
wrong: readers use the original package snapshot to inspect detailed spans. No
start/finish boundary or latency is synthesized.

Ruling: keep the existing export-request/response and manifest-1 path as explicit
presentation-2 compatibility, and add checked diagnostic-export variants for
presentation 3 — accepting preferences without honoring them would be misleading —
cost if wrong: both readers/render paths must remain covered. Fresh CLI/file reports
and current Web controls select presentation 3; original bytes remain unchanged.

The account limit interrupted an approval review before the proposed command ran;
no action was executed on that rejection. After the owner confirmed reset, the
ordinary approved container checks resumed. No bypass, real endpoint call,
external write, image acceptance or independent review occurred.

Fast-2 passed all eight children, 451 Python tests and 20 Node tests. Focused-1
passed 67 and failed one stale presentation-2 filename assertion for a new CLI
retest; it now expects document-view.json/presentation 3.0, retaining all four-call,
lineage, source-result and FAIL exit assertions. Browser-all1 passed all 73 tests
in 4.4 minutes with unchanged source and successful cleanup, including selected
comparison export and offline in-file theme/language changes.

A separate ignored probe first failed on its own import path, then observed a
real privacy collision: globally replacing a credential-reference name FAIL or
example rewrote verdict/model strings. Two formal tests observed RED. Credential
references are now omitted by configuration field, while only complete endpoint
addresses are scrubbed from prose. Comparison credential-reference deltas are
explicitly omitted; original source files are unchanged. This corrects presentation
without altering the source judgments. Final rerun is pending.

Ruling: retain legacy in-memory renderers as presentation 2 when no presentation
option is supplied; an explicit presentation-3 request without a bound ReportSource
raises document_source_identity_required — a RunResult alone has no observed
source-file digest — cost if wrong: library callers must load a checked source
and use the new document builder for presentation 3. CLI/file/export entry points
already use that source boundary and default to presentation 3.

Final Task 13 iteration: focused-2 passed 31. Fast-3 passed all eight children
(453 Python and 20 Node). Browser-all2 passed 73 and failed four newly added narrow
checks. The retained overflow attachment identified MAIN 479px and FOOTER 457px
against a 390px viewport/346px content area; wrapping the long footer digest fixed
it without hiding content or widening tolerances. Browser-doc-final passed all 16
report combinations, including narrow keyboard scrolling and measured contrast.
Fast-4 again passed all eight children with 453 Python and 20 Node tests;
focused-final passed 32, including the formal six-request presentation-invariance
check. The refreshed owned preview has no active jobs and retains its original
synthetic records; actual GUI preview/generation produced version-3 downloads.
The final post-commit whole-browser task-done run remains pending.

Task 13 completed at source commit 5780956. The post-commit task-done run passed
all 77 Chromium tests in 3.8 minutes on unchanged source; prerequisites and cleanup
passed. Final fast-4 passed eight children (453 Python/20 Node), and focused-final
passed 32. No original result/evidence/legacy golden was changed. Tasks 14–15,
whole-W2 image/full-Python acceptance and the sole independent review remain open.
