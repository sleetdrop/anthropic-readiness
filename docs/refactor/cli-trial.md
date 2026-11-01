# First TypeScript CLI trial

Use Node 24 LTS. No Python, Docker or Dev Container is needed. The CLI implements
five migrated endpoint scenarios, validated against disposable synthetic services;
real endpoint behavior is not established by those tests. The Web interface,
SDK/Claude Code workflows and wider scenario catalog remain unfinished.

## Preview without requests

From the repository root, replace the example URL and model with your own:

```sh
npm --prefix next start -- plan --endpoint https://api.example.com/v1 --model YOUR_MODEL
```

This resolves the Messages address and prints the selected scope and budgets. It
makes no request and does not read credential values. With no --profile flags,
all five scenarios reserve up to six request attempts. A smaller max-requests
allowance is rejected; it never silently reduces selected scope.

## Run and retain evidence

Choose a new output directory whose parent already exists:

```sh
npm --prefix next start -- run --endpoint https://api.example.com/v1 --model YOUR_MODEL \
  --allow-live --max-requests 6 --run-ms 300000 --attempt-ms 30000 \
  --out /tmp/readiness-trial-001
```

No authentication header is sent by default. For endpoints requiring a key already
present in your environment, add --auth-env ENV_NAME and --auth-mode api_key or
bearer. Values are never accepted as command-line keys or saved request headers.
Do not use real keys in source, public issues or shared shell transcripts.

For slower reasoning endpoints, explicitly raise --max-tokens, --attempt-ms,
--read-ms and --run-ms as appropriate. Defaults are 2048 output tokens, 30 seconds
per attempt/read, at most 5 seconds for connection, five minutes for the run and
2 MiB retained per response. --connect-ms and --max-bytes are also configurable.
The operator chooses finite bounds; the tool neither retries nor follows redirects.

Profiles can be repeated: anthropic-basic (three text cases),
anthropic-tools-smoke (forced tool call) and anthropic-tool-loop (two-request
result round trip). Model identity requires the requested name or explicit
--model-alias values; --structure-only records that identity was not checked.

## Read the result

- report.md: Chinese summary by default; --language en selects English. Protocol,
  task behavior, reported model and admitted request attempts are separate.
- result.json: typescript-run/1 structured result with selected/unexecuted cases,
  observations, source bytes/hashes, SSE events and explicitly derived messages.
- response-ID.json: raw capture plus request-body bytes/hashes, written before
  JSON/SSE validation. These survive a later parsing/reporting failure. Request
  authentication headers are not included. Base64 decodes to the captured bytes;
  sha256/requestSha256 bind retained response/request bodies, not provider identity.

Output directories cannot be overwritten. Files are private to the local owner.
Response bodies can contain sensitive model/business data; review before sharing.
Interrupted cases remain incomplete and all selected cases stay represented.
Exit codes: 0 selected checks passed, 1 observed failure, 2 invalid invocation,
3 incomplete/blocked, 4 internal failure with any captured evidence retained.

## Exact scope and gaps

The three text cases now use deterministic replies (HELLO, streamed HELLO and
exactly 1 2 3 4 5) rather than semantic greeting heuristics. They and the stricter
nonce-only tool-result case are case revision 2; forced tool selection remains
revision 1. The result round trip places its fresh token only in the actual tool
result. Extra tool calls cannot earn a successful token-only reply.

The new development rule snapshot is
`typescript-messages-2023-06-01-core/0.2.0-dev`, with API header 2023-06-01 and no
betas. It is not a claim of byte-for-byte equivalence with the former Python rule
bundle, nor a reader for old archives. Model behavior is not pinned by an API date.

The CLI detects selected message field/type/identity faults, SSE lifecycle/index/
framing problems, invalid tool JSON, missing task output and tool-result misuse.
Unknown extensions, service errors, policy limits and incomplete capture retain
conservative outcomes. Cumulative message_delta updates and intermediate null
stop reasons are allowed; malformed event envelopes remain faults.

Compressed response decoding and duplicate JSON-key detection are not implemented.
Streaming tool round trips, broader multi-turn/error scenarios, version matrices,
real SDK/client workflows, HTML/ZIP delivery and the new Web UI remain gaps.
SSE tool-fragment unit controls are not a streamed-tool endpoint scenario.
