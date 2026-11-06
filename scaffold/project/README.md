# Anthropic Readiness test project

Use this directory for one Anthropic Messages-compatible endpoint.

1. Open `target.json` locally and fill in `endpoint`, `model`, and `authMode`.
   Set `apiVersion` to the header you intend to test. Use `api_key`, `bearer`,
   or `none` for `authMode`.
2. For `api_key` or `bearer`, put the credential on one line in `token.txt`.
   It is a local plaintext file. The runner reads it at execution time.
3. Open this project in an agent that can load the `anthropic-readiness` Skill
   and run Node 24 LTS. Give it the symptom and any capture under `evidence/`.
   For a live run, explicitly authorize the target, maximum request count,
   and total time limit.

For example:

> Use Anthropic Readiness to diagnose why this Anthropic Messages stream stalls.
> Check the saved evidence first. If a live probe is needed, I authorize this
> configured target for up to 3 requests within 90 seconds.

The agent previews probes offline and writes each live run to a new directory
under `runs/`. The project ignores the target, credential, evidence, and run
records in Git. Review evidence before sharing it.
