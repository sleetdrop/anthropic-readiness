# W1 Web console ledger

## Design and authorization

- 2026-10-16: owner chose individual local Docker deployment.
- 2026-10-16: owner approved the interactive console/report visual direction.
- Written specification: [local Web console](../superpowers/specs/2026-10-16-local-web-console-design.md),
  revision 1; explicitly approved by the owner on 2026-10-16.
- Implementation plan: [self-reviewed revision 1](../superpowers/plans/2026-10-16-local-web-console-implementation.md),
  14 sequential tasks; self-review completed and owner approval received on 2026-10-17.
- Execution: current chat, sequentially; owner chose the current checkout/Dev Container.
  W1 branch is `codex/local-web-console`, starting from `ad83593`. Tasks 1–6 are complete;
  tasks 7–14 and whole-W1 acceptance remain pending.

## Observed design checks

- Prior ignored synthetic visual mockup: browser view switching, matrix/finding
  navigation, failure filter and export-content preview were observed. This is
  design material, not production browser or export acceptance.
- Written spec self-review covers scope, lifecycle, source integrity, credential
  handling, CLI independence and old-result compatibility. Documentation-only
  checks are recorded separately from future product checks.
- Linux/Python 3.12 Dev Container: `UV_OFFLINE=1 uv run --frozen python
  scripts/check_docs.py` passed (`documentation_collaboration: passed`).
- `git diff --check` passed. No product fast/full suite, browser acceptance,
  image build or live endpoint check was run for these documentation-only changes.

## Historical boundaries

Frozen Stage A ledgers/manifests and private endpoint results remain historical.
Do not repeat the completed Stage A independent review or prior live calls.
W1 requires its own sequential plan, failing behavior tests, Linux verification,
image/browser/export acceptance and one independent whole-milestone review.

## Historical owner-requested pause (2026-10-16)

The owner paused work to close the laptop and leave work; the owner explicitly
resumed on 2026-10-17. No dependency installation, product worker or model request
was started in the paused planning turn. The local visual companion was stopped;
its ignored HTML/screenshots remain available and it can restart at the same project.

The pause checkpoint recorded these five self-review items, all resolved in plan
revision 1 on resume:

1. Put operational schema-loading validation in an adapter such as
   `operations/contracts.py`, keeping operational value records independent of I/O.
2. Make manager admission take plan ID/session/idempotency key and consult existing
   admission before expiring a preview, so a lost response cannot break safe retry.
3. Specify Web job versus exclusive assessment-output directory layout and CLI
   operational sidecars; the existing runner creates its output directory exclusively.
4. Bind the worker/result/checkpoints to the job's run ID through an optional shared
   execution argument; currently the runner allocates its result ID at finalization.
5. Add concrete assertion snippets to task test steps, check cross-task signatures,
   and verify documentation links. No W1 execution acceptance has been run.

## Resume and plan self-review (2026-10-17)

Completed the five recorded items without implementing product behavior. Also
specified parent-only event sequencing, hashed session owner bindings, explicit
local defaults, admission-created flags, source/operational snapshot ownership,
and real-browser versus pure-state test responsibilities. The plan maps all
W1-01 through W1-12 requirements to its 14 tasks. Existing specification approval
and current-chat sequential execution remain in force; await owner plan review.

Observed planning checks on 2026-10-17: the existing Linux/Python 3.12 Dev Container
passed `UV_OFFLINE=1 uv run --frozen python scripts/check_docs.py`
(`documentation_collaboration: passed`), and `git diff --check` passed. Only planning
and handoff documentation changed; product suites and all W1 acceptance remain unrun.

The owner subsequently approved execution; the observations below supersede that
planning-only checkpoint.

## Task 1: operational contracts and development preparation

In progress on `codex/local-web-console`, BASE `ad83593`. Existing full offline
baseline passed all eleven gates. RED log in the plan workspace recorded 55
behavior failures, followed by 69 passing core checks with the pending Node check
deselected. This does not complete the task. Python Web extra/dev packages are
locked and prepared; official Node 24.22.0 archive and npm/browser preparation remain
separate. No image, browser or real-endpoint outcome is implied.

Ruling: retain the recursive wheel resource checker because the new controlled
missing-schema inventory test already exercises it. If incorrect, an omitted
resource could remain undetected until Task 13's required installed-wheel acceptance.
Frozen Stage A records remain unchanged.

