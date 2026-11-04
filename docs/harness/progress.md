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
