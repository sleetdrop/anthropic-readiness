# Diagnostic Workbench and Portable Repair Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Repository instructions require sequential implementation by the current agent and one independent whole-stage review at the end; do not create per-task implementer agents.

**Goal:** Deliver a Chinese/English, light/dark diagnostic workbench and a portable, evidence-backed colleague/agent repair-verification loop over the four installed cases.

**Architecture:** Keep one runner and authoritative result/evidence reader. Add versioned portable metadata, bounded archive/storage adapters and pure eligibility/comparison projections. Workbench views and standalone documents compose the same checked facts independently; CLI and Web call the same diagnostic services.

**Tech Stack:** Existing Python package, FastAPI/Jinja, SQLite, stdlib ZIP/hash/filesystem support, packaged HTML/CSS/JavaScript with strict JSDoc/TypeScript checks, existing Node/Chromium harness and Docker images. No SPA, archive execution, hosted service or model judge. Task 2 promotes already-locked packaging 26.3 from build tooling to a runtime dependency for standards-compliant Requires-Dist marker/extras parsing; no package version upgrade or network preparation was needed.

**Spec:** [W2 specification revision 2](../specs/2026-10-18-diagnostic-workbench-design.md), approved with this plan on 2026-10-18.

**Status:** owner-approved for sequential implementation in the current session on 2026-10-18 ("确认，请实施"). Revision-2 written scope and companion compositions are included. Tasks 0–5 are complete; Task 6 is next, Tasks 6–15 remain pending. Existing task numbers are retained for traceability.

## Owner review summary

The accepted overview pair is the visual baseline for one shared light/dark
system. Companion issue/comparison/document surfaces inherit that system while
keeping their different operational and reading purposes. The completed review
covers the revision-2 written amendment, those companion compositions and this
plan together; do not request another choice among superseded overview images.

| Checkpoint | Tasks | Reviewable delivery |
| --- | --- | --- |
| Presentation and trustworthy assessment metadata | 0–4 | Checked Chinese/English catalogs, paired theme tokens, immutable identities and full-scope retest preparation. |
| Colleague handoff and CLI/Web operations | 5–10 | Bounded import/export, explicit local retest preview and paired-check comparison. |
| Quiet interactive workbench | 11–12 | Single-screen overview, issue/case inspectors, comparison and activity views in both languages/themes. |
| Independent assessment documents | 13 | Offline HTML/Markdown, coverage/difference matrices, evidence-linked findings and agent entry point. |
| Delivery acceptance | 14–15 | Isolated repair/new-failure scenario, package/image checks and one independent whole-stage review. |

Keep the previously chosen execution method: the current agent implements
sequentially in the existing checkout/prepared Dev Container. Every task retains
meaningful RED/GREEN evidence and a scoped local commit. This plan approval does
not authorize registry publication or real-endpoint requests.

## Global Constraints

- Use the checked-in Dev Container, Linux/Python 3.12. Preparation: `uv sync --locked`. Run verification with `UV_OFFLINE=1` and `uv run --frozen`.
- Source, comments, machine fields, new documents and commits are English. Product UI and reports default to Simplified Chinese.
- Supported presentation locales are `zh-CN` and `en`, default `zh-CN`. Themes are `light`, `dark`, `system`, default `system`. These options never change requests, rules, evidence, recipe identity or comparison semantics.
- Four formal cases only; repeat remains one and retry zero. Full original selected-profile scope is retained for retests. Do not import the private assessment into product fixtures.
- Preserve result 1.0, historical captures, original evidence bytes, required-profile accounting and frozen Stage A artifacts. New contracts are packaged resources with their own identities.
- Keep framing/domain/validators pure; HTTP, archive, filesystem, package metadata and SQLite work belong to adapters.
- Import, configuration, preview, comparison, browsing and export make zero upstream requests. Explicit start admits a finite request/time/size-bounded live plan.
- At 1280x800 and 1440x900 CSS pixels at 100% zoom, the overview exposes global state and its attention/action area without document scrolling. At 200% zoom and narrow widths, readable reflow takes precedence.
- Application tabs: Overview, Issues, Cases, Compare and Activity. Completion is neutral; compatibility PASS is green. Unknown/unassessed outcomes remain distinct.
- New report presentation is 3.0. Diagnostic-package, retest-recipe, assessment-context, imported-baseline and comparison schemas start at 1.0. Do not silently reinterpret old exports.
- Monetary limits are not implemented. Do not expose fake prices, repeated-sampling controls, arbitrary case selection or whole-Claude-Code certification.
- Local commits are part of delivery. Remote writes, publishing and real endpoint work are not authorized by this plan.
- One independent whole-W2 review follows implementation, then one recorded author correction pass as needed. Prior completed W1/Stage A reviews are not reopened.

## Review Focus

1. A code change retains its human revision label: compare implementation digests, not labels, and refuse a verified same-test retest when identities differ. Owned by Tasks 2, 4 and 8.
2. A valid ZIP contains hostile paths, misleading HTML or a huge expansion: validate and stream with finite limits, never execute/serve uploaded presentation, and preserve the normal local request boundary. Owned by Tasks 5, 6 and 10.
3. A retest changes aliases, model, scope or deadlines: show the condition change and do not manufacture a recovery or hide unmatched checks. Owned by Tasks 4, 8 and 9.
4. A run finishes, loses its worker or changes language/theme while the user reads evidence: preserve focus/context, bind views to a consistent result generation, and distinguish service connectivity from upstream progress. Owned by Tasks 0, 11 and 12.
5. A colleague has a legacy/partial/evidence-omitted package or a localized export of the same source: preserve useful reading, distinguish export variants from source conflicts, and never merge proof status or start requests silently. Owned by Tasks 6, 8, 10 and 14.

## Design source and fixture story

Selected structural reference: `artifacts/w2/visual-20261018/exec-4e87de9b-ef7e-4626-ac6e-105bedcae9ed.png` (the first displayed concept). Preserve its application rail, group progress and attention column. The owner-approved current overview visual targets are light `artifacts/w2/visual-20261018/exec-1775e6e7-1d1e-4f9f-a2c3-28ca19665826.png` and dark `artifacts/w2/visual-20261018/exec-771e5e11-ce7f-493f-bae8-d81bbbc96698.png`. Share typography, spacing and geometry, keep the target alias as title and model secondary, and implement neutral execution-completion indicators even where generated light-image colors differ. Earlier dark images are superseded. See the visual handoff for token proposals, exact hashes and image limitations.

Task 0 starts from these semantic color pairs; Tasks 12/13 measure rendered
contrast and may record justified token adjustments without changing semantics.
Divider tokens are decorative separators, not substitutes for focus/control
boundaries that require stronger contrast.

| Role | Light | Dark |
| --- | --- | --- |
| Page / rail | `#fafbf9` / `#f1f3f0` | `#202226` / `#191b1f` |
| Primary / secondary text | `#20272b` / `#59636b` | `#eeefed` / `#b1b5bd` |
| Divider / selected navigation | `#d7dcd8` / `#e6ede7` | `#3c4047` / `#2c3035` |
| Navigation/focus accent | `#355e50` | `#a6c8b7` |
| Progress fill / track | `#737e7b` / `#e2e6e2` | `#abb1b8` / `#41464d` |
| Check PASS / FAIL / waiting | `#326950` / `#a84a32` / `#8c650d` | `#a6c8b7` / `#eca798` / `#e3c18b` |

Use shared system/CJK sans-serif typography, a separate monospace stack for raw
fields/code, a 16px body baseline, 14px secondary labels, 28px run title and 40px
tabular headline numerals at normal desktop scale. Responsive compact/reflow
rules apply equally to both themes. Document reading typography remains distinct;
it shares semantic colors and accessible status expression, not dashboard density.
Use flat tokens rather than generated shading; add no remote font dependency.

