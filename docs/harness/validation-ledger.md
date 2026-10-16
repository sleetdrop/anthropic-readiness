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
