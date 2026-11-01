# Current architecture

The owner-approved direction is a local-first TypeScript application on one Node
LTS runtime. [The rewrite entry point](refactor/README.md) owns the implementation
sequence and module boundaries; [project intent](../intends.md) owns product scope.

One execution engine supplies CLI and local Web adapters. Pure protocol validation
receives captured data and produces located observations. Raw protocol, task and
SDK/client results remain distinct. The accepted investigation/report presentation
is governed by [design.md](../design.md). No container dependency or multi-provider
framework is part of the initial implementation.

The current next/ package contains shared contracts, selection controls and a small
check harness. It is not yet a complete runner or Web product. The former Python
architecture is retained as [reference](architecture-python-legacy.md); its worker,
SQLite, export and compatibility-reader layers are not requirements to port.
