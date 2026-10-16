# Stage A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver an installable, containerized Anthropic Messages black-box smoke tester with a pinned protocol contract, trustworthy offline validators, and consistent JSON/HTML/Markdown evidence reports.

**Architecture:** Keep framing, domain data and validators independent of transport and storage. Resolve one immutable contract bundle, plan four optional-by-profile API cases, capture bounded responses, validate them, sanitize evidence, and render deterministic reports. The same offline check entry point runs in the Dev Container and GitHub Actions.

**Tech Stack:** Python >=3.11; standard development Python 3.12; httpx, jsonschema, PyYAML; uv/Hatchling; Ruff, mypy strict, Import Linter, pytest; Docker/Dev Containers; GitHub Actions.

**Spec:** [Detailed design, revision 6](../specs/2026-10-14-anthropic-readiness-design.md).

**Status:** Approved by the user for native, sequential implementation in the current chat. Execution evidence lives in `docs/harness/progress.md` and the task ledger; unchecked plan steps are not evidence of acceptance. Do not spawn implementation agents merely because the standard header mentions that option.

## Global Constraints

- Implement Stage A only. Matrix execution, live streaming tools/tool loops, real Claude CLI workflows, retries/reliability, re-scoring, public release, and the protocol-update skill belong to B/C/D.
- Use `src/anthropic_readiness`, one `pyproject.toml`, and one `uv.lock`. Code, comments, IDs, commits and public contribution materials are English. User-facing reports default to Simplified Chinese.
- Standard development runs in a Linux Dev Container. Support the Python 3.11 floor and development Python 3.12; never claim macOS-native execution as container acceptance.
- Package runtime schemas/contracts under `src/anthropic_readiness/resources`; resolve them with `importlib.resources`, not the current working directory.
- Contract: `anthropic.messages`, API date `2023-06-01`, bundle `anthropic-messages-2023-06-01-core`, revision `1.0.0`, empty beta set. Acquire real source metadata/hashes at implementation time.
- Five assertion statuses: PASS, FAIL, SKIP, BLOCKED, INDETERMINATE. Preserve mixed results and known failures. Empty required coverage never passes.
- CLI exits: 0 success, 1 required failure, 2 usage/config/output error, 3 incomplete, 4 internal error, 130 SIGINT, 143 SIGTERM; signal/internal exits take precedence over ordinary evaluation exits.
- Default `anthropic-basic` has 3 HTTP requests; selecting `anthropic-tools-smoke` adds 1. No retries, caching, hidden requests or live execution without `--allow-live`.
- Generic examples only; the historical evaluation directory is read-only. No real endpoint/model/logs or credentials enter source, image layers or public CI artifacts.
- `linux/amd64` and `linux/arm64` both need build/run evidence for complete Stage A container acceptance. Emulation must be disclosed.
- Commit locally in scoped task checkpoints. Do not create/push a GitHub repository, publish an image, configure account secrets or run real target tests as an implied side effect.
- Report product readiness, developer checks, container acceptance and remote CI runs separately. Documentation/configuration existing is not execution evidence.

## Review Focus

1. YAML duplicate keys and string/boolean/integer confusion must be rejected before any request (Task 3).
2. A valid `message_stop` followed by an open connection must retain proven assertions while marking capture completeness indeterminate (Tasks 5 and 7).
3. A credential spanning reads or changed byte lengths must not leak or be replayed using stale offsets (Task 8).
4. Installed wheels must work outside the repository, including every schema and contract resource (Tasks 10 and 11).
5. Failure after earlier cases pass, missing checks, and cancellation must never produce an all-green report or hide known failures (Tasks 1, 9 and 12).

## File Ownership and Dependency Map