Task 1 verification: final fast graph passed all seven gates; the complete bare
pytest suite passed 245 tests. Official Node 24.22.0 archive checksum was verified,
Node/npm installed only inside the Dev Container, and exact npm versions/lock were
recorded in `web-toolchain.json`. Chromium OS/font/binary preparation remains
asynchronous; actual browser/new-image acceptance is not claimed. The combined
draft schema/lifecycle test was split into explicit shape checks and 49 transition
tests, preserving its intended coverage; actual names are reflected in the plan.

Task 1 committed as `dceceb9`; its task-done rerun passed 70 tests.

## Task 2: journal, checkpoints and observed spans

RED recorded ten initial behavior failures and two focused storage-boundary
failures. The first GREEN ran 15 targeted journal/span/evidence tests. A further
fault test proved durable events survive snapshot-write failure. A missing published
checkpoint initially escaped inventory verification; its failing test preceded
the required-inventory fix. Failed attempts remain in the ignored plan workspace.

Ruling: split operational storage and pure reduction into separate modules, adding
the reducer to the enforced pure dependency contract. This keeps locks/filesystem
work outside state reduction; if incorrect, additional modules could obscure the
single-writer boundary. Add an optional explicit `evidence_root` to RunJournal so
the future Web job layout and CLI sidecars share verification without guessing
paths; if incorrect, a wrong root fails hash/reference checks instead of publishing
a case. Snapshot replacement stays separate from exclusive source-evidence writes.

Final Linux verification passed all seven fast gates and all 257 pytest tests.
This establishes source/offline storage behavior; Web/browser/image acceptance
and endpoint behavior remain outside these observations.

## Task 3: shared application and observable bounded execution

CLI and application adapters now share document planning, explicit credential
providers and runner execution. Live CLI/replay write operational sidecars without
requiring Web packages. Run identity is allocated before observations, output
creation stays exclusive, and required cases receive verified checkpoints.
Cancellation is sticky across callback registration and interrupts active transport;
mandatory observation failures stop subsequent dispatch. Content activity is
coalesced and observations contain safe phase metadata rather than model text.

Observed RED: twelve initial behavior failures, no-auth credential resolution,
premature completion timestamps and checkpoint-accounting regressions. An
accounting fixture initially changed detached copies; corrected fixtures reproduced
two real failures against the isolated Task 2 implementation before current GREEN.
The original CLI timeout also caught a performance regression. Profiling attributed
12.735 of 14.414 seconds to repeated schema compilation; the unchanged timeout then
passed after caching compilation while retaining complete per-record validation.

Ruling: cache compiled immutable packaged operational schemas within each process.
If resources were replaced in a running installation, restart is needed to load
them; no document result is cached or validation weakened. Ruling: `commit_case`
returns its verified receipt, letting the runner timestamp completion after durable
publication. The synthetic delay test proves the ordering. Future adapters must
implement this refined source interface; persisted contracts do not change.

Final Linux verification: 17 task-specific tests, all seven fast gates, and all
274 pytest tests passed. The existing CLI, replay, HTTP/deadline and golden protocol
checks remain green. No W1 Web/browser/image, remote CI or real endpoint acceptance
is implied. Browser download remains asynchronous and source separation is retained.

## Task 4: frozen previews, presets and atomic admission

Implemented versioned SQLite indexes and immutable hashed preview/job-plan files.
Previews bind the hashed session owner and expire after 900 seconds. Transactions
deduplicate session/operation keys and enforce one admitted job per plan, at most
one active worker and eight waiting jobs. New keys for an already consumed plan
return that job; a new test needs a fresh explicit preview. Presets retain validated
non-secret targets without changing prior frozen plans. History has bound filters,
bounded opaque pagination and safe identifiers. URL resolution accepts only an
origin or explicit `/v1` base for automatic suffixes; no host alias substitution.

RED: 22 behavior failures preceded implementation. GREEN: 22 targeted tests,
all seven fast gates and all 296 pytest tests passed in Linux Python 3.12. Concurrent
duplicate admission produces one creator; lost-response retries still return the
same job after preview expiry. No upstream request is needed for these observations.

Ruling: add internal `get_admitted_plan(run_id)` for integrity-checked access after
queue admission, independent of preview expiry. If mistakenly used by a preview
HTTP route, it could bypass expiry; that route must retain session-bound `get_plan`.
Ruling: deduplicate across new keys for the same consumed plan as well; otherwise
double execution could occur. Repeat testing requires a new preview, as specified.

