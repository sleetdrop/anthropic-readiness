# Stage A execution progress

Plan: `docs/superpowers/plans/2026-10-15-stage-a-implementation.md`.

Execution method: native, sequential, approved on 2026-10-15.
Baseline: `676f105` on `feat/stage-a`; current project directory was explicitly selected for this new repository.

Task 1: in progress. Docker access confirmed with authorized execution; no product tests have passed yet.

Ruling: use the dedicated new repository in place, on a feature branch — the approved plan selected this directory and no existing application checkout needs isolation.

Environment preparation: dev image and actual Dev Container built/started successfully (arm64). Python 3.12.15, uv 0.13.1, Dev Container CLI 0.89.0. Dependency lock resolved 39 packages. Initial four check-runner behavior tests observed RED then GREEN inside Linux; formal pytest and strict checks await environment sync.

Task 1 verified: Dev Container pytest 4/4 passed; bootstrap fast graph passed lock, format, lint, strict types and tests. Installed CLI help ran from `/tmp`. This verifies the development foundation only. Source/validator/runtime acceptance remains incomplete.

Task 2 verified: eight domain/schema tests pass, including mixed-result round-trip and structurally valid inconsistent readiness rejection. Initial RED exposed absent modules; the first implementation also exposed and corrected aggregate precedence. Bootstrap graph remains green (12 total tests). Six packaged schemas and pure shared records are present; filesystem evidence checks remain Task 8.

Task 3: strict config/contract tests 18/18 passed. Five official sources retrieved at 2026-10-15 15:58 UTC; normalized hashes recorded in the packaged manifest. Runtime resolution stays offline. API date 2023-06-01 with no beta is the sole supported contract. Fixture hashes cover legal and defective controls; detector coverage is implemented in Tasks 4–6.

Task 4 verified: nine framing tests pass, including all byte split positions, one-byte delivery, 30 seeded multi-split plans, invalid UTF-8, EOF tails and event limits. Full bootstrap graph passed with 39 tests. Framing has no transport or Anthropic imports beyond domain records.

Task 5 verified: 30 streaming tests and the 69-test bootstrap suite pass. Versioned legal/defect fixtures retain verdicts at every split position. Regression tests preserve initial-field defects, duplicate-stop failures and known bad tool input alongside unknown extensions; complete message stops remain proven when capture times out. Shared message checks were introduced here to avoid two different reconstruction/nonstream verdict engines; Task 6 adds direct acceptance coverage.

Task 6 verified: direct message/case tests 24/24 pass. Unknown stop reasons remain indeterminate, non-object tool input fails protocol structure, and max_tokens preserves protocol validity but fails short-task completion. Exactly four case/version definitions retain 3/4 request selection and explicit capability exclusions. The complete bootstrap suite passed (93 tests), including strict types and lint.

Task 7 verified: 17 transport/deadline tests pass against loopback synthetic HTTP and injected transport seams. No retries/redirect following; exact headers and no-auth verified. Absolute deadlines stop active ping streams and preserve message_stop before timeout/reset. Incremental gzip decoding is bounded; observed read sizes remain distinct from retained bytes. Test socket guards reject external connections. Public transport stays synchronous; one internal async request enforces portable absolute cancellation without concurrent cases.