| Unit | Files | Owns |
| --- | --- | --- |
| Development harness | `pyproject.toml`, `uv.lock`, `.python-version`, `scripts/check.py`, `AGENTS.md`, `.devcontainer/devcontainer.json`, `Dockerfile` | Locked environment, check runner, developer navigation |
| Domain and documents | `models.py`, `schema.py`, `resources/schemas/*.schema.json` | Typed records, structural validation and pure relational validation |
| Config and contracts | `config.py`, `contracts.py`, `resources/contracts/**` | File/resource loading, target validation, immutable bundle resolution |
| Framing and validators | `sse.py`, `validation/messages.py`, `validation/stream.py`, `cases.py` | Pure protocol/behavior checks and request definitions |
| I/O | `transport.py`, `evidence.py` | Bounded network capture and sanitized, immutable evidence |
| Execution/reporting | `runner.py`, `cli.py`, `reporting.py`, `resources/report.css` | Plans, attempts, CLI, consistent report rendering |
| Collaboration/CI | `CONTRIBUTING.md`, `.github/**`, `.pre-commit-config.yaml`, `docs/*.md` | Public contribution path and hosted equivalents of local checks |
| Tests | `tests/unit`, `tests/integration`, `tests/acceptance`, `tests/harness`, `tests/fixtures` | Meaningful positive/negative verification |

All package paths below are relative to `src/anthropic_readiness/`. Do not make validators import file loaders to obtain types; `ContractSpec` and `CaseContract` live in `models.py`.

## Task 1: Runnable Development Environment and Minimal Check Harness

**Files:** Create `pyproject.toml`, `uv.lock`, `.python-version`, `src/anthropic_readiness/{__init__.py,__main__.py,cli.py,py.typed}`, `scripts/check.py`, `tests/harness/test_check_runner.py`, `.gitignore`, `.dockerignore`, `Dockerfile` (`base`/`dev` targets), `.devcontainer/devcontainer.json`, `AGENTS.md`, `docs/development.md`, `docs/harness/{acceptance.json,progress.md}`.

**Interfaces:** Produce `CheckSpec(check_id, argv, timeout_s, check_kind, required)` and `run_checks(checks: Sequence[CheckSpec], output_dir: Path) -> int` inside `scripts/check.py`; `check_kind` distinguishes ordinary commands and pytest checks. Pytest checks collect a designated JUnit artifact and reject a missing report or zero collected cases even if a test command exits zero. Emit versioned `check-result.json` with per-check status, return code and input fingerprints. The script initially describes its bootstrap scope, not complete Stage A readiness.

- [x] **Step 1 — Preflight:** Inspect the four existing documentation files and applicable instructions. Confirm there is still no Git repository/code; initialize a local repository at implementation time and preserve all existing documents. Recheck Docker availability through normal permission handling; record a blocked socket separately from an absent daemon. Resolve actual Python/uv/base-image versions and digests without guessing.
- [x] **Step 2 — Red:** Add check-runner subprocess tests: `test_failed_command_fails_suite`, `test_missing_command_is_blocked`, `test_timeout_is_not_pass`, and `test_zero_collected_tests_is_not_pass`. Assert nonzero overall exit and the expected check status, rather than only matching console output. Create only the packaging/bootstrap needed to run these tests.
- [x] **Step 3 — Verify red:** In the dev container run `uv run --frozen python -m pytest tests/harness/test_check_runner.py -q`; confirm the check-runner assertions fail before its implementation, not because the environment cannot start.
- [x] **Step 4 — Green:** Implement the runner with argument-list subprocess calls, bounded timeouts and non-mutating checks. Pin Hatchling and all development/build dependencies; configure Ruff, mypy strict and pytest strict/importlib settings. Use a container-owned virtual environment/cache, normal developer user, and no Docker socket mount. Keep unimplemented acceptance requirements incomplete.
- [x] **Step 5 — Verify:** Rerun the focused tests in the Dev Container, inspect a generated `check-result.json`, and verify CLI help is importable without network or output-directory side effects. Record the actual environment; if containers are blocked, report that limitation and do not mark environment acceptance complete.
- [x] **Step 6 — Commit:** Commit the development foundation and observed evidence references with `chore: establish reproducible development harness`.

