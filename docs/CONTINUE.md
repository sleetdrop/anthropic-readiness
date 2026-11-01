# Current work

## Local-first TypeScript rewrite

The owner authorized replacing the Python stack on 2026-11-01 and deferring Docker,
Compose and Dev Container until useful mature operation. Read [AGENTS.md](../AGENTS.md)
and [the rewrite entry point](refactor/README.md); use [development](development.md)
for the one Node check entry point. Historical milestone rules do not govern this work.

Branch: codex/typescript-refactor. The Node CLI now executes the five migrated
scenarios, reserving six request attempts for complete scope. It writes raw capture
records before parsing, then result.json and Chinese/English report.md. See
[the trial guide](refactor/cli-trial.md); preview makes no requests and execution
requires explicit live admission. Synthetic service/CLI checks passed. One
owner-authorized real endpoint trial is now complete; no new Web UI or SDK/client
compatibility is claimed.

T1/T2 were implemented in chat 01a1957d-20a0-7491-aefb-2a509bc9a836, with
coordinator review/corrections. The coordinator implemented HTTP capture, shared
execution and CLI; baseline 1706639 was independently reviewed in that chat.
Task false-passes were reproduced and corrected using deterministic text, strict
counting and nonce-only tool results. Related case revisions are now 2. The new
rule snapshot is typescript-messages-2023-06-01-core/0.2.0-dev, not the old Python
bundle identifier. Final strict types and 60 executed tests passed, no skips/todos.

The first real CLI trial completed five scenarios/six requests within the agreed
budget: all task behaviors passed, while strict checks found omitted stop fields
and a request/response model-name difference. Model-name differences require
alias confirmation, not an inference of wrong routing. Thinking/delta support is
a known validator/assembly gap; its inconclusive observations are not endpoint
faults. Raw requests/responses and private interpretation remain outside tracked
source. See progress for the evidence boundary. Broader streamed-tool, multi-turn/error
cases and SDK tests remain product priorities; five migrated cases are not the
finished catalog. The new Web flow should reuse accepted design when implemented.

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
