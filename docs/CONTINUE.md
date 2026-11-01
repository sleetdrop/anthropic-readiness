# Current work

## Goal and delivery route

Build the focused Anthropic Messages assessment tool in [intends.md](../intends.md):
run an explicit protocol scope through Web or CLI, inspect/share reproducible
findings, then verify a repair. Read [the delivery route](refactor/README.md) and
[coverage inventory](refactor/coverage.md). They replace migration-first sequencing;
completed T1/T2 files are historical task records, not the next product objective.

The coordinator owns coherent delivery, not case-by-case requests for the owner to
choose work. The next product checkpoint is route A: an operable Node Web/CLI
application together with expanded core Agent conversations and honest findings.
Implement internally in small commits; do not call another validator or a five-case
GUI the delivered product. Preserve the accepted design; no new visual exploration.

## Implemented and verified

Branch codex/typescript-refactor; active package next/, one Node 24 LTS. No initial
Python/Docker/Dev Container dependency. Shared HTTP engine, final-message/SSE
validators and CLI run five migrated scenarios with six attempts. Captures are
written before parsing; outputs are result.json and Chinese/English report.md.
[CLI guide](refactor/cli-trial.md). No new Node Web server/UI, SDK or Claude Code
workflow exists. Do not present the old Python UI as the rewritten application.

Source/corrections: 1706639/058cec9. Last strict-type/Node gate: 60 executed tests,
no failures/skips/todos, Node24.22.0. One owner-authorized real trial completed all
six requests in about 8.6 seconds; all five task behaviors passed. Raw inspection
confirmed missing stop fields and different request/response model names. The
latter is an identity-policy outcome, not proof of wrong routing. Thinking/delta
validation/assembly is incomplete; original events survive. Private captures remain
outside source. No additional/expanded live calls are authorized by that used budget.

The current header is 2023-06-01 with no beta and development rules label
0.2.0-dev; immutable source snapshots, selection and version matrices are absent.
Official current docs now default to 2026-10-21. The previous manual latest-source
comparison is not a completed version-specific audit. Preserve previous results;
bind applicable rules/sources before claiming reproducible version conformance.

## Remaining work and verification boundaries

Route A covers working Web interaction, core thinking/tool/multi-turn execution,
evidence and portable reports, plus source/manifest and verdict-policy corrections.
B completes selected-contract coverage and repair replay/reruns. C completes real
SDK/Claude Code, maintained/selectable snapshots, repair handoff and Node cutover.
D defers distribution until mature use. The inventory retains optional-feature,
negative-request and supplemental API gaps; none are implicitly retired.

Keep the known startup-input race as an explicit delayed-initialization browser
regression during Web migration. Old PR4 merge 4ed2bd5 passed required PR checks;
later main CI had a real container browser failure (108 pass/one fail). Retained
history/draft is not a tested fix in Node. New CI has not run remotely; no rewrite
push/publication is authorized. Use npm --prefix next run check; reuse unchanged
source evidence and add Node browser acceptance for implemented Web behavior.

[Progress](harness/progress.md) records evidence. Previous full handoffs and old
Python milestone files are reference, not current requirements or acceptance.
