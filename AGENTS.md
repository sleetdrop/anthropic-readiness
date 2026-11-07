# Repository guide

Read [intends.md](intends.md) and [current status](docs/CONTINUE.md). Follow
the [Skill](scaffold/skills/anthropic-readiness/SKILL.md) for assessments and
incident work.
The standalone assessment application is historical. Its records are indexed
in [current status](docs/CONTINUE.md).

- Use Node 24 LTS. Install locked tools with `npm --prefix next ci`.
  Run `npm run check` for strict types and executed tests.
- Keep protocol validators pure and I/O in adapters. Reuse the synthetic
  normal and faulty captures. Reproduce a behavior defect with a meaningful
  failing control before changing it. Preserve existing rules and test evidence.
- Distinguish raw protocol, task behavior and client outcomes. Missing,
  skipped or unrun checks do not establish a passing result.
- Keep credentials, private targets and original service logs out of source
  and shared artifacts. Live endpoint calls require explicit opt-in and
  request/time bounds. Use synthetic services for repository checks.
- Write source, comments, machine fields and commits in English. Respond to
  Skill users in their language.
- Keep `docs/CONTINUE.md` current and record material results in
  `docs/harness/progress.md`. Put large local logs in ignored `artifacts/`.
  Make scoped local commits. Obtain explicit authorization for remote writes.
