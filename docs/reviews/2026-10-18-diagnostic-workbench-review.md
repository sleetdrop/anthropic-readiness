# W2 independent review and author closure

One independent read-only whole-W2 review covered
`91544f8b247c59cf5ef6bd7758d474af54c50db1` through
`bfeb4f0d1ec1ae2cf3c6b5b36dac24ad878afbfe`. The original report and four
probe/input outputs are retained under `artifacts/w2/task15/`. The following
findings describe that candidate, not independent approval of later corrections.
The author retains both Important grades and defers the single Minor.

## Strengths

- Implementation identity is bound to code, resources, runtime and dependency digests. Recipe regeneration checks installed cases and captured requests; presentation changes remain outside execution identity.
- ZIP handling checks directory allocation, paths, actual expansion, CRC/hash integrity and shared deadlines. Uploads retain Host/Origin/session/CSRF protections, and uploaded HTML is not used for application rendering.
- Comparison preserves required-case/check denominators, unmatched observations and semantic condition changes. Localized exports remain separate variants without sharing proof status.
- Operational and document presentations are meaningfully separated. Inspected retained overview, dark inspector and document captures against the approved references; the overall hierarchy, neutral lifecycle treatment and explicit coverage limitations follow the design.
- Backward compatibility is explicitly versioned. Existing presentation-2 assertions remain intact behind the explicit legacy branch.

## Issues

### Critical

None found.

### Important

**1. Cancelled assessments regain comparison eligibility through `source_facts`.**

- Location: `src/anthropic_readiness/diagnostics/service.py:243`.
- Trigger: cancel a normal assessment after its first committed case. The runner still writes a valid final `result.json`, with `execution_environment.interruption=2` and remaining cases indeterminate.
- Problem: `source_facts()` defines completeness solely as `source.result is not None`. This differs from `validate_import()`, which also rejects interruption/internal-error results. Comparison reads recompute eligibility using the weaker rule, including after validating an imported baseline.
- Impact: a baseline correctly presented as ineligible during import can subsequently produce `comparable=true` and controlled transition labels. Missing-check counts remain visible, but they do not repair the contradictory proof claim.
- Observed disposable reproduction:

  ```text
  states: PASS, INDETERMINATE, INDETERMINATE, INDETERMINATE
  local eligibility: retest=true, compare=true
  imported eligibility: retest=false, compare=false
  imported reason: diagnostic_partial_source
  compare(imported cancelled baseline, local cancelled source).comparable: true
  ```

- Fix: share one completeness/eligibility derivation between import and comparison. Cover cancellation and internal errors with final result files, through both local and imported paths. Preserve readable facts while preventing controlled recovery/regression claims.

**2. A failed HTML refresh can permanently leave the completed run displaying stale content.**

- Location: `src/anthropic_readiness/resources/web/workbench.js:265`, especially the generation check at line 270 and polling termination at line 278.
- Ordering:
  1. DOM displays generation A, running.
  2. Workbench API returns generation B, completed.
  3. `state.snapshot` advances to B.
  4. The subsequent HTML request fails transiently.
  5. Retry API returns B again; the generation comparison is now equal, so HTML is never requested again.
  6. Connection becomes ended and polling stops.
- Impact: old counters, issues and actions can remain indefinitely, alongside worker/connection information from the completed generation. This violates the consistent-generation and reliable-completion requirements.
- Observed module-level reproduction with controlled browser ports:

  ```text
  after transient failure: API reads=1, HTML fetches=1, retry callbacks=1
  after successful retry: API reads=2, HTML fetches=1, retry callbacks=0
  DOM never patched
  ```

- Fix: track successfully rendered generation separately from observed API generation, or retain a pending-render flag until patching succeeds. Do not stop terminal retries while the displayed generation remains stale. Add a browser regression with one failed HTML response followed by successful recovery.

### Minor

**3. Chinese Markdown retains an English authored table header.**

- Location: `src/anthropic_readiness/document_rendering.py:535`.
- `| Case | Check | State | Source data |` is emitted regardless of selected locale.
- Impact: the default Chinese report is not fully localized despite the available catalog-based rendering elsewhere.
- Fix: translate these controlled headings; retain raw check identifiers and machine status values unchanged.

## Verification and reproduction evidence

Independent focused execution in the existing Linux Dev Container:

```text
115 passed in 22.51s
```

Covered identity, archive boundaries, recipe regeneration, pure comparison and comparison-service tests. Both additional probes reproduced the Important defects without real endpoint calls.