## Task 2: Typed Result Records, Schemas and Honest Aggregation

**Files:** Create `models.py`, `schema.py`, `resources/schemas/{result,capture,target,contract,check-result,acceptance}.schema.json`, `tests/unit/test_results.py`, `tests/unit/test_schemas.py`, and `tests/fixtures/results/`.

**Interfaces:** Define `JsonValue`, `JsonObject`, `Status`, `AssertionResult`, `EvidenceRef`, `ValidationResult`, `RunResult`, `ContractSpec`, `CaseContract`, `RequestSpec`, `ReadRecord`, `SSEFrame`, `DecodeTail`, `Capture`, and `CaptureEnd`/`ProtocolEnd` in `models.py`. Produce `aggregate_required(statuses: Sequence[Status]) -> Status`, `validate_document(value: object, schema: JsonObject) -> None`, and `validate_result_semantics(value: JsonObject) -> list[str]`. Empty `aggregate_required` returns INDETERMINATE; the profile-level mapping remains `incomplete`. Serialization must not perform file I/O.

- [x] **Step 1 — Red:** Add `test_fail_survives_incomplete_capture`, `test_empty_required_set_never_passes`, `test_missing_required_case_is_incomplete`, `test_boolean_count_is_rejected`, and `test_unknown_status_is_rejected`. Assert precedence FAIL > BLOCKED > INDETERMINATE > SKIP > PASS, with `not_evaluated` used only for an untested dimension, not a sixth assertion status.
- [x] **Step 2 — Verify red:** Run `uv run --frozen python -m pytest tests/unit/test_results.py tests/unit/test_schemas.py -q` and confirm the missing behavior is the failure.
- [x] **Step 3 — Green:** Implement immutable typed records and serialization, with every top-level result field in spec section 9. Separate JSON Schema checks from plan/case/assertion uniqueness, counts, required coverage and aggregate consistency. Reject external schema references rather than fetching them.
- [x] **Step 4 — Verify:** Rerun the focused tests and mypy. Add a mixed synthetic result that round-trips and a structurally valid but semantically inconsistent result that is rejected. Filesystem evidence verification remains Task 8.
- [x] **Step 5 — Commit:** `feat: define versioned results and assertion aggregation`.

## Task 3: Strict Targets and Immutable Protocol Bundle

**Files:** Create `config.py`, `contracts.py`, `resources/contracts/anthropic-messages-2023-06-01-core/1.0.0/manifest.json`, accompanying rule/source data, `examples/target.yaml`, `tests/unit/{test_config,test_contracts}.py`.

**Interfaces:** Produce `load_target(path: Path) -> TargetConfig`, `resolve_contract(contract_id: str, revision: str) -> ContractBundle`, and `validate_target_contract(target: TargetConfig, bundle: ContractBundle) -> None`. Define `TargetConfig` and `Limits` as typed configuration records; `TargetConfig` owns parsed limits/auth/capabilities. `ContractBundle` owns resource/source metadata and `.spec`, the pure `ContractSpec` consumed by validators. Secrets are supplied by execution, not stored in the target record.

