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

## Pull request workflow

Use a short-lived topic branch based on `main` for code, documentation, and
release preparation. Make scoped commits on that branch and open a pull
request targeting `main`; do not commit or push directly to `main` by default.

Run `npm run check` before opening the PR. Report the checks that actually ran
and any remaining gaps. Keep protocol findings, task outcomes, and actual
client behavior separate. Review the changes and wait for `ci-required` to
pass before merging.

Agents need explicit authorization for remote writes, including branch
pushes and opening or merging PRs. A direct push to `main` is an exception
that requires the owner's explicit authorization for that change. Release
work is not an automatic exception; see [publishing](docs/releasing.md).

## Issues and protocol updates

For tool defects, include a minimal reproduction, expected and actual results,
and the relevant versions. Use synthetic inputs. For protocol-rule changes,
link the official contract and include normal and faulty controls.

Never put credentials, private endpoint URLs, unredacted captures, or private
chats in issues or pull requests. Live endpoint tests are optional and require
explicit authorization with request and time limits. Repository checks use
synthetic services.
