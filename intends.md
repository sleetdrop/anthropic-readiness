# Project intent

Help an agent assess the Anthropic Messages protocol implementation exposed
by a combination of model, inference software, and API conversion software.
The exposed endpoint is the assessment target, including when the underlying
inference service uses another protocol. Record known components and versions
so results from different combinations can be compared.

The main workflow selects core and relevant capability checks, executes the
agreed scope, and reports verified behavior, protocol differences, and coverage
gaps with retained evidence. Missing or unrun checks do not establish a pass.
Keep protocol, task, and actual client outcomes separate. A successful task
can coexist with a protocol deviation.

Deterministic helpers capture or inspect evidence and report rule findings.
The agent chooses the scope, interprets the results, and can investigate an
individual failure with the smallest useful comparison. Attribute a difference
to a particular component only when evidence distinguishes that component.

The deliverable is the `@sleetdrop/anthropic-readiness` npm scaffold. It
creates a project for one target with a local configuration, the bundled
[assessment Skill](scaffold/skills/anthropic-readiness/SKILL.md), and Node
helpers. The user's agent drives the assessment and any focused investigation.
The investigation requires explicit opt-in and request/time bounds before
making live endpoint calls.