- [x] **Step 1 — Red:** Add `test_duplicate_yaml_key_rejected`, `test_string_false_and_boolean_timeout_rejected`, `test_url_credentials_query_fragment_rejected`, `test_local_url_accepted`, `test_unknown_bundle_rejected_before_transport`, `test_bundle_tamper_rejected`, and `test_beta_mismatch_rejected`. Test both model policies and missing/empty credentials as execution preconditions.
- [x] **Step 2 — Verify red:** Run `uv run --frozen python -m pytest tests/unit/test_config.py tests/unit/test_contracts.py -q`.
- [x] **Step 3 — Green:** Implement safe YAML loading and schema validation with exact revision resolution and normalized fingerprints. Copy the spec defaults exactly: 5/30/90/300 second connect/read/attempt/run limits; 4194304 body bytes, 262144 event bytes, 10000 events, 4 requests and 512 tokens.
- [x] **Step 4 — Source provenance:** Retrieve the approved official versioning, Messages, streaming and SSE sources at implementation time. Record actual retrieval dates, normalized source hashes, rule anchors and tested coverage. Hash manifests excluding their own digest, validate shipped runtime resources, and keep fixture references as a build-time integrity list. Do not invent source digests or claim beta/legacy coverage.
- [x] **Step 5 — Verify:** Rerun the focused tests, validate the generic example and assert `auth.mode=none` creates no key. Test resource lookup from a temporary working directory and an unknown contract without making a network request.
- [x] **Step 6 — Commit:** `feat: load strict targets and pinned protocol contracts`.

## Task 4: Incremental SSE Framing

**Files:** Create `sse.py`, `tests/unit/test_sse.py`, and `tests/fixtures/sse/{valid,multiline,utf8,tail}/`.

**Interfaces:** Produce `SSEDecoder(max_event_bytes: int, max_events: int)`, `feed(chunk: bytes, received_ms: float) -> list[SSEFrame]`, and `finish() -> DecodeTail`. The decoder understands framing only; it must not import HTTP or Anthropic validators.

- [x] **Step 1 — Red:** Add `test_all_single_split_positions_preserve_frames`, `test_utf8_and_crlf_across_reads`, `test_multiline_data_uses_newline`, `test_bom_comments_and_bare_fields`, `test_unknown_fields_are_ignored`, `test_eof_does_not_dispatch_partial_event`, and `test_event_limits_bound_pending_data`.
- [x] **Step 2 — Verify red:** Run `uv run --frozen python -m pytest tests/unit/test_sse.py -q`.
- [x] **Step 3 — Green:** Implement incremental UTF-8 and CR/LF state, one leading BOM, blank-line dispatch, event/id/retry behavior and bounded pending data. Retain explicit encoding problems and unfinished-tail metadata; do not confuse a read with an event.
- [x] **Step 4 — Verify:** Compare whole-body, one-byte, every single split and seeded multi-split delivery for the same valid bytes; assert identical semantic frames and differing read metadata only.
- [x] **Step 5 — Commit:** `feat: decode bounded incremental SSE frames`.

## Task 5: Lifecycle and Streaming Tool Validators

**Files:** Create `validation/__init__.py`, `validation/stream.py`, `tests/unit/test_stream_validation.py`, and the versioned valid/defect stream fixture manifest.

**Interfaces:** Produce `StreamValidator(contract: CaseContract)`, `consume(frame: SSEFrame) -> None`, and `finish(protocol_end: ProtocolEnd, capture_end: CaptureEnd, tail: DecodeTail) -> ValidationResult`. Return stable assertion IDs and evidence locations, not only an overall boolean.

- [x] **Step 1 — Red:** Pin tests `test_duplicate_message_start_hits_expected_assertion`, `test_wrong_index_and_closed_block_delta_fail`, `test_multiple_message_delta_and_empty_block_pass`, `test_unknown_event_does_not_hide_known_failure`, `test_unknown_delta_is_indeterminate`, `test_error_event_is_task_failure_not_missing_stop`, and `test_valid_stop_with_capture_timeout_is_incomplete`.
- [x] **Step 2 — Verify red:** Run `uv run --frozen python -m pytest tests/unit/test_stream_validation.py -q`.
- [x] **Step 3 — Green:** Implement the spec's message and per-index block states without overwriting duplicate events. Check event/data type agreement, strict JSON, completed block inputs and final stop reason. Separate protocol-valid error expression, task failure and capture completeness.
- [x] **Step 4 — Complete detector matrix:** Add legal split tool JSON, schema-allowed empty input, missing required input, wrong names/IDs, malformed fragments, pre-start and post-stop events, normal EOF truncation versus reset/limit, and harmless trailing comments. Tool stream tests are offline only in A.
- [x] **Step 5 — Verify:** Rerun all unit tests; each single-defect fixture must hit its named assertion, each legal control must avoid it, and every split variant must retain the same verdict.
- [x] **Step 6 — Commit:** `feat: validate Anthropic stream lifecycle and tool fragments`.