## Task 5: one owned worker and crash recovery

Implemented a nonblocking service ownership lock, one spawned worker and private
bounded JSON control/observation pipes. Credentials travel only through private
initialization; queued values stay in memory. The parent validates initial context,
sequences events and acknowledges persistence before the worker continues. Worker
checkpoints stay exclusive. Parent-control EOF stops subsequent dispatch and has
a bounded self-shutdown fallback. Cancellation allows five seconds, then forced
stop records interruption. Restart never resends; verified final artifacts can
repair the index only when their complete frozen target/plan identity matches.
Cancellation/completion terminal decisions serialize under the manager lock.

Observed RED: eleven initial lifecycle failures; unbound jobs after arbitrary
provider failure; continued admission after mandatory storage failure; stale
cancellation delivery after loop closure; contradictory result target identity;
and a private initial-context diagnostic entering persistence. These failures were
fixed without changing protocol expectations. Two fixture corrections are recorded:
worker discovery must use the owning process handle rather than another thread's
`/proc` child list, and JSONL corruption fixtures must keep one record per line.
The corrected target fixture reproduced the actual wrong-completion result.

Final Linux checks passed seven fast gates and all 314 pytest tests. Acceptance
uses disposable loopback peers, owned SIGTERM/forced-stop processes and pidfd-bound
cleanup. Verified checkpoint survival after parent termination, zero subsequent
requests, allowlisted credentials, safe IPC rejection, immutable terminal results
and no leaked live owned child. No real model request or W1 runtime-image/browser
acceptance occurred. Pinned browser/OS/font preparation has now exited successfully;
this is preparation only.

Rulings and costs:

- Bounded JSON plus per-message acknowledgement preserves the publication barrier;
  parent disk latency can increase execution time, while UI reading stays independent.
- The parent commits the terminal decision after verified result publication and
  before acknowledgement. Worker terminal transitions are validated advisory
  duplicates; they cannot mutate a committed terminal state.
- Queued snapshots have explicit null execution until begin, unless terminated
  before start. Consumers must handle this instead of inventing timing.
- Internal `JobStore.observe` keeps sequences/result pointers monotonic without
  bypassing lifecycle CAS; nonblocking locks reject a second service owner.

## Task 6: optional local HTTP boundary

Added lazy `serve`, explicit local bind/port settings, process-local expiring
sessions, host-only HttpOnly SameSite=Strict cookies, exact Origin/CSRF checks,
bounded strict JSON input, safe errors and private response headers. The app
lifespan owns exactly one manager and resolves only explicitly allowlisted server
credential names. New session/health response variants are closed packaged Web
contracts. Route exceptions are neither reflected nor traceback-logged; ordinary
CLI use still imports no optional Web dependency.

The initial test collection was blocked by Starlette's deprecated TestClient
fallback under the existing warnings-as-errors gate. HTTPX ASGITransport with
explicit lifespan/AnyIO asyncio fixtures preserves that gate without adding a
network dependency. After restoring collection seams, RED observed four failures
and nine missing-app setup errors. Later RED reproduced non-ASCII CSRF causing an
internal error and overflowing JSON numbers reaching dispatch; both now reject
safely. Test-only recursive-response inference and a draft exit-status assumption
were corrected from installed primary-source evidence, without weakening original
protocol goldens, schemas, warnings or timeouts.

Final Linux verification: 15 HTTP/serve tests, seven fast gates and all 329 pytest
tests passed. A real loopback server was started and signalled; no real model call
was made. The home page remains a boundary-stage placeholder until Task 11; neither
this result nor the prepared browser establishes GUI/image acceptance.

Rulings and costs:

- ASGITransport exercises the HTTP application without a socket; real serve,
  browser and image checks remain separate required gates.
- The locked Uvicorn source replays SIGTERM after lifespan shutdown. Serve
  acceptance requires that signal status and rejects arbitrary/forced exits;
  future dependency changes need review of this new command's contract.
- Closed session/health response variants extend the unreleased Web API schema;
  Task 7's generated OpenAPI comparison must check the same packaged shapes.

## Task 7: versioned operations API and resumable progress

Added catalog/preview/start/history/cancel/preset/evidence routes, closed packaged
wire contracts and OpenAPI derived from exactly those shapes. Preview makes no
upstream request. Duplicate start returns the same admitted job before resolving
credentials. Raw credentials remain start-only, and a raw value plus a server
reference is rejected. Evidence uses opaque inventory IDs and verified bytes with
a fixed attachment content type. Traversal, symlink and changed evidence are rejected.
SSE is an observer: snapshot/replay/reset, 15-second heartbeat, terminal closure and
disconnect do not start or cancel assessments. Parent-coordinated journal reads
preserve sequence consistency independently of browser backpressure.

