# Connect to an endpoint

For a live probe, establish the endpoint, model, API version, authentication
mode, request cap, and time bound. Use the supplied model name exactly.
The same HTTP client supports local and remote HTTP or HTTPS endpoints.

## Use a test project

The project contains `target.json`, `token.txt`, `evidence/` and `runs/`.
Fill in `endpoint`, `model`, `apiVersion`, and `authMode` in `target.json`.
Use `api_key`, `bearer`, or `none` for the mode. For authenticated runs,
put the credential on one line in the local `token.txt` file.

A root URL or a URL ending in `/v1` selects `/v1/messages`. If a gateway uses a different prefix, supply
its full Messages URL, such as `https://gateway.example.com/anthropic/v1/messages`.
The count probes append `/count_tokens` to the Messages path. The URL must
not contain credentials, a query string, or a fragment.

Use `SKILL_DIR` from the [skill instructions](../SKILL.md). From the target
project, preview the smallest relevant profile with the agreed limits:

```sh
node "$SKILL_DIR/scripts/src/cli/main.ts" plan --target-dir . \
  --profile anthropic-basic --max-requests 3 --run-ms 90000
```

Preview reads the target without reading credentials or making requests.
After explicit authorization for that target and those limits, use a fresh
output directory under `runs/`:

```sh
node "$SKILL_DIR/scripts/src/cli/main.ts" run --target-dir . \
  --profile anthropic-basic --max-requests 3 --run-ms 90000 \
  --allow-live --out runs/first-probe
```

The project mode requires both limits for execution and reads the token
directly only for `api_key` or `bearer`. Ask the user to fix missing files
locally. Keep the token file out of the conversation. Select one target
source per invocation. Project mode takes all connection settings from the
directory.

## Use environment variables or explicit arguments

Pass `--endpoint URL` and `--model NAME` to configure the target explicitly,
or add `--use-env` to read the following variables. Target selection is
independent of the agent host's provider settings.

| Variable | Purpose | Values |
| --- | --- | --- |
| `AR_DIAG_ENDPOINT_URL` | Endpoint under test | HTTP or HTTPS Messages URL or supported base URL |
| `AR_DIAG_MODEL` | Model under test | Exact model name accepted by the endpoint |
| `AR_DIAG_AUTH_MODE` | Authentication mode | `api_key`, `bearer`, `none` |
| `AR_DIAG_AUTH_TOKEN` | Credential for the target | Supplied locally by the user or secret manager |
| `AR_DIAG_API_VERSION` | API version sent | `2023-06-01` or `2026-10-21` |

A command-line `--endpoint`, `--model`, `--auth-mode` or `--api-version`
overrides the corresponding environment value. The API version defaults to
`2023-06-01` and the authentication mode to `api_key` when not supplied.
Endpoint and model are required.

| Selected mode | Request header | Credential |
| --- | --- | --- |
| `api_key` | `x-api-key: <value>` | Required for an environment-configured run |
| `bearer` | `Authorization: Bearer <value>` | Required for an environment-configured run |
| `none` | Neither authentication header | Ignored, including an explicit `--auth-env` |

With `--use-env`, the selected credential source is `AR_DIAG_AUTH_TOKEN`.
An explicit `--auth-env OTHER_VARIABLE` selects that variable instead.
This lets the user reuse an existing credential without copying its value.
A named empty or unavailable credential stops an authenticated run before
creating output or making a request. Planning does not need a credential.

In command-line-only mode, `--auth-env VARIABLE_NAME` explicitly selects the
credential. Omitting it sends no authentication header, preserving the direct
CLI workflow. Use `--auth-mode none` to explicitly select unauthenticated access.

Ask for the credential variable name and check availability without printing
values or dumping the environment. The variables must be available to the
agent process that starts the probe. The helper does not load `.env` files.

## Security boundary

The token file and environment values are plaintext. Keep test projects local
and use their Git ignore rules for target details, tokens, evidence, and run
records. Code with sufficient local permissions can read credentials from
these sources.

Use a credential restricted to the target service and the required access,
with a short lifetime or easy revocation when supported. Use HTTPS for remote
authenticated endpoints. The probe does not follow redirects, so it does not
forward the credential to a redirect target. If the host provides vault-based
header injection restricted to an exact hostname, prefer that mechanism when
available.

Request authorization headers are not included in captured request records.
Response headers and bodies remain original evidence and may contain
server-returned sensitive content. Review them before sharing.


See [Anthropic's Skill credential guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise),
[host-side header injection](https://platform.claude.com/docs/en/managed-agents/secure-deployment),
[Codex environment filtering](https://learn.chatgpt.com/docs/config-file/config-advanced),
and [process-scoped automation credentials](https://learn.chatgpt.com/docs/non-interactive-mode).
