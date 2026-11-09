# Anthropic Readiness workbench

This directory assesses the Anthropic Messages API exposed by one configured
combination of model, inference software, and API conversion software.
Use Node.js 22.18+ (22.x) or 24.2+ and the bundled helpers from this directory.
Prefer the latest patch of a maintained LTS release; checks cover 22, 24, and 26.

Read the [Anthropic Readiness Skill]({{SKILL_PATH}}/SKILL.md) before an
assessment or diagnosis, even if your agent does not discover skills
automatically. Follow its linked probe and reporting guides as needed.

- `target.json` contains the user's endpoint, model, API version, and auth
  mode. Preserve these settings unless the user requests a change.
- `token.txt` is a local credential file. Let the runner read it directly;
  keep its value out of conversations and reports.
- `evidence/` holds saved captures. Preserve original bytes and distinguish
  complete captures from partial ones.
- `runs/` holds outputs. Use a new directory for each run and retain the
  evidence needed for the assessment.

Preview the selected scope without networking. Before a live run, establish
authorization for the configured target, a request cap, and a time bound.
Use existing authorization when it already covers the planned run. Loading
this workbench does not authorize requests by itself.

Keep protocol findings, task behavior, and actual client outcomes separate.
Report unknown component versions and incomplete checks explicitly. Respond
in the user's language and use the Skill's renderer for formal reports.