Companion images are design references, not golden runtime outputs. All copy/counts come from deterministic fixtures. The report's matrix explicitly labels its counts as passing cases over assessed cases; do not reproduce ambiguous `FAIL 0/4` notation. The overview must not display the full catalog as its main list when the catalog grows.

Use two isolated synthetic peers and fresh data roots. Baseline has missing stop fields and a response-model-policy failure. Retest corrects the stop fields, retains the model-policy failure and adds a stream-lifecycle failure in one streaming case. All four behavioral tasks still complete. Exact assertion transitions must come from existing validators, not fabricated report records. Larger lists are separately labeled presentation stress fixtures and never advertised as installed tests.

## File and service boundaries

| Files | Responsibility |
| --- | --- |
| `presentation.py`, `localization.py`, `resources/locales/*.json`, `resources/themes.css` | Pure presentation choices, packaged checked catalogs and theme tokens, independent of judgment logic. |
| `diagnostics/models.py`, `diagnostics/reduction.py`, `diagnostics/comparison.py` | Pure value types, eligibility, paired-check transitions and counts. |
| `diagnostics/contracts.py`, packaged schemas | Strict versioned diagnostic contract loading/validation. |
| `diagnostics/identity.py`, packaged identity manifest | Installed implementation/resource/dependency identity, with no archive-supplied executable code. |
| `diagnostics/recipes.py` | Installed-plan recipe generation and exact-condition retest preparation. |
| `diagnostics/archive.py`, `diagnostics/store.py` | Bounded ZIP inspection/extraction and immutable imported baseline/preview persistence. |
| `diagnostics/service.py`, `diagnostics/context.py` | Shared CLI/Web orchestration and pre-execution identity/lineage sidecars. |
| `diagnostics/cli.py` | New command parser/dispatch without importing Web extras. |
| `web/diagnostics.py` | Narrow authenticated upload, import, retest-preview and comparison routes. |
| `workbench.py`, `web/workbench.py`, `resources/web/workbench-*` | Checked operational projection, templates and focused browser updates. |
| `documents.py`, `document_rendering.py`, `resources/report-v3.*` | Presentation-3 standalone documents over shared facts. |
| Existing runner/application/job/report/export adapters | Minimal integration preserving old result and lifecycle contracts. |

Keep `web/api.py`, `web/pages.py` and `resources/web/app.js` from absorbing every new feature. New routes/browser controllers own the new flow. Add explicit architecture checks for the pure modules and CLI independence.

Unless a repository-root path is shown, Python/resource module paths in task
file lists are relative to `src/anthropic_readiness/`. Test/script/document paths
are repository-relative. The companion design rationale and artifact mapping are
in [the visual handoff](../../reviews/2026-10-18-diagnostic-workbench-visual-design.md).

## Contracts and integration decisions

### Checked values and schemas

New `diagnostics/models.py` defines frozen wrappers `ImplementationIdentity`, `RetestRecipe`, `AssessmentContext`, `DiagnosticPackage`, `BaselineRecord`, `Comparison`, `WorkbenchView` and `DocumentView`, each with `document: JsonObject`. They are data only. Adapters validate documents before construction; pure projections return values validated at their application boundary. No Path/HTTP/SQLite/schema-resource I/O enters pure wrappers/reduction/comparison.

`diagnostics/contracts.py` exports `validate_diagnostic(document: JsonObject, name: str) -> None` using packaged schemas, never a schema named or loaded by an archive. Schema names are `implementation-identity`, `retest-recipe`, `assessment-context`, `diagnostic-package`, `imported-baseline`, `comparison`, `workbench-view` and `document-view`.

Also package `export-manifest-v2.schema.json` with schema version 2.0 and presentation version 3.0; retain `export-manifest.schema.json` for legacy 1.0/2.0 deliveries. Readers dispatch by version instead of weakening the old const.

- Identity records the schema/semantic revision, sorted package-file digest map, installed relevant distribution versions, Python implementation/major.minor and its canonical content digest.
- Recipe records the original selected profiles/cases/checks, effective limits, API/betas, model/alias policy, capability exclusions, normalized generated requests and implementation/rule identities. It contains no URL, secret, credential reference, executable code or free-form request template.
- Context binds run ID, frozen plan fingerprint, recipe digest, baseline source identity if any and declared changes. It is a sidecar, not a new result field.
- Package binds the source result/partial records, context/recipe and export inventory digests, with explicit evidence delivery and omissions. The package marker is `diagnostic-package.json`; the existing `manifest.json` remains an export manifest.
- Baseline records local UUID, archive digest, external run/assessment IDs, source result digest, import time, relative artifact root, eligibility and reason codes. External completion time is never import time or a local job event.
- Comparison records both source identities, condition deltas, paired check transitions, unmatched checks/cases, baseline/new/matched denominators, evidence quality and scoped summary. Finding labels are presentation, not join keys.
- Workbench/document views have schema version 1.0 and independently versioned presentation metadata. Existing report-view 1.0 remains readable; do not change its const in place.

The new workbench/document contracts carry existing checked report-view 1.0 facts
under `facts`, using a self-contained copy of that frozen schema boundary. Their
root composition and presentation metadata are new and independent. No report
body is embedded into application templates. Task 11 selects operational fields;
Task 13 localizes controlled prose and removes raw endpoint/auth-reference context
from document presentation without rewriting the original source. Comparison
coverage explicitly names check and case denominators; transition counts state
their unit as checks. These schema-valid structural fixtures alone do not prove
an eligible baseline; source/recipe/evidence relationships remain service checks.

`presentation-options`, `preferences` and `localization-catalog` schemas, created
by Task 0, also start at 1.0. Catalog documents have `schema_version`, `locale`
and a `messages` map with stable machine keys and text values. View/export
metadata records locale, initial theme and available locales;
recipe, original result and paired-check facts do not. Exclude localization/theme
assets from core execution identity by keeping their imports in adapters/renderers.
Export-manifest 2.0 includes the selected presentation options. A changed localized
view/archive hash is expected and is not a changed source-result identity.

Schema structural validation is necessary but insufficient: validate recipe/result/plan/request relationships and reference ownership in the services that have those inputs. A complete final result can still contain skipped or unresolved required checks; result completeness is not compatibility completeness.

### Implementation identity

Include `__init__.py` and the new `diagnostics/recipes.py` and
`diagnostics/context.py` roots when they are introduced; eligibility-critical
metadata generation belongs to the checked closure too. The manifest cannot
certify itself merely by recording a revision label.

Add `resources/diagnostic-identity.json` as a versioned, allowlisted dependency manifest. Seed its package closure from request generation, runner, result validation, captures and Messages/SSE validators. Enumerate `cases.py`, `config.py`, `contracts.py`, `context.py`, `credentials.py`, `evidence.py`, `json_validation.py`, `models.py`, `requirements.py`, `runner.py`, `schema.py`, `sse.py`, `transport.py`, validation modules and imported operational value/port modules; include any additional transitive internal dependencies discovered by the closure check. Include packaged core rule/schema resources used by those modules. Do not include Web/templates/report presentation merely because they share a distribution.

The identity check traverses static package imports from these roots and rejects an unlisted reachable module/resource or undeclared dynamic local import. Permit only explicitly enumerated stdlib dynamic calls; no archive controls this manifest. Record installed non-stdlib dependencies reachable from those roots, including their installed transitive requirements, using distribution metadata; missing metadata prevents eligibility. Do not use Git HEAD, a wheel path, frontend hash or human version label as execution identity. Test installed wheel and editable checkout equivalence under identical bytes/dependencies. A report-only change must not change core identity; a validator-byte or relevant-dependency change must.

