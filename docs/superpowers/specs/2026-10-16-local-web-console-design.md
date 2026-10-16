# Local Web console and visual reports

Revision: 1. Status: written specification for owner review.
The owner approved the local deployment direction and interactive visual design
on 2026-10-16. This document formalizes that direction; its implementation plan
has not yet been written or approved.

## 1. Outcome and scope

Each user runs the application on their own computer using Docker. A browser
provides target configuration, explicit test planning, live progress, investigation,
history and on-demand exports. The CLI remains independently usable, including
automatic reports, dry runs and offline replay. Both interfaces use one test
engine, one authoritative result contract and one report reader model.

Milestone **W1** delivers this complete local workflow against the existing four
Stage A cases. It includes history and offline sharing, rather than stopping at a
GUI that launches a process. The 24-case visual mockup is fictional design material.
The private comprehensive assessment is not a packaged suite and is not imported.

W1 does not implement new protocol cases, version-matrix execution, SDK/Claude Code
workflows, protocol-update tooling, shared remote service, user accounts or load
testing. Those retain separately scoped B/C/D contracts. W1 shows the actual
installed catalog and explicitly unavailable future groups. No universal
compatibility score or whole-protocol certification is introduced.

This spec amends the future UI, execution-service and presentation scope of the
[original design](2026-10-14-anthropic-readiness-design.md). It permits optional
packaged scripts in new offline reports and adds a Web image. Historical Stage A
acceptance, frozen ledgers/manifests, capture/result schemas and observed failures
are not rewritten. The [Web reference study](../../reviews/2026-10-16-web-console-reference-study.md)
and [visual study](../../reviews/2026-10-16-visual-expression-design.md) provide
rationale; this document governs W1 where earlier proposals differ.

## 2. User journey

### Configure and preview

The new-assessment page accepts a display name, endpoint, model, authentication
mode, response-model policy/aliases, installed rule bundle, available profiles
and finite request/time/response limits. Existing target-schema restrictions apply.
Non-secret target presets can be saved, edited and copied; a run freezes its own
resolved target and is unaffected by later preset edits. Presets are local data,
not repository fixtures or exported credentials.

Show the final Messages URL before starting. Support an explicitly labeled base
URL helper and a full Messages URL input; display the helper's resulting URL and
reject ambiguous paths instead of guessing. Never silently translate loopback to
the Docker host alias. Provide a concise platform-specific Docker address hint.

Configuration validation and plan preview make zero upstream requests. Preview
shows exact case IDs/versions, required membership, rule identity, API date/betas,
model/alias policy, request cap, time limits and no-retry policy. Available choices
come from the installed immutable catalog, not guessed model capabilities.

Clicking **Start test** opts into that exact live plan. Configuration changes
invalidate its preview. W1 does not make automatic connection/discovery requests
on field edits, page loads or preview. Existing CLI live opt-in remains mandatory.

### Observe and investigate

The run URL remains stable from queue through completion. Show case accounting,
actual requests/cap, elapsed time/limit, current case, observed phase and last
activity. Completed-case results appear while other cases continue. Distinguish
pending/running from protocol-result statuses. Closing or refreshing the browser
does not stop the worker. Reconnection resumes observation without new model calls.

Provide explicit cancellation. A completed run shows its scoped conclusion,
capability matrix, status distribution, finding impact, recorded timeline and
evidence-backed details. Filters separate failures from unresolved outcomes.
Activating a matrix cell opens its cases; a finding opens expected/actual fields,
affected cases, impact, suggested action, rule source and verified evidence.
Back/close restores the prior filter and reading context.

### History and exports

History lists lifecycle, target label, model, rule/API/beta identities, timestamps,
duration and result summary. Filter by target/model, rule snapshot, date and lifecycle.
W1 has no automatic retention deletion. Rerun copies configuration into a new preview;
it never mutates the old assessment or immediately sends requests.

