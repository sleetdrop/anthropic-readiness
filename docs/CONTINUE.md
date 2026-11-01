# Current work

## Local-first TypeScript rewrite

The owner authorized replacing the Python stack on 2026-11-01 and deferring Docker,
Compose and Dev Container until useful mature operation. Read [AGENTS.md](../AGENTS.md)
and [the rewrite entry point](refactor/README.md); use [development](development.md)
for the one Node check entry point. Historical milestone rules do not govern this work.

Branch: codex/typescript-refactor. Baseline 7f836d1 introduced next/ with shared
observations/evidence locations, a complete five-case/six-request migration inventory
and five core controls. No TypeScript endpoint runner, SDK check or Web flow is
implemented yet; no added endpoint coverage is claimed by scaffolding/harness work.

The owner will create an economical-model implementation chat for
[T1 message validation](refactor/task-01-message-validation.md). It owns only its
protocol implementation/test files; the coordinator owns interfaces, orchestration
and integration review. Communicate directly under the owner's authorization.

The active harness now uses Node checks/hooks/CI only. Old docs have explicit
legacy entry points; scheduled image CI is outside .github/workflows. See
[progress](harness/progress.md) for actual local checks. Remote CI remains unrun
for the rewrite; no remote push was authorized in this step.

## Defects and remaining scope

The previous main had a real startup race: delayed initialization overwrote early
endpoint input. Original CI/trace is retained; the new form must explicitly test
that behavior. Broader streaming tools, multi-turn state, invalid-request/error
handling, SDK/Claude Code workflows and protocol-version maintenance remain core
goals. Do not stop at a five-case migration or defer them behind container work.

PR 4 merged as 4ed2bd5. Its required PR checks passed; later main CI passed both
Python jobs/runtime smoke but failed one container browser case (108 passed, one
failed). See [the outcome](https://github.com/sleetdrop/anthropic-readiness/pull/4).
Existing installed data/private reports are not migration fixtures.

The [previous full continuation](CONTINUE-python-legacy.md),
[old progress](harness/progress-legacy.md) and [old handoff](HANDOFF-python-legacy.md)
remain historical evidence, not instructions to restart those plans.
