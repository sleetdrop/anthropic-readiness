# Anthropic Readiness

**Development stopped, 2026-11-01.** Existing alternatives now invalidate the
reason to build a separate tool in this category. Start with
[llm-comply](https://github.com/Oaklight/llm-comply); see
[the research and decision](docs/reviews/2026-11-01-existing-tools.md).
The implementation below is retained as-is, with its limitations, rather than
presented as an actively progressing rewrite. No complete compatibility is claimed.

A local assessment tool for self-hosted model APIs claiming Anthropic Messages
compatibility. Evaluate the selected protocol scope, inspect concrete deviations
and export what is compatible, unsupported, inconclusive or untested. Endpoint
consumers and providers can compare later runs as implementations/models change.

## Current status

The TypeScript/Node implementation in next/ now has a runnable CLI for five migrated
scenarios: plain/streamed controlled text, streamed counting, forced tool selection
and a tool-result round trip. The complete scope reserves six request attempts.
Read [the CLI trial guide](docs/refactor/cli-trial.md) for preview, explicit live
admission, evidence and limits. Synthetic checks passed, and one owner-selected
real endpoint trial completed all five tasks; strict findings remain. This is
sampled evidence, not broad compatibility. The new Web UI, broader cases and
SDK/client checks remain unfinished.

The [delivery route](docs/refactor/README.md) records coherent product checkpoints;
[the coverage inventory](docs/refactor/coverage.md) makes remaining scope explicit.
The [current status](docs/CONTINUE.md) records actual delivery. The previous Python application,
its container instructions and historical outcomes are [reference only](README.python.md).
Existing installed records and private captures must not be overwritten.

## Develop locally

Use Node 24 LTS, then:

```sh
npm --prefix next ci
npm --prefix next run check
```

No Python, Docker, Compose or Dev Container setup is required. Local checks,
optional hooks and CI use the same Node entry point. See
[development](docs/development.md) and [contribution guidance](CONTRIBUTING.md).
Container delivery is deferred until the tool is useful and mature.

The target remains one shared CLI/Web engine, raw protocol inspection and separate
SDK/client results, clear Chinese/English evidence and portable reports. Preserve
[the accepted visual baseline](design.md); broader protocol, tool and error coverage
remain required by [project intent](intends.md). SDK/Claude Code assessments are
optional supplements, not prerequisites for using the protocol assessment.

Live endpoint calls require explicit operator opt-in and request/time bounds.
Do not commit private endpoint configuration, credentials or original service logs.
This tool is not an Anthropic certification or a claim of Claude Code support.

## License

[MIT](LICENSE). The retained Heroicons have a
[separate license](src/anthropic_readiness/resources/web/icons/LICENSE).
