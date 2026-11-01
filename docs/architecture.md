# Current architecture

The owner-approved direction is a local-first TypeScript application on one Node
LTS runtime. [The rewrite entry point](refactor/README.md) owns the implementation
sequence and module boundaries; [project intent](../intends.md) owns product scope.

One execution engine supplies CLI and local Web adapters. Pure protocol validation
receives captured data and produces located observations. Raw protocol, task and
SDK/client results remain distinct. Assess selected protocol claims across
self-hosted APIs; optional client tests do not define the protocol verdict.
The accepted investigation/report presentation
is governed by [design.md](../design.md). No container dependency or multi-provider
framework is part of the initial implementation.

The next/ package now runs the five migrated scenarios through shared raw HTTP,
message/SSE validators and a CLI that writes evidence before parsing and final
JSON/Markdown reports. See [the trial guide](refactor/cli-trial.md) for scope/gaps.
It is not yet the new Web product or a real SDK/client test. The former Python
architecture is retained as [reference](architecture-python-legacy.md); its worker,
SQLite, export and compatibility-reader layers are not requirements to port.