Core metadata validation lives in `diagnostics/core_contracts.py`, with the
existing `validate_diagnostic` public adapter delegating core names to it. Future
recipe/context modules import the core adapter and use unrebound guarded
`TYPE_CHECKING` imports for presentation-only annotations. This keeps view schemas
out of execution closure. The internal manifest has its own packaged schema and
is itself hashed. The repository resource check verifies its declared source root;
only `installed_identity()` is used by assessment code. Parse dependency markers
and selected transitive extras with packaging; ignore inactive extras, never
install/import a dependency discovered from metadata. Check both actual wheel
installation and a no-Git fresh process in the recorded verification.

### Archive and local storage limits

Use stdlib ZIP with ZIP_STORED/ZIP_DEFLATED regular files only. Reject encrypted members, links/devices, directory ambiguity, non-ASCII or absolute member paths, backslashes, empty/dot/parent components, duplicate names and case-fold collisions. Allow only `[A-Za-z0-9_./-]` safe relative names of at most 240 bytes. No `extractall()` or path-derived execution.

Limits: compressed upload 256 MiB, expanded total 512 MiB, one expanded member 256 MiB, one parsed JSON document 64 MiB, 4096 members, 64 MiB central-directory metadata. Enforce actual streamed byte counts in addition to declared ZIP sizes, CRC/hash validation and a 60-second monotonic processing deadline. Check the ZIP footer/count/directory size before constructing `ZipFile` to bound central-directory allocation; support a bounded classic ZIP only, rejecting ZIP64/split archives in W2. Tests set smaller injected limits for boundaries rather than allocating hundreds of MiB. Export must respect the same supported envelope and reject a package that its importer cannot read.

Use `diagnostics/previews/<uuid>/` and `diagnostics/baselines/<uuid>/`; mode 0700 directories and 0600 files. Import previews are session-bound, expire after 15 minutes and are capped at two per local service. Cleanup removes only expired/uncommitted owned preview directories. Never automatically delete committed baselines. Store an immutable original archive and checked source files; `index.sqlite3` is a rebuildable local index with a uniqueness constraint on archive digest. Deduplicate identical archives. Retain different archives as separate records; link matching authoritative result/context/recipe identities as export variants, and label conflicting external IDs only when authoritative identities differ. Never merge evidence delivery/eligibility across variants. Atomic activation publishes no partially checked baseline. Reopen/revalidation detects later corruption rather than trusting an old green badge.

### HTTP boundary

Add `POST /api/v1/preferences`, a normal small JSON mutation protected by the same
session/Origin/CSRF rules. Its checked body contains locale/theme; set only the
HttpOnly, SameSite=Strict, path=/ `readiness_preferences` cookie with max-age
31536000 and strictly parsed format `v1.zh-CN.system` (supported values only).
Malformed cookies fall back to `zh-CN`/`system`; unsupported explicit updates are
rejected. No credentials/content enter the cookie or browser storage. SSR applies
`lang`/theme before CSS paint. Both catalogs are packaged/bootstrap data, never a
translation network call. Locale is request-local; do not use process-global
`locale.setlocale` or mutate argparse/framework global translation functions.

Keep the 64 KiB JSON body limit and all Host/Origin/session/CSRF protections. Add a single binary upload route `POST /api/v1/diagnostics/imports/preview` with `Content-Type: application/zip`; stream to an owned file, never `request.body()` or base64 JSON. Only that exact route receives the binary bounded-body branch. No multipart dependency or general content-type bypass.

Other new routes use packaged JSON contracts:

- `POST /api/v1/diagnostics/imports/commit` with `preview_id`.
- `GET /api/v1/diagnostics/baselines/{id}` for regenerated read-only facts/eligibility.
- `POST /api/v1/diagnostics/retests/preview` with baseline ID and explicit local target.
- `POST /api/v1/diagnostics/comparisons` with typed local run/baseline references.
- `GET /api/v1/runs/{id}/workbench` for a generation-consistent projection, including observed worker state.

HTML routes include `/imports`, `/baselines/{id}` and `/new?baseline={id}`.
The last opens configuration with a blank local endpoint and no credentials,
showing source test conditions as reference. Existing local runs can also be
selected as comparison baselines through typed run references; import is not
required merely to compare two runs already stored on this machine.

Responses use existing sanitized error handling. Add exact codes for archive limits/integrity, unsupported identity, expired import preview, context mismatch and incomparable conditions. Uploaded file names/content never become reflected exception text. No Web request accepts arbitrary host filesystem paths.

### Preview, admission and execution identity

Keep `FrozenPlan` and plan 1.0 unchanged. Add an optional schema-validated context to `JobStore.create_plan(..., context: JsonObject | None = None)`, persisted in a new transactional `diagnostic_plan_contexts` table, and `JobStore.get_plan_context(plan_id: str) -> JsonObject | None`. New Web planning always supplies it. Old plans without it remain explicitly legacy; do not backfill proof for a historic run.

`JobManager.submit` validates a present context against the current installed identity before admission. `JobStore.admit` binds that context to the newly allocated run ID and atomically writes `assessment-context.json` under the job root before publishing the transaction/queue admission. Existing idempotency returns the same context/job. The worker validates the sidecar again before its first request; failure is an execution error with zero requests.

For standalone CLI, `run_assessment` gains an optional `assessment_context: JsonObject | None = None` keyword and installs a `ContextObserver`. Its `begin()` runs after `execute_run` creates its fresh output directory and before any request; it binds the actual run ID and persists the context inside the output directory, then delegates observation. Do not pre-create that output directory or weaken `create_run_directory`. CLI planning always builds new metadata; direct legacy core calls without it remain legacy. Check core identity before execution and after finalization; changed-on-disk identity invalidates portable eligibility while preserving raw results.

Recipe verification compares regenerated requests excluding only URL/auth and explicit display/transport context. W2 permits a different endpoint/build label, reported prominently. Changed model/API/betas/aliases/exclusions/scope/semantic identities cannot receive controlled recovery badges. Changed time/size/event limits conservatively make the whole comparison incomparable in W2. Requests remain finite and profile-required membership stays complete.

The pre-request context stays immutable. After execution, write the separate
packaged-schema-validated `assessment-context-verification.json`, binding its
`context_sha256` to the exact header bytes, the expected/observed implementation
digests and `identity_status` (`unchanged`, `changed`, `unavailable`) with reason
codes. A missing final check is not verified identity. Tasks 6/7 require an
unchanged matching record for controlled baseline eligibility and retain it in
exports; changed/unavailable records preserve observed result/evidence bytes.
Task 3 adds this private core schema and hashes it with metadata-generation code.
The application execution adapter joins the identity roots when it owns finalization.

Admission validation runs inside `JobStore.admit` after its existing-job branches,
so `JobManager.submit` reaches the same guarded transaction without breaking
idempotent replies. The worker and `ContextObserver.begin` revalidate independently.
Migration 3 adds the context table; old plans are not backfilled with proof.

Frozen execution plans retain their original assertion fields. The pure explicit
`diagnostics/inventory.py` mapping adds categories only to new diagnostic recipes;
unknown assertion IDs fail rather than guessing. Worker initialization carries
the original stored context digest, not unbounded metadata, so a missing/replaced
sidecar is rejected before requests. The final verification is written before
forwarding `result_committed`, since that event exposes terminal state to readers.