## Task 6: Message Validation and Four Case Definitions

**Files:** Create `validation/messages.py`, `cases.py`, `tests/unit/{test_messages,test_cases}.py`, and JSON message fixtures.

**Interfaces:** Produce `validate_message(value: object, contract: CaseContract) -> ValidationResult`, `list_cases() -> tuple[CaseDefinition, ...]`, `select_cases(profile_ids: Sequence[str]) -> tuple[CaseDefinition, ...]`, and `build_request(case: CaseDefinition, target: TargetConfig) -> RequestSpec`. `CaseDefinition` supplies ID/version, capability preconditions, profile membership and `CaseContract`.

- [x] **Step 1 — Red:** Test empty/non-object tool input, wrong name, missing/duplicate ID, schema-required `location`, exact `Hanoi`, correct `tool_use` stop, model structure versus identity policies, unknown stop reason, and valid `max_tokens` protocol termination with incomplete task behavior.
- [x] **Step 2 — Verify red:** Run `uv run --frozen python -m pytest tests/unit/test_messages.py tests/unit/test_cases.py -q`.
- [x] **Step 3 — Green:** Register exactly `ANT-MESSAGE-001`, `ANT-TEXT-SSE-001`, `ANT-TEXT-SSE-002`, and `ANT-TOOL-FORCED-001`, version 1. Fix prompts and tool schema to spec section 7, including `max_tokens=min(512, target.limits.max_tokens)`.
- [x] **Step 4 — Verify:** Assert basic selects 3 requests and adding tools-smoke selects 4 without duplication. Count behavior extracts all digit sequences and requires `1,2,3,4,5`; greeting only proves nonempty text. Reject unimplemented profiles, preserve selected capability skips, and keep tag sightings diagnostic.
- [x] **Step 5 — Commit:** `feat: add versioned message and forced-tool smoke cases`.

## Task 7: Bounded HTTP Capture and Termination

**Files:** Create `transport.py`, `tests/integration/{test_transport,test_deadlines}.py`, and `tests/fixtures/http/` synthetic server behaviors.

**Interfaces:** Produce `HttpTransport.send(request: RequestSpec, limits: Limits, deadline: float) -> Capture`. Inject monotonic clock/transport seams for deterministic tests; use real isolated synthetic HTTP/SSE tests for the integration boundary.

- [x] **Step 1 — Red:** Test no-auth headers, exact version/beta serialization, redirects not followed, HTTP non-2xx, refused connection, a complete message/error, early EOF, read reset, never-ending pings, body/event limits, and stop followed by a connection that stays open.
- [x] **Step 2 — Verify red:** Run `uv run --frozen python -m pytest tests/integration/test_transport.py tests/integration/test_deadlines.py -q` inside the isolated test network.
- [x] **Step 3 — Green:** Use httpx with `trust_env=False`, TLS verification, no redirect/retry and streaming application reads. Enforce monotonic run/attempt deadlines independently of read activity. Bound retained decompressed bytes during decoding, including compressed synthetic responses; do not allocate the full decompressed body before checking limits.
- [x] **Step 4 — Preserve observations:** Record response headers/body, read lengths/times and frame dispatch times. Return `protocol_end` and `capture_end` independently, captured/observed sizes, exact truncation/limit reasons and partial evidence. Network failures must not be mislabeled as JSON/protocol defects.
- [x] **Step 5 — Verify:** Assert the synthetic server saw exactly the planned requests and correct headers; a pings-only stream terminates at the overall deadline. Reproduce the known-defect fixture over HTTP and retain its validator evidence.
- [x] **Step 6 — Commit:** `feat: capture bounded HTTP and SSE responses`.

