# Repository guide

Read [architecture](docs/architecture.md) and [current status](docs/CONTINUE.md).
Follow the [Skill](templates/skills/anthropic-readiness/SKILL.md) for protocol
assessments and incident work.

- Use Node 24 LTS. Install locked tools with `npm ci`. Run `npm run check`
  for strict types and executed tests.
- Keep protocol validators pure and I/O in adapters. Reuse synthetic normal
  and faulty captures. Reproduce behavior defects with a meaningful failing
  control before changing them. Preserve existing rules and test evidence.
- Distinguish protocol, task behavior, and client outcomes. Missing, skipped,
  or unrun checks do not establish a pass.
- Keep credentials, private targets, and original service logs out of source
  and shared artifacts. Live endpoint calls require explicit opt-in and
  request/time bounds. Use synthetic services for repository checks.
- Write source, comments, machine fields, and commits in English. Respond to
  Skill users in their language.
- Keep `docs/CONTINUE.md` current. Record material verification results in
  `docs/history/verification.md`. Put large local logs in ignored `artifacts/`.
  Make scoped local commits. Remote writes require explicit authorization.
