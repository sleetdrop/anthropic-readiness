# Architecture

The CLI selects an immutable contract and explicit case plan before any request.
Four versioned cases feed a sequential runner. Transport enforces absolute
budgets, response limits, TLS verification, no redirects and no implicit retries.
Evidence is sanitized in memory before exclusive atomic writes. Replay consumes
verified persisted captures without network access. Reports expose scope,
non-PASS assertions, missing coverage and a versioned offline reader guide.

## Dependency direction

`cli` → `runner` / `reporting` → adapters and cases → `config` →
`schema` / stream validation → message validation → pure JSON validation /
SSE framing → `models`. Import Linter enforces these layers and forbids pure
modules from importing adapters, filesystem/resource loaders, HTTP or YAML.
`schema` loads packaged resources; `json_validation` performs pure offline
validation and rejects external references. No validation fetches a remote schema.

JSON Schema governs shape; relational validation governs required case/profile
membership, assertion accounting and aggregates. Evidence hashes and relative
pointers are verified independently. The five statuses preserve uncertainty:
FAIL is an observed defect; INDETERMINATE, BLOCKED and SKIP cannot prove support.

## Scope and provenance

The first core bundle fixes API version, empty beta set, rule sources and fixture
hashes. It tests a subset, not the whole vendor protocol. API dates, beta headers,
rule revision, SDK/CLI versions and actual model behavior are distinct axes.
Later stages add matrices, tool loops, client workflows and reviewed protocol
maintenance; current reports must not imply they already exist.

The harness checks source, schemas, synthetic behavior, installed packaging and
collaboration definitions. Image acceptance, visual review, independent review,
remote CI and real endpoint outcomes are distinct evidence. See the
[acceptance map](harness/acceptance.json) and [progress record](harness/progress.md).

The pure `requirements` registry is shared by planning and result validation.
Imported profile/case/assertion membership and versions cannot be reduced merely
by editing both sides of a result. Public rehydration also compares the contract
against the exact packaged manifest; arbitrary domain-only records are not public
compatibility certificates.

Capture schema 1.1 adds an optional-value lifecycle projection digest. Before
redaction the writer compares event identities, type/index and block-creation
fields with a freshly decoded sanitized body; only identical projections earn a
proof. Replay verifies that digest and preserves only those lifecycle assertions.
Other body semantics remain conservative. Schema 1.0 captures remain readable;
transformed legacy captures have no such proof. This attests sanitizer-preserved
structure, not origin authenticity or a signature. Never treat self-contained
file hashes as independent proof of who produced a capture.

## Local console and shared engine

The optional Web adapter and CLI use the same application/runner.
`application` builds canonical plans and binds ephemeral credentials. Pure operational
values/ports and reduction code do not import Web/SQLite/filesystem adapters.
The parent-side job service owns SQLite admission, immutable plan identity and the
sole ordered progress journal; one spawned worker owns model I/O, source evidence,
exclusive checkpoints and the final result. Bounded private JSON pipes carry keys
and events. Parent acknowledgment follows durable validation before the worker can
continue. Keys do not enter argv, persistent plans/presets or reports.

Queue capacity, preview expiry and idempotency are operational contracts, separate
from the five compatibility verdicts. Parent loss, worker failure, cancellation and
service replacement preserve committed evidence and never automatically resume a
model request. Parent-only snapshots and advertised checkpoint receipts define the
readable prefix; unrelated worker files cannot become published evidence.

The HTTP boundary enforces exact local Host/Origin, memory sessions, CSRF, bounded
strict JSON and safe exception responses. SSE carries observations, snapshots and
recoverable cursors, not execution commands. Closing a browser or reconnecting cannot
start/cancel a job. API/page reads and exports all use the verified source loader.

`report_sources` performs bounded path/hash/schema/identity verification. Frozen
report-view 1.0/presentation 2.0 facts remain a compatibility boundary. Python
file writers select this frozen branch only with explicit `presentation=None`;
their default and the public CLI produce presentation 3.0. The legacy branch
rejects a paired comparison instead of silently discarding it.
`workbench` composes operational views; `documents` composes presentation-3 reading
without an embedded report in the application. Both preserve original case/check
judgments. Document-only routing omission never rewrites verdict/model strings.
The pure projection has no per-call resource I/O; checked schema compilation is
cached at the existing report-value boundary. Renderers own escaping/localization.

Independent HTML has packaged local styles/scripts, two catalogs and one factual
dataset, meaningful captions/coverage denominators and equivalent tables. Native
impact bars count distinct affected cases; overlapping families are not summed.
Only recorded timing that explains a finding merits a timing figure. No-script
reading and selected-language light printing remain usable. Legacy rendering/assets
remain explicit compatibility paths. Presentation changes do not change original
result/capture judgments or core execution identity.

Diagnostic services are shared by CLI and Web. Before requests, an immutable
assessment-context header binds the frozen plan, recipe and installed code/rule/
relevant-dependency identity; final verification is a separate sidecar. Recipes
regenerate the entire original scope from installed cases and never execute archive
code or templates. Comparison joins canonical case/request/check identities and
versions, never display labels. Semantic changes are incomparable; context changes
are disclosed. Recovery is scoped to matching checks and does not suppress new
failures, gaps, unmatched members or required-coverage deficits.

ZIP intake is a bounded classic archive with streamed actual expansion/count/time
limits, safe relative names and no links/ZIP64/execution. Session-bound previews
activate an immutable baseline only after complete verification and an atomic
commit marker. SQLite is a rebuildable index, not proof. Reopen revalidates source,
recipe/evidence relationships and implementation eligibility. Unknown lineage,
partial or evidence-omitted sources remain read-only and cannot mint proof.

Exports preserve original bytes with explicit omissions; a sealed publication
record is last. Presentation-3 uses document-view 1.0, document-manifest 2.0 and
export-manifest 2.0. HTTP diagnostic-export variants honor explicit locale/theme
and optional owned baseline; old request/response variants retain presentation 2.
CLI-only document rendering imports no optional Web dependency. Original raw source
in full packages can retain endpoint/auth-reference/model/business context; alias
presentation is not archive anonymization. Hashes detect byte changes and are not
signatures, source authentication or independent certification.

The `web` dependency extra and Docker target are independent from minimal CLI
installation and `runtime`. Node/Chromium belong only to development/CI. A personal
Compose deployment binds the host port to loopback and stores data in one owned
nonroot volume with a read-only root filesystem. This is not a shared-host service.
See the [W2 specification](superpowers/specs/2026-10-18-diagnostic-workbench-design.md)
and [W2 ledger](harness/diagnostic-workbench-ledger.md); they do not expand the four-case
protocol scope into tool loops, API version matrices or client certification.
