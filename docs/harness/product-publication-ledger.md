# Accumulated product publication

## Authorized outcome and scope

On 2026-11-01 the owner requested merging the remaining local work into GitHub
main, referencing the optional-Dev-Container chat. That chat was read before
relying on its scope. PRs 2 and 3 had published the host-development/test changes
separately; their post-merge main CI 41215465572 is now confirmed successful.

Initial checkout: clean codex/tool-result-round-trip at 9305241. Current remote
main: b6043c52ed67325d19c0f9631381c722270b90d2. This publication includes the
previously local product work, not only the already-published macOS changes:

- One additional formal endpoint scenario: non-stream tool-result round trip,
  raising the catalog from four to five. It checks observable use of the supplied
  tool result; it does not establish streaming tools or actual Claude Code support.
- Simpler Web configuration, endpoint/model input history without credential
  storage, investigation navigation and retained context, node-adjacent evidence
  annotations, UI deployment identity and the accepted design/project guides.

Use the CLI or Web catalog to select the tool-loop profile; inspect a run's Issues
and View evidence for the updated investigation flow. This publishes existing
implemented diagnostics; no new endpoint calls or additional coverage are produced
by the publication work itself. Activity interaction details, broader protocol and
actual SDK/Claude Code workflows remain unfinished goals in docs/CONTINUE.md.
No registry publication, account changes or local trial reinstall is included.

## Sequential ledger

1. DONE: read intent/handoff and referenced chat; fetched remote state and verified
   the repository, main CI and absence of duplicate open PRs.
2. DONE: merge latest main into the current branch without rewriting history.
   Three documentation conflicts retained both local and isolated-main evidence;
   main's worker-exit ledger and test-race fixes remain. No production or test
   conflict was resolved by choosing one side wholesale.
3. DONE: Mac combined-source fast graph passed all eight gates on unchanged
   source (507 Python unit/harness and 33 frontend unit checks); documentation
   check passed. One independent publication/merge review found no blocker and
   verified main's test fixes, retained records and scoped privacy checks. Earlier
   per-feature results do not substitute for current PR CI.
4. PENDING: merge commit, push feature branch, create PR, await every required
   GitHub job and merge the exact checked head after success.
5. PENDING: verify remote main and its post-merge CI, reconcile local state and
   record the final outcome without treating skipped/pending work as PASS.

Detailed outputs stay ignored under artifacts/publication-20261101/. Original
failures and records from PRs 2/3 remain retained. Remote writes are explicitly
authorized by this request; never force-push or bypass checks to complete it.
