# Local Web Console and Visual Reports Implementation Plan

Status: DRAFT checkpoint at the owner's explicit pause. Tasks are not started.
The self-review below is incomplete; do not treat its closing handoff paragraph
as completed review. Resume with the open items in the W1 ledger before asking
the owner to approve this plan.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Repository instructions require sequential native execution, not per-task implementer agents; arrange one independent whole-W1 review at the end.

**Goal:** Deliver the approved local Docker Web workflow and visual offline reports while retaining independent CLI operation and the original evidence-led judgments.

**Architecture:** CLI and HTTP adapt shared planning/execution/report services. A single scheduler owns a persistent queue and one child worker; the parent alone sequences operational events. Server-rendered pages and packaged browser modules consume the same verified report projection used by offline exports.

**Tech Stack:** Python 3.11+ package, Linux/Python 3.12 Dev Container, FastAPI/Uvicorn/Jinja2 optional Web extra, SQLite, private multiprocessing pipes, SSE, native SVG, strictly checked JavaScript/JSDoc, Node 24 LTS development tooling, npm lock, Playwright Chromium.

**Spec:** [Approved W1 specification](../specs/2026-10-16-local-web-console-design.md), revision 1, approved by the owner on 2026-10-16.

## Global Constraints

- "Milestone **W1** delivers this complete local workflow against the existing four Stage A cases."
- "The standalone CLI does not require the Web extra, SQLite job store, active service or browser."
- "The local service has one scheduler and at most one active assessment. Queue capacity is eight waiting jobs"; reject overflow without a request.
- "A preview freezes the canonical resolved plan and fingerprint under an opaque ID for 15 minutes."
- "Allow five seconds for checkpoint/finalization" before hard termination; record forced termination as interrupted.
- "Coalesce activity notifications to at most one per second per active request; send a heartbeat every 15 seconds."
- "Keep the existing result 1.0 and capture reader/writer contracts"; new operational schemas start at 1.0 and report presentation becomes 2.0.
- "Default Web port is 8765"; Compose maps `127.0.0.1:8765:8765`.
- "Node is development/CI tooling only"; no Node, browser, Docker socket or real target data in runtime images.
- "Core content remains readable with scripts disabled"; offline HTML makes no fetch/CDN/font/analytics request.
- Source, comments, machine fields and commits are English; reader-facing reports default to Simplified Chinese.
- Preserve immutable cases, assertions, limits, required accounting, evidence bytes and old failed attempts. Never edit frozen Stage A manifests/ledgers to make W1 pass.
- Use meaningful assertion-level RED before behavior changes. A collection error, missing executable, zero tests or skipped gate is not RED or PASS evidence. Minimal signatures may enable collection; they must not implement the behavior under test.
- Execute commands below inside the Dev Container unless explicitly identified as host Docker orchestration. Prepare once with network, then use `UV_OFFLINE=1 uv run --frozen ...`; do not retry installs on every check.
- No new live endpoint calls, remote writes or registry publishing are part of this plan.
- Record each task's RED/GREEN, checks, source commit and limits in [the W1 ledger](../../harness/web-console-ledger.md) and progress. Each task ends with a scoped English local commit.

## Review Focus

1. A start response is lost or two tabs submit it: exactly one admitted job/request sequence, including after preview expiry (Tasks 4, 7).
2. A parent exits between worker checkpoint and terminal indexing: retained evidence stays readable, no orphan sends another request and no silent restart occurs (Tasks 2, 5).
3. A target body or filename contains `</script>`, HTML or path escapes: browsing and standalone export never execute it or read outside the run (Tasks 6, 9, 10).
4. Evidence is replaced between verification and archive copying: reject a clean export rather than signing different copied bytes under the old hash (Task 10).
5. A browser reconnects with an expired session or cursor ahead of the journal: show a recoverable state without duplicate execution or invented completion (Tasks 6, 7, 11).

## File and interface map

Paths below are relative to the repository. Do not split the existing validator modules.

