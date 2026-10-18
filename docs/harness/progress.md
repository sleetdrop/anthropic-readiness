# Stage A execution progress

Plan: `docs/superpowers/plans/2026-10-15-stage-a-implementation.md`.
Execution: approved sequential implementation in this chat; no implementer agents.
Baseline: `676f105`; delivery branch: `feat/stage-a`.

Current milestone: all 12 tasks complete; local offline developer/container
acceptance passed. Remote CI and registry publication are unrun. The original
handoff did not include real endpoints; a later private observation is recorded below.
The machine-readable evidence is [handoff.json](handoff.json); this status does not
certify a service. Local artifact paths refer to this checkout and are ignored by Git.

## Completed implementation

Tasks 1–3 established the Dev Container, locked modern Python package, strict
domain/config/result contracts, packaged schemas and immutable official-source
API bundle. Tasks 4–6 added incremental SSE framing, lifecycle/message validation
and the four fixed cases. Tasks 7–9 added bounded transport, redaction/evidence,
required-case accounting, offline replay and explicit live opt-in. Task 10 added
restrained Chinese HTML/Markdown reports, reader guidance, sources and installed
wheel acceptance. Task 11 added quality gates, negative gate controls, pinned
GitHub workflows, contribution templates and two-architecture image validation.
Task 12 mapped coverage, arranged the independent review, fixed its findings,
revalidated final sources and assembled the handoff.

Meaningful counterexamples were observed RED before behavior was implemented;
legal controls/goldens were retained. The permanent
[implementation ledger](implementation-ledger.md) records task ranges, commands,
review fixes and all scope rulings. Historical intermediate status snapshots are
retained in Git and ignored artifacts/implementation-history; their former pending
wording is not the current milestone.

## Final observations

Verification commit: `be168d9962ff3dacd5e480818dd537d9f3438593`, observed clean on the host.
Source fingerprint: `f7cdcacf4a7942b286f3c2c8f5e7ad14e9a3d3f7ce6bceb7ca59778d694daebd`.
Lock SHA-256: `8025bb668b4aa0aa8a8b949f71c166b895c973f74eb038570c13d655be98043d`.
Container Git metadata was unavailable/null where recorded; host proof, source/lock
fingerprints and runtime revision labels are bound separately without inventing fields.

- Python 3.12.15 Dev Container: all 11 full gates passed; 166 tests.
- Python 3.11.17 compatibility floor: all 11 gates passed; 166 tests; network disconnected.
- Fast graph: all seven gates and 107 unit/harness tests passed.
- Full count per graph: 107 unit/harness, 22 integration, 36 acceptance, one installed-package;
  zero failures, errors or skips. Image-prepared dev full graphs independently passed.
- linux/arm64: native; artifacts/images/1792129994691446000-arm64/image-result.json; runtime sha256:70de0d813e37b7ad0634939d8ea84518898d54fb9aa0563bde5f403fa81b6de7.
- linux/amd64: emulated; artifacts/images/1792131819611604000-amd64/image-result.json; runtime sha256:3414c59a88956b16812a6a5d290a532f3db393cdb8711dfa263ce33396d400c1.
- Image controls include UID 10001 by default, read-only root, bounded tmpfs, no-network
  replay, retained output, internal synthetic peer, SIGINT 130/SIGTERM 143, package/OS
  inventories and host.docker.internal against a temporary generic loopback server.
- Exported wheel/sdist built offline; wheel resources matched source and the exported
  wheel installed/executed in a clean Linux venv outside source. The initial standalone
  export command did not select the prepared project environment and lacked its
  backend on the subprocess path; invoking it through uv run corrected the command.
  No dependency declaration was changed and the failed attempt is retained.
- Desktop, narrow and four-page print visual checks passed. Layout CSS was unchanged
  by final review fixes. The mixed synthetic layout sample intentionally lacks evidence.

## Independent review closure and boundaries

