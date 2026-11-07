# Current work

The repository delivers the `@sleetdrop/anthropic-readiness` npm scaffold.
Each [generated project](../README.md#create-a-test-project) contains a
local target configuration and the bundled
[Anthropic Readiness Skill](../scaffold/skills/anthropic-readiness/SKILL.md).
Use the [local tarball workflow](development.md#try-the-npm-package-locally)
to try the package from the current checkout.

The local check covers offline npm packaging, project creation, and one
bounded authenticated request against a synthetic endpoint. Independent
acceptance regenerated the consumer project from the npm tarball and passed
explicit and implicit Skill use in fresh Codex CLI chats. A separate agent
previewed the configured target and completed one bounded synthetic request.
A subsequent fresh chat completed all 22 core cases in 27 synthetic requests,
detected an intentional missing-field control in one additional request, and
generated the formal English assessment with the bundled renderer. The source
session independently checked the saved outcomes, distinct case count, and all
57 local report links and anchors. No actual SDK client was exercised.
The [offline exercise](offline-exercise.md) describes the diagnosis controls.
See the [verification record](harness/progress.md) for the tested scope.

The next npm package candidate is `0.2.1`, with assessment-oriented Skill and
project instructions. The existing local `v0.2.0` tag is unchanged. Follow the
[release sequence](development.md#release-the-npm-package): pass acceptance,
merge into `main`, create the matching annotated version tag, then publish
the inspected package from that revision after explicit authorization for
remote writes. Registry installation remains unverified.

An owner-authorized private configuration check completed one real request:
HTTP 200 and the forced-tool task passed, but response checks found a model
identifier mismatch, missing `stop_sequence`, and a thinking block without
`signature`. This confirms the configured target can complete that task;
the requested model routing and broader compatibility remain unverified.
Original evidence and target details stay in the local consumer project.

The subsequent full private assessment selected all 32 non-migration cases
under `2023-06-01`. It completed 36 attempts in approximately 87.5 seconds;
two planned tool continuations were prevented by failed prerequisites. Case
results were 27 FAIL and 5 BLOCKED, while task results were 15 PASS, 7 FAIL,
4 INDETERMINATE, and 6 SKIP. A formal English report separates protocol
deviations, explicit input rejection, uncertain capabilities, and untested
scope. The source session verified every capture hash, all 82 selected
evidence references, and 107 local report links and anchors. See the
[verification record](harness/progress.md) for the tested scope and workflow
changes. Original private captures and reports remain in the consumer project.

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