Recipe/source binding uses `validate_recipe_binding` for regenerated source-plan
semantics and `validate_recipe_evidence(recipe, source, root)` for bounded hash/
semantic checks of actual captured requests. ReportSource has no file root or raw
request bytes. Tasks 6/7 must require both checks; exact recorded case/attempt paths
are required, not only equal request counts. `baseline_eligibility` accepts explicit
source_valid, complete, recipe_valid, recipe_bound, context_verified and
evidence_verified booleans plus identity_reasons; missing proof blocks controlled
operations. Changed installed identities block same-test preparation; target
semantic changes return a declared difference document without repair eligibility.

### CLI interface and exit semantics

Add `--language {zh-CN,en}` and `--theme {light,dark,system}` to report-producing
commands (`run`, `replay`, `report`, diagnostic `export`, `retest`, `compare`).
`add_presentation_options(parser: argparse.ArgumentParser) -> None` belongs to the
CLI adapter and returns no execution configuration. Pass a `PresentationOptions`
value only to report/export functions. Command names, English help grammar and
machine stdout keys/status/error codes remain stable; these flags do not enable
terminal color or translate captured data. Defaults are `zh-CN` and `system`.

Add `diagnostics import --package PATH --data-dir PATH`, `diagnostics inspect --baseline ID --data-dir PATH`, `diagnostics export --input RESULT --out PATH [--include-evidence]`, `diagnostics retest --baseline ID --data-dir PATH --target PATH --out PATH [--dry-run | --allow-live]` and `diagnostics compare --baseline ID --data-dir PATH --input RESULT --out PATH`.

Import performs the same inspection/activation service as Web but is an explicit one-command local action. Inspect/export/compare are offline. Retest without either opt-in flag returns 2 and makes zero requests; dry-run writes only its preview document, not an assessment or reports. Live retest returns the existing runner exit code and automatic HTML/Markdown/JSON. Import/inspect/export/compare return 0 for a successfully represented operation, including an explicitly incomparable comparison; malformed inputs return 2 and unexpected internal faults 4. Comparison JSON states comparability explicitly; zero never means compatible. Existing commands keep their meanings and CLI imports no FastAPI/Jinja module.

## Sequential tasks

Each task starts with a meaningful failing test, implements only its boundary,
reruns that test and relevant local regressions, and ends with a scoped local
commit. Commands below execute inside the prepared Dev Container. Record RED and
GREEN evidence in ignored `artifacts/w2/`; do not erase failures. No per-task
independent reviewer or implementer agent is dispatched.

### Task 0: Shared bilingual catalogs and appearance foundation

**Files:** Create `src/anthropic_readiness/presentation.py`, `src/anthropic_readiness/localization.py`, `src/anthropic_readiness/resources/locales/{zh-CN,en}.json`, `src/anthropic_readiness/resources/themes.css`, `src/anthropic_readiness/resources/schemas/{presentation-options,preferences,localization-catalog}.schema.json`, `tests/unit/test_localization.py`, `tests/unit/test_presentation_options.py`; modify `scripts/validate_resources.py` and `pyproject.toml` architecture/resource checks.

**Interfaces:** `Locale = Literal["zh-CN", "en"]`; `Theme = Literal["light", "dark", "system"]`; frozen `PresentationOptions(locale: Locale = "zh-CN", theme: Theme = "system")` with `to_json() -> JsonObject`. Pure `presentation.py` validates supported values without I/O. `load_catalog(locale: Locale) -> Mapping[str, str]` and `translate(catalog: Mapping[str, str], key: str, params: Mapping[str, str | int | float] | None = None) -> str` live in the resource adapter. Named placeholders cannot use attribute/index expressions, conversions or arbitrary format execution.

- [x] Write tests asserting identical key sets and named parameters in both catalogs, complete singular/plural message forms, strict option/cookie-value enums, missing-key/parameter errors and original protocol/code/data values untouched. Parameters remain ordinary text, never trusted markup; HTML escaping is tested at the actual template boundary in Task 11. Unknown historical reason codes receive a localized generic explanation plus explicitly raw source text; they are not missing authored keys.
- [x] Run `UV_OFFLINE=1 uv run --frozen pytest -q tests/unit/test_localization.py tests/unit/test_presentation_options.py`; retain RED before the new foundation exists.
- [x] Implement small packaged catalogs and semantic theme tokens for background/surface/text/muted/border/status/code/focus/selection/native controls. Use CSS media queries for system appearance, explicit selectors for overrides and forced light print tokens. Keep English command help and original data outside catalog translation. No translation service, i18n runtime dependency or browser storage is added.
- [x] Rerun focused tests and architecture/resource checks. Verify strict catalog validation rejects a deliberately removed key or mismatched placeholder. Contrast and actual layout/interaction are verified in Tasks 12/13, not claimed from token declarations.
- [x] Commit: `feat: define bilingual presentation catalogs and theme tokens`.

### Task 1: Versioned diagnostic contracts and pure values

**Files:** Create `src/anthropic_readiness/diagnostics/{__init__,models,contracts}.py` and the nine schemas listed above under `resources/schemas/`. Modify `scripts/validate_resources.py`, `pyproject.toml`; create `tests/unit/test_diagnostic_contracts.py`.

**Interfaces:** Produce the eight frozen document wrappers and `validate_diagnostic(document: JsonObject, name: str) -> None`. Consumers use these names throughout this plan.

- [x] Write `test_contract_versions_and_required_identities` asserting each valid v1 fixture validates, missing recipe/check/file identity is rejected, unknown version/additional properties are rejected, and existing result/export/report-view fixtures still validate unchanged.
- [x] Run `UV_OFFLINE=1 uv run --frozen pytest -q tests/unit/test_diagnostic_contracts.py`; retain the failure for missing diagnostic contracts.
- [x] Implement wrappers, packaged schemas, relational-validation entry boundaries and pure-module import prohibitions. Register resources without editing frozen schemas.
- [x] Rerun the focused file and `tests/unit/test_schemas.py tests/harness/test_architecture.py`; validate installed-resource coverage in the packaging task later.
- [x] Commit: `feat: define versioned diagnostic handoff contracts`.

### Task 2: Installed implementation identity with a checked closure

**Files:** Create `diagnostics/identity.py`, `resources/diagnostic-identity.json`, `tests/unit/test_diagnostic_identity.py`; modify `scripts/validate_resources.py` and `tests/harness/test_architecture.py`.

**Interfaces:** `installed_identity() -> ImplementationIdentity`; `check_identity(expected: ImplementationIdentity, actual: ImplementationIdentity) -> tuple[str, ...]`. Identity file/resource access stays in this adapter; comparison/reduction receives its checked document.

- [x] Write `test_same_label_changed_bytes_rejects`, `test_missing_transitive_dependency_blocks`, `test_report_only_change_preserves_identity`, `test_catalog_theme_changes_preserve_identity` and `test_new_reachable_module_requires_manifest_entry`. Assert identical named revision plus changed validator bytes is unequal; no Git/host path enters the digest. Locale/theme resources stay outside the judgment dependency closure.
- [x] Run `UV_OFFLINE=1 uv run --frozen pytest -q tests/unit/test_diagnostic_identity.py` and retain RED.
- [x] Implement canonical sorted digest construction, static dependency-closure validation and distribution metadata traversal. Include actual rule/schema bytes; never load archive paths as modules.
- [x] Rerun identity tests, architecture checks and a fresh subprocess without `.git`; assert metadata absence gives ineligibility rather than fabricated identity.
- [x] Commit: `feat: bind diagnostic recipes to installed execution identities`.

### Task 3: Pre-request provenance and plan-context persistence

**Files:** Create `diagnostics/context.py`; modify `application.py`, `jobs/store.py`, `jobs/manager.py`, `jobs/worker.py`; create `tests/integration/test_diagnostic_context.py`; extend `tests/integration/test_history_migration.py`.