Web runs persist results/evidence independently of export. Export is on demand;
CLI runs continue writing reports automatically. Exporting, reading history or
opening evidence never initiates an upstream request.

## 3. Components and dependencies

Use FastAPI with server-rendered HTML and small progressively enhanced browser
modules. Templates/static assets are packaged resources. Use native SVG for the
initial small charts; no chart CDN, frontend server or full SPA is required.
Browser code uses strict JavaScript checking with TypeScript/JSDoc, formatting,
lint and browser acceptance gates. Node is development/CI tooling only; pin its
toolchain and package lock in the implementation plan and Dev Container.

Dependency direction:

```text
CLI adapter -------------------> shared application services
Web HTTP adapter -> job manager -> worker -> shared application services
shared services -> runner, reporting, persistence/transport adapters
validators/framing/domain remain pure and depend on neither UI
```

Extract only the application boundaries needed for planning, credential resolution,
execution observation, cancellation, checkpointing and report construction. Do not
parse terminal output to drive the Web UI. HTTP/framework types and job storage
do not enter validators. Extend Import Linter contracts to enforce this direction.

The standalone CLI does not require the Web extra, SQLite job store, active service
or browser. Existing command options, machine stdout and exit-code meanings stay
compatible. Interactive terminal progress goes to stderr. Optional HTTP remote CLI
control is not W1 scope.

## 4. Plans, jobs and lifecycle

The local service has one scheduler and at most one active assessment. Queue
capacity is eight waiting jobs; a full queue rejects a start without making a
request. A filesystem ownership lock prevents two schedulers sharing a data root.
No Redis, distributed worker or Docker socket is required.

A preview freezes the canonical resolved plan and fingerprint under an opaque ID
for 15 minutes. Start requires that ID, matching session and explicit live consent.
Repeated submission of the same start operation returns the same job. It cannot
create duplicate requests. An expired/changed plan requires another local preview.
Queued admission retains the frozen plan even after preview expiry.

Job lifecycle is separate from compatibility results:

| State | Meaning and allowed next states |
| --- | --- |
| `queued` | Admitted, no worker; next `running`, `cancelled`, `interrupted` or `error`. |
| `running` | Worker owns execution; next `cancelling`, `completed`, `interrupted` or `error`. |
| `cancelling` | Stop requested; next `cancelled`, `interrupted` or `error`. |
| `completed` | Valid final result committed; may include FAIL/BLOCKED/INDETERMINATE/SKIP. |
| `cancelled` | Explicit cancellation completed; retained result may be partial. |
| `interrupted` | Service/worker disappeared or was forcibly terminated. |
| `error` | Application/storage failure prevented normal completion. |

Terminal jobs are immutable. A cancel arriving after committed completion returns
the completed state. Finalization and cancellation serialize so only one terminal
state wins. Existing compatibility states retain their original semantics.

Each job runs in a child process with its own main-thread signal handling.
Cancellation stops new requests and interrupts the active transport. Allow five
seconds for checkpoint/finalization, then terminate the owned worker if needed;
hard termination is recorded as interrupted, not successfully finalized cancellation.
Previously committed evidence survives. Do not claim the current request was
captured completely when it was not.

Workers watch their private parent-control channel; loss stops further requests
and initiates bounded shutdown. On service restart, unfinished persisted jobs become
interrupted and are never automatically resent or resumed. A new run needs a new
explicit start. Reconstruct a final result only when its validated committed
artifacts prove completion; never infer success from a missing worker.

## 5. Persistence, events and crash recovery

The Docker volume contains local SQLite job/preset indexes and separate per-run
directories. Preserve immutable plan, versioned case checkpoints, sanitized evidence,
ordered events, execution metadata, final result and generated exports. Result JSON
and verified evidence remain authoritative; SQLite is an index and lifecycle store.
Reconciliation may repair an index, never change a recorded compatibility judgment.

