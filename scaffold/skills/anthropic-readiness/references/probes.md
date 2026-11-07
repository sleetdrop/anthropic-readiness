# Anthropic Messages probes

Use a saved capture first for incident diagnosis. For an endpoint assessment,
preview the core suite without sending requests. Use `SKILL_DIR` from the
[skill instructions](../SKILL.md):

```sh
node "$SKILL_DIR/scripts/src/cli/main.ts" plan --endpoint https://api.example.com/v1 \
  --model YOUR_MODEL --profile anthropic-core --api-version 2023-06-01
```

The plan lists every case, its revision, and its maximum request count. The
CLI defaults to `anthropic-core` and API version `2023-06-01`. Use
`--api-version 2026-10-21` to test the same endpoint under the newer header.
Run the versions separately and compare the result by case ID. The reported
version is the header the tool sent. The three migration probes specifically
test whether the endpoint applies documented 2026 request restrictions.
Profiles can be repeated on one command and overlapping cases run once.
[API versions](https://platform.claude.com/docs/en/api/versioning) ·
[2026 migration](https://platform.claude.com/docs/en/api/migration-2026-10-21)

## Core cases

| Profile | Cases | Max requests | Checks |
| --- | ---: | ---: | --- |
| `anthropic-core` | 22 | 27 | All seven core groups below |
| `anthropic-basic` | 3 | 3 | Plain JSON greeting, SSE greeting and SSE counting; message shape, usage and stream lifecycle |
| `anthropic-text` | 6 | 7 | Top-level system and multipart user text, genuine multi-turn history recall, matching custom stop sequence and token-limit termination in JSON and SSE |
| `anthropic-tools-smoke` | 1 | 1 | Named forced tool, requested argument |
| `anthropic-tool-loop` | 1 | 2 | Real tool ID round trip and consumption of a fresh result token |
| `anthropic-tools` | 5 | 8 | `none`, `any` with parallel disabled, streamed argument reconstruction and continuation, two parallel tool results, and an `is_error` result |
| `anthropic-count` | 2 | 2 | `POST /v1/messages/count_tokens` with text/system and with tool definitions; positive integer result |
| `anthropic-errors` | 4 | 4 | Missing generation limit, illegal message role, mismatched tool result ID, missing count messages; HTTP 400 and Anthropic error envelope |

The token count is an estimate, so it is checked for shape and positive value
for the supplied nonempty inputs. It is not compared to generation usage.
In the parallel case, a model that does not emit two distinct calls leaves the
round trip undetermined. A 2xx for a deliberately invalid request is a protocol
failure. A 401 or upstream error that prevents reaching the check is blocked.
The error and count probes have no inference task, so task status is `SKIP`.
[Create a Message](https://platform.claude.com/docs/en/api/messages/create) ·
[Streaming](https://platform.claude.com/docs/en/build-with-claude/streaming) ·
[Tool definitions](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools) ·
[Token counting](https://platform.claude.com/docs/en/api/messages/count_tokens) ·
[Errors](https://platform.claude.com/docs/en/api/errors)

## Explicitly selected capabilities

| Profile | Cases | Max requests | Checks and prerequisites |
| --- | ---: | ---: | --- |
| `anthropic-version-2026` | 3 | 3 | Rejects a sampling parameter, an assistant document and a nonempty citation in user text. Requires `--api-version 2026-10-21`. |
| `anthropic-prefill` | 1 | 1 | Assistant prefill continuation. Select for models that support prefilling. |
| `anthropic-structured` | 3 | 3 | JSON-schema output in JSON and SSE, plus a strict named tool. |
| `anthropic-thinking` | 2 | 2 | Adaptive thinking in JSON and SSE, including thinking blocks and the streamed signature. A valid response without thinking leaves the capability undetermined. |
| `anthropic-vision` | 1 | 1 | Read a self-contained red PNG from a base64 image block. |
| `anthropic-pdf` | 1 | 1 | Read one word from an inline one-page PDF. |
| `anthropic-citations` | 1 | 1 | Return a matching character-range citation into a known plain-text document. |
| `anthropic-cache` | 1 | 2 | Send the same isolated, approximately 5,200-word prefix twice; observe creation then read counters. No hit means cache behavior was not established. |

There are **35 presets** across these profiles. Model-dependent profiles should
be selected according to the endpoint's declared capabilities. A generic
rejection or an unobserved effect does not establish unsupported capability.
For an explicitly requested exploration of all listed capabilities under
`2023-06-01`, the core plus all non-migration profiles select 32 cases with a
maximum of 38 requests. The three migration cases require `2026-10-21`.
The adaptive probe requires a model that accepts `thinking.type=adaptive`.
Thinking signatures are checked for wire shape and sequence, not
cryptographically verified.
[Prefilling restrictions](https://platform.claude.com/docs/en/api/errors#prefilling-restrictions) ·
[Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) ·
[Thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) ·
[Vision](https://platform.claude.com/docs/en/build-with-claude/vision) ·
[PDF](https://platform.claude.com/docs/en/build-with-claude/pdf-support) ·
[Citations](https://platform.claude.com/docs/en/build-with-claude/citations) ·
[Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

## Run and interpret

After explicit authorization, use a fresh output directory whose parent exists:

```sh
node "$SKILL_DIR/scripts/src/cli/main.ts" run --endpoint https://api.example.com/v1 \
  --model YOUR_MODEL --profile anthropic-core --api-version 2023-06-01 \
  --allow-live --max-requests 27 --run-ms 600000 --attempt-ms 90000 \
  --out /tmp/incident-probe
```

Use the [connection guide](connection.md)
for API-key, Bearer, or unauthenticated access and custom gateway paths.
Select `--use-env` to read the five `AR_DIAG_` target variables.
Alternatively, supply the target through command-line arguments and select a
credential with `--auth-env ENV_NAME`. Use `--auth-mode api_key`, `bearer`
or `none`. Explicit arguments take precedence. The selected credential
variable must be available to the process running the probe.
Use `--model-alias` for a known alias, or `--structure-only` when model identity
is outside the investigation. A deadline or failed prerequisite can prevent a
follow-up. Inspect attempts started and case outcomes before interpreting coverage.

The output contains `result.json`, an HTML check record (`report.html`), and the
request and response bytes per exchange. Reports and JSON viewer labels default
to English. Use `--language zh` for Chinese. Report links open offline syntax-highlighted
JSON views with a link to open the original attachment. For a human-facing assessment across
one or more runs, use the [Skill report guide](reporting.md)
to write a synthesis above those records. Preset probes generate diagnostic requests and
cannot reproduce an original incident byte for byte. Share evidence only after
reviewing it for sensitive content.

### Coverage boundaries

These presets exercise the Messages create and count routes without beta
headers. Hosted tools such as web search, web fetch, and code execution,
the Files and Batches APIs, beta modes, legacy manual thinking, remote
image/document URLs, and actual SDK or Claude Code runs have no presets here.
Rate limits, authentication failures, overload, refusal and context exhaustion
are incident conditions to investigate when observed. The suite does not
induce them on real endpoints.