The fresh-context gpt-6-astra/xhigh review found six Important defects and independently
passed the earlier 152-test candidate. The author reproduced and fixed required
membership, transformed replay, deep JSON/capture persistence, assertion evidence
verification, interrupted UTF-8 and installed provenance in one RED-to-GREEN pass.
Two onboarding/domain documentation errors were regraded Important and fixed in
the same pass. Final full suites passed 166 tests. No second review or deferred
minor remains. See [review closure](../reviews/2026-10-16-stage-a-review.md).

Capture writer 1.1 versions the lifecycle projection proof; 1.0 reads remain
conservative. API bundle 1.0.0, prompts and historical results are unchanged.
Tool loops/matrices, real Claude Code, protocol-update Agent command and remote
release/account operations remain outside A. Native amd64 remote CI, real service
compatibility and published-image availability remain unobserved.

Handoff-only follow-up commits affect excluded records and do not rebuild or
relabel the verified images. The next stage requires separate owner scope.

## Post-handoff private endpoint observation (2026-10-16)

An owner-authorized private real endpoint assessment completed after the frozen
Stage A offline handoff. Four planned/four actual requests, zero retries, 20.74 seconds,
exit 1. All four returned HTTP 200 and complete captures; behavior passed for all
four cases. Protocol failed under the selected fixed core/identity contract:
MSG-CORE (missing stop metadata fields) and MSG-MODEL (unallowlisted response alias).
The response alias must be confirmed by the operator before a separately configured
assessment; no identity policy or original result was weakened to obtain PASS.
The saved report was re-rendered with network=none: evidence status verified, no errors.
Thinking, multi-turn tools, real clients and version-selection semantics remain untested.

Private target configuration, model identifiers, response bytes and detailed reports
remain outside Git and image build contexts. No additional API request or proxy/code
change was made. The original handoff manifest retains its historical not_run
endpoint status; this later observation does not rewrite that frozen acceptance.
See [the validation ledger](validation-ledger.md) for the scoped observation.

## Report readability follow-up (2026-10-16)

The owner approved a bounded presentation update after the private report was hard
to interpret. The renderer now leads with Chinese task/protocol summaries and groups
repeated findings; verified field/model excerpts explain the recorded failures.
Original results, contracts and endpoint evidence are unchanged; no new API call.
See [the report ledger](report-readability-ledger.md) for RED-to-GREEN evidence and
the explicit static-render versus browser acceptance boundary. The frozen Stage A
handoff/image manifests still describe their original baseline, not this new renderer.

Final report follow-up verification: all 11 full gates passed, 171 tests, zero
failures/errors/skips; source remained unchanged during the run. Check manifest: artifacts/checks/1792138109363923672/check-result.json.

## Reference-informed report refinement (2026-10-16)

At the owner's request, inspected actual AI Ping HTML examples and primary
Schemathesis, Allure and Inspect documentation. Presentation 1.2 adds a compact run
summary, contextual conclusion, numbered/linked findings, partial JSON comparisons
and per-case source links. Format differences and identity configuration have
separate treatment labels while original assertion statuses remain intact.
See [the reference study](../reviews/2026-10-16-report-reference-study.md) and
[reader ledger](report-readability-ledger.md) for rationale and RED-to-GREEN evidence.

All 11 full Linux/Python 3.12 gates passed; 175 tests, zero failures/errors/skips.
Check manifest: artifacts/checks/1792140545162506299/check-result.json. Source unchanged during verification.
Static desktop/narrow layouts and eight A4 pages were inspected with URL fetching
disabled; actual browser interaction and responsive acceptance remain unrun.
The private offline render preserved original result bytes and all 20 evidence files,
with verified evidence/errors=[] and zero new API calls. No image rebuild, remote
CI or publication was performed. Frozen Stage A records remain historical.

## Second owner-authorized private model assessment (2026-10-16)

The owner requested the same four-case live validation for another model on the
local proxy. Offline validation/dry-run passed, then exactly four requests completed
in 12.557 seconds with HTTP 200 and complete captures, zero retries. Task behavior
passed in all four cases; the fixed protocol/identity contract failed in all four.
Observed failures are missing stop fields and an unallowlisted response-name alias;
no model routing cause is inferred. See [the validation ledger](validation-ledger.md).