Keep the existing result 1.0 and capture reader/writer contracts. New operational
records have separate packaged schemas: job, execution, checkpoint, progress event,
report view and export manifest, initially revision 1.0. Report presentation becomes
2.0; rendering an old result does not migrate its original bytes. The report-view
schema version is independent of protocol, result and presentation versions.

Persist evidence and a schema-validated case checkpoint before publishing a case
completion event. A checkpoint contains the original case record and evidence
references; it is not a valid final RunResult by itself. Final result assembly runs
the existing schema, relational required-case and evidence checks before atomic
publication. Missing required cases remain accounted for under interruption rules.

If a crash prevents valid final assembly, show an explicitly partial operational
view of verified checkpoints. Do not manufacture a compatibility certificate.
Any damaged or missing evidence is prominent in both Web reading and export.

Progress events have schema revision, run ID, monotonically increasing sequence,
UTC occurrence time, elapsed duration, kind and an allowlisted payload. Types cover
job transition, case start, request start, observed transport phase, case commitment
and final-result commitment. Durations use monotonic time; persist real case/phase
spans rather than deriving chronology from summed request durations.

SSE uses sequence IDs and supports a snapshot plus later-event replay. A snapshot
includes its last committed sequence, preventing gaps or duplicates on reconnection.
Repeated/outdated IDs do not replay execution. A client ahead of available history
receives a reset snapshot. Coalesce activity notifications to at most one per second
per active request; send a heartbeat every 15 seconds. These do not consume API budget.
An unwritable progress/checkpoint store stops further upstream work and surfaces an
operational error. Do not continue a run whose mandatory evidence cannot be retained.

Events never contain credentials, raw model text or arbitrary unfiltered exceptions.
UI consumption cannot slow the worker: it reads persisted observations independently.

## 6. HTTP boundary

HTTP API is versioned under `/api/v1`. All mutations use the local session and CSRF
protection; errors carry stable English codes and safe Chinese-facing explanations.
No client-supplied filesystem path or shell command is accepted.

| Operation | Contract |
| --- | --- |
| `GET /catalog` | Installed contracts, profiles and case metadata; zero upstream calls. |
| `POST /plans` | Validate canonical target and create immutable preview. |
| `GET /plans/{id}` | Resolve the session-owned unexpired preview. |
| `POST /runs` | Start the reviewed plan with live consent and idempotency key. |
| `GET /runs` | Bounded, paginated history filters. |
| `GET /runs/{id}` | Lifecycle, snapshot and available verified result projection. |
| `GET /runs/{id}/events` | SSE observation with reconnect cursor. |
| `POST /runs/{id}/cancel` | Idempotent cancellation of queued/active work. |
| `GET /runs/{id}/evidence/{ref}` | Validated relative evidence identifier, safe text/download handling. |
| `POST /runs/{id}/exports` | Local generation with selected formats/evidence policy; no upstream calls. |
| `GET /runs/{id}/exports/{export_id}` | Download a committed export by opaque ID. |
| `GET/POST /presets`, `PUT /presets/{id}` | Read/save/edit schema-validated non-secret target presets. |

The table uses routes relative to `/api/v1`. Request/response shapes are packaged
and tested against generated OpenAPI. Plan start mismatches use 409, expired plans
410, invalid input 422 and exhausted queue 429. Evidence/export routes require local
session access and reject traversal, symlink escape and unknown references.

## 7. Credentials and local access

W1 supports existing `none` and `api_key` modes without arbitrary header overrides.
Browser-entered keys remain in per-job server/worker memory and travel to the worker
through a private IPC channel, never argv, shell text or a persisted target. Resolve
them through an application credential provider; do not broaden the public target
schema to permit literal secrets. CLI environment-variable resolution remains valid.

Server-provided credential references must use an explicit deployment allowlist.
The UI cannot enumerate arbitrary environment values. Clear entered form secrets
after start; never save them in localStorage, URLs, history, logs, SQLite or exports.
Lost queued secrets after restart are not recovered automatically; the job becomes
interrupted and a new explicit run requires re-entry or an available allowed reference.
Use existing in-memory sanitization before all evidence and error persistence.