**Interfaces:** `ContextObserver` implements the existing `ExecutionObserver`; `context_for_plan(plan: RunPlan, recipe: RetestRecipe, *, baseline: BaselineRecord | None = None) -> AssessmentContext`; `JobStore.get_plan_context(plan_id: str) -> JsonObject | None`; optional `context` create-plan keyword and optional `assessment_context` application keyword as specified above. This task consumes validated recipe fixtures; Task 4 supplies real recipe generation and Web planning integration.

- [x] Write `test_context_exists_before_first_request`, `test_admission_context_is_idempotent`, `test_identity_changes_between_preview_and_start`, `test_context_write_failure_sends_zero_requests` and `test_old_store_is_not_backfilled_as_verified`. Assert an observer checks sidecar bytes before the synthetic transport records its first call; an old plan remains legacy.
- [x] Run `UV_OFFLINE=1 uv run --frozen python -m pytest -q tests/integration/test_diagnostic_context.py`; retain RED.
- [x] Implement transactional additive migration/context publication and worker/application guards. Preserve create-directory behavior, worker ownership, cancellation and finalization. Capture baseline linkage before networking, without adding fields to result 1.0.
- [x] Rerun the focused file plus `test_job_store.py`, `test_job_manager.py`, `test_worker_lifecycle.py`, `test_history_migration.py` and `tests/unit/test_application.py`. Inject restart between filesystem write and DB commit; no orphan record may trigger requests or overwrite a result.
- [x] Commit: `feat: persist immutable diagnostic context before execution`.

### Task 4: Installed-plan recipes and retest preparation

**Files:** Create `diagnostics/recipes.py`, `diagnostics/reduction.py`, `tests/unit/test_diagnostic_recipes.py`; modify `application.py` to expose shared preparation and `web/api.py` to bind fresh normal plan previews to the generated context.

**Interfaces:** `build_recipe(plan: RunPlan, identity: ImplementationIdentity) -> RetestRecipe`; `validate_recipe_binding(recipe: RetestRecipe, source: ReportSource) -> tuple[str, ...]`; `prepare_retest(recipe: RetestRecipe, target: JsonObject, identity: ImplementationIdentity) -> tuple[RunPlan, JsonObject]`; `baseline_eligibility(metadata: JsonObject) -> JsonObject` is pure and returns named operations/reasons.

- [x] Write `test_recipe_contains_no_endpoint_or_auth`, `test_retest_preserves_all_profiles_and_required_cases`, `test_missing_revision_never_selects_latest`, `test_changed_alias_model_or_limit_is_declared` and `test_redacted_semantic_input_blocks_exact_retest`. Assert all original cases remain even if previously PASS or SKIP; changed semantic inputs are not treated as transport rebinding.
- [x] Run `UV_OFFLINE=1 uv run --frozen python -m pytest -q tests/unit/test_diagnostic_recipes.py`; retain RED.
- [x] Implement installed fixed-case regeneration and binding to actual plan/captures; no arbitrary imported request execution. Keep an explicit difference document even when a new test is permitted but controlled comparison is ineligible. An execution-identity mismatch blocks same-test retest and requires a separately configured current test.
- [x] Rerun focused tests and `tests/unit/test_cases.py tests/acceptance/test_runner.py`; assert preview/rebinding calls no transport and caps cannot silently remove cases.
- [x] Commit: `feat: prepare explicit full-scope retests from portable recipes`.

### Task 5: Bounded ZIP inspection and extraction

**Files:** Create `diagnostics/archive.py`, `tests/unit/test_diagnostic_archive.py`.

**Interfaces:** `ArchiveLimits` is a frozen dataclass with the constants above; `inspect_archive(path: Path, limits: ArchiveLimits, *, clock: Callable[[], float] = time.monotonic) -> JsonObject`; `extract_checked_archive(path: Path, destination: Path, inventory: JsonObject, limits: ArchiveLimits, *, clock: Callable[[], float] = time.monotonic) -> None`. Import `Callable` from `collections.abc`; both functions use the injected monotonic clock for deterministic deadline tests. Destination must be owned, new and empty.

- [x] Write parameterized tests for traversal, duplicate/case-fold names, links, ZIP64/encryption, forged sizes, CRC/hash mismatch, oversized directory/member/JSON/expansion, excess members and processing timeout. Assert no path outside staging changes, no module loads and no socket opens.
- [x] Run `UV_OFFLINE=1 uv run --frozen python -m pytest -q tests/unit/test_diagnostic_archive.py`; retain RED.
- [x] Implement footer preflight, strict inventory checks and chunked bounded copy. Actual expanded-byte limits apply before publishing a file. Reject unsafe archives rather than normalizing them into acceptable ones.
- [x] Rerun focused tests with small injected limits and a valid archive at every permitted boundary. On failure remove only owned partial staging artifacts; do not activate a baseline.
- [x] Commit: `feat: inspect diagnostic archives within strict local limits`.

### Task 6: Read-only import preview and immutable baseline storage

**Files:** Create `diagnostics/store.py`, `diagnostics/service.py`, `tests/integration/test_diagnostic_import.py`, `tests/diagnostic_fixtures.py`.

**Interfaces:** `DiagnosticStore(root: Path)` exposes `preview(archive: Path, owner: str, *, now: datetime) -> JsonObject`, `commit(preview_id: str, owner: str, *, now: datetime) -> BaselineRecord`, `get(baseline_id: str) -> BaselineRecord` and `load_source(baseline_id: str) -> ReportSource`. `DiagnosticService(root: Path)` wraps this store and exposes the same import operations for adapters.

- [ ] Write `test_complete_legacy_partial_and_omitted_eligibility`, `test_duplicate_archive_deduplicates`, `test_external_id_collision_stays_separate`, `test_localized_exports_are_variants_not_conflicts`, `test_variant_evidence_is_not_merged`, `test_activation_crash_is_not_visible` and `test_changed_import_bytes_revoke_eligibility`. Assert import time is separate from external time and no local job row/event is created. Different languages/themes with matching authoritative source/context/recipe remain export variants; genuinely changed source identities remain conflicts.
- [ ] Run `UV_OFFLINE=1 uv run --frozen pytest -q tests/integration/test_diagnostic_import.py`; retain RED.
- [ ] Implement session-bound 15-minute previews, the two-preview cap, atomic activation and rebuildable digest index. Regenerate views from checked structured facts; never render uploaded HTML/JS. Validate every baseline/result/evidence/recipe relationship before granting operations.
- [ ] Rerun focused tests and export/report-source integration tests. Assert expired previews reject and cleanup never deletes committed baselines or another session's active preview. Block all sockets during inspection/commit/read.
- [ ] Commit: `feat: import diagnostic baselines without executing their content`.

### Task 7: New portable packages for CLI and Web sources

**Files:** Create `diagnostics/packages.py`, `tests/integration/test_diagnostic_export.py`; modify `exports.py` to delegate portable-package composition while retaining legacy export reads.

**Interfaces:** `build_package_files(source: ReportSource, context: AssessmentContext | None, *, include_evidence: bool, comparison: Comparison | None = None) -> dict[str, bytes]`; `write_package(files: dict[str, bytes], destination: Path) -> JsonObject`; `DiagnosticService.export(source_dir: Path, destination: Path, *, include_evidence: bool) -> JsonObject`.

