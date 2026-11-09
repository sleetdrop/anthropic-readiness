# Architecture

Anthropic Readiness tests the Anthropic Messages API exposed by a combination
of model, inference software, and API conversion software. The external API
is the target even when the inference server uses another protocol.

The npm command creates a workbench for one target. The user's agent selects
checks, runs them within agreed limits, reviews the evidence, and produces an
assessment. Focused diagnosis uses saved captures and the smallest useful
comparison. Record known stack components and versions; leave unknowns explicit.

## Repository layout

```text
bin/                     npm command
templates/               files copied into each workbench
   skills/               bundled Skill and its runtime
scripts/                 repository checks
tests/                   tests and synthetic protocol fixtures
docs/                    development and release guides
   history/              earlier reviews and verification records
```

`package.json` at the repository root is the published npm package. Its file
allowlist includes only `bin/` and `templates/`, plus npm's package metadata,
README, and license. Tests and development tools are not runtime dependencies.

## Runtime

The canonical runtime lives under
`templates/skills/anthropic-readiness/scripts/`. Workbenches receive that
complete directory, so they can run without the source repository or an npm
install. The initializer is JavaScript; the copied TypeScript helpers run
with native type stripping outside `node_modules`. Runtime requirements are
Node.js 22.18+ on 22.x or 24.2+ on newer release lines, including
`import.meta.main` support. Checks cover recent Node 22, 24, and 26 releases;
the initializer also accepts future stable major versions. Development and
publication use the Node 24 version pinned in `.node-version`.

Within the Skill's `scripts/src/`:

- `catalog.ts` defines cases, profiles, and request reservations.
- `protocol/` contains pure JSON, SSE, count, and error validators.
- `runner/` handles bounded HTTP capture, probe execution, and task checks.
- `cli/` reads configuration, inspects captures, and writes run artifacts.

The assessment renderer combines retained runs and agent-written findings into
HTML. It resolves evidence references against actual exchanges. The agent
owns the interpretation; deterministic helpers own capture and rule checks.

## Evidence and scope

Preserve original request and response bytes and their hashes. Derived messages
must not replace the original evidence. Partial captures cannot establish
missing terminal events.

Report protocol, task, and actual client outcomes separately. A successful task
can contain a protocol deviation. A response model label does not prove backend
identity, and a single endpoint observation cannot identify which component
introduced a difference. Unrun checks and unobserved effects do not earn a pass.