Default direct serving binds to `127.0.0.1`. Docker listens internally on the required
container interface but its documented host mapping is loopback-only. Enforce Host
and Origin allowlists, local HttpOnly SameSite session cookies, CSRF checks on mutations,
and frame restrictions. SSE carries no session secret in its URL. API credentials
never go to the browser after submission. HTTP localhost cookies cannot rely on
HTTPS-only settings to function. Shared/public exposure is outside supported W1 use.

Treat upstream names, bodies and error text as hostile display content. Escape HTML,
serialize embedded report data safely, and never execute upstream HTML, scripts,
Markdown raw HTML or exported payload filenames. Target private-network access is
intentional for this local tool; keep existing URL validation, TLS checks, limits,
no redirects and no implicit retries.

## 8. Visual and report contracts

Use the approved light engineering style, compact metadata, clear typography,
aligned numbers and restrained semantic colors. Every status also has a label or
symbol. Charts carry captions, units, counting basis and accessible data tables.
Essential interpretation must not depend on color, hover, animation or scripting.

| Figure | Required semantics |
| --- | --- |
| Capability matrix | Declared groups/cases by behavior, protocol and environment; exact per-status counts and route to original cases. Do not collapse a mixed cell into an unqualified pass. |
| Status distribution | Count cases with explicit denominator; show all original statuses and separate operational pending/running during execution. Do not mix assertion and case counts. |
| Finding impact | Distinct affected cases per issue; overlapping issues need not sum to scope. Ranking is impact count, not inferred severity. |
| Execution timeline | Recorded spans with real gaps and terminal/ongoing markers. Old results without spans show labeled duration comparison or an unavailable explanation. |
| Expected/actual | Verified local projections, missing versus null, exact case/assertion references and explicit excerpt omissions. |

Do not substitute fake progress, invented capability scores, token speed from bytes,
or unsupported percentile claims. W1 may have only a few rows; preserve truthful
scope rather than populating the mockup's fictional groups. Multi-version comparison
is future work with explicit comparability controls and real versioned catalogs.

Web and exported views derive from the same validated ReportView. That projection
records source result identity/hash, evidence quality, figure IDs, counting units,
denominators, findings, source links and available execution spans. It never rescores
or normalizes responses to hide a violation. Old results retain original status and
contract identities; missing new metadata is visibly unavailable.

W1 exports:

- **HTML:** a standalone file, essential content rendered as HTML/SVG, embedded safe
  data and optional packaged interaction for matrix filters/details. Works from
  `file://` without fetch, server, CDN, remote fonts or analytics. Referenced evidence
  is either explicitly excluded or available in the full ZIP; no broken silent links.
- **Markdown + JSON:** equivalent facts and chart tables with figure IDs, captions,
  limitations, references, schema/presentation/rule identities and evidence pointers.
- **ZIP:** reports, selected sanitized evidence, a README explaining scope and how
  an agent should interpret statuses, and a SHA-256 manifest. Preview included data
  and exclusions before generation. Do not bundle deployment config, keys, service
  internals or unrelated run files. Retained responses may still contain private data.

Full-fidelity ZIP preserves source result/evidence bytes. A report-only export
explicitly omits evidence, includes integrity warnings/provenance and cannot claim
independently verified capture contents. Verify source references before generating
figures; missing/mismatched evidence gets visible qualifiers, never invented snippets.
Damaged sources may produce a labeled diagnostic report, not a clean evidence claim.
Export inputs and policy freeze under a unique export ID; generation never overwrites
an earlier export. Terminal partial runs can export verified checkpoints with a
partial label and operational schema, not an invalid final result masquerading as one.

Print styling retains conclusion, matrix, figures, captions and key references while
removing controls and exposing essential detail. PDF generation is not W1 scope;
browser printing is supported. Keyboard operation, focus restoration and narrow-screen
table access are required. Core content remains readable with scripts disabled.

