# Current work

The repository delivers the
[Anthropic Incident Diagnosis Skill](../skills/anthropic-incident-diagnosis/SKILL.md).
Start with its offline inspector and a saved response. Use
[the exercise](../skills/anthropic-incident-diagnosis/references/offline-exercise.md)
to verify the workflow on synthetic evidence.

An independent offline walkthrough passed on a saved real SSE response and
two controls. See [the verification record](harness/progress.md) for the
scope and observations.

The initial Skill prototype is at `8048934`. That commit also contains the
former standalone application, design records, and the comparison with
llm-comply. Read a particular historical reference with Git when it helps
diagnose a problem:

```sh
git show 8048934:docs/reviews/2026-11-02-llm-comply-maturity.md
git show 8048934:docs/harness/progress.md
```
