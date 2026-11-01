# Anthropic Readiness

A focused local tool for diagnosing Anthropic Messages incompatibilities across
inference servers, protocol translators and gateways. The intended workflow is
run checks, inspect concrete evidence, share a diagnosis and verify a repair.

## Current status

The active implementation is a TypeScript/Node rewrite in next/. It currently has
shared contracts, a five-case/six-request migration inventory and core/harness
controls. It does not yet execute endpoint requests or provide the new Web flow.
A catalog or passing tool self-test is not implemented endpoint coverage.

The [rewrite entry point](docs/refactor/README.md) records the delivery sequence;
[current status](docs/CONTINUE.md) stays concise. The previous Python application,
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
[the accepted visual baseline](design.md); broader protocol, tool, error and actual
client coverage remain required by [project intent](intends.md).

Live endpoint calls require explicit operator opt-in and request/time bounds.
Do not commit private endpoint configuration, credentials or original service logs.
This tool is not an Anthropic certification or a claim of Claude Code support.

## License

[MIT](LICENSE). The retained Heroicons have a
[separate license](src/anthropic_readiness/resources/web/icons/LICENSE).