## 9. Packaging and quality gates

Add optional Python Web dependencies and a `serve` subcommand; minimal CLI imports
must work without that extra. Retain the existing `runtime` Docker target and add
a `web` target with packaged UI assets and server dependencies. Both contain the
same engine version. Neither includes development sources/toolchains, Docker socket,
real configuration or credentials. Document nonroot output-volume ownership, read-only
root filesystem, bounded temporary storage and Docker host access on supported hosts.

Default Web port is 8765. Provide a local Compose example mapping
`127.0.0.1:8765:8765` and a persistent data volume. Direct CLI and replay containers
remain usable without published ports or the Web service. Registry publishing and
GitHub remote writes still require separate explicit owner authorization.

Develop and verify in the checked-in Linux/Python 3.12 Dev Container. Extend the
unified fast/full check graph with frontend static checks, packaged schema checks,
HTTP/job integration and browser tests. Use locked toolchains and synthetic HTTP
peers, including a delayed streaming peer. No CI credential or real model is needed.
GitHub CI should run relevant checks and build both image targets; unrun remote CI
or architecture builds cannot be reported as passed. Keep local/network preparation
separate from offline verification. One independent whole-W1 review follows sequential
implementation, not a repeat of the completed Stage A review.

## 10. Acceptance and handoff

| ID | Required observable evidence |
| --- | --- |
| W1-01 | CLI and Web plans/results agree on synthetic captures, after excluding documented run IDs/timing/environment metadata; existing CLI interfaces and exits remain valid. |
| W1-02 | Form validation and preview emit zero requests; duplicate starts emit one run; changed/expired plans and full queue cannot dispatch requests. |
| W1-03 | Delayed-peer progress shows observed phases, correct accounting and recoverable SSE snapshots; reconnect/refresh creates no extra upstream call. |
| W1-04 | Queued/active cancellation, parent loss, worker crash, service restart and finalization races preserve committed evidence and required-case accounting without automatic resend. |
| W1-05 | A persisted partial job is visibly distinct from a schema-valid final result; damaged/missing evidence cannot yield a clean report claim. |
| W1-06 | Browser credentials/hostile fields cannot leak into storage, events, logs, exports or executable markup; local request protections and safe evidence paths are exercised. |
| W1-07 | Matrices/charts exactly match original statuses and counting units, include accessible data, and navigate to the correct cases/findings. Old results lack invented timing. |
| W1-08 | Standalone HTML works with network unavailable, optional scripts disabled and keyboard use; exported figures, print/narrow layouts and JSON/Markdown agree. |
| W1-09 | ZIP selection, manifest hashes, local links, source-byte preservation and explicit report-only/partial omissions are verified. Export creates zero upstream calls. |
| W1-10 | Preset edits do not alter old runs; history survives restart and shows correct model/rule identities and terminal states. |
| W1-11 | Installed CLI-only/Web wheels and CLI/Web image targets pass their own acceptance, including volume persistence, shutdown and generic Docker host access. |
| W1-12 | Required Python/frontend/schema/architecture gates and an independent whole-W1 review are recorded, with remote CI, real endpoints and untested platforms reported separately. |

Implementation proceeds sequentially under a new W1 plan and
[ledger](../../harness/web-console-ledger.md). Record observed checks and decisions
there and in progress; large logs and private captures remain ignored. Final local
commits are part of delivery. No live endpoint request is authorized by design
approval; such verification needs a separately explicit target and request/time budget.

## 11. Self-review

Checked scope against the approved local visual direction and the original phased
design. Resolved operational/result-status separation, crash/checkpoint limitations,
credential loss, replay/idempotency, old-result timing gaps, offline report scripting,
source-evidence omissions, fictional catalog scope and CLI dependency independence.
The full W1 workflow is required; broader suites and version comparison remain
separate milestones. No product implementation or acceptance is claimed here.
