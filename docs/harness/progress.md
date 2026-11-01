# Current rewrite progress

Use [the active harness index](README.md), [development](../development.md) and
[the rewrite entry point](../refactor/README.md). The prior 2,213-line mixed
progress record is preserved verbatim as [historical evidence](progress-legacy.md).
Its environment requirements and PASS results do not apply to the rewrite.

## 2026-11-01: rewrite baseline 7f836d1

Owner-approved local-first TypeScript/Node replacement, with containers deferred.
Added next/ shared observations/evidence locations, five-case/six-request migration
inventory and five core controls. Initial missing-implementation RED preceded
passing strict types and five Node tests. An isolated copy installed its own
locked dependencies offline and passed; an earlier offline preparation cache miss
was preserved separately. No Python/container dependency or endpoint runner.
The old delayed-session browser test draft remains an ignored patch, not an
executed fix. Original main CI failures/traces and PR 4 outcome remain retained.

## 2026-11-01: active harness cleanup

Reviewed current guidance, hooks, contribution/PR templates, CI and historical
entry points. Removed active Python/container/full-matrix requirements, archived
old guidance/workflows and reduced current navigation to short entry points.
Pre-commit, root check forwarding and the single Node CI job now use the same
TypeScript check command. Added actual-test-report acceptance that rejects empty,
skipped/todo/cancelled, inconsistent and failing executions, with saved logs and
machine-readable outcomes. A regression reproduced the legacy runtime references
before hooks/CI were changed. Final strict types and seven executed Node tests
passed with zero failures/skips/todos; root forwarding also passed. Local links
were checked across 67 Markdown documents. The new CI YAML and hook were reviewed
locally, not run on GitHub or installed as a global hook. Existing historical
records/workflows were copied byte-for-byte before replacing active entry points.

This is supporting-only work: no additional endpoint scenario, protocol fault
validator, SDK workflow or actual model call was implemented by the cleanup.
No remote push, Actions execution, registry change or existing data migration.