RED: eight initial behavior failures. Initial GREEN passed eight tests, then three
additional tests covered private credentials/lazy duplicate binding, idempotent
queued/active cancellation and disconnect of an actual active worker. Strict typing
caught framework-hook assignment and asynchronous return annotations. A typed
FastAPI subclass supplies the OpenAPI extension point; no type gate was suppressed.
After the owner resumed from the account-limit pause, seven fast gates and 40
API/events/security/worker lifecycle tests passed in Linux Python 3.12. Duplicate
starts and repeated cursor reads retained exactly three synthetic requests. Full
pytest passed all 340 tests in 69.58s; this does not establish GUI/browser/image or real endpoint acceptance.

Rulings and costs:

- Initial and ahead cursors receive a current snapshot; valid saved cursors replay
  only later entries under the parent manager lock. This avoids stale events over
  a newer snapshot. Consumers must retain their saved snapshot or request `after=0`.
- Credential references resolve only after idempotent admission. A new invalid
  reference consumes a terminal error job; another attempt needs a fresh preview.
- New closed response variants and a shared contract-derived OpenAPI extend the
  unreleased Web API only. Framework extension changes need explicit review.
- Ambiguous credential sources are rejected; opaque evidence IDs and fixed safe
  attachments avoid client-controlled paths or active upstream content. Clients
  must explicitly choose a credential source and use the returned inventory.

## Task 8: verified shared report projection

Added an I/O-only source loader and deterministic report projection. Final results
retain their original cases/assertions and source-byte hash. Partial runs expose
only advertised, hash-verified checkpoints with explicit pending scope and no
fabricated final RunResult. Evidence inventory and assertion references are checked
before local field diagnostics; damaged evidence retains original verdicts but has
no snippets. Operational timing requires matching run, frozen target/contract/plan,
source hash, case membership and valid span coordinates. Unsafe/mismatched sidecars
become visible diagnostics beside a valid original result. Partial target bindings
also recompute the frozen configuration fingerprint.

Four stable figures describe exact capability counts, status distribution, distinct
finding impact and observed spans (or labeled duration-only comparison for legacy
sources). Current groups match all four real catalog IDs: messages, streaming and
forced tool selection, explicitly excluding a full tool loop. All original states,
counting units, denominators and untested client/version semantics remain explicit.
The projection retains full source provenance and original assertion/reason indexes
for later agent interpretation without changing result/capture contracts.

Observed RED: 18 initial behavior assertions; additional provenance omission,
first-call schema I/O, an unsafe sidecar hiding a valid result and an unbound partial
target. All received fixes with regression tests. The earlier 362-test
pass preceded the final two sidecar fixes. Final verification passed all seven fast
gates and all 364 pytest tests in 74.07s.
Report/source and unchanged report acceptance currently pass 39 tests. No browser,
new renderer/runtime-image or real endpoint acceptance is implied.

Rulings and costs:

- Add closed provenance plus assertion/reason indexes to the unreleased report-view
  1.0 contract and its Web API embedding. The initial draft omitted facts needed by
  unchanged CLI details. Consumers of that unshipped draft would need to update.
- Precompile the immutable projection schema at model initialization; every build
  still validates, with no resource I/O during projection. Schema replacement needs
  a process restart.
- Partial views use advertised verified checkpoints only; unavailable records stay
  unassessed pending with diagnostics. Consumers must inspect partial scope and
  limitations rather than interpreting a status color alone.
- Exact known catalog IDs define the three truthful groups, with a coverage gate;
  unknown historical IDs have an explicit other group. Catalog changes must update
  this presentation mapping before that gate passes.

## Task 9: progressive visual reports and compatible CLI adapters

The new presentation 2.0 renders a capability matrix, case status distribution,
distinct finding impact and observed timing (duration-only for legacy results).
Native SVG figures include units/captions and exact equivalent data tables. Core
content and details are server-rendered; packaged optional JavaScript filters and
opens the original case records without fetching. Standalone HTML inlines its
assets with a restrictive CSP. Print/narrow styles, labels alongside colors,
keyboard navigation, escaped local-field comparisons and explicit evidence quality
retain the engineering reading order. JSON projection, Markdown figure tables and
full original assertion/provenance details use the same validated view.

