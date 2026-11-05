# Current work

The repository delivers the
[Anthropic Readiness Skill](../skills/anthropic-readiness/SKILL.md).
Start with its offline inspector and a saved response. Use
[the exercise](../skills/anthropic-readiness/references/offline-exercise.md)
to verify the workflow on synthetic evidence.

An independent offline walkthrough passed on a saved real SSE response and
two controls. See [the verification record](harness/progress.md) for the
scope and observations.

The probe catalog now covers 22 core cases (27 requests) and 13 separately
selectable version or capability cases. See the [probe guide](probes.md) for
version selection, explicit request caps and coverage boundaries. For a shared
assessment, follow the [Skill report guide](../skills/anthropic-readiness/references/reporting.md)
and render the English synthesis from retained runs.

A [current implementation review](reviews/2026-11-05-current-implementation.md)
reported five correctness issues across its initial and follow-up reviews. R1–R5
are fixed with synthetic controls. Saved response records can be inspected
directly, including `count_tokens` captures, and capture records retain header
and first-byte timings. The Node 24 gate passes 82 tests. See the
[verification record](harness/progress.md) for the fixes and improvement
assessment.

The initial Skill prototype is at `8048934`. That commit also contains the
former standalone application, design records, and the comparison with
llm-comply. Read a particular historical reference with Git when it helps
diagnose a problem:

```sh
git show 8048934:docs/reviews/2026-11-02-llm-comply-maturity.md
git show 8048934:docs/harness/progress.md
```
