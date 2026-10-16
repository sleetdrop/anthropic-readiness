# W1 Web console ledger

## Design and authorization

- 2026-10-16: owner chose individual local Docker deployment.
- 2026-10-16: owner approved the interactive console/report visual direction.
- Written specification: [local Web console](../superpowers/specs/2026-10-16-local-web-console-design.md),
  revision 1; explicitly approved by the owner on 2026-10-16.
- Implementation plan: [self-reviewed revision 1](../superpowers/plans/2026-10-16-local-web-console-implementation.md),
  14 sequential tasks; self-review completed and owner approval received on 2026-10-17.
- Execution: current chat, sequentially; owner chose the current checkout/Dev Container.
  W1 branch is `codex/local-web-console`, starting from `ad83593`. Tasks 1–4 are complete;
  tasks 5–14 and whole-W1 acceptance remain pending.

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
