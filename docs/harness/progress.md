# Verification record

## 2026-11-04: Repository transition to the diagnosis Skill

The Skill, Node helpers, contract fixtures, and Node CI are the active
project. The former standalone assessment and its evidence are available in
the parent commit `8048934`. The inspector, probe implementation, and fixture
bytes were reused. This transition adds no endpoint cases.

A fresh worktree installed the locked Node tools and passed strict
TypeScript validation and all 63 tests on Node 24.22.2. The offline exercise
returned PASS for the normal stream, located the duplicate message start
at event index 1, and returned INDETERMINATE for the partial stream. The
forced-tool probe preview planned one request. Skill metadata and local
documentation links validated. The full check used synthetic HTTP peers.

## 2026-11-04: Live diagnosis walkthrough

An owner-authorized local trial completed the three basic probes against the
corrected model selection. All returned HTTP 200 and complete captures. All
task checks passed. Offline inspection verified the saved body hashes and
located omitted stop fields in the JSON message, the SSE start message, and
the SSE delta. Both SSE captures included the terminal event. Thinking
blocks remain outside the inspector's implemented rules.

Three probes using the previously used model name completed before the
correction. Both selections returned the same declared model label and the
same stop-field omissions. The declared label is evidence for checking the
routing configuration. It does not establish the backend model identity.
Private captures and report outputs are stored outside the repository. This
walkthrough exercised existing scenarios and added no endpoint coverage.

## 2026-11-04: Independent offline diagnosis

A fresh agent received the Skill, three anonymously named SSE bodies, and
the known capture completeness. It received neither expected findings nor
previous reports. One body came from the authorized local trial and the
other two were synthetic controls.

The agent matched all three reference outcomes. It located the missing
stop fields at event indexes 0 and 40 in the complete saved response. It
kept thinking extensions outside the tested rules and identified the
properly framed terminal event. The partial control was inconclusive.
Its terminal event text was present and its bytes matched the passing
control apart from the final two LF bytes. The passing control established
only that the inspected rules passed.

The agent kept protocol findings separate from client behavior and suggested
comparing captures before and after serialization to locate where the
fields disappear. The exercise made zero endpoint requests and added no
endpoint cases. The Skill and inspector code were unchanged.