Reusable probes and captured outputs:

- Refresh probe (`/tmp/w2-review-refresh.mjs`), output (`/tmp/w2-review-refresh.log`)
- Cancellation probe (`/tmp/w2-review-cancellation.py`), output (`/tmp/w2-review-cancellation.log`)

Run the first through `docker exec -i ... node --input-type=module` and the second through `docker exec -i -e UV_OFFLINE=1 ... uv run --frozen python -`, using `/workspaces/anthropic-readiness` in container `37e2df3d035d`.

HEAD remained `bfeb4f0d1ec1ae2cf3c6b5b36dac24ad878afbfe`; tracked working tree remained clean.

## Review Focus outcomes

1. **Same label, changed implementation:** checked owning identity/recipe/context code and tests; no additional finding.
2. **Hostile archive or presentation:** checked archive/import/storage/security code and boundary tests; no additional finding.
3. **Changed retest conditions:** checked regeneration, semantic keys, limits and missing coverage; no additional finding.
4. **Completion, worker loss and presentation changes:** finding 2; ordered snapshots alone do not guarantee that the DOM received that generation.
5. **Legacy, partial, omitted and localized packages:** finding 1; variant separation and evidence-omission handling otherwise retain conservative distinctions.

## Recommendations

Address both Important findings in the single author correction pass, retaining failing regressions first. Complete final source/image acceptance against the corrected identities and update the handoff records. Earlier image results and retained screenshots do not certify the final candidate.

## Declined to judge

- Real endpoint behavior, Claude Code workflows and broader catalogs: outside authorized W2 execution; four installed cases remain the product scope.
- Remote CI, publication and native AMD64 developer execution: unobserved and not authorized as review operations.
- Native browser-chrome 200% zoom integration: retained evidence explicitly exercises equivalent layout/density, not native zoom controls.
- Previously completed Stage A/W1 acceptance: excluded from this W2 review; only W2 integration/backward compatibility was considered.
- Final corrected-source full graph and image acceptance: pending author delivery work, not treated as passed.

## Assessment

**Ready to merge: With fixes.**

The architecture and defensive boundaries are substantial, but interrupted-source proof escalation and lost terminal rendering are user-visible correctness defects. Both require correction, followed by final candidate acceptance and honest handoff completion.

## Author correction evidence

Both Important behaviors now have observed RED-to-GREEN regressions in the single
author pass; no second review ran. Cancellation/internal-error cases with final
result files failed before the shared pure-value completeness predicate, then
51 focused import/comparison tests passed. All four comparison-service tests also
passed after the strict typing/dependency-boundary correction. Original source
result/evidence bytes and read availability remain intact.

The actual browser test failed with the DOM still running 20 seconds after API
completion and one injected HTML 503. After separately tracking the last patched
generation, all 78 browser cases passed; the new case recovered and still counted
exactly four upstream requests. Its parent correctly rejected source mutation
during the concurrent Python boundary correction, so that run is regression
evidence only. The corrected fast graph passed all eight gates. Final immutable
source/full-image acceptance is recorded below. M3 stays Minor and deferred.

## Final author acceptance (not a second independent review)

Corrected source `35b59f5ef8ff4d78740283a81a5090d18b9b0aa5` passed all thirteen
required developer gates on unchanged, clean source: 463 unit/harness, 216
integration, 84 acceptance and five installed-package Python tests (768 total),
20 Node and 78 Chromium tests; zero failures/errors/skips. Both Important findings
are closed by the failing-first regressions and that whole-source execution.

Fresh native ARM64 and emulated AMD64 full CLI/Web image jobs each passed 68
actual checks on the same context, with builds executed and no missing child.
Each job independently prepared/disconnected a native Linux ARM64 development
container and passed the same complete test counts. Actual receiving volumes
imported, retested four cases with fresh credentials, exported paired comparisons
and preserved exact bytes across restart. Both jobs' owned containers, networks
and temporary run volumes were observed absent afterward. The synthetic preview
was refreshed and GUI export/hash preservation was observed without model calls.

The [handoff](../harness/diagnostic-workbench-handoff.json) records exact artifact
hashes and identities. Remote CI, supplemental Python 3.11, native AMD64 developer
execution and real endpoint/Claude Code outcomes remain not_run. Prior Stage A/W1
outcomes are not recertified. M3 is the sole deferred W2 Minor. No re-review ran;
the independent verdict above describes its original candidate.
