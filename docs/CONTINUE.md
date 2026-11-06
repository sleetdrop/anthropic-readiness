# Current work

The repository delivers the `@sleetdrop/anthropic-readiness` npm scaffold.
Each [generated project](../README.md#create-a-test-project) contains a
local target configuration and the bundled
[Anthropic Readiness Skill](../scaffold/skills/anthropic-readiness/SKILL.md).
Use the [local tarball workflow](development.md#try-the-npm-package-locally)
to try the package from the current checkout.

The local check covers offline npm packaging, project creation, and one
bounded authenticated request against a synthetic endpoint. Codex discovered
the Skill from a generated project. The
[offline exercise](offline-exercise.md) covers model-driven diagnosis.
See the [verification record](harness/progress.md) for the tested scope.

An independent offline walkthrough passed on a saved real SSE response and
two controls. See [the verification record](harness/progress.md) for the
scope and observations.

The probe catalog now covers 22 core cases (27 requests) and 13 separately
selectable version or capability cases. See the
[probe guide](../scaffold/skills/anthropic-readiness/references/probes.md) for version
selection, explicit request caps and coverage boundaries. For a shared
assessment, follow the [Skill report guide](../scaffold/skills/anthropic-readiness/references/reporting.md)
and render the English synthesis from retained runs.

A [current implementation review](reviews/2026-11-05-current-implementation.md)
reported five correctness issues across its initial and follow-up reviews. R1–R5
are fixed with synthetic controls. Saved response records can be inspected
directly, including `count_tokens` captures, and capture records retain header
and first-byte timings. See the [verification record](harness/progress.md)
for the fixes and the latest Node 24 check.

The initial Skill prototype is at `8048934`. That commit also contains the
former standalone application, design records, and the comparison with
llm-comply. Read a particular historical reference with Git when it helps
diagnose a problem:

```sh
git show 8048934:docs/reviews/2026-11-02-llm-comply-maturity.md
git show 8048934:docs/harness/progress.md
```