## Task 8: Sanitized Evidence and Replayable Captures

**Files:** Create `evidence.py`, `tests/unit/test_redaction.py`, `tests/integration/test_evidence.py`, and `tests/fixtures/captures/` with a versioned capture manifest.

**Interfaces:** Produce `sanitize_capture(capture: Capture, secrets: Sequence[str]) -> SanitizedCapture`, `create_run_directory(path: Path) -> None`, `persist_capture(root: Path, case_id: str, attempt_id: str, capture: SanitizedCapture) -> CaptureRefs`, `load_capture(path: Path) -> SanitizedCapture`, and `verify_evidence(root: Path, refs: Sequence[EvidenceRef]) -> list[str]`.

- [x] **Step 1 — Red:** Test authentication-header case variants, raw and JSON-escaped keys in body/errors, a key crossing reads, altered byte lengths, existing output directory rejection, traversal/symlink escape, bad hash, bad event pointer and interrupted partial capture.
- [x] **Step 2 — Verify red:** Run `uv run --frozen python -m pytest tests/unit/test_redaction.py tests/integration/test_evidence.py -q`.
- [x] **Step 3 — Green:** Apply the exact header allowlists and secret sanitation before any temporary/final write. Create directories exclusively, use 0700/0600 where supported and atomic file replacement. Hash persisted files, retain original body digest/length separately and mark transformations.
- [x] **Step 4 — Replay semantics:** Store response metadata, body, reads and sanitized event view. Reuse original boundaries only for untransformed compatible captures; re-chunk transformed bodies and mark affected semantic checks indeterminate. Never score masked values as original facts or execute references from a capture.
- [x] **Step 5 — Verify:** Recursively scan generated fixture output for the synthetic secret; validate every reference and load the capture from a different cwd. A second run cannot overwrite the first. Missing/unwritable output produces an explicit execution error, not false service success.
- [x] **Step 6 — Commit:** `feat: persist sanitized immutable capture evidence`.

## Task 9: Runner and User CLI

**Files:** Create `runner.py`; expand `cli.py`/`__main__.py`; create `tests/acceptance/{test_cli,test_runner,test_replay}.py` and a mixed-outcome run fixture.

**Interfaces:** Produce `plan_run(target: TargetConfig, bundle: ContractBundle, profiles: Sequence[str]) -> RunPlan`, `execute_run(plan: RunPlan, transport: HttpTransport, output_dir: Path) -> RunResult`, and `main(argv: Sequence[str] | None = None) -> int`. Replay uses the same validators with captured input, `mode=replay` and zero actual requests.

- [x] **Step 1 — Red:** Test validate, contracts list/show, dry-run, run without allow-live, request-budget rejection, 3/4-case selection, missing credentials, capability exclusion, run-deadline exhaustion, failure after earlier success, signal cleanup and expected exit-code precedence.
- [x] **Step 2 — Verify red:** Run `uv run --frozen python -m pytest tests/acceptance/test_cli.py tests/acceptance/test_runner.py tests/acceptance/test_replay.py -q`.
- [x] **Step 3 — Green:** Implement `validate --target`, `contracts list/show`, `run --target --profile --out [--allow-live|--dry-run]`, and `replay --capture --target --case --out`. Stage A accepts a single capture for replay; later re-scoring is not implicitly enabled. Allocate UUIDs and preserve all selected required cases, including preconditions and unexecuted cases.
- [x] **Step 4 — Result integrity:** Bind actual requests, contract/hash, config/test fingerprints and execution metadata to the result. Perform structural/relational/evidence validation before final result output. Catch recoverable failures and signals, retain partial results, and disclose failed writes or internal errors.
- [x] **Step 5 — Verify:** Execute CLI subprocesses against isolated synthetic targets and captures. Assert `result.json` matches actual server request count, a bad replay exits 1, incomplete evaluation exits 3, and pure commands access no network.
- [x] **Step 6 — Commit:** `feat: execute and replay explicit smoke-test plans`.

