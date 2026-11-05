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

## Authentication

Ask the user for the credential's environment variable name and the expected
header, rather than the secret value. The variable must be available to the
process that starts the probe. A `.env` file is not loaded automatically.
If the agent cannot read the variable in its environment, give the user the
bounded command to run in a shell that has access to it.

| Endpoint requirement | Arguments | Header sent |
| --- | --- | --- |
| Anthropic API key | `--auth-env INCIDENT_DIAGNOSIS_ENDPOINT_TOKEN --auth-mode api_key` | `x-api-key: <value>` |
| Bearer token | `--auth-env INCIDENT_DIAGNOSIS_ENDPOINT_TOKEN --auth-mode bearer` | `Authorization: Bearer <value>` |
| No authentication | Omit `--auth-env` | Neither authentication header |

`INCIDENT_DIAGNOSIS_ENDPOINT_TOKEN` is the recommended name. The full words
identify its purpose as the credential for an endpoint being diagnosed.
Keep it separate from credentials used by the agent host itself.
`--auth-env` accepts another explicitly chosen name, including separate names
for separate targets. The helper reads no credential variable unless the user
selects it with `--auth-env`. It does not reuse an agent host's own API key.

The default mode is `api_key`. An explicitly named empty or unavailable
variable stops the run before the output directory is created or a request
is sent. The tool reads the variable for each invocation. It does not obtain,
refresh, or persist credentials. Arbitrary authentication headers, simultaneous
key-plus-token authentication, OAuth login, and mTLS configuration have no
CLI options.

Preview a three-request text probe. Planning needs no credential:

```sh
node next/src/cli/main.ts plan \
  --endpoint https://gateway.example.com/v1 --model YOUR_MODEL \
  --profile anthropic-basic --max-requests 3 --run-ms 90000
```

For a one-off Bash run, let the user enter the secret in their own terminal.
The subshell limits the variable's lifetime to this command group. The parent
of the new output directory must already exist.

```bash
(
  set +x
  printf 'Endpoint API token: '
  IFS= read -r -s INCIDENT_DIAGNOSIS_ENDPOINT_TOKEN
  printf '\n'
  export INCIDENT_DIAGNOSIS_ENDPOINT_TOKEN

  node next/src/cli/main.ts run \
    --endpoint https://gateway.example.com/v1 --model YOUR_MODEL \
    --profile anthropic-basic --max-requests 3 --run-ms 90000 \
    --auth-env INCIDENT_DIAGNOSIS_ENDPOINT_TOKEN --auth-mode api_key \
    --allow-live --out /tmp/diagnosis-run
)
```

For a Bearer endpoint, change `--auth-mode api_key` to `--auth-mode bearer`.
For an unauthenticated endpoint, omit the token prompt and authentication
arguments. In an agent session, provide the endpoint, mode and chosen variable
name. Confirm availability without printing the value or dumping the environment.

For repeated use, store the credential in an OS credential store or the
organization's secret manager. Have that system supply the chosen variable to
the probe process when needed. The Skill defines the variable interface and
does not implement a vault, OS keychain integration, or token refresh.
In CI, inject only a dedicated test credential into the authorized live-probe
step. The repository's normal checks need no endpoint secrets.

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
