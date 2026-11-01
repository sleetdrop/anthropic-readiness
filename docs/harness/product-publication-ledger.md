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

## PR 4 first CI and image-inventory correction

PR 4 was opened on checked head 3aa3762. First CI 41267386643 failed the amd64
Web image check with web_page_scope. Retained job logs/artifacts show the installed
page was rejected by an outdated hard-coded four-case count and old preview label,
while this publication deliberately ships five cases and a simplified entry page.
This is an acceptance-harness mismatch, not a transient network failure or proof
that the endpoint protocol is broken. No blind retry was used.

The harness now checks all five exact case IDs, duplicates/missing/unexpected IDs,
and exactly one enabled, non-hidden preview submit button, independently of its
localized caption. A source-catalog alignment regression detects future drift.
The existing four-case smoke conversation, request accounting, source/exports,
restart and cancellation checks are unchanged. This intentionally updates the
installed-page inventory expectation to the already-versioned fifth case; it does
not weaken endpoint assertions or change golden results. The host image runner
retains only standard-library dependencies.

Seven initial controls were RED before implementation. Ten final controls plus
existing image-harness tests passed (38 focused tests total). The final Mac fast
graph passed all eight gates on unchanged source, 517 Python unit/harness and 33
frontend unit checks. A bounded follow-up review found no issue; the earlier whole
publication review was not repeated. Original failed logs, raw escaped job log,
sanitized text and the runtime artifact remain ignored under the publication
artifact directory. Fresh exact-head PR CI and merge remain pending.

## Browser suite envelope correction

The first PR run also stopped both quality jobs in the browser stage. The retained
Python 3.12 artifact proves prerequisites passed with the locked browser; the
actual 109-case serial suite hit its 300-second total limit after 64 passing cases
and no case failures. Those passing cases alone consumed approximately 287 seconds.
This is an undersized suite envelope, not evidence of missing browser installation
or a complete passing suite. Original failures and partial JUnit remain retained.

The browser command now permits 600 seconds, and its outer gate permits 720 seconds
for reporting and owned-process cleanup. Other frontend commands, individual
Playwright test/expect deadlines, retries, assertion accounting and cleanup rules
are unchanged. A new regression requires at least 120 seconds between child and
outer deadlines. An initial test invocation used an incorrect helper name; the
corrected RED demonstrated the actual 420 < 600 + 120 mismatch before changing
the outer limit. Focused regression and final checks are recorded below when run.
No endpoint behavior or diagnostic coverage changes in this correction.

All 24 focused browser-gate tests passed, including timeout/owned-descendant cleanup.
The first fast run retained three failures caused by denied loopback binds; an
unchanged-source rerun with local-service permission passed all eight fast gates,
518 Python unit/harness and 33 frontend unit checks. A bounded independent review
found no specific regression. The second pre-budget CI run 41268709597 already
passed runtime-amd64; quality/container graphs passed every stage except browser.
The original failed runs remain evidence; the next exact-head full run must prove
all 109 browser cases and required jobs completed successfully. Final PR checks,
merge and post-merge status are recorded in the linked PR 4 timeline, so this
pre-merge snapshot is not a later claim about remote state.