Presentation 1.2 was generated offline from the saved result, preserving its bytes
and all 20 evidence files, with evidence verified/errors=[] and no extra API call.
Private inputs and outputs remain outside the repository. This endpoint observation
does not replace frozen Stage A acceptance or establish client workflow readiness.

## Comprehensive private API and client validation (2026-10-16)

At the owner's explicit request, completed a private disposable black-box assessment:
90 API scenarios, four official SDK cases, three fixed Claude Code workflows and
127 actual upstream requests within a 200-request/60-minute envelope. All seven
client scenarios passed independent observable conditions. The API reader audit
reports 61 PASS, 18 FAIL, eight INDETERMINATE, one optional rejection and two blocked
prerequisites; no unified compatibility percentage is inferred.

Six harness controls and seven audit controls passed offline; original failed
attempts and pre-audit interpretations are retained. The final report verified
799 evidence hash references without errors. See [validation ledger](validation-ledger.md)
and [assessment method](../reviews/2026-10-16-private-comprehensive-assessment.md).
Only handoff/validation documentation changes enter Git. Private scripts and actual
responses remain outside source and builds; Stage B/C remain unimplemented in the
shipped CLI. No source/image/full-product/remote-CI acceptance is implied by this
private run.

## Private assessment finalization after owner resume (2026-10-16)

Resumed from the explicit limit pause without new endpoint requests. Rechecked
127 request records, all 90 API/seven client scenario accounting, 799 evidence
hash references, 1036 report links and the official CLI checksum. Both recorded
live containers exited successfully and have been removed; private preparation
copies in the Dev Container were cleaned. Product source and lock remain unchanged.

Final report timing now uses the full relay observation window including the last
two ID probes, rather than the main run's earlier checkpoint, and displays the
explicit Asia/Shanghai offset. The corrected window is 1073.07 seconds, within
the 60-minute budget. Pre-finalization presentations and indexes remain archived
privately; original assertions, captures and verdict files were not rewritten.
Final provenance binds original plans, test/audit scripts, client checksums,
container records, reader output and this documentation closure.

## Local Web console design research (2026-10-16)

The owner requested a Docker-hosted GUI with target entry, live progress and optional
report export, while retaining independent CLI execution and automatic reports.
The owner selected individual local Docker deployment for the first version.
Read the [reference study and proposed direction](../reviews/2026-10-16-web-console-reference-study.md).
Official Promptfoo, Inspect, Postman, Locust, FastAPI and browser SSE documentation
informed the proposal. This is awaiting owner design feedback, not an approved spec
or implementation plan. No product code, dependency, frozen Stage A ledger or
acceptance manifest changed; no model call or product check was run.

## Visual report and console proposal (2026-10-16)

The owner requested stronger charts, matrices and interaction while retaining a
restrained professional style, and approved a browser visual companion. Read the
[visual-expression proposal](../reviews/2026-10-16-visual-expression-design.md).
The ignored synthetic mockup connects a running console, capability matrix,
status distribution, timeline, finding impact and expected/actual drawers.
Browser interaction observations are recorded in the proposal; no product-source,
dependency, live-endpoint or frozen Stage A acceptance change is claimed.

## W1 visual direction approved and written specification (2026-10-16)

The owner approved the browser console/report design and requested advancement.
The [written W1 specification](../superpowers/specs/2026-10-16-local-web-console-design.md)
formalizes local Docker use, shared CLI/Web services, durable job events, visual
reports and offline exports. Self-review resolved lifecycle/result separation,
restart/credential-loss behavior, source integrity and actual catalog scope.
Written-spec review is pending; the [new W1 ledger](web-console-ledger.md) separates
this milestone from frozen Stage A records. No implementation plan, new dependency,
product check, image acceptance, remote CI or live request is claimed.
The existing Linux/Python 3.12 Dev Container passed the offline documentation/link
and collaboration check; `git diff --check` also passed. These are documentation
checks only, not W1 implementation acceptance.

## W1 specification approved; planning paused by owner (2026-10-16)