| Unit | Files and responsibility |
| --- | --- |
| Operational values/ports | `operations/models.py`, `operations/ports.py`: immutable records, lifecycle and observer/control interfaces; no Web/SQLite imports. |
| Shared application | `application.py`, `credentials.py`: build plans from canonical documents and bind ephemeral credentials; no framework types. |
| Durable observations | `operations/journal.py`, `operations/checkpoints.py`: atomic immutable records, ordered events and verified recovery. |
| Engine integration | existing `runner.py`, `transport.py`, `config.py`: observer hooks, cancellation and document loading without changing judgments. |
| Local jobs | `jobs/store.py`, `jobs/plans.py`, `jobs/manager.py`, `jobs/worker.py`: SQLite indexes/admission, scheduler and private worker IPC. |
| HTTP | `web/settings.py`, `web/security.py`, `web/app.py`, `web/api.py`, `web/events.py`, `web/pages.py`, `web/serve.py`: local access, API, SSE, pages and lifecycle composition. |
| Report projection | `report_models.py`, `report_sources.py`, `report_view.py`: verified I/O loading followed by pure visual projection. |
| Rendering/export | `report_rendering.py`, `exports.py`, existing `reporting.py`: shared progressive HTML/Markdown, byte-preserving packaging and compatible public wrappers. |
| Browser resources | `resources/web/{base,configure,run,history}.html`, `resources/web/{app,forms,progress,report}.js`, `resources/web/app.css`, `resources/report-v2.html`, `resources/report-v2.js`, `resources/report-v2.css`. |
| Contracts | `resources/schemas/{job,execution,checkpoint,progress-event,report-view,export-manifest,web-api}.schema.json`: packaged operational/API schemas; original result/capture schemas remain unchanged. |
| Harness | root npm/TypeScript/ESLint/Prettier/Playwright configs, `tests/browser`, `scripts/browser_fixture.py`, `scripts/check_frontend.py`; extend existing check/package/image/CI scripts. |

Shared types established in Task 1:

- `JobState = Literal['queued','running','cancelling','completed','cancelled','interrupted','error']`.
- `EventKind = Literal['job_transition','case_started','request_started','transport_phase','case_committed','result_committed']`.
- `FrozenPlan(id: str, session_id: str, created_at: str, expires_at: str, config_sha256: str, target: JsonObject, profiles: tuple[str, ...], plan: JsonObject)`.
- `JobRecord(id: str, plan_id: str, state: JobState, created_at: str, updated_at: str, last_sequence: int, result_path: str | None)`.
- `WorkerEvent(kind: EventKind, occurred_at: str, elapsed_ms: float, payload: JsonObject)`; no sequence until the parent accepts it.
- `ProgressEvent(schema_version: str, run_id: str, sequence: int, event: WorkerEvent)` with `to_json() -> JsonObject` on each persisted record.
- `ExecutionObserver.emit(event: WorkerEvent) -> None` and `ExecutionObserver.commit_case(case: JsonObject, refs: tuple[EvidenceRef, ...]) -> None` are protocols. Case commit must finish before its completion becomes visible.
- `CancelToken.cancel(reason_code: str) -> None`, `.requested: bool`, `.reason_code: str | None`, with thread-safe reads/writes.
- `CredentialProvider.resolve() -> str | None`; a provider is already bound to its target/allowed reference. No raw secret in a value record.

## Commands and preparation policy

`P <paths>` below means `UV_OFFLINE=1 uv run --frozen python -m pytest -q <paths>`.
`F` means `UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite fast`.
`A` means the same entry point with `--suite full` after all new gates exist.
All selected tests must execute, with zero failures/errors/unexpected skips.

Task 1 resolves compatible stable releases once: Web ranges
`fastapi>=0.115,<1`, `uvicorn>=0.34,<1`, `jinja2>=3.1,<4`; dev packages TypeScript,
ESLint, typescript-eslint, Prettier, `@playwright/test`, `@types/node` and an
accessibility checker for browser tests. Save exact npm direct versions and all
transitives in `package-lock.json`, Python resolutions in `uv.lock`. Choose the
newest published stable Node 24 patch from the official release index at preparation
time, record its version, per-architecture SHA-256 and matching official image digest
in `docs/harness/web-toolchain.json`; do not leave floating image tags in the commit.
This is a preparation action, not a claim that those versions are already installed.

Use Node's built-in test runner and `tsc --allowJs --checkJs --noEmit --strict` for
browser modules. Runtime modules are plain packaged JavaScript. Download Playwright's
locked Chromium and required Linux libraries during preparation, then run browser
checks offline. Missing browser/library is BLOCKED. Respect patient network preparation
and roughly ten-minute download-progress checks; never record a waiting download as a test.

