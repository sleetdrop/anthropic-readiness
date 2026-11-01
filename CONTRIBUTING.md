# Contributing

Start with [AGENTS.md](AGENTS.md), [project intent](intends.md),
[current status](docs/CONTINUE.md) and [the rewrite](docs/refactor/README.md).
The active source is next/. The former Python contribution guide is retained as
[historical reference](CONTRIBUTING.python.md), not a second set of requirements.

## Work and verify

Use Node 24 LTS. From the repository root:

```sh
npm --prefix next ci
npm --prefix next run check
```

No Python or container setup is required. Run focused tests during implementation,
then the complete check once for delivery. It checks strict types and actually
executed tests, retaining failures and rejecting empty/skipped/todo success.
Describe the concrete fault or user-visible outcome; introduce a meaningful failing
control before fixing it. Keep protocol evidence independent of SDK/task results.
Use the [development guide](docs/development.md) for commands and result locations.

Respect assigned file ownership when collaborating across chats. Make scoped local
commits. Remote publishing and model calls require the owner's explicit permission.
Use synthetic fixtures; never upload real keys, private endpoints or original logs.
Recorded unknown/not_run outcomes are valid. Old manifests do not certify new code.

For interface work, follow [the accepted design](design.md); no new visual exploration
is needed to migrate accepted interactions. Test the behavior actually changed,
including delayed initialization when touching form startup. Add browser checks
when the new Web flow exists; do not invoke the Python browser fixture.

Keep the handoff short: behavior, tested scope/results and remaining gaps. Include
new protocol/client cases separately from assertions and tool self-tests. Changes
to a selected protocol snapshot need official references and valid/faulty controls.
The [issue forms](.github/ISSUE_TEMPLATE) and [PR template](.github/PULL_REQUEST_TEMPLATE.md)
request relevant evidence, not every historical environment or milestone gate.
