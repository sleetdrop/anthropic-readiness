# Stage A execution progress

Plan: `docs/superpowers/plans/2026-10-15-stage-a-implementation.md`.
Execution: approved sequential implementation in this chat; no implementer agents.
Baseline: `676f105`; delivery branch: `feat/stage-a`.

Current milestone: all 12 tasks complete; local offline developer/container
acceptance passed. Remote CI, actual endpoints and registry publication are unrun.
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
