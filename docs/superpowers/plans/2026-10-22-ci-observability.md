# CI Evidence and Observability Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans sequentially in the existing checkout and prepared Dev Container.

**Goal:** Retain diagnostic evidence from every CI environment and make recorded outcomes easy to inspect.

**Architecture:** Keep the existing check graph and fail-closed aggregator. Add a standard-library presentation script over existing result records, then upload both image-controller and inner developer evidence. The summary never replaces a gate or independently certifies readiness.

**Tech Stack:** GitHub Actions, Python 3.12 Dev Container, pytest, existing JSON/JUnit records.

**Spec:** Owner-approved CI assessment in this chat: first deliver evidence and observability, retaining existing coverage; defer repository protection, remote full matrix execution and caching/repartitioning.

## Global Constraints

- No product assertions, golden files, test deadlines, dependencies or required jobs change.
- Keep pinned Actions, read-only permissions and no publishing or real API calls.
- Reuse the existing directory/container; use local branch `codex/ci-evidence-observability`.
- Do not push, alter repository rules or dispatch workflows in this bounded task.

## Review Focus

- Preparation failure produces no report: say evidence unavailable, never passed.
- Failed/blocked records remain visible and do not become aggregate success.
- JUnit declared totals may be wrong: count actual testcase nodes, retain failures/skips.
- Multiple or partial records must remain separate; malformed evidence is identified.
- Report content must not inject Markdown/HTML; expose only selected diagnostic fields.

## Task 1: Evidence presentation and workflow wiring

**Files:** Create `scripts/ci_summary.py`, `tests/harness/test_ci_summary.py`; modify both `.github/workflows/*.yml`, `docs/development.md` and the current handoff/ledger.

**Interfaces:** `render_summary(root: Path) -> str`; CLI `python scripts/ci_summary.py --root artifacts` writes Markdown to stdout for `GITHUB_STEP_SUMMARY`. Reads `checks/**/check-result.json` and `images/**/image-result.json`, plus adjacent JUnit; never parses original target logs/configuration.

- [x] Write behavior tests for missing/failed/malformed evidence, actual JUnit counts, multiple records and escaping; observe RED in Linux.
- [x] Implement the summary; observe GREEN. Missing evidence is explicit, not a new gate verdict.
- [x] Add `always()` summary/upload to Dev Container, include `artifacts/checks/` in full matrix uploads; retain current quality/runtime uploads.
- [x] Configure quality/dev/smoke/aggregate job limits at 30/45/15/5 minutes, full matrix at 180 minutes. These outer operational budgets do not increase test deadlines. Full matrix uses per-ref concurrency without cancelling running acceptance. Set artifact retention to 14 days; original historical artifacts remain intact.
- [x] Run synthetic summary CLI and existing collaboration/required-child checks, then the offline full graph in Linux. Inspect YAML and script wiring; no local run represents remote workflow execution.
- [x] Arrange one independent review of this bounded diff, address material findings and record results; deliver one scoped local commit, then stop the container without remote writes.

## Execution Ledger

- 2026-10-22: Plan self-review complete; implementing the already approved bounded task sequentially. Prior consent to reuse the checkout/container persists. Source baseline is `7fb1bcd6d0762e61a622fd1a0e3a0d205429c3f2`.
- RED: The first direct `pytest` invocation could not resolve repository harness imports; corrected to the documented `python -m pytest`. With a presentation stub, five behavior assertions failed as expected, then passed. A Markdown-link injection case separately failed before escaping was extended. Original logs remain under ignored `artifacts/ci-observability-20261022/`.
- Review: One independent bounded review identified P2 overflow of `math.isfinite` on huge JSON integers; static review also raised nested metadata disclosure. Both were reproduced with real JSON inputs (two RED cases), then fixed. Eight summary cases plus six existing gate-contract cases passed (14 total). Strict typing and Ruff passed for the changed Python files.
- Wiring: A disposable runner workspace executed the exact four checked-in summary shell commands with missing and failed evidence. All succeeded in displaying the observations, and actual path expansion included Dev Container checks plus both full-matrix evidence trees. Existing remote artifacts were replayed offline; this is neither a GitHub run nor full container acceptance.
- Intermediate full graph: Retain the first attempt, which exposed Ruff SIM102. The source changed while that diagnostic attempt completed, so it cannot establish acceptance even where individual testcases passed. Its failed lint and source-change-detected browser wrapper remain recorded; no failed evidence was erased or reinterpreted as acceptance.
- Final verification: `UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite full --out artifacts/ci-observability-20261022/full-final` exited 0 in Linux ARM64/Python 3.12.15. All thirteen gates passed; actual JUnit nodes: 492 unit/harness, 258 integration, 84 acceptance, 5 package, 20 Node and 78 Chromium; zero failures/errors/skips. Browser gate 188.59 seconds, integration 208.83 seconds, with original deadlines intact.
- Provenance: Full graph ran the uncommitted patch on `7fb1bcd`, not a clean future commit. Source remained unchanged at `946ea1950af2d0b0a78c351c339110db547f6cb1cac846779c3719ae1b9cd3bb`; full-final/check-result.json SHA-256 `1dfbaafe65713a4d24c30b4fac8768472ed74a0f9b2e46f2fda88dc626bde107`. The independent accounting helper verified every expected positive testcase count, zero defects/skips and matching current source bytes. Full records are retained in ignored artifacts.
- Ruling: The new 180-minute full-matrix job budget is an outer operational bound, not measured remote acceptance. First remote execution, branch protection, caching and test repartitioning remain separate follow-ups. No remote write or real API call occurred in this task.

## Owner-authorized PR publication follow-up

- The owner approved the next bounded operation: push the existing feature branch, create a PR and inspect its real CI; stop before merging or dispatching the full image matrix. Code `eb82885` was pushed without force, and PR 1 was created against main. Current source bytes were rechecked against the retained local full-run fingerprint before pushing; no product tests ran on the host.
- PR CI run `39718653050` failed. Quality 3.11 and AMD64 smoke succeeded; quality 3.12 and Dev Container failed acceptance; the aggregator correctly failed. Non-default-branch push run `39718218768` was skipped by design. The PR validates clean virtual merge commit `4af5a8e9c2748a711ff962cf294fb699d9262f19`, not a dirty worktree.
- All four summary steps and artifact uploads succeeded. The four artifacts expire on 2026-11-05 (14 days). Complete downloaded Python 3.12/Dev Container evidence matches the local source fingerprint; each has 492 unit/harness, 258 integration, 84 acceptance (82 passed, 2 failed), 5 package, 20 Node and 78 Chromium cases with zero skips. All other twelve gates passed. The committed reporter correctly renders the failed downloaded evidence; the GitHub summary page was not visually inspected.
- Both first fail `test_real_serve_start_and_signal_shutdown` at the existing five-second readiness deadline, followed by unclosed-file ResourceWarnings in different later report cases. Actual failed case names and record hashes are in ignored `pr-observed-summary.json`. This establishes symptoms, not startup root cause or proof of an environmental flake. No source/test correction, deadline change or rerun was performed.
- Network/download observations: the initial host accounting helper needed documented repository import-path setup; the corrected read-only invocation matched existing source bytes and JUnit. Bulk artifact download was slow but completed. A parallel selective HTTP-range attempt timed out after 120 seconds; its diagnostic log is retained and no fallback artifact result is claimed. The complete bulk downloads are the authoritative inspected records.
- PR description was updated with actual failures and limits. PR remains open/unmerged. Observation changes are recorded in a local docs-only commit, intentionally not pushed, so no extra PR CI is triggered. No full matrix, protection setting, registry publication or real model request was performed.
