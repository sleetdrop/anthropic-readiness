# Existing-tool research and development decision

Date: 2026-11-01 (Asia/Shanghai). The owner requested a fresh market search and
explicitly directed stopping this project if tools in this category already exist.

## Decision

Stop independent feature development. Existing tools directly assess arbitrary
Anthropic-compatible endpoints; lack of such tooling is no longer a reason to
build this application. Preserve local source and evidence. Do not implement the
retained A-D route, delete data, archive GitHub or publish changes automatically.
First evaluate an existing tool if the owner subsequently requests further work.

## Direct candidates and primary evidence

### llm-comply: first candidate for local evaluation

[Repository](https://github.com/Oaklight/llm-comply),
[Anthropic test source](https://github.com/Oaklight/llm-comply/blob/master/src/llm_comply/tests/anthropic.py),
[PyPI](https://pypi.org/project/llm-comply/),
[changelog](https://github.com/Oaklight/llm-comply/blob/master/CHANGELOG.md),
[hosted UI](https://llm-comply.service.oaklight.top/).

MIT-licensed endpoint compliance tool with custom URL/model/headers, local CLI and
Web, progress and JSON output. Actual test definitions were inspected, including
message, system/multi-turn, tools, SSE/usage and thinking probes. Current repository
README additionally documents expanded coverage, bundled schema-source manifests,
spec checks/updates and a scheduled upstream refresh workflow. It is a direct
category match, not merely an API-key ping or a model benchmark.

PyPI lists 0.5.0 dated 2026-09-12, so the tool predates this project's October work.
The earlier assumption that no tool existed was incomplete research, not evidence
that all alternatives appeared during our development. Package releases, repository
head and cached file views differ; do not conflate their case counts/features.

Limits to verify in a real trial: the viewed thinking probe uses model-name-based
eligibility, which can skip non-Claude names. README describes documented schema
relaxations and optional checks. Inspect selected cases, skips and relaxed rules
before interpreting a self-hosted DeepSeek/GLM result. This is not a complete source
audit or a promise of exhaustive protocol-version conformance.

### ModelsExam: Web/report alternative

[Repository and setup](https://github.com/modelsell/ModelsExam),
[README source](https://raw.githubusercontent.com/modelsell/ModelsExam/main/README.md),
[website](https://modelsexam.com/).

AGPL-3.0 application with custom Anthropic Messages targets, Web progress,
persistent/shareable reports and comparison baselines. Its broader model-authenticity
and performance focus is less aligned with pure protocol assessment. Local/private
targets require its documented local deployment settings; the hosted website is
not a way for its remote server to reach this computer's loopback proxy. Reviewed
readme/site descriptions do not establish exhaustive protocol coverage or maturity.

### Additional hosted match

[JinDaGe compatibility tester](https://jindage.com/en/api-compatibility) exposes an
Anthropic mode and a seven-check capability matrix covering generation, streaming,
tools, structured JSON, vision, models and errors. This is supporting category
existence evidence; local hosting, source and deep conformance were not verified.
It is not the primary replacement recommendation.

## What this investigation did and did not establish

Searched English/Chinese web results, inspected primary repository/package pages,
read actual Anthropic test definitions and checked publicly available Web forms.
These tools exist and overlap the core product purpose. No candidate was installed,
executed, credentialed, or sent a request to the private endpoint. Documentation
and source inspection establish candidacy, not real endpoint results, report quality
or exhaustive coverage. Some public source views differ in revision or contain
outdated wording; prefer a pinned candidate revision for any future trial.

No flaw or missing convenience feature in a candidate automatically restarts this
project. The economical next choice is bounded adoption testing, then upstream
contributions if useful. Resuming independent development requires a new explicit
owner decision, not sunk-cost reasoning or an expanded feature wishlist.
