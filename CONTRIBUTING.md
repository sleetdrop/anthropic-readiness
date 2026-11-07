# Contributing

Use Node 24 LTS. Install locked tools with `npm ci`, then run `npm run check`.
See [development](docs/development.md) for focused checks and the local
package workflow.

## Changes

Keep changes scoped to one problem. Explain the expected behavior and how you
verified it. For a behavior defect, add a synthetic failing control before
changing the implementation. Preserve passing controls and original fixture
bytes.

Protocol validators belong in the bundled Skill and should remain pure.
Keep network and file access in adapters. Do not duplicate the runtime in the
repository or add a dependency on the source checkout to generated workbenches.
See [architecture](docs/architecture.md) for the layout.

Run `npm run check` before submitting a pull request. Report the checks that
actually ran and any remaining gaps. Keep protocol findings, task outcomes,
and actual client behavior separate.

## Issues and protocol updates

For tool defects, include a minimal reproduction, expected and actual results,
and the relevant versions. Use synthetic inputs. For protocol-rule changes,
link the official contract and include normal and faulty controls.

Never put credentials, private endpoint URLs, unredacted captures, or private
chats in issues or pull requests. Live endpoint tests are optional and require
explicit authorization with request and time limits. Repository checks use
synthetic services.