## Task 10: Engineering Reports and Installed-Package Acceptance

**Files:** Create `reporting.py`, `resources/report.css`, report-context/reference data and `tests/acceptance/{test_reports,test_installed_package}.py`; add `report --input <result.json> --out <new-directory>` to the CLI, rendering both HTML and Markdown by default.

**Interfaces:** Produce `render_html(result: RunResult) -> str`, `render_markdown(result: RunResult) -> str`, and `write_reports(result: RunResult, output_dir: Path) -> None`. Both renderers consume one validated result; rerendering never modifies the source result.

- [x] **Step 1 — Red:** Test matching IDs/counts/statuses across JSON/HTML/Markdown, self-contained method/scope/limits in Markdown, real reference IDs, synthetic labels, no Claude Code ready, long IDs/Chinese content, malicious HTML/fences and missing evidence disclosure.
- [x] **Step 2 — Verify red:** Run `uv run --frozen python -m pytest tests/acceptance/test_reports.py tests/acceptance/test_installed_package.py -q`.
- [x] **Step 3 — Green:** Implement the restrained typography, tables and print styles from spec section 18, with no remote assets/scripts. Add versioned methodology/glossary/reader notes and rule citations; keep observations separate from suggested explanations and never call a model or fetch documents during rendering.
- [x] **Step 4 — Wheel verification:** Build wheel/sdist using preinstalled locked build requirements, install the wheel non-editably in a fresh environment without source-path injection, then run help, contracts show, validate, replay and report outside the repository. Validate packaged resources and schema inventory.
- [x] **Step 5 — Visual verification:** Render mixed synthetic reports and inspect desktop, narrow-screen and print output. Save local preview evidence, fix clipping/overflows/poor contrast, and record what was inspected without calling those screenshots service test evidence.
- [x] **Step 6 — Commit:** `feat: render traceable offline engineering reports`.

## Task 11: Complete Quality Gates, Runtime Images and GitHub Collaboration

**Files:** Expand `scripts/check.py`, `pyproject.toml`, `Dockerfile` (`build`/`runtime` targets), and `.devcontainer/devcontainer.json`; create `.pre-commit-config.yaml`, `.github/workflows/{ci,container-matrix}.yml`, `.github/ISSUE_TEMPLATE/{bug_report,compatibility_report,feature_request,protocol_update}.yml`, `.github/PULL_REQUEST_TEMPLATE.md`, `CONTRIBUTING.md`, `README.md`, `docs/{architecture,container-usage}.md`, `tests/harness/{test_architecture,test_gate_contracts,test_documentation}.py`.

**Interfaces:** Complete the existing fast/full check graph; CI calls that graph. Build/runtime consumes the same tested wheel and locked runtime dependencies, with ordinary-user CLI entry point. `ci-required` verifies all required child jobs; image jobs record architecture, provenance and verdicts without pushing.

