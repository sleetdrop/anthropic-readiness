# Contributing

Humans and coding Agents use the same contracts and evidence. Start with
[AGENTS.md](AGENTS.md), [current milestone](docs/CONTINUE.md),
[architecture](docs/architecture.md) and the approved scope linked there.
Read existing code before proposing a change. Discuss scope changes in an issue.

## Work and validate

1. Open the Dev Container and prepare with `uv sync --locked`.
2. Reproduce behavioral defects with a meaningful failing synthetic test.
3. Keep domain/framing/validators pure, I/O in adapters and typing strict.
4. Run `UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite fast`;
   run `--suite full` before review. Container changes also require the documented
   two-architecture image checks. A missing check is blocked or not_run.
5. Update packaged schemas, versioned contracts and evidence mappings when their
   semantics change. Never weaken a golden expectation merely to pass a gate.
6. Describe behavior, validation, limits and remaining checks in the PR template.

Keep source, comments, machine fields and commits in English. User-facing reports
default to Simplified Chinese. Optional pre-commit hooks call the same fast graph;
CI is the authority for remote job outcomes. See [development](docs/development.md).

## Safe, useful issues

Use the bug, compatibility, feature or protocol-update forms. Include public case,
assertion and bundle IDs, versions, expected/observed behavior and sanitized minimal
synthetic reproduction. `unknown` and `not_run` are valid answers. Do not attach
credentials, private endpoint addresses, original provider logs or private chat
history. A compatibility report is bounded by its tested model, headers and date.

Agents must read the repository guide, preserve failed evidence and leave an
honest handoff. Do not report tools or tests as passing unless they actually ran.
Remote publication, credentials and account setup require owner authorization.
Protocol updates currently use the issue form and reviewed immutable bundles;
the runnable maintenance command is deferred to Stage D.
