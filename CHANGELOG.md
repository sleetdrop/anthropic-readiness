# Changelog

## Unreleased

- Support Node.js 22.18+ on 22.x and 24.2+ on newer release lines, removing
  the initializer's Node 24-only restriction and upper engine bound.
- Check packed workbenches on Node 22, 24, and 26, with strict engine checks.

## 0.1.0 - 2026-11-08

- Generate a local workbench with target configuration, a credential file,
  `AGENTS.md`, and a bundled Anthropic Readiness Skill.
- Run bounded Anthropic Messages probes and inspect saved JSON or SSE captures.
- Separate protocol findings, task behavior, and untested client outcomes.
- Produce HTML assessments with links to retained request/response evidence.
