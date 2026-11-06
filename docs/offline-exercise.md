# Offline incident exercise

Install the Skill from a fixed commit in a separate Codex project using the
[installation instructions](../README.md#install-in-a-codex-project). Open a
fresh chat in the consumer project. Keep the source checkout, fixture names,
and expected findings out of the chat.

Copy these synthetic captures from
[`tests/fixtures/contracts/core-1.0.0/`](../tests/fixtures/contracts/core-1.0.0/)
to neutral filenames in the consumer project:

| Source fixture | Example name | Capture completeness | Expected result |
| --- | --- | --- | --- |
| `stream-duplicate-start.sse` | `response-a.sse` | Complete | `FAIL` with duplicate `message_start` at zero-based event index 1 |
| `stream-valid.sse` | `response-b.sse` | Complete | `PASS` for the inspected rules |
| `stream-invalid-tail.sse` | `response-c.sse` | Partial | `INDETERMINATE`, with the terminal event unverified |

Explicitly select `anthropic-readiness` and give the agent the failing capture
with this request:

> The stream ends, but the client rejects it. Inspect this complete synthetic
> response body and identify the smallest protocol deviation and how to verify it.
> Do not call any endpoint.

Supply the normal capture as a comparison and the partial capture with its
known completeness. A successful investigation cites the event in the original
capture, identifies the one-event difference, and distinguishes it from the
reported client symptom. Treat client execution as unverified.

To check implicit selection, open another fresh chat in the consumer project
with the same model. Give it the same incident request and failing capture
without mentioning the Skill. Record whether Codex selected the installed Skill,
the observed findings, and the installed commit.