The owner explicitly approved written specification revision 1. A 14-task native
sequential plan was drafted, but the owner paused before its self-review finished
to close the laptop and travel home. The plan is explicitly DRAFT, with open review
items and resume instructions in the W1 ledger. Do not begin implementation or ask
for plan approval from this unfinished checkpoint. No new dependency installation,
product process, model call or W1 acceptance was started during planning.

## W1 planning resumed and self-reviewed (2026-10-17)

The owner explicitly resumed from home after reconnecting the network. Completed
the plan's five recorded self-review items and mapped all twelve W1 acceptance
requirements to fourteen sequential tasks. Clarified exclusive assessment output
versus job directories, shared early run identity, idempotent admission before
preview expiry, schema adapter purity and concrete regression assertions. The
approved spec's scope is unchanged. The plan now awaits owner review; no product
implementation, dependency preparation, browser acceptance or live call was started.
The existing Linux/Python 3.12 Dev Container passed the offline documentation/link
and collaboration check on the resumed plan; whitespace validation also passed.
These observations do not establish any W1 product acceptance.

## W1 execution approved; Task 1 in progress (2026-10-17)

The owner approved the 14-task plan and chose the existing checkout/Dev Container.
Created local branch `codex/local-web-console` from `ad83593`; the original full
11-gate offline baseline passed before implementation. Task 1 added pure operational
records/ports, packaged operational schemas and optional Web dependencies. Observed
RED failures preceded implementation; 69 targeted checks now pass while the Node
check awaits official preparation. The first fast run failed test-style lint and
the missing toolchain marker; these are retained instead of whole-task PASS.
Toolchain preparation remains in progress. No W1 live endpoint call, runtime image
acceptance or remote CI has run.

Task 1's final fast graph passed all seven gates; complete pytest passed 245 tests.
The official Node archive and immutable image digest are verified, with exact
Python/npm tool versions locked. Browser preparation is separate and still in
progress; no W1 browser/image acceptance is implied by these source checks.

## W1 Task 2: recoverable operational records (2026-10-17)

Implemented schema-checked ordered events, private replaceable execution snapshots,
exclusive case checkpoints and pure observed-span reduction. Meaningful RED covered
write failure, symlinks, interrupted logs and missing published checkpoints. Recovery
retains committed prefixes and evidence; corrupt interior records fail explicitly.
Durable events recover even when snapshot replacement fails. Final Linux Python 3.12
fast graph passed seven gates and complete pytest passed 257 tests. Source contracts
and frozen Stage A records remain unchanged. Browser preparation is still separate;
no Web/image/remote/live acceptance is claimed. See the W1 ledger for design rulings.

## W1 Task 3: shared observable execution (2026-10-17)

Added the shared application/credential boundary, early shared run identity, lazy
CLI sidecars, durable case publication, observed/coalesced transport phases and
sticky cancellation. Existing assertion semantics, stdout and exit behavior are
preserved. RED covered adapter behavior, cancellation, failed mandatory writes,
unexecuted/incomplete checkpoint certification and premature completion timestamps.
The unchanged CLI timeout exposed repeated schema compilation; a retained profile
guided compilation caching without bypassing document validation. Corrected
accounting fixtures were replayed against the isolated prior implementation to
establish actual RED evidence. Final checks passed 17 targeted tests, seven fast
gates and all 274 pytest tests in Linux Python 3.12. No W1 live requests were made.
See the W1 ledger for interface/cache rulings and remaining acceptance boundaries.

## W1 Task 4: persistent previews and queue admission (2026-10-17)

Twenty-two observed RED failures preceded the SQLite/frozen-plan implementation.
Final targeted checks passed 22 tests, fast checks passed seven gates and complete
pytest passed 296 tests. Verified owner binding/900-second expiry, immutable plan
hashes, concurrent idempotency, one active/eight waiting capacity, preset isolation,
history pagination and strict explicit URL resolution. Planning made zero upstream
requests. The W1 ledger records admitted-plan access and consumed-plan deduplication
rulings. Process supervision and all later Web/browser/image acceptance remain pending.

## W1 Task 5: worker supervision and recovery (2026-10-17)

