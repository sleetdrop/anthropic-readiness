# Post-handoff validation ledger

This ledger covers later operator-authorized validations, separately from the
completed and immutable Stage A implementation ledger/evidence index.

## 2026-10-16: private local endpoint, fixed core subset

- Authorization: owner requested one real local proxy/model validation and stated
  that authentication was unnecessary. No auth header or credential was sent.
- Budget: four requests, zero retries; 60-second attempt / 180-second run limits.
- Runtime: previously accepted Linux arm64 installed wheel/image, source verification
  commit be168d9962ff3dacd5e480818dd537d9f3438593; checkout record d4b5530.
- Preflight: container TCP reachability passed; offline validate passed; network-none
  dry-run planned four requests and sent zero.
- Observation: four requests, all HTTP 200, all EOF captures, 20.74 seconds;
  behavior PASS in all four cases; protocol FAIL, both profiles not_ready, exit 1.
- Failing assertions: MSG-CORE missing stop fields; MSG-MODEL unallowlisted alias.
  Operator alias confirmation is outstanding; no post-hoc allowlist was applied.
- Evidence: JSON/HTML/Markdown and sanitized capture files retained privately outside
  the repository/build context. Offline report verification passed (verified, errors=[]).
- Limits: no thinking, tool-result round trip, client workflow, beta or version-selector
  proof; no proxy modification, retry or extra API request. The completed disposable
  container was automatically removed before optional runtime inspection; immutable
  image identity and configured launch isolation were recorded separately.
- Outcome: local detector/real-service integration exercised successfully; endpoint
  compatibility not established under the selected contract. Frozen implementation
  acceptance and historical artifacts remain unchanged.

## 2026-10-16: second private model on the same local proxy

- Authorization: owner explicitly requested one additional model assessment on the
  same local proxy. Kept no-auth mode and the fixed core 1.0.0/no-beta contract.
- Budget: four requests, zero retries; 60-second attempt / 180-second run limits.
- Preflight: offline validation and network-none dry-run passed, planning four
  requests without sending any. The accepted installed arm64 runtime image from
  be168d9962ff3dacd5e480818dd537d9f3438593 executed the actual calls.
- Observation: four requests, all HTTP 200, all captures EOF, 12.557 seconds, exit 1.
  All four behavior dimensions PASS; all four protocol dimensions FAIL. Both
  streaming responses completed with message_stop. The forced tool case passed
  its behavior checks. Both selected profiles remain not_ready.
- Findings: nonstream messages omit stop_sequence; streaming starting messages
  omit stop_reason and stop_sequence. MSG-MODEL also fails because the declared
  response name differs from the request and no alias was configured. These are
  the same observed failure classes as the earlier model; no internal cause or
  actual model weights/routing is established.
- Report: renderer commit 13711bf14e70a735dfa7f444f95796fe90d52e18 produced
  presentation 1.2 offline. Original result bytes and all 20 evidence files were
  preserved; evidence status verified, errors empty. No extra service call.
- Runtime: the created and finished container inspections were retained privately
  before cleanup, including image identity, ordinary-user/read-only isolation and
  exit status. Private config, model identifiers, captures, reports and provenance
  remain outside source/build contexts.
- Limits: basic single-turn cases only; no thinking, tool-result round trip, beta,
  client workflow or version-selector proof. No proxy/configuration modification,
  allowlist relaxation, image rebuild, remote CI or publication occurred.
