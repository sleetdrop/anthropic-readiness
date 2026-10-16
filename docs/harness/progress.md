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
