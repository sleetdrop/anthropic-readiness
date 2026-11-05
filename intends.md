# Project intent

Help an agent investigate a concrete failure on an Anthropic
Messages-compatible endpoint. Start from the user's symptom and existing
evidence. Prefer the smallest comparison that can distinguish the suspected
fault from other explanations.

Deterministic helpers capture or inspect evidence and report rule findings.
The agent chooses relevant evidence and probes, explains what they establish,
and identifies the next discriminating check when the cause remains uncertain.
A report should point to the observed event or field and separate protocol,
task, and client outcomes.

The deliverable is the repository-scoped
[diagnosis Skill](skills/anthropic-readiness/SKILL.md), its Node
helpers, and synthetic examples. The investigation requires explicit opt-in
and request/time bounds before making live endpoint calls.
