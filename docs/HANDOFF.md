# Stage A handoff

Use the source/lock/contract fingerprints and check artifacts listed in
[harness/handoff.json](harness/handoff.json). That manifest distinguishes local
checks, image execution, independent review, remote CI and real endpoint outcomes.
It is not an endpoint compatibility certificate. The owner has authorized local
commits and synthetic checks; remote writes/publication and actual API tests need
explicit authorization for those operations.

## Reproduce offline

Open the checked-in Dev Container, prepare once with `uv sync --locked`, then:

```sh
UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite fast
UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite full
uv run --frozen anthropic-readiness contracts show anthropic-messages-2023-06-01-core --revision 1.0.0
```

Use new, absent output directories for each command. Legal synthetic replay exits 0:

```sh
UV_OFFLINE=1 uv run --frozen anthropic-readiness replay --target examples/target.yaml \
  --capture tests/fixtures/captures/valid/evidence/ANT-TEXT-SSE-001/fixture-attempt/response.json \
  --case ANT-TEXT-SSE-001 --out artifacts/handoff-valid
```

The duplicate-start control exits 1 and exposes `STR-START` FAIL:

```sh
UV_OFFLINE=1 uv run --frozen anthropic-readiness replay --target examples/target.yaml \
  --capture tests/fixtures/captures/duplicate-start/evidence/ANT-TEXT-SSE-001/fixture-attempt/response.json \
  --case ANT-TEXT-SSE-001 --out artifacts/handoff-invalid
```

Each output includes result.json, report.html, report.md, report-manifest.json and
verified sanitized evidence. Replay labels synthetic/user-capture scope and does
not prove the full live profile. To share with an Agent, include report.md for an
initial reading; include result.json and the referenced evidence for independent
verification. The reader guide, glossary and source references are embedded.

Report presentation 1.2 includes a compact run summary, Chinese conclusion,
task/protocol case table and linked grouped findings. Partial expected/observed
field comparisons distinguish format differences from identity configuration; stop
fields and model names are supplemented
only from verified evidence. Technical IDs, full assertions and provenance remain
in the appendix. Re-rendering keeps the original result.json bytes and verdicts;
it does not rescore or make new API calls. See the
[readability follow-up ledger](harness/report-readability-ledger.md) for its separate checks.

The mixed synthetic sample used for visual QA deliberately omits evidence. It
supports layout/interpretation checks only. See [visual review](reviews/2026-10-16-report-visual-review.md)
and [requirement coverage](reviews/2026-10-16-stage-a-coverage.md).

## Containers and connectivity

See [container usage](container-usage.md) for build, ordinary-user/read-only
execution, output ownership, bounded temporary storage and two architecture jobs.
Images are local artifacts. amd64 emulation on an arm64 host is explicitly labeled;
it does not substitute for an observed native amd64 CI run. Docker Desktop's host
alias was tested against a generic temporary loopback server, not the real daemon.
No daemon address, firewall, credentials or configuration was changed.

Remote GitHub checks/branch protection and Docker Hub publishing remain unrun.
When the owner authorizes repository setup, connect the workflows and require
`ci-required` after its first successful run. Configure registry publishing and
license selection separately with the owner; no registry credentials are needed
for the current workflows.

## Real endpoint acceptance (separate authorization)

Keep a private target outside Git/build contexts. Its URL must be reachable from
the selected environment, with an explicit finite request/time budget and exact
API/beta/bundle selection. Run validate and dry-run before a live call. After the
operator grants live authorization, use both `anthropic-basic` and
`anthropic-tools-smoke` for four unique case requests; never copy private target
configuration, original service logs or credentials into this repository.

Only the observed model, contract, transport path and selected cases are covered.
Version header acceptance does not prove version-selection semantics. No result
here establishes tool loops, thinking/parallel behavior, beta support or Claude Code
readiness. B adds tool loops/matrices, C real fixed-client workflows, and D the
protocol-update Agent command and reviewed maintenance/publishing path. Stop at A
unless the owner authorizes the next stage.
