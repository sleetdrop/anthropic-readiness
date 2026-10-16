# Stage A coverage map

This map describes implementation ownership and executable evidence. It is not an
endpoint certificate. Actual check/image/review outcomes are recorded in
`docs/harness/progress.md` and the handoff manifest; a mapped test is not itself a
claim that it ran successfully on the final source.

| Specification | Stage A implementation / executable checks | Explicit limits |
| --- | --- | --- |
| 1–3 scope and interfaces | src package, CLI, Import Linter; unit/harness/acceptance gates | Sequential cases; no plugin/workflow engine |
| 4 strict configuration | test_config, test_contracts, schema gate | One exact core bundle; unsupported API/beta rejected |
| 5 request budgets and capture | test_transport, test_deadlines, test_evidence, test_redaction | No real target credentials or original service records |
| 6 framing and lifecycle | test_sse, test_stream_validation, test_messages; versioned golden fixtures | Unknown extensions remain visible; offline tools are not live tool loops |
| 7 four cases/profiles | test_cases, test_runner, test_cli | Three basic and one tools-smoke case; no thinking/parallel/client profile |
| 8 status and exits | test_results, test_runner, test_cli, image signals | Non-PASS coverage cannot become readiness PASS |
| 9 result/schema/evidence | test_schemas, test_evidence, test_replay, test_reports | JSON is fact source; missing/transformed evidence disclosed |
| 10 detector matrix | tests/unit plus integration deadlines and acceptance replay | Critical negative controls paired with legal controls; later-phase failures excluded |
| 11 future contracts | documented boundaries in architecture/spec | Tool loops, CLI workflows, comparison, repeat/retry and rescoring deferred |
| 12 independent acceptance | full graph, image orchestrator, final independent review | Remote CI and actual endpoint outcomes separate |
| 13 official basis | packaged manifest with actual retrieval hashes and source summaries | Links explain rules; they do not prove endpoint behavior |
| 14 exact version selection | test_contracts, test_transport, test_replay; schema/bundle gate | Matrix/update command/pinning recipes deferred; version semantics unverified |
| 15 containers | actual Dev Container; check_images on amd64 and arm64 | Native/emulated labeled; host networking checked only where observed |
| 16 Python/harness | locked uv, Ruff, mypy strict, JSON Schema, Import Linter, negative gate controls, installed wheel | Bootstrap/fast/full/image are distinct scopes |
| 17 GitHub/open source | workflow and issue-form validation, ci_required negative tests, CONTRIBUTING and PR template | No remote protection/push/registry login; protocol Agent command is Stage D |
| 18 reports | test_reports, installed replay, desktop/narrow/print review | Offline Chinese HTML/MD; synthetic marker, references, glossary and reader limits |

## Detector evidence locations

The unit framing tests exercise all byte splits, one-byte chunks and seeded split
plans. Streaming tests cover valid text/tool flows, duplicate/missing lifecycle
transitions, indices, typed deltas, usage, stop reasons, unknown extensions and
error events. Integration tests cover redirects, status/transport errors, ping and
absolute deadlines, bounded decompression, reset after stop, redaction and capture
integrity. Acceptance tests cover opt-in, budgets, required-case accounting,
partial signal results, replay isolation, output safety and installed resources.
The whole-stage reviewer must assess blind spots independently; this mapping does
not waive defects in an implemented path merely because a test exists.