Added owned spawn supervision, parent-acknowledged bounded JSON IPC, memory-only
credential binding, five-second cancellation and parent-loss shutdown. Restart
retains checkpoints and never redispatches. Final-result recovery requires verified
evidence and the complete frozen target/plan identity. Actual RED failures and
fixture corrections are retained in the task workspace and summarized in the W1
ledger. Final Linux Python 3.12 verification passed seven fast gates and all 314
pytest tests, including synthetic parent death, SIGTERM, unresponsive worker,
terminal races, storage/provider failure, IPC and secret-persistence boundaries.
Pinned Chromium, dependencies and CJK fonts completed preparation with exit 0;
actual browser, new image and HTTP acceptance remain pending. No real endpoint call,
remote CI, publication or registry push was made.

## W1 Task 6: local HTTP service (2026-10-17)

Added optional lazy serve entry, exact local request protections, expiring sessions,
bounded strict JSON and fixed safe errors, with one lifespan-owned manager.
Retained warnings-as-errors by replacing a deprecated upstream test adapter with
locked HTTPX ASGI transport. Meaningful RED preceded HTTP integration; extra RED
covered non-ASCII CSRF and infinite numeric input. Fixture/source rulings and their
costs are recorded in the W1 ledger. Final Linux Python 3.12 checks passed 15 targeted
HTTP/serve tests, seven fast gates and all 329 pytest tests. Real socket startup and
SIGTERM shutdown were observed on loopback. This is HTTP-boundary acceptance, not
GUI/browser/runtime-image acceptance; no upstream model call occurred.

## W1 Task 7: operations API and resumable SSE (2026-10-17)

Implemented schema-validated preview/start/history/cancel/preset/evidence routes
and read-only reconnectable SSE. Eight observed initial RED failures preceded
behavior; extra regressions cover credentials, duplicate binding and cancellation.
Final Linux Python 3.12 checks passed seven fast gates, 40 targeted tests and all
340 pytest tests. Repeated starts/cursor reads retained exactly three planned
synthetic requests; observer disconnect did not cancel the active worker. The W1
ledger records snapshot/replay, lazy credentials and typed OpenAPI rulings. GUI,
browser and runtime-image acceptance remain pending. No real model call was made.

## W1 Task 8: shared verified visual projection (2026-10-17)

Added verified source loading and schema-validated report-view 1.0/presentation 2.0
projection. Matrix/status/impact counts preserve original case and assertion facts;
observed spans retain coordinates, while legacy results get labeled duration-only
comparison. Partial checkpoints remain distinct from final results. Evidence damage
removes field excerpts; unsafe/mismatched sidecars leave an explicit diagnostic
beside a readable valid result. Provenance and original assertion indexes remain
available for agents. Initial 18 RED assertions and additional targeted REDs are
recorded in the W1 ledger. Final Linux Python 3.12 verification passed seven fast
gates and all 364 pytest tests (74.07s), including 24 new projection/source checks.
No new renderer, GUI/browser, runtime-image or real endpoint acceptance is claimed.

## W1 Task 9: visual offline reports and CLI adapters (2026-10-17)

Added presentation 2.0 with server-rendered capability matrix, native SVG charts,
exact figure tables, evidence comparisons, source/contract appendix and safe optional
packaged interactions. CLI automatic reports and public rerender calls remain;
original result/evidence bytes and exclusive output are preserved. HTML CSP hashes
cover actual formatted script bytes; unclosed intervals have explicit markers.
Corrected a copied-fixture writeback issue, reproduced marker RED against the
corrected fixture, and fixed an observed partial replay mode regression. One old
presentation expectation intentionally changes 1.2 to 2.0; protocol goldens do not.
Final Linux Python 3.12 checks passed seven fast gates, strict frontend type/lint/
format, two Node tests and all 370 pytest tests (76.05s). A prior 368-pass/one-fail
attempt remains recorded. Browser/offline interaction/print/narrow visual acceptance
is deferred to the required Task 12 gate; no runtime-image or live endpoint claim.

## W1 Task 10: immutable report exports (2026-10-17)