- [ ] Write `test_export_preserves_source_bytes_and_binds_recipe`, `test_old_source_exports_as_legacy_not_verified`, `test_evidence_omission_lowers_delivery`, `test_source_url_is_disclosed_in_preview` and `test_package_export_import_limits_match`. Hash-check result/capture bytes before and after; a report-only package cannot claim independent verification. Task 13 extends the actual localized export test, including invalidating only the export preview when its presentation choices change.
- [ ] Run `UV_OFFLINE=1 uv run --frozen pytest -q tests/integration/test_diagnostic_export.py`; retain RED.
- [ ] Implement package marker/inventory/context and a minimal agent entry point using the current checked report facts. Task 13 replaces its document composition with the final design. Preserve existing export-manifest 1.0 reads; publish presentation-3 files with the separate export-manifest 2.0 branch when Task 13 integrates them. Do not mutate an existing const/golden file. Full diagnostic archives retain the source result even when evidence is omitted; standalone HTML/Markdown provide summary sharing without those attachments. Never call the original-evidence ZIP anonymized.
- [ ] Rerun focused tests, `test_exports.py`, `tests/acceptance/test_export_integrity.py` and `test_recovered_reports.py`. Round-trip complete, partial and omitted packages through Task 6; reject mismatches without rewriting old bytes.
- [ ] Commit: `feat: export portable diagnostic packages with honest provenance`.

### Task 8: Pure paired-check comparison and scoped conclusions

**Files:** Create `diagnostics/comparison.py`, `tests/unit/test_diagnostic_comparison.py`; extend `diagnostics/reduction.py` and `diagnostics/service.py`.

**Interfaces:** `compare_assessments(before: JsonObject, after: JsonObject) -> Comparison` consumes normalized checked source facts prepared by the service; `DiagnosticService.compare(baseline_id: str, source_dir: Path) -> Comparison`; `DiagnosticService.compare_sources(before_dir: Path, after_dir: Path) -> Comparison`; `DiagnosticService.source_facts(source_dir: Path) -> JsonObject`. The imported-baseline convenience method delegates to `compare_sources`; Web adapters resolve run/baseline IDs to owned roots before calling it, never user-supplied paths. Facts contain source identity, plan/check inventory, original statuses, recipe/context and evidence quality, not HTML.

- [ ] Write a transition-table test for FAIL/PASS, FAIL/FAIL, PASS/FAIL, PASS/PASS, missing baseline, unresolved new checks and unmatched checks. Add `test_changed_conditions_have_no_recovery_badge`, `test_same_label_changed_implementation_incomparable`, `test_omitted_evidence_no_verified_headline` and `test_missing_required_check_not_hidden_in_denominator`.
- [ ] Run `UV_OFFLINE=1 uv run --frozen pytest -q tests/unit/test_diagnostic_comparison.py`; retain RED.
- [ ] Implement canonical joins by case/generator/request/judgment identities and conservative whole-pair ineligibility for changed effective limits. Enumerate all unmatched checks; issue summaries derive from paired assertions and list their members, never from F01 or a status string. Preserve input objects unchanged.
- [ ] Rerun focused tests and schema tests. Assert "all previous failing checks passed this sample" requires full comparable coverage, and new failures/gaps remain beside any recovery count. Compare the same checked facts under different presentation choices and assert identical semantic comparison output. No claim of cause or stability is generated.
- [ ] Commit: `feat: compare repair observations without hiding verification gaps`.

### Task 9: Standalone diagnostic CLI operations

**Files:** Create `diagnostics/cli.py`, `tests/acceptance/test_diagnostic_cli.py`; modify `cli.py` for subparser delegation and `application.py` for context integration.

**Interfaces:** `add_diagnostic_commands(parser: argparse.ArgumentParser) -> None` and `dispatch_diagnostics(args: argparse.Namespace) -> int` own the exact commands/flags defined above. The root CLI first creates `commands.add_parser("diagnostics")` and passes that parser to the helper; the helper creates only its child subcommands. No private argparse generic, Any or suppression is needed.

- [ ] Write subprocess tests for each command, missing live opt-in, dry-run zero requests, immutable baseline bytes, legacy manual-current-test guidance and explicit incomparable JSON. Deny importing `fastapi`, `jinja2` and `uvicorn` in a clean CLI-only installation. Task 13 adds and tests the presentation flags when localized document rendering is available; this task does not accept and silently ignore unsupported presentation choices.
- [ ] Run `UV_OFFLINE=1 uv run --frozen pytest -q tests/acceptance/test_diagnostic_cli.py`; retain RED.
- [ ] Implement parser/dispatch through the shared service. Keep existing stdout machine-readable, operation explanations on stderr, secret values absent from errors and existing run exit meanings unchanged. Dry-run output cannot create a report that looks executed. The additional language/theme helper and report-option forwarding are integrated in Task 13, preserving this task's command/exit contracts.
- [ ] Rerun focused tests and `tests/acceptance/test_cli.py tests/acceptance/test_replay.py tests/acceptance/test_serve_command.py`. Exercise live opt-in only against the disposable local synthetic peer with a four-request plan.
- [ ] Commit: `feat: expose portable diagnosis and repair verification in the CLI`.

### Task 10: Authenticated binary import and shared Web diagnostic routes

**Files:** Create `web/diagnostics.py`, `tests/integration/test_web_diagnostics.py`; modify `web/security.py`, `web/settings.py`, `web/app.py`, `web/contracts.py`, `resources/schemas/web-api.schema.json` through additive variants only; update `resources/web/contracts.d.ts`.

**Interfaces:** The routes in the HTTP decision section call `DiagnosticService`; upload preview streams an archive to `DiagnosticStore` staging. JSON routes retain existing `LocalRoute`, error envelopes and published contracts. Retest preview produces a normal frozen plan plus its diagnostic context, not a new execution endpoint.

- [ ] Write tests for valid chunked ZIP, oversized/deceptive Content-Length, disconnect cleanup, wrong media type, missing Origin/session/CSRF and applying ZIP to every other route. Assert JSON stays at 65536 bytes, expired/mismatched preview owners cannot commit, and all requests before normal start produce zero upstream calls. Add checked preference-cookie update/default/malformed/expiry tests and localized human error messages with identical machine error codes; preference mutation still requires session/Origin/CSRF.
- [ ] Run `UV_OFFLINE=1 uv run --frozen pytest -q tests/integration/test_web_diagnostics.py`; retain RED.
- [ ] Implement the one-route streaming branch after the same security checks as JSON, plus the ordinary preferences route/cookie parser and request-local error-message localization. Keep upload processing off the event loop using the existing threadpool pattern; cap concurrent previews and return a useful busy response. Preserve sanitized errors/CSP and never use uploaded HTML as a page. Add versioned diagnostic export request options rather than weakening old export-request schemas.
- [ ] Rerun focused tests plus `test_web_security.py test_web_api.py test_web_events.py`; validate OpenAPI declares binary upload correctly and JSON response schema names match runtime validation.
- [ ] Commit: `feat: add bounded local diagnostic import and retest endpoints`.

### Task 11: Operational facts, liveness and workbench views

**Files:** Create `workbench.py`, `web/workbench.py`, `resources/web/workbench.html`, `resources/web/workbench-overview.html`, `resources/web/workbench-issues.html`, `resources/web/workbench-cases.html`, `resources/web/workbench-compare.html`, `resources/web/workbench-activity.html`, `resources/web/import.html`, `resources/web/baseline.html`; modify `web/pages.py`, `jobs/manager.py`, `resources/web/base.html`, `resources/web/configure.html`, `resources/web/app.css`; create `tests/unit/test_workbench_view.py`, `tests/integration/test_workbench_pages.py`.

**Interfaces:** `build_workbench_view(run: JsonObject, *, worker_observation: JsonObject) -> WorkbenchView` is pure; `JobManager.worker_observation(run_id: str) -> JsonObject` observes the owned process with timestamp under its existing synchronization; no inferred heartbeat from elapsed time. `web/workbench.py` composes local run/baseline views without calling `render_report_body`.

