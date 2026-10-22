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
