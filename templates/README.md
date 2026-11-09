# Anthropic Readiness workbench

Use this directory to assess one Anthropic Messages endpoint exposed by your
model, inference software, and API conversion software.

1. Open `target.json` locally and fill in `endpoint`, `model`, and `authMode`.
   Set `apiVersion` to the header you intend to test. Use `api_key`, `bearer`,
   or `none` for `authMode`.
2. For `api_key` or `bearer`, put the credential on one line in `token.txt`.
   It is a local plaintext file. The runner reads it at execution time.
3. Open this workbench in an agent that can read files and run Node.js
   22.18+ (22.x) or 24.2+. Prefer the latest patch of a maintained LTS
   release; compatibility checks cover Node 22, 24, and 26.
   Its [AGENTS.md](AGENTS.md) points to the bundled `anthropic-readiness`
   Skill. If instructions are not loaded automatically, ask the agent to
   read `AGENTS.md` first. Ask for a protocol assessment and provide known
   inference and conversion software versions. For an individual failure,
   give it the symptom and any capture under `evidence/`.
   For a live run, explicitly authorize the target, maximum request count,
   and total time limit.

For example:

> Use Anthropic Readiness to assess this endpoint's Anthropic Messages
> implementation. Preview the full core suite, then run it with at most
> 27 requests within 10 minutes. Report protocol differences, task outcomes,
> supporting evidence, and untested scope.

The core suite has 22 cases and reserves up to 27 requests. Additional
capability profiles require a suitable API version and their own request
budget. Tell the agent which capabilities to include. A task may pass while
protocol checks fail; both results belong in the assessment.

The agent previews probes offline and writes each live run to a new directory
under `runs/`. The project ignores the target, credential, evidence, and run
records in Git. Review evidence before sharing it.
