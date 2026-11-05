# Connect to an endpoint

For a live probe, establish the endpoint, model, API version, authentication
mode, request cap, and time bound. Use the supplied model name exactly.
The same HTTP client supports local and remote HTTP or HTTPS endpoints.

## Endpoint

Pass `--endpoint URL` and `--model NAME`. A root URL or a URL ending in
`/v1` selects `/v1/messages`. If a gateway uses a different prefix, supply
its full Messages URL, such as `https://gateway.example.com/anthropic/v1/messages`.
The count probes append `/count_tokens` to the Messages path. The URL must
not contain credentials, a query string, or a fragment.

## Select the target configuration

Add `--use-env` to explicitly read this group. Without that option, target
settings come from the command line. Neither mode reads the agent host's own
provider settings.

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

## Supply the values

Ask for the endpoint, model, mode and credential variable name, rather than
the secret value. The variables must be available to the process that starts
the probe. A `.env` file is not loaded automatically. If the agent cannot
access that process environment, give the user the bounded command to run
in a shell that has access.

For a one-off Bash run, let the user enter the token in their own terminal.
The subshell limits the variables' lifetime to this command group.
The output directory must be new and its parent must already exist.

```bash
(
  set +x
  export AR_DIAG_ENDPOINT_URL='https://gateway.example.com/v1'
  export AR_DIAG_MODEL='YOUR_MODEL'
  export AR_DIAG_AUTH_MODE='api_key'
  export AR_DIAG_API_VERSION='2023-06-01'

  printf 'Endpoint API token: '
  IFS= read -r -s AR_DIAG_AUTH_TOKEN
  printf '\n'
  export AR_DIAG_AUTH_TOKEN

  node next/src/cli/main.ts plan --use-env \
    --profile anthropic-basic --max-requests 3 --run-ms 90000

  node next/src/cli/main.ts run --use-env \
    --profile anthropic-basic --max-requests 3 --run-ms 90000 \
    --allow-live --out /tmp/diagnosis-run
)
```

For a Bearer endpoint, set `AR_DIAG_AUTH_MODE=bearer`.
For an unauthenticated endpoint, set `AR_DIAG_AUTH_MODE=none` and omit the
token prompt. In an agent session, provide the selected target and authorize
the request/time bounds. Confirm variable availability without printing
values or dumping the environment.

For repeated use, store the credential in an OS credential store or the
organization's secret manager and supply it to the probe process when needed.
The Skill does not implement a vault, OS keychain integration, OAuth login,
or token refresh. Arbitrary headers, simultaneous key-plus-token authentication
and mTLS have no CLI options. In CI, inject a dedicated test credential only
into the authorized live-probe step. Normal repository checks need no secrets.

## Security boundary

An environment variable is plaintext in the process environment. Code running
with sufficient local permissions, including an agent's shell tools, may read
it. A namespace prevents accidental naming overlap but does not provide access
control. A subshell reduces exposure time and inherited scope. It does not
isolate a secret from other authorized code running in that environment.

Use a credential restricted to the target service and the required access,
with a short lifetime or easy revocation when supported. Use HTTPS for remote
authenticated endpoints. The probe does not follow redirects, so it does not
forward the credential to a redirect target. If the host provides vault-based
header injection restricted to an exact hostname, prefer that mechanism when
available. The current local helper consumes a real environment value.

Request authorization headers are not included in captured request records.
Response headers and bodies remain original evidence and may contain
server-returned sensitive content. Review them before sharing.


See [Anthropic's Skill credential guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise),
[host-side header injection](https://platform.claude.com/docs/en/managed-agents/secure-deployment),
[Codex environment filtering](https://learn.chatgpt.com/docs/config-file/config-advanced),
and [process-scoped automation credentials](https://learn.chatgpt.com/docs/non-interactive-mode).