- [ ] Write tests for active, complete, interrupted, empty and mixed states; distinguish upstream timestamps, service connectivity and observed worker liveness. A terminal result/publication race must yield one coherent projection generation. Assert original dimensions and unassessed client state survive.
- [ ] Run `UV_OFFLINE=1 uv run --frozen pytest -q tests/unit/test_workbench_view.py tests/integration/test_workbench_pages.py`; retain RED.
- [ ] Implement selected-layout shell and distinct views with query parameters `view`, `issue`, `case`, `filter`, `baseline`, plus the import/baseline/retest-configuration HTML routes. SSR applies the checked preference and includes both catalogs; autonym language and light/dark/system controls are available globally. Render neutral completion; green denotes PASS only. Derive counts from facts; explicitly label matrix passing-count denominators. Evidence details reference checked IDs, never arbitrary paths. Configuration labels the actual installed suite/count, keeps all original profiles for retest, and groups finite execution controls into details rather than a pricing workflow.
- [ ] Rerun focused tests and existing Web page/source recovery tests. Preserve old run URLs and map old `#capabilities`, `#finding-*`, `#case-*` links to the appropriate view/selection without changing source identities. No-JS links work.
- [ ] Verify localized parameters containing hostile markup remain literal text through the actual escaped template boundary, without double-escaping original field values.
- [ ] Commit: `feat: separate operational workbench views from report documents`.

### Task 12: Focus-preserving browser interaction and layout acceptance

**Files:** Create `resources/web/workbench.js`, `resources/web/diagnostics.js`, `tests/frontend/workbench.test.js`, `tests/browser/workbench.spec.js`, `tests/browser/diagnostics.spec.js`; modify `resources/web/app.js`, `resources/web/progress.js`, `scripts/browser_fixture.py`, `tests/browser/helpers.js` and static asset allowlists.

**Interfaces:** `deriveActivity(execution: Execution | null, nowMs: number) -> ActivityView` and `reduceWorkbench(state: WorkbenchState, event: WorkbenchEvent) -> WorkbenchState` have strict JSDoc types in `contracts.d.ts`. Browser controllers mount view-specific behavior and patch keyed facts instead of replacing inspector/root HTML.

- [ ] Write Node tests for distinct activity clocks and stale/out-of-order snapshots. Browser tests cover tabs/Back/refresh, selected-row retention on issue arrival, evidence disclosure focus, import/retest preview, keyboard filters, empty issues, cancellation and service reconnect with exact request counting. Locale/theme switching must preserve a valid execution-plan preview; changing export presentation must require a fresh export preview.
- [ ] Run `UV_OFFLINE=1 uv run --frozen python -m scripts.check_frontend --suite static --out artifacts/w2/task12-static-red` and the new browser tests through the existing harness with a fresh output directory; preserve meaningful assertion failures.
- [ ] Implement keyboard-accessible navigation and narrow list/detail flow, unique IDs, focused live-region summaries and bounded updates. Language/theme updates patch product-owned text/accessibility labels and CSS tokens without replacing controls, translating data, clearing inputs or restarting observation. Set `<html lang>` correctly. While active, refresh worker observation at most every five seconds via the local workbench route; this is not upstream activity. SSE events remain ordered and reconnection never starts work. Do not auto-open issues or silently reseat selection.
- [ ] At the same viewport, locale and frozen synthetic state, switch light/dark and compare header, navigation, metric and inspector bounding boxes within one CSS pixel. Theme tokens must not change typography, spacing or panel geometry. Capture the accepted pair and actual screenshots together for visual comparison; inspect long English/Chinese names, empty and interrupted states as well as the nominal four-case run. Record justified differences rather than treating a generated PNG as a pixel-perfect runtime golden.
- [ ] Verify 1280x800, 1440x900, 390px narrow and 200% zoom in both languages and explicit light/dark themes, plus system-theme changes and explicit overrides. Assert desktop document height does not exceed viewport height for overview attention/global state; no horizontal clipping of primary actions. Measure normal text contrast at least 4.5:1, large text at least 3:1 and meaningful non-text contrast at least 3:1, including code/status/focus/selected states. Test switching during an active synthetic run with unchanged request counts and source hashes, cookie persistence, clean first paint, no localStorage/sessionStorage, a synthetic 96-row list, no-JS links, missing evidence, unknown lineage and axe checks. Run the entire existing browser suite after updating intentional view expectations, retaining old report/source fixture outcomes.
- [ ] Commit: `feat: make workbench monitoring quiet and context preserving`.

### Task 13: Standalone presentation-3 reports and agent entry point

**Files:** Create `documents.py`, `document_rendering.py`, `cli_presentation.py`, `resources/report-v3.html`, `resources/report-v3.css`, `resources/report-v3.js`, `tests/unit/test_document_view.py`, `tests/acceptance/test_diagnostic_documents.py`; modify `cli.py`, `diagnostics/cli.py`, `tests/acceptance/test_diagnostic_cli.py`, `reporting.py`, `exports.py`, `diagnostics/service.py`, `diagnostics/packages.py`, `package.json`, `scripts/check_templates.py`, frontend resource/type/lint coverage as needed.

**Interfaces:** `build_document_view(source: ReportSource, *, comparison: Comparison | None = None, presentation: PresentationOptions = PresentationOptions()) -> DocumentView`; `render_document_html(view: DocumentView) -> str`; `render_document_markdown(view: DocumentView) -> str`; `render_agent_index(view: DocumentView) -> str`; `cli_presentation.add_presentation_options(parser: argparse.ArgumentParser) -> None`. Add the same optional `presentation` keyword to shared report/export service entry points and existing public report-output functions; never add it to `run_assessment` execution configuration. Existing public report entry points select new presentation explicitly while preserving old readers/assets and original source bytes.

- [ ] Write tests asserting standalone HTML has conclusion/scope/matrix/findings/method/evidence links and no run tabs/cancel/export form. Assert Markdown/JSON and HTML share counts, omissions and comparison limits. Add subprocess tests for presentation flags/defaults on every report-producing command and unchanged machine stdout/exit semantics; compare original result/evidence hashes and request parameters across locales/themes. Hostile prompts/metadata remain escaped data; references cannot execute script or reference non-HTTPS external actions.
- [ ] Run `UV_OFFLINE=1 uv run --frozen pytest -q tests/unit/test_document_view.py tests/acceptance/test_diagnostic_documents.py`; retain RED.
- [ ] Implement the editorial report direction with explicit passing/assessed labels, numbered tables/figures and useful default-expanded findings. Reuse existing verified field extraction and reference facts; do not independently rejudge assertions. Include comparison only when present and accurately scoped. Add an agent index linking to result, recipe, comparison and evidence identifiers with content-as-data instructions. Standalone HTML/Markdown identify the endpoint by its display alias and omit raw endpoint/auth-reference fields, including embedded page data; actual requested/observed model identities remain because they are evidence. The source result in a full ZIP retains its original fields and is disclosed as such. Route fresh CLI/Web reports through presentation 3.0 while retaining existing `report_rendering` functions/assets for explicit presentation-2 tests and legacy reads; record this intentional versioned presentation change without altering original fixture outcomes.
- [ ] Verify the coverage matrix retains passing/assessed denominators and unassessed dimensions, an issue-impact bar uses affected-case counts without adding overlapping families as unique failures, and a comparison matrix shows recovery, persistent/new failures and gaps together when supplied. Include a timing figure only when recorded boundaries explain a finding. Give every figure a caption, accessible name and equivalent table; keep all graphics local/offline and meaningful without relying on color.
- [ ] Run focused tests and browser offline/no-script/print checks using synthetic generated reports in both languages and all three theme choices. HTML embeds two catalogs and one fact set; initial exported language works without scripts, while enabled in-file switches need no service/cookie/storage and do not mutate evidence. Markdown remains one selected language. Deny all network requests during reading, exercise direct-file fixture opening, verify print forces light while retaining selected language, inspect chart/code/control contrast and narrow tables. Existing actual private exported-file browser restrictions are not bypassed; use the normal synthetic harness.
- [ ] Commit: `feat: publish independent diagnostic documents for humans and agents`.

