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
| Anthropic API key | `--auth-env DIAG_API_TOKEN --auth-mode api_key` | `x-api-key: <value>` |
| Bearer token | `--auth-env DIAG_API_TOKEN --auth-mode bearer` | `Authorization: Bearer <value>` |
| No authentication | Omit `--auth-env` | Neither authentication header |

The default mode is `api_key`. An explicitly named empty or unavailable
variable stops the run before the output directory is created or a request
is sent. The tool reads the variable for each invocation. It does not obtain,
refresh, or persist credentials. Arbitrary authentication headers, simultaneous
key-plus-token authentication, OAuth login, and mTLS configuration have no
CLI options.

In a Bash shell, enter a token without displaying it or placing its value in
the command history:

```bash
printf 'API token: '
IFS= read -r -s DIAG_API_TOKEN
printf '\n'
export DIAG_API_TOKEN
```

Preview a three-request text probe. Planning needs no credential:

```sh
node next/src/cli/main.ts plan \
  --endpoint https://gateway.example.com/v1 --model YOUR_MODEL \
  --profile anthropic-basic --max-requests 3 --run-ms 90000
```

With the user's live authorization, run the same selection. The parent of
the new output directory must already exist:

```sh
node next/src/cli/main.ts run \
  --endpoint https://gateway.example.com/v1 --model YOUR_MODEL \
  --profile anthropic-basic --max-requests 3 --run-ms 90000 \
  --auth-env DIAG_API_TOKEN --auth-mode api_key \
  --allow-live --out /tmp/diagnosis-run
```

For a Bearer endpoint, change `--auth-mode api_key` to `--auth-mode bearer`.
For an unauthenticated endpoint, omit both authentication arguments.
Remove the temporary variable from the shell when finished:

```sh
unset DIAG_API_TOKEN
```

Request authorization headers are not included in captured request records.
Response headers and bodies remain original evidence and may contain
server-returned sensitive content. Review them before sharing.
