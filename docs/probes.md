# Targeted endpoint probes

Use the saved response first. If a preset probe answers a specific open
question, confirm the target, request cap and time bound before execution.
The presets send Anthropic API version `2023-06-01` with no betas. They
generate their own requests and cannot replay the original incident exactly.

Choose a profile and preview it without sending requests:

```sh
npm --prefix next start -- plan --endpoint https://api.example.com/v1 \
  --model YOUR_MODEL --profile anthropic-tools-smoke
```

| Profile | Scope | Maximum requests |
| --- | --- | ---: |
| `anthropic-basic` | JSON and streamed text | 3 |
| `anthropic-tools-smoke` | Forced tool selection | 1 |
| `anthropic-tool-loop` | Non-streamed tool result round trip | 2 |

Run the selected probe only after explicit authorization. Choose a fresh
output directory whose parent already exists:

```sh
npm --prefix next start -- run --endpoint https://api.example.com/v1 \
  --model YOUR_MODEL --profile anthropic-tools-smoke --allow-live \
  --max-requests 1 --run-ms 30000 --attempt-ms 30000 --out /tmp/incident-probe
```

For authentication, set a local environment variable and pass its name with
`--auth-env ENV_NAME`. Choose `--auth-mode api_key` or `bearer` for the endpoint.
Use `--model-alias` for a known alias, or `--structure-only` when model identity
is outside the investigation.

The output contains the structured result, Markdown summary, and per-response
capture records. Read the selected and attempted cases, capture completeness,
and the separate task and protocol findings before drawing a conclusion.