Public CLI reporting functions are now thin adapters. Automatic reports remain;
explicit rerender preserves original result and verified evidence bytes, writes a
new projection/manifest, and keeps exclusive output semantics. Original run IDs
and contract/source hashes remain in the appendix. Unsafe capture strings stay data.

RED covered three initial Python visual/export failures and two JS helper failures.
Unchanged report regressions then exposed Markdown excerpt escaping and early
navigation-label ordering. Further RED found formatting-induced CSP digest mismatch
and an unmarked ongoing span; both were fixed. The lone changed legacy expectation
is the approved presentation manifest version 1.2 to 2.0. All protocol/result/capture
expectations remain untouched. Final verification passed seven fast gates, frontend types/lint/format,
two Node tests and all 370 pytest tests in 76.05s;
real browser/offline/print visual acceptance remains Task 12 work.

Rulings and costs:

- Retain the documented public reporting calls as shared-projection adapters and
  remove the obsolete renderer. Consumers of private legacy helper names need the
  new public projection/rendering API.
- Presentation 2.0 intentionally updates the old manifest expectation. Consumers
  requiring presentation 1.2 must retain an older artifact; original source contracts
  remain unchanged.
- Use matched current/future frontend format globs instead of individually missing
  later-task paths. Overall unmatched inputs still fail; future inventory/browser
  gates must reject missing mandatory modules rather than recording zero checks.
- Standalone reports use textual evidence pointers, avoiding silent broken local
  attachment links. Full ZIP users navigate the verified manifest/evidence tree.

The initial full attempt passed 368 tests and failed the ongoing fixture: its array
helper validates by copying, so the edited figure was not written back. After fixing
the fixture, marker-less rendering reproduced RED before restoring the implementation.
The partial-checkpoint fixture now similarly writes back its one-request prefix.
A separate actual RED found a partial replay labeled live; frozen zero planned
requests now preserves replay mode. This is the only live/replay inference for a
partial source; a future zero-request live plan needs an explicit mode revision.
All prior failing attempts remain retained. Final source verification passed.

## Task 10: immutable on-demand exports

Added schema-checked export policy, preview, publication and downloads. Each export
uses a new opaque ID and freezes selected report formats, original source identity,
evidence-delivery policy and omissions. ZIP delivery contains Chinese README/agent
interpretation, source/projection, selected reports, optional verified sanitized
captures and a SHA-256/byte-count manifest. Final result/evidence/checkpoint bytes
are preserved; partial runs include a frozen operational snapshot and advertised
verified checkpoints without a fabricated result.json. Unrelated configuration,
credentials and logs are excluded. Damaged sources support qualified report-only
delivery, while full-evidence publication is rejected.

Source bytes are rehashed while copied. A schema-validated exclusive record is the
last publication barrier; interrupted generation can leave an unavailable orphan
folder, never a downloadable committed artifact. Downloads verify the actual returned
bytes and retain prior export IDs. Preview and publication share selection,
omissions and evidence-delivery metadata. The default download is a ZIP; an enum
format query offers a selected standalone HTML/Markdown/JSON without accepting paths.

Observed RED: eight initial behavior failures, then mismatched preview omissions
and delivery metadata. Initial eight-test GREEN preserved failed cases and partial
checkpoints, detected source replacement during copying and retained exactly three
synthetic requests across HTTP preview/export/download. Additional regressions cover
damaged-source qualification, changed/unselected standalone files and publication
failure. Strict type/list/nullable/re-export errors and lint failures were repaired
without ignores or changed protocol expectations. Final verification passed seven fast gates, 39 export/source/evidence/API
regressions and all 382 pytest tests in 83.94s.

Rulings and costs:

- Source verification and evidence delivery are separate optional operational
  metadata. Locally verified excerpts do not imply captures are included; consumers
  must read delivery notices/omissions rather than treat a report-only export as an
  independently verifiable evidence package.
- Always retain a ZIP transport with README/manifest and selected formats, with an
  allowlisted format query for standalone files. Clients can use the default ZIP;
  no client-supplied filename/path is accepted.
- Publish the exclusive record last and verify exact returned bytes. Failed orphan
  directories consume local disk but remain unavailable through download APIs.
- Bound selected payloads/artifacts at 256 MiB with an actionable error. Larger
  captures need smaller selections or a future streaming path; sources and failed
  attempts are never erased or truncated.