- [x] **Step 1 — Red:** In disposable synthetic projects inject a Ruff violation, mypy error, reversed architecture dependency, invalid schema, missing check executable and missing wheel resource. Assert each designated gate blocks; do not weaken real checks or mutate production sources for these tests.
- [x] **Step 2 — Verify red:** Run `uv run --frozen python -m pytest tests/harness/test_architecture.py tests/harness/test_gate_contracts.py tests/harness/test_documentation.py -q`.
- [x] **Step 3 — Green:** Install Import Linter contracts and the complete locked check graph, with offline verification after environment/wheelhouse preparation. Add local pre-commit shortcuts and stable CI check IDs; fork PR jobs use no secrets, paid model or real target. Templates link the same commands and evidence IDs, allow honest not-run values and omit private logs.
- [x] **Step 4 — Container acceptance:** Build dev/runtime for amd64 and arm64, record native/emulated execution, run runtime as ordinary user with read-only root and explicit output/temp mounts, and run pure replay under network=none. Verify persisted outputs, SIGINT/SIGTERM handling and no credential/config/test-workspace contamination. Test a synthetic server on the supported isolated/host network paths without changing the real daemon.
- [x] **Step 5 — CI definition checks:** Validate workflow/template YAML and required-job aggregation, then exercise the same commands locally. Mark remote GitHub checks not_run until a repository is explicitly connected. Keep registry login/push, release workflow and Agent protocol-maintenance command outside A.
- [x] **Step 6 — Verify:** Run the focused harness tests, full check suite, installed-package smoke and both architecture image jobs. Record blockers separately; one platform's success cannot complete two-platform acceptance.
- [x] **Step 7 — Commit:** `ci: enforce quality gates and container build acceptance`.

## Task 12: Whole-Stage Review and Independent Handoff

**Files:** Update `docs/harness/{acceptance.json,progress.md}`, `docs/CONTINUE.md`, and `docs/reviews/<actual-date>-stage-a-review.md`; create sanitized synthetic samples and check artifacts under ignored `artifacts/`.

**Interfaces:** Produce a handoff manifest tying source/lock/contract fingerprints, task commits, full/image-check results, runnable commands, sample outputs and explicit limitations together. It is not a real-endpoint compatibility certificate.

- [x] **Step 1 — Coverage review:** Map every A requirement from spec sections 1–18 to tests/checks or a clearly excluded later phase. Verify no required behavior disappears from the acceptance index and no placeholder becomes an advertised capability.
- [x] **Step 2 — Fresh verification:** Run fast/full, supported Python checks and both image validations on the handoff content. Missing tools, zero tests, failed capture, unrun remote jobs and unavailable platforms stay visible. Preserve actual commit/dirty metadata; rebuild artifacts when claiming a clean fixed-commit build.
- [x] **Step 3 — Review:** Request an independent code review using the applicable review workflow; if no authorized independent reviewer is available, record self-review accurately and keep that gate incomplete. Verify findings against evidence, fix actionable defects and rerun the affected checks before final full validation.
- [x] **Step 4 — Handoff:** Provide commands for valid and intentionally invalid replay, JSON/HTML/Markdown examples, Docker network/output setup, package/contract provenance and known limits. The existing evaluation chat may independently run a fixed commit against the real target under its own authorization; do not send messages or run live probes beyond the user's granted scope.
- [x] **Step 5 — Commit and report:** Make the scoped local Stage A checkpoint, report verified developer/container acceptance separately from real service status, and stop before B unless the user has authorized proceeding. Do not push or publish as part of completion.

## Spec Coverage and Plan Self-Review

| Spec area | Owning tasks |
| --- | --- |
| 1–4: scope, modules, target and contract | 1–3, 6, 9 |
| 5: transport, limits, evidence, privacy | 7–9 |
| 6–7: framing, lifecycle, messages, four cases | 4–6 |
| 8–10: statuses, results, detector matrix | 2, 4–10, 12 |
| 11–12: phase boundaries and independent acceptance | 9, 11–12; B/C/D implementation excluded |
| 13–14: official provenance and exact contract selection | 3, 9; matrix/update/re-scoring excluded |
| 15: Dev Container, runtime, architectures | 1, 10–12; optional Claude runner excluded |
| 16: Python organization and SDLC harness | 1–2, 10–12 |
| 17: GitHub checks/contribution entry points | 11; registry publishing and maintenance skill excluded |
| 18: restrained, Agent-readable reports | 8, 10 |

Type ownership and cross-task interface names were checked against this plan. The five Review Focus items each have named tests in their owning tasks. External source hashes, exact tool/image versions and actual execution outcomes remain implementation-time observations, not fabricated planning data.