Added policy/selection preview, opaque export publication and verified downloads.
ZIPs contain selected offline reports, original result or partial operational
records, optional sanitized evidence, Chinese README/agent guidance and a checked
SHA-256 inventory. Original failed/partial attempts remain intact. Source bytes
are rehashed during copying, publication record is last, and downloads validate
exact returned bytes. Report-only delivery explicitly distinguishes local source
verification from omitted captures. Preview selection/omissions are checked against
the delivered package. Initial eight RED failures and an extra preview mismatch
preceded fixes. Final Linux Python 3.12 verification passed seven fast gates,
39 export/source/evidence/API regressions and all 382 pytest tests (83.94s). Export
preview/create/repeated ZIP and standalone downloads added zero requests beyond the
three synthetic model calls. No GUI/browser/new image/live endpoint acceptance yet.

## W1 Task 11: configuration/live/history interface (2026-10-17)

Added actual four-case local Web pages, strict plain JS preview/progress modules,
recorded lifecycle display, cancellation, presets, contextual evidence drawers and
on-demand exports. History now filters frozen rule/API metadata through transactional
SQLite index v2; corrupt v1 plans abort migration without partial schema changes.
Actual RED regressions and fixture/formatter/process rulings are retained in the W1
ledger. Parent-unpublished evidence no longer leaks into the browsable inventory.
Final Linux Python 3.12 verification passed seven fast gates, nine Node tests,
frontend type/lint/format, 37 Web/store regressions and all 388 pytest tests (88.10s).
Targeted Chromium visual smoke/probes passed against four-case synthetic data with
zero browser errors; full Task 12 browser/offline/print/accessibility gates, new
runtime images, remote CI and real endpoint checks remain distinct and pending.

## W1 Task 12: required browser/frontend gates (2026-10-17)

Unified offline full now includes strict frontend types/lint/format, real Node JUnit,
Jinja compilation/resource inventory and actual locked Chromium. Missing prerequisites
are BLOCKED and zero/claimed-only/skipped test reports cannot pass. Both Python CI
matrix jobs prepare locked Node/npm/Chromium before offline full; remote jobs remain
unrun. Owned fixture/listener and timeout-child cleanup have assertion-level checks.

Actual browser RED exposed missing initial config capability fields, ambiguous
terminal partial labels and print overload; fixes preserve schemas/raw verdicts.
Final unchanged-source Linux Python 3.12 full passed 405 Python tests, nine Node tests,
13 Chromium cases and explicit fixture cleanup. Inspected configuration, summary,
matrix/timeline, drawer, narrow and print screenshots. GUI preview/export/reconnect
request accounting, fake secret clearing, keyboard/accessibility, hostile strings,
network-blocked file HTML and script-disabled essentials all passed. Details and
rulings are in the W1 ledger; failed attempts remain ignored artifacts.
Task 13 owns new CLI/Web image acceptance and delivery docs. Whole-W1 review and
handoff, remote CI and any real endpoint verification remain separate.

## W1 Task 13: delivery source ready, image acceptance pending (2026-10-17)

Implemented separate CLI/Web Docker dependency targets, local nonroot/read-only
Compose, installed Web resource checks and independent Web image observations.
The selected image contract is now packaged image-result 2.0; archived Stage A
1.0 records remain unchanged. Updated Web/CLI/contributor/container guidance.

Observed source verification passed 419 Python tests, Node 9 and Chromium 13.
After reproducing container Git ownership refusal, 22 focused provenance/harness
checks and all eight fast gates passed with scoped read-only Git trust and fsmonitor
disabled. New image source is ready for local baseline commit; native/emulated image
acceptance and Task 14 whole-W1 review/handoff are still pending. Network preparation
uses original locked sources and is not counted as image acceptance.

Task 13 refinement verification passed all 13 source gates: 427 Python tests,
ten Node cases and 14 actual Chromium cases with fixture cleanup. Regressions cover
late credentials with equivalent alias membership, platform-specific synthetic host
routing and revision/platform browser-cache mounts. These source observations do
not replace the pending native/emulated full image acceptance or final W1 review.

Task 13 full native attempts remain retained failures. The latest completed attempt
passed disconnected source gates and CLI checks but exposed a Web partial/final
snapshot race during service replacement. Exact installed responses and two permanent
RED cases now document that boundary. The fix passed 14 HTTP/page regressions and
strict checks; full images must be rebuilt and verified before delivery claims.

