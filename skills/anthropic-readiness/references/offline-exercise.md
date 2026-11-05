# Offline incident exercise

Give the agent this request and the failing capture, without telling it which
rule to expect:

> The stream ends, but the client rejects it. Inspect this complete synthetic
> response body and identify the smallest protocol deviation and how to verify it.
> Do not call any endpoint.

Copy `tests/fixtures/contracts/core-1.0.0/stream-duplicate-start.sse` to a neutral
temporary name such as `response.sse` before presenting it to the agent. The
adjacent `stream-valid.sse` is a comparison, not proof
that any client was executed. A successful investigation should cite the
specific event in the original capture, distinguish that observation from the
user's client symptom, and identify the one-event difference. Repeat using
`stream-invalid-tail.sse` labeled partial: absence after truncation must remain
inconclusive. Run from the repository root with Node 24.