Primary compatibility references checked during planning:
[FastAPI templates](https://fastapi.tiangolo.com/advanced/templates/),
[Playwright requirements](https://playwright.dev/docs/intro#system-requirements),
[Node release schedule](https://github.com/nodejs/Release/blob/main/schedule.json).

### Task 1: Operational contracts and optional Web tooling

**Files:** Create `operations/__init__.py`, `operations/models.py`, `operations/ports.py`,
the seven schema files above, `package.json`, `package-lock.json`, `tsconfig.json`,
`eslint.config.js`, `.prettierignore`, `.prettierrc.json`, `docs/harness/web-toolchain.json`;
modify `pyproject.toml`, `uv.lock`, `Dockerfile` dev target, `.devcontainer/devcontainer.json`,
`scripts/validate_resources.py`, `scripts/check_package.py`; test `tests/unit/test_operations.py`,
`tests/harness/test_web_toolchain.py`.

**Interfaces:** Produces the shared types above and `validate_operational(document: JsonObject, schema_name: str) -> None` in `operations/models.py`, delegating schema I/O through a boundary in `schema.py`; keep immutable value construction independent of resource loading. Runtime CLI never imports FastAPI while discovering commands.

- [ ] **RED:** `test_operational_contracts_reject_secret_and_illegal_state` asserts extra `credential` fields, nonterminal-to-terminal violations, negative sequence and unknown event kinds are rejected; every new resource is in an installed-wheel inventory. `test_web_extra_is_optional` asserts `import anthropic_readiness.cli` succeeds without Web packages. Run the two named test files and observe assertion failures.
- [ ] **Implement:** Define records/ports and packaged schemas, add the optional `web` extra plus Web packages to the dev dependency group, prepare/pin the toolchain as above, and include Node/browser preparation only in dev stages. Extend schema/resource inventory without changing original rule/capture/result content.
- [ ] **GREEN:** Run `P tests/unit/test_operations.py tests/harness/test_web_toolchain.py`, resource validation and `F`; record exact resolved versions and any pending browser download honestly.
- [ ] **Commit:** `feat: define operational contracts and optional web tooling`.

### Task 2: Durable journal, checkpoints and execution spans

**Files:** Create `operations/journal.py`, `operations/checkpoints.py`;
test `tests/integration/test_run_journal.py`, `tests/unit/test_execution_spans.py`.

**Interfaces:** `RunJournal(root: Path, run_id: str).append(event: WorkerEvent) -> ProgressEvent`,
`.after(sequence: int) -> tuple[ProgressEvent, ...]`, `.snapshot() -> JsonObject`;
`CheckpointStore(root: Path, run_id: str).commit(case: JsonObject, refs: tuple[EvidenceRef, ...]) -> JsonObject`,
`.load_verified() -> tuple[JsonObject, ...]`. Only the parent or standalone CLI owns a journal writer.

- [ ] **RED:** `test_case_is_visible_only_after_evidence_and_checkpoint` asserts a failed checkpoint write leaves no case-completion event. `test_restart_retains_committed_prefix` simulates a torn last event and preserves valid prefix/checkpoints with an interruption warning, never erasing an attempt. `test_spans_preserve_real_gaps` asserts a deliberate gap is visible rather than reconstructed from duration sums. Run the two files.
- [ ] **Implement:** Use exclusive safe paths/atomic file publication, run-scoped writer locking and schema-checked JSONL. Tolerate only an incomplete last event as uncommitted; corrupt interior records stop recovery and raise a diagnostic. Persist UTC plus monotonic elapsed spans; no raw text in payloads. Verify referenced hashes before checkpoint acceptance.
- [ ] **GREEN:** Run `P tests/integration/test_run_journal.py tests/unit/test_execution_spans.py` and existing evidence integration tests. A storage failure cannot publish successful completion.
- [ ] **Commit:** `feat: persist ordered execution events and verified checkpoints`.

### Task 3: Shared application, observable runner and cancellation

**Files:** Create `application.py`, `credentials.py`; modify `config.py`, `runner.py`,
`transport.py`, `cli.py`; test `tests/unit/test_application.py`, `tests/integration/test_execution_observer.py`,
`tests/integration/test_execution_cancel.py`; reuse existing runner/transport/CLI tests.

**Interfaces:** `config.target_from_document(value: JsonObject) -> TargetConfig` is the existing loader validation extracted from file I/O; `load_target` still rejects duplicate YAML keys.
`application.build_plan(target: JsonObject, profiles: Sequence[str]) -> RunPlan`;
`application.run_assessment(plan: RunPlan, output: Path, *, credentials: CredentialProvider, observer: ExecutionObserver | None = None, control: CancelToken | None = None) -> RunResult`.
Extend `execute_run` with optional observer/control/provider keyword arguments, preserving old callers/environment behavior.
`HttpTransport(..., observer: ExecutionObserver | None = None, control: CancelToken | None = None)` emits only observed safe phase events.
Provide bound `EnvironmentCredentials` and `MemoryCredentials` implementations in `credentials.py`.

- [ ] **RED:** `test_cli_and_observed_run_keep_identical_assertion_semantics` compares assertion IDs/versions/required/status/reasons, plan fingerprints and response-body hashes for the same synthetic target; exclude only UUIDs, timestamp/duration/environment fields and timing-bearing evidence metadata. `test_cancel_before_transport_callback_registration` proves no dispatch through the cancellation race. `test_observer_failure_stops_next_request` asserts no later request after a mandatory write failure. Run the three new files.
- [ ] **Implement:** Emit case/request/observed headers/content/validation/commit phases, coalesce content activity to one event/second, and checkpoint all completed or precondition cases. Do not label “connecting” as established TCP or a first event as first output token. Honor token before dispatch and during transport; unify signal cancellation with the token and preserve existing CLI exits. Standalone CLI gets a local journal/checkpoint observer, keeping machine stdout stable and reports automatic.
- [ ] **GREEN:** Run new tests plus `tests/acceptance/test_cli.py`, `test_runner.py`, `test_replay.py`, existing transport/deadline tests, then `F`. Source result/capture schemas and golden protocol expectations remain unchanged.
- [ ] **Commit:** `feat: share observable bounded execution across adapters`.

### Task 4: Persistent plans, presets and atomic queue admission

**Files:** Create `jobs/__init__.py`, `jobs/store.py`, `jobs/plans.py`;
test `tests/integration/test_job_store.py`, `tests/unit/test_web_plans.py`.

**Interfaces:** `JobStore(root: Path)` provides `create_plan(target: JsonObject, profiles: tuple[str, ...], session_id: str, *, now: datetime) -> FrozenPlan`,
`get_plan(plan_id: str, session_id: str, *, now: datetime) -> FrozenPlan`,
`admit(plan_id: str, session_id: str, idempotency_key: str, *, now: datetime) -> JobRecord`,
`get_job(run_id: str) -> JobRecord`, `transition(run_id: str, expected: JobState, next_state: JobState) -> JobRecord`,
`history(filters: JsonObject, cursor: str | None, limit: int = 50) -> JsonObject`,
`save_preset(preset_id: str | None, target: JsonObject) -> str`, `presets() -> tuple[JsonObject, ...]`.
`jobs.plans.resolve_messages_url(value: str, mode: Literal['base','messages']) -> str`.

- [ ] **RED:** `test_duplicate_start_after_lost_reply_is_one_job` asserts identical admission returns the original job even if its preview subsequently expires; a reused key with different input rejects. `test_capacity_is_one_active_plus_eight_waiting` asserts ninth waiting job fails and queued plans survive preview expiry. `test_presets_cannot_change_old_plan` verifies old bytes/fingerprints. `test_expired_or_foreign_plan_is_rejected` covers 900-second TTL and session ownership. Run both files with a deterministic clock.
- [ ] **Implement:** Use SQLite transactions/unique indexes for session+idempotency key and one admitted job per plan, schema-versioned migration under the ownership lock, immutable plan files and safe preset records. Page limits are 1–100, default 50, opaque cursors and bound SQL parameters. URL helper appends `/v1/messages` only to an origin or `/messages` to an explicit `/v1` base; other base paths require the full URL mode. Never substitute host aliases.
- [ ] **GREEN:** Run the two files with concurrent admission and clock tests; local planning/URL handling causes zero upstream requests. Classify expired/mismatch/overflow with stable codes for Tasks 6–7.
- [ ] **Commit:** `feat: persist frozen plans presets and bounded job admission`.

### Task 5: One owned worker, safe IPC and restart reconciliation

**Files:** Create `jobs/manager.py`, `jobs/worker.py`;
test `tests/integration/test_job_manager.py`, `tests/integration/test_worker_lifecycle.py`,
`tests/fixtures/http/slow_peer.py`.

**Interfaces:** `JobManager(store: JobStore, *, credential_allowlist: Mapping[str, str])` exposes
`start() -> None`, `submit(plan: FrozenPlan, idempotency_key: str, credentials: CredentialProvider) -> JobRecord`,
`cancel(run_id: str) -> JobRecord`, `snapshot(run_id: str) -> JsonObject`, `close() -> None`.
`jobs.worker.worker_main(plan: JsonObject, root: Path, control: Connection, observations: Connection) -> None` uses spawn, not a shell. Handshake/secret/control messages are private; only validated `WorkerEvent` messages may enter persistence.

- [ ] **RED:** `test_parent_loss_after_checkpoint_never_sends_next_request` checks synthetic peer call count and retained checkpoint after terminating the parent. `test_force_stop_after_five_seconds_is_interrupted` uses an unresponsive disposable worker. `test_cancel_completion_race_has_one_terminal_state` and `test_restart_never_redispatches` pin finalization and restart behavior. `test_secret_never_enters_persisted_worker_messages` scans synthetic artifacts. Run both lifecycle files.
- [ ] **Implement:** Own one process handle and a filesystem service lock; keep eight queued secrets in memory only, release per-run secrets at termination, validate IPC shape/size and transport them over private pipes, never argv/environment. Parent assigns event sequences after checking referenced commits; worker never concurrently writes the parent's journal. A parent-channel watchdog sets cancellation on EOF, with bounded self-shutdown if necessary. Restart reconciles valid final artifacts or records interruption, with no resend. Storage failure stops scheduling/worker requests.
- [ ] **GREEN:** Run lifecycle/store/journal tests against slow peers, SIGTERM and deliberate crashes. Verify no leaked owned processes and distinguish cancelled, interrupted and application error.
- [ ] **Commit:** `feat: supervise single-worker jobs with durable crash recovery`.

### Task 6: Local HTTP boundary and CLI serve entry

**Files:** Create `web/__init__.py`, `web/settings.py`, `web/security.py`, `web/app.py`,
`web/serve.py`; modify `cli.py`; test `tests/integration/test_web_security.py`,
`tests/acceptance/test_serve_command.py`.

**Interfaces:** `WebSettings` is a frozen dataclass with `host: str = '127.0.0.1'`,
`port: int = 8765`, `allowed_hosts: tuple[str, ...]`, `allowed_origins: tuple[str, ...]`,
`credential_env_allowlist: tuple[str, ...]`, `max_body_bytes: int = 65536` (remaining fields have explicit safe defaults).
`create_app(*, data_root: Path, settings: WebSettings) -> FastAPI`;
`serve(data_root: Path, settings: WebSettings) -> int`.
CLI adds `serve --data-dir PATH [--host HOST] [--port PORT] [--credential-env NAME]` with lazy optional imports.

- [ ] **RED:** `test_cross_origin_mutation_and_rebinding_host_rejected` checks Host, missing/wrong Origin, CSRF and cookies; `test_expired_session_can_bootstrap_without_restarting_job` pins recovery. `test_oversized_and_nested_body_rejected_before_dispatch` verifies 64 KiB bound and strict JSON depth. `test_missing_web_extra_returns_actionable_error` verifies CLI-only import/help and clear serve error. Run both files.
- [ ] **Implement:** Create process-local random sessions/CSRF bootstrap, HttpOnly SameSite=Strict host-only cookies, no credential URL, no permissive CORS, `frame-ancestors 'none'`, `nosniff`, no-store for private pages/API. Use `strict_json` and operational schemas before dispatch. Return structured `{error: {code, message}}`; sanitize exceptions. Bind one Uvicorn worker; acquire/release manager under app lifespan. Resolve server secrets only through the explicit allowlist.
- [ ] **GREEN:** Run HTTP security and serve/CLI acceptance with disposable data roots; no real endpoint or shared unauthenticated deployment is needed.
- [ ] **Commit:** `feat: expose a protected local web service and serve command`.

### Task 7: Run APIs, history and reconnectable SSE

**Files:** Create `web/api.py`, `web/events.py`; modify `web/app.py`, API schema;
test `tests/integration/test_web_api.py`, `tests/integration/test_web_events.py`.

**Interfaces:** `api.router` mounts the approved `/api/v1` catalog/plan/run/cancel/preset/evidence routes.
`events.event_stream(run_id: str, after: int, manager: JobManager) -> AsyncIterator[str]`;
SSE endpoint reads `Last-Event-ID`, sessions and safe cursors. Bind the Task 4/5 store/manager during app lifespan, no independent scheduler per route.

- [ ] **RED:** `test_preview_and_duplicate_start_request_counts` checks zero calls for catalog/preview and exactly the planned count despite duplicate POSTs. `test_snapshot_cursor_gap_and_ahead_reset` verifies committed snapshot+events, repeated cursor and ahead reset; `test_sse_heartbeat_never_dispatches` asserts a 15-second heartbeat through injected clock. `test_history_and_evidence_are_scoped_and_safe` covers 422/409/410/429 semantics, traversal/symlinks and fixed safe download content types. Run both files.
- [ ] **Implement:** Map schema-validated payloads to shared services; credentials are a separate start-only field/reference, never returned. Query parameter `after` supports first connection from a saved snapshot; subsequent reconnect uses event IDs. Serialize snapshot plus later events atomically under journal read coordination. Handle a terminal job without endless polling; disconnect SSE without cancelling the worker. Evidence is plain escaped display or attachment, never active upstream HTML.
- [ ] **GREEN:** Run Web API/events/security/job lifecycle tests. Capture peer call counts before/after repeated reconnect and confirm equality.
- [ ] **Commit:** `feat: add planned execution history evidence and resumable progress APIs`.

### Task 8: Verified shared report projection

**Files:** Create `report_models.py`, `report_sources.py`, `report_view.py`;
modify `report_reading.py` only to share existing pure explanations; test
`tests/unit/test_report_view.py`, `tests/integration/test_report_sources.py`.

**Interfaces:** `ReportSource` contains `result: RunResult | None`, `result_sha256: str | None`,
`case_records: tuple[JsonObject, ...]`, `execution: JsonObject | None`,
`evidence_verification: JsonObject`, `diagnostics: tuple[JsonObject, ...]`, `plan: JsonObject`.
`ReportView(document: JsonObject)` validates against report-view 1.0.
`report_sources.load_report_source(root: Path) -> ReportSource` performs all I/O;
`report_view.build_report_view(source: ReportSource) -> ReportView` is pure.

- [ ] **RED:** `test_matrix_counts_all_original_states_without_rescoring` asserts mixed status cells and distinct affected-case counts. `test_old_result_has_no_fabricated_timeline` requires duration-only/unavailable instead. `test_partial_checkpoint_is_not_final_result` keeps pending scope explicit. `test_missing_evidence_removes_snippets_and_warns` pins damaged-capture behavior. Run both files, including current core fixtures.
- [ ] **Implement:** Reuse original grouped explanations and verified diagnostics; add stable figure IDs, exact counting units/denominators, sources and independently versioned projection metadata. Use actual catalog metadata: W1 groups message, streaming and forced tool selection; never call the last one a complete tool loop. Bind execution sidecar run ID, source result hash and planned membership before drawing spans. Keep source result bytes unchanged.
- [ ] **GREEN:** Run report-view/source and all existing report acceptance tests relevant to verdict/evidence preservation. New presentation expectations are intentional 2.0 changes, not silent edits of protocol goldens.
- [ ] **Commit:** `feat: derive truthful visual reports from verified assessment sources`.

### Task 9: Progressive visual reports and CLI report compatibility

**Files:** Create `report_rendering.py`, `resources/report-v2.{html,js,css}`;
modify `reporting.py`; test `tests/acceptance/test_visual_reports.py`,
`tests/frontend/report.test.js`; retain all existing reader/report tests.

**Interfaces:** `report_rendering.render_report_html(view: ReportView) -> str`,
`render_report_markdown(view: ReportView) -> str`; retain public
`render_html`, `render_markdown`, `write_reports`, `render_from_file` entry points as adapters.
`report-v2.js` exports `filterCapabilities(rows, mode)` and `selectFinding(view, id)`
with JSDoc types derived from report-view; DOM bootstrap is separate from pure helpers.

- [ ] **RED:** `test_report_has_matrix_charts_captions_and_equivalent_tables` checks exact figure/count equivalence; `test_embedded_hostile_text_is_not_executable` uses `</script>` and attribute payloads. `test_rerender_keeps_source_and_evidence_bytes` checks hashes and presentation 2.0 manifest. Browser-helper tests assert filters and lookup preserve original states. Run `P tests/acceptance/test_visual_reports.py` and `node --test tests/frontend/report.test.js` in the container.
- [ ] **Implement:** Render essential HTML/SVG/table/details server-side, safely embed JSON, inline required assets for `file://`, and enhance filtering/drawers without fetch or eval. Preserve existing exclusive output behavior; `report` emits a new projection/render alongside unchanged original result/evidence. Markdown contains equivalent figure tables, captions, source references and limitations. Print reveals essential details and removes controls. CLI automatic HTML/MD remains enabled.
- [ ] **GREEN:** Run new tests, existing readable-report/replay/regression acceptance, frontend type/lint/format and `F`. Deferred real-browser coverage is completed in Task 12; do not claim it now.
- [ ] **Commit:** `feat: render interactive offline matrices charts and evidence details`.

### Task 10: Immutable exports and evidence-aware ZIP delivery

**Files:** Create `exports.py`; extend `web/api.py`; test
`tests/integration/test_exports.py`, `tests/acceptance/test_export_integrity.py`.

**Interfaces:** `ExportPolicy(formats: tuple[Literal['html','markdown','json','zip'], ...], include_evidence: bool)`;
`ExportService(data_root: Path).preview(run_id: str, policy: ExportPolicy) -> JsonObject`,
`.create(run_id: str, policy: ExportPolicy) -> JsonObject`, `.resolve(run_id: str, export_id: str) -> Path`.
Export records/manifests are schema-checked and opaque. Task 7 adds the approved POST/download routes through this service.

- [ ] **RED:** `test_export_preserves_sources_and_manifest_hashes` verifies every archive entry and local link; `test_report_only_and_partial_exports_disclose_omissions` checks proper schema/labels and no clean certificate. `test_export_rejects_changed_source_between_verification_and_copy` replaces a source during copying and requires rejection or explicitly diagnostic output. `test_export_ignores_unrelated_files_and_secret_values` checks allowlisted contents and zero upstream calls. Run both files.
- [ ] **Implement:** Freeze policy/source identity under a new export ID, use only whitelisted verified files, reject symlink/traversal/unsafe names, rehash the bytes actually copied and publish only after manifest validation. Preserve original result/evidence bytes. Include Chinese README, agent interpretation, versions, limitations, references and SHA-256 manifest; self-hash is a provenance inventory, not a source signature. Never overwrite prior exports or raw captures; damaged sources get a diagnostic-only path.
- [ ] **GREEN:** Run export, report-source/evidence and Web API tests; reconstruct archive and compare all retained bytes, including deliberately failed/partial attempts.
- [ ] **Commit:** `feat: export immutable offline reports and verified evidence packages`.

### Task 11: Configuration, live console and history pages

**Files:** Create `web/pages.py`, `resources/web/{base,configure,run,history}.html`,
`resources/web/{app,forms,progress,report}.js`, `resources/web/app.css`;
test `tests/frontend/forms.test.js`, `tests/frontend/progress.test.js`,
`tests/integration/test_web_pages.py`.

**Interfaces:** `pages.router` provides `/`, `/new`, `/runs/{id}` and `/history`.
Browser `forms.js` exports `resolvePreviewState(current, edited)`, `progress.js`
exports `reduceSnapshot(snapshot, event)`; both have strict JSDoc input/output
contracts matching web-api/progress-event schemas. No browser module starts a test
on import, reconnect, view change or preset editing.

- [ ] **RED:** `test_edit_invalidates_preview_and_clears_submitted_secret` checks explicit start only; `test_reducer_deduplicates_and_recovers_ahead_cursor` preserves last committed sequence and pending counts. `test_page_renders_only_installed_capabilities` requires exactly the chosen Stage A catalog and correct partial labels. Run frontend Node tests and the page integration file.
- [ ] **Implement:** Follow the approved visual hierarchy: compact conclusion, matrix, state distribution, issue impact, real timeline and contextual drawer. Add plan preview/effective URL, finite budgets, generic Docker hint, safe authentication input, persistent run navigation, history filters/preset editing and export preview. Reauthenticate local session on expiry without resubmitting a run; reconnect with snapshot cursor. Restore focus/filter context, expose table data and all five result states. Do not ship the prototype's fake names/counts/events or simulation timers.
- [ ] **GREEN:** Run named tests plus static frontend checks and Web integration. Inspect the actual four-case layout rather than filling empty space with fictional capabilities.
- [ ] **Commit:** `feat: add local configuration live assessment and history interfaces`.

### Task 12: Browser acceptance and unified frontend/CI gates

**Files:** Create `playwright.config.js`, `tests/browser/{console,offline-report,accessibility}.spec.js`,
`scripts/browser_fixture.py`, `scripts/check_frontend.py`, `tests/harness/test_frontend_gate.py`;
modify `scripts/check.py`, `.github/workflows/ci.yml`, `scripts/check_docs.py` only where needed.

**Interfaces:** `check_frontend.py --suite static|browser --out PATH` writes a schema-validated check record plus JUnit/browser artifacts; reports BLOCKED for missing tools and FAIL for zero executed cases.
`browser_fixture.py --port PORT --root PATH` starts the local app and a synthetic delayed endpoint, writes disposable control records, and shuts down owned children. Browser tests use no real target or credentials.

- [ ] **RED:** `test_frontend_gate_cannot_pass_with_missing_browser_or_zero_cases` pins truthful aggregation. Browser tests require: preview zero calls; duplicate start one run; close/reopen observation; cancellation; expired-session recovery; exact matrix/detail/figure data; hostile fields inert; keyboard focus restoration; 390px and 1280px layouts; print styles; script-disabled essentials; direct `file://` report with all network requests blocked. Run the new gate test and selected browser specs and observe behavior failures.
- [ ] **Implement:** Wire static checks into fast and browser checks into full, with browser JUnit attached to required accounting. Lock Chromium through the npm Playwright version; CI prepares deps/browser then runs offline. Add/check any new CI child in `ci-required` with pinned action SHAs, read-only permissions and no publishing. Preserve Python 3.11/3.12 matrix; browser acceptance runs in Linux/Python 3.12 with Node 24. Add synthetic fixture process cleanup and request-count assertions.
- [ ] **GREEN:** Run `A`, inspect browser screenshots for summary/matrix/timeline/detail/configuration/print/narrow views, and record actual observations. Automated screenshots do not replace checking their contents. No whole-stage acceptance until image/package/review tasks finish.
- [ ] **Commit:** `test: gate web and offline report behavior in the unified harness`.

### Task 13: Installed package, Docker targets and user guidance

**Files:** Modify `Dockerfile`, `.dockerignore`, `.devcontainer/devcontainer.json`,
`scripts/check_images.py`, `tests/acceptance/test_installed_package.py`,
`.github/workflows/container-matrix.yml`, `README.md`, `CONTRIBUTING.md`,
`docs/container-usage.md`, `docs/development.md`, `docs/architecture.md`;
create `compose.yaml`, `tests/acceptance/test_web_package.py`, `tests/harness/test_web_images.py`.

**Interfaces:** Preserve image script defaults and add `--targets runtime,web` (default both after W1).
`compose.yaml` starts the Web image with loopback port 8765, one named data volume,
nonroot user, read-only root and bounded tmpfs; server credential variables are
explicit optional configuration, never baked into image examples or commits.

- [ ] **RED:** `test_cli_install_works_without_web_extra` and `test_web_install_contains_templates_schemas_and_assets` exercise isolated installs outside source. `test_web_image_is_not_cli_only_acceptance` requires separate image checks, volume restart/cancellation/host alias results and failure on missing Web assets. `test_compose_binds_only_host_loopback` verifies mapping and no Docker socket. Run new package/image harness tests.
- [ ] **Implement:** Add a separate Web dependency build environment/image target; retain CLI-only runtime and avoid copying Node/browser/dev state into either. Extend actual Dev Container with pinned toolchain/browser preparation, excluding private session/artifact/config data. Add Web image smoke and full amd64/arm64 matrix to existing CI without publication. Document GUI/CLI quick starts, literal-versus-host-loopback behavior, secrets, history, exports, limits and contribution checks.
- [ ] **GREEN:** Run installed-wheel tests and `A`; host Docker orchestrator runs image acceptance for both targets on linux/arm64 and linux/amd64. Native/emulated observations are labeled separately, and generic Docker-host synthetic access is tested. Confirm volumes survive service replacement and no browser/dev tools are in runtime images. Unavailable architecture stays BLOCKED, not passed.
- [ ] **Commit:** `feat: package local web and cli workflows with container acceptance`.

### Task 14: Whole-W1 acceptance, independent review and handoff

**Files:** Create `docs/harness/web-console-acceptance.json`,
`docs/harness/web-console-handoff.json`, `docs/reviews/2026-10-16-web-console-review.md`
(use actual review date if later); update W1 ledger, progress, `docs/CONTINUE.md`,
`docs/HANDOFF.md` with an additive W1 section only.

**Interfaces:** New acceptance/handoff records map W1-01…W1-12 to concrete check
artifacts, immutable source/lock/toolchain/image identities and unresolved limits.
Do not repoint the frozen Stage A manifest to new source artifacts.

- [ ] **Run acceptance:** Verify `A`, installed package, both runtime images and actual browser/export results for the same unchanged source commit. Re-run only checks affected by subsequent fixes; retain all failed attempts and exact check manifests.
- [ ] **Independent review:** Request one fresh whole-W1 reviewer as authorized by `AGENTS.md`, with the approved spec/plan, immutable diff range and observed evidence. Ask specifically about source integrity, parent/worker races, credential boundaries, safe offline rendering, scope honesty and actual installed artifacts. No per-task reviewer/implementer agents.
- [ ] **Resolve findings:** Reproduce actionable findings with assertion-level RED, fix without weakening assertions and run relevant/full gates as needed. Record rejected suggestions with evidence. Do not repeat the already completed Stage A review or suppress review findings to close the milestone.
- [ ] **Finalize and commit:** Publish local handoff records and scoped commits; show actual GUI with synthetic data and an offline export for user review. State remote CI, public registry, live endpoints and untested platforms separately. W1 is complete only when its required evidence/review is complete; otherwise record the precise remaining check.

## Acceptance traceability

| Spec acceptance | Owning tasks |
| --- | --- |
| W1-01 shared engine and independent CLI | 1, 3, 8–9, 13 |
| W1-02 preview, opt-in and admission | 4, 6–7, 11–12 |
| W1-03 progress/reconnection | 2–3, 7, 11–12 |
| W1-04 cancellation/crash/races | 2–5, 7, 12–13 |
| W1-05 partial and damaged evidence | 2, 5, 8, 10 |
| W1-06 secrets/rendering/local access | 3, 5–7, 9–10, 12 |
| W1-07 figures/counts/navigation | 8–9, 11–12 |
| W1-08 standalone/accessibility/print | 9, 11–12 |
| W1-09 ZIP/source integrity | 8, 10, 12 |
| W1-10 presets/history/restart | 4–5, 7, 11–13 |
| W1-11 wheels/images | 1, 6, 12–13 |
| W1-12 gates/review/handoff | 12–14 |

## Plan self-review and execution handoff

Reviewed each specification section against the traceability table. Checked common
type/function names across tasks, parent-only event sequencing, credential IPC,
API/body/session boundaries, old-report fallbacks, immutable export inputs and
all five Review Focus scenarios. Tool preparation is a prerequisite with pinned
outputs, not an unrun check labeled passed. Implementation remains sequential in
this chat; the written plan awaits owner review before Task 1 starts.