### Task 14: End-to-end two-environment repair handoff and packaging

**Files:** Create `tests/acceptance/test_diagnostic_handoff.py`; extend `tests/fixtures/http/server.py`, `tests/acceptance/test_installed_package.py`, `tests/acceptance/test_web_package.py`, `scripts/web_image_checks.py`, `scripts/check_images.py`, `scripts/check_package.py`, `scripts/validate_resources.py`; update `docs/{development,container-usage,architecture}.md`, `README.md`, `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/compatibility_report.yml` and CI evidence coverage as required.

**Interfaces:** Existing image harness CLI flags remain `--platform linux/arm64|linux/amd64 --scope full --targets runtime,web --out PATH`. New checks call the shared public CLI/HTTP operations, not private helper shortcuts.

- [ ] Write a complete handoff acceptance scenario: baseline peer A produces verified failures; export package; copy it to fresh B storage; import through the actual adapter; supply B endpoint/auth locally; preview/run all four cases; compare and export. Peer B repairs stop fields but retains the model-policy failure and introduces one stream defect. Assert the actual validator transitions, source/ZIP hashes, zero import/read calls, full original required scope and visible new failure. B must have no A storage/presets/credentials.
- [ ] Run `UV_OFFLINE=1 uv run --frozen pytest -q tests/acceptance/test_diagnostic_handoff.py`; retain RED from the public flow before completing integration.
- [ ] Complete integration, wheel/sdist resource inclusion, CLI-only dependency isolation, Web volume import persistence and legacy index migration. Document sharing content/identity limits and the new commands. Use generic synthetic addresses only; never include private targets or captured service logs.
- [ ] Run focused handoff/installed-package checks, then fast/full check graphs. Build and exercise both image targets on native ARM64 and emulated AMD64 with the maintained image orchestrator; product Python checks run in Linux containers. Preserve disconnected operation, nonroot/read-only runtime and signal/cancellation checks. CI stays synthetic/read-only and reports all required children; do not publish. Missing tools/jobs remain blocked/not_run, never PASS.
- [ ] Commit: `test: verify portable repair handoff across isolated environments`.

### Task 15: Whole-stage review, author corrections and local handoff

**Files:** Create `docs/reviews/2026-10-18-diagnostic-workbench-review.md`, `docs/harness/diagnostic-workbench-acceptance.json`, `docs/harness/diagnostic-workbench-handoff.json`, their packaged schemas and `tests/harness/test_diagnostic_acceptance.py`; maintain `docs/harness/diagnostic-workbench-ledger.md`, `docs/harness/progress.md`, `docs/CONTINUE.md` and plan checkboxes.

**Interfaces:** Acceptance maps W2-01 through W2-17 to exact source identities, executed checks and retained artifacts. Handoff separates source, offline/browser/package, container, remote CI, independent review and real endpoint outcomes. New acceptance schemas are validated by the existing resource/document harness.

- [ ] Write an acceptance-schema regression rejecting a missing requirement, unknown source identity, zero tests or an unrun child marked passed. Run it RED, then add only the validation/recording boundary required to represent observed W2 outcomes.
- [ ] Freeze a clean candidate commit and arrange exactly one independent whole-W2 review under repository policy. Provide the approved spec, selected design, this plan, immutable diff range, new/old contract fixtures, check records and the complete handoff scenario. Reviewer is read-only; no per-task implementers or repeated review loop.
- [ ] Evaluate findings against evidence; record accepted/rejected/deferred rulings. For accepted behavior defects, demonstrate RED and GREEN without weakening original assertions. Run appropriate focused regressions, then full/container verification again if affected source changed. Do not bind old image evidence to the new source.
- [ ] Use `UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite full --out artifacts/w2/final-full-<source>` for final local developer acceptance. Read every required result and actual test counts; separately record image evidence, review disposition and all unobserved external outcomes. Use unique output paths for retries and retain failures.
- [ ] Commit the verified source locally, then scope a handoff-only commit with final artifacts/ledger. Do not push, merge, publish, run a real endpoint or remove retained scratch/evidence as a side effect. Mark completion only when the whole W2 scope is met; otherwise list remaining requirements honestly.

## Acceptance coverage map

| Spec requirement | Owning tasks |
| --- | --- |
| W2-01 shared facts and immutable evidence | 3, 7, 11, 13, 14 |
| W2-02 desktop overview and reflow | 11, 12 |
| W2-03 honest slow-peer activity and reconnect | 3, 11, 12, 14 |
| W2-04 focus/navigation during live changes | 12 |
| W2-05 issues/matrix/evidence and impact limits | 8, 11, 12, 13 |
| W2-06 independent offline/no-script/print document | 13, 14 |
| W2-07 cross-machine handoff/retest | 4, 6, 7, 9, 10, 14 |
| W2-08 semantic implementation and judgment identity | 1, 2, 3, 4, 8 |
| W2-09 paired transitions and coverage gaps | 8, 12, 13, 14 |
| W2-10 legacy/partial/hostile archives | 5, 6, 7, 10, 14 |
| W2-11 original/imported/new identity separation | 3, 6, 7, 8, 14 |
| W2-12 CLI independence, images and restart | 9, 10, 14 |
| W2-13 full harness and honest external status | 1, 12, 13, 14, 15 |
| W2-14 independent whole-stage review | 15 |
| W2-15 complete bilingual presentation and catalogs | 0, 9, 10, 11, 12, 13, 14 |
| W2-16 light/dark/system, offline and print | 0, 11, 12, 13, 14 |
| W2-17 presentation invariance and archive variants | 0, 2, 6, 7, 8, 9, 12, 13, 14 |

The localization/theme amendment adds Task 0 and extends existing adapter/report
tasks without changing their order. CLI presentation flags are deliberately wired
in Task 13, after their renderer exists, rather than exposing nonfunctional options
in Task 9. The amendment also adds tests for same-source export variants, retains
per-archive evidence quality and keeps presentation modules out of core identity.
Amendment self-review also distinguishes execution-preview preservation from
export-preview invalidation, covers all three new acceptance IDs, and retains
English CLI help/machine grammar while localizing product UI and report prose.

## Author self-review and execution handoff

Author self-review completed on 2026-10-18: all W2 acceptance requirements map to
tasks; the recipe/context dependency, public CLI parser interface, legacy export
version branch, source-summary distinction and passing-count labels were corrected.
No implementation checkbox is checked and no runtime outcome is inferred from
the generated images or this document review.

The final paired-design self-review checked all seventeen acceptance IDs against
the task map, cross-task signatures, the five Review Focus owners and dependencies.
It pinned the shared theme/typography starting values, theme geometry acceptance,
the archive clock-injection signatures and report-figure evidence/denominators.
Template escaping is checked where actual rendering exists. These checks concern
plan completeness, not an observed runtime outcome. The plan is a set of
contracts/testable decisions, not prewritten implementation. If implementation
reveals an unsatisfied contract, record the issue and resolve it visibly rather
than weakening required checks or quietly expanding scope.

Preserve the owner's execution method: current checkout/prepared Dev Container,
sequential current-agent implementation, one independent end review. Written-plan
approval and companion visual review completed on 2026-10-18. Execute sequentially
without per-task permission prompts. Real endpoint requests remain separately
authorized operations; do not reopen completed W1 work.