Task 13 now distinguishes runtime image architecture from native Linux developer
validation. A translated amd64 browser lost fractional numbers and reported null
for known black/white contrast; that path remains unaccepted. Image observations
2.1 record Docker engine/runtime/developer identities, preserving 2.0 records.
All original lifecycle/Axe assertions remain; numeric calibration blocks invalid
tooling, and a new black/white browser case passed natively. The latest source full
passed 433 Python tests, ten Node cases, 15 Chromium cases and all 13 gates. Updated
native/emulated runtime image jobs and final whole-W1 review are still pending.

Native image fifth passed all developer/CLI checks but caught the terminal-read
retry-exhaustion edge in the actual installed Web image. Its response/trace remain
retained, including the missing normal manifest. Three RED regressions now cover
that edge and failed controller/cleanup publication; 39 focused checks and strict
validation passed. New full image observations are required for these source bytes.

## W1 Task 13 completed; Task 14 candidate acceptance (2026-10-18)

Clean verification source `7739ec18d8be914ec7f311311fcfabc9cc003830` passed
all 13 offline gates with 436 Python tests (251 unit/harness, 127 integration,
54 acceptance and four installed-package cases), ten Node cases and 15 actual
Chromium cases. No test was skipped. Task 13's completion rerun in the prepared
Linux development container also passed the full graph.

The latest native ARM64 and emulated AMD64 CLI/Web image jobs both passed full
acceptance against that same unchanged source and image-context fingerprint.
Both used a separately identified native Linux ARM64 development/browser baseline.
Image-result 2.1 records passed their packaged schema. Actual requested-architecture
runtime, nonroot/read-only isolation, shutdown, volume replacement, cancellation,
export and generic host routing passed. Owned temporary containers were absent
after cleanup. Native AMD64 CI, real Linux-host execution and remote CI remain unrun.

The retained Compose demonstration was upgraded to the exact verified ARM Web
image. Its earlier synthetic volume and results remained readable. Actual visible
GUI preview/export produced a new bundle: all 25 manifest files matched copied
and ZIP bytes, and original result bytes remained identical. A narrow-view matrix
wrapping concern and actual screenshots are explicitly included in final review
materials. This demonstration is synthetic, not a real endpoint observation.

Candidate W1 acceptance/handoff records map all twelve requirements to retained
checks. The independent review is still not_run, so W1-12 and whole-W1 completion
remain pending. The frozen Stage A handoff and 29 protected files are unchanged.
All earlier failures remain retained; no normal manifest was fabricated for the
failed controller attempt that did not produce one.

## W1 independent review and author fixes (2026-10-18)

The sole whole-W1 reviewer completed review of `ad83593..0d1191e`, resuming the
same context after a quota interruption. Verdict: With fixes; five Important,
two Minor, no verified Critical. The author accepted all five Important findings
and regraded the partial-skip gate as Important because it could certify missing
selected checks. Separate failure/unresolved capability filters remain deferred.
See the [review and author disposition](../reviews/2026-10-18-web-console-review.md).

One author RED/GREEN fix pass covers recovered interrupted checkpoints, final
publication/source-hash consistency, honest unknown origin, readable keyboard-
scrollable matrices, matching matrix navigation and selected-test skip rejection.
Focused regressions passed, including actual parent termination, HTTP evidence,
ZIP hashes, mixed-state offline/no-script navigation and Web focus/refresh.
Strict formatting/lint/types passed. Whole new-source and rebuilt-image acceptance
remain pending until their exact observed records are read; old image observations
continue to bind their original verification source only. No real endpoint or
remote publication occurred during W1 review/fixes.

The corrected full author graph passed all13 required gates:454 Python tests,
10 Node cases and22 actual Chromium cases, zero failures/errors/skips. The retained
first full attempt failed a test-only TypeScript module-URL resolution check;
that was corrected without type suppression, then the whole graph reran green.
Fresh native ARM64/emulated AMD64 image jobs are required for this updated source.
