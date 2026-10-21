# Independent review correction ledger

## Scope and stopping rule

The owner authorized one complete correction per turn on 2026-10-20, followed by
a pause rather than starting another finding with an uncertain usage allowance.
Work stays on the existing checkout and prepared Linux/Python 3.12 Dev Container.
Local commits are required; no remote write, live endpoint call or new whole-stage
review is part of this correction. The completed W2 plan and its historical
acceptance records remain unchanged.

Review source: `0ac72c6be5ac3d16ea76abf487026e3efb55c2be`.
Original review and synthetic probes are retained, without modification, under
ignored `artifacts/independent-review-20261020/`. The report records four reproduced
findings; their original regression cases have been corrected. The later bounded
review below adds two related evidence-validation findings requiring correction.

| Finding | Priority | Current state | Next action |
| --- | --- | --- | --- |
| F01: malformed intermediate message delta is overwritten | P1 | Fixed and locally verified in 6ea328d | Complete |
| F02: missing response evidence can still support recovery claims | P1 | Original regression fixed in fe5b4ad; F05/F06 corrected locally | Complete within recorded scope |
| F03: replay trusts contradictory cached tail metadata | P2 | Fixed and locally verified in 575f279 | Complete |
| F04: imported dimensions and request counts contradict facts | P2 | Fixed and locally verified in 9a30567 | Complete |
| F05: report reader accepts internally contradictory capture metadata | Important | Fixed and locally verified in 12f9217 | Complete |
| F06: observed PASS assertions accept request-only proof | Important | Fixed and locally verified in this delivery | Complete |

## F01: retain malformed stop-field failures

Root cause: `StreamValidator.consume` merged `stop_reason` and `stop_sequence`
directly into the reconstructed message. Later valid values erased the only
observable malformed values before final-message validation. Existing `_record`
already preserves failures once they have actually been recorded.

Correction: inspect each present stop field before merging it. A non-null value
must be a string; otherwise record `STR-JSON=FAIL` with the event sequence. Reuse
the existing failure-retention mechanism and final-message checks. Missing keys,
null/string values, legal multiple deltas and unknown extension fields retain
their existing behavior. No enum, catalog, schema, golden or required-case change
is introduced. The execution implementation identity covers the changed validator;
old source acceptance is not rebound to this patch.

The regression catches removal of the event-level type check: integer, Boolean,
object and array values for either field must remain FAIL after a legal terminal
delta. It checks the offending event identity and confirms final stop checks are
PASS, proving that the preserved failure comes from the intermediate event.
Four legal controls cover omitted fields, null fields, string stop reason and an
unknown extension field.

### Observed checks

All product execution used the existing Linux ARM64/Python 3.12.15 Dev Container
with `UV_OFFLINE=1` and locked dependencies. Evidence root:
`artifacts/review-fixes-20261020/f01/`.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Regression before implementation | 8 expected failures, 4 legal controls passed | `red.xml` |
| Original reviewer runner probe before implementation | Malformed and valid controls both incorrectly returned exit 0 / passed | `probe-red/delta-summary.json` |
| Stream and final-message regression suite after implementation | 59 passed; zero failures/errors/skips | `green.xml` |
| Same reviewer runner probe after implementation | Malformed stream exit 1 / not_ready; valid control exit 0 / passed; all three planned cases remain accounted | `probe-green/delta-summary.json` |
| Runner, historical review regressions and comparison service | 26 passed; zero failures/errors/skips | `runner-comparison.xml` |
| Fast verification | All 8 gates passed, unchanged source; 475 Python unit/harness tests passed | `fast/check-result.json`, `fast/unit.xml`, `fast/frontend-static/` |

The fast run observed the uncommitted patch on base `0ac72c6`, not a clean-source
whole-stage release. Its source fingerprint was
`9f1c8454141c19bc512e90a7b9f5444882fc1195bf3cc2d7c7a1a2b3c868252e`.
Focused suite counts overlap the fast suite and are not summed as unique tests.
The standalone runner probe uses synthetic transport, not a real endpoint.

### Limits and handoff

No full browser graph, installation/multi-architecture image rebuild, remote CI
or real endpoint/client workflow was run for this two-line validator patch.
Existing runtime images and retained preview data have not been updated or
migrated. The prior W2 image/full records certify their old source only.
No existing evidence or failed attempt was deleted or rewritten.

The development container was stopped before this turn and was restored to that
same stopped state after all checks completed. The final Docker state is recorded
in `container-final-state.json` (`exited`, `running=false`, exit code 0). No check
or build process remains running in it. No replacement container, network or volume
was created. This F01 turn stopped without starting another finding. The owner
subsequently authorized the separate F02 turn recorded below.

## F02: require complete, attempt-bound response proof

Base: `6ea328d` after F01. The owner authorized proceeding with F02 only if it
could finish within the remaining allowance, retaining the one-fix stopping rule.
No F03/F04 correction or new independent review is included.

Root cause: report-source quality verified only the declared top-level references.
It did not check the capture's own file inventory, and required nonempty assertion
references only for FAIL. A self-consistent enclosing package could therefore omit
response files, retain PASS claims, and regain comparison/retest eligibility.

Correction: share the existing capture-schema/exact-four-file inventory check
between the replay loader and report-source reader. For each captured attempt,
require its response metadata and all four inventoried files in the verified
top-level inventory, with the same hashes. Observed PASS assertions require a
reference; attempt assertions cannot borrow proof from another attempt. An
interrupted/internal attempt that never produced a capture remains readable with
its existing indeterminate execution assertion. No source bytes are rewritten,
no schema/golden/catalog changes are made, and replay framing behavior is not
changed as part of this extraction. Existing implementation identity accounts for
the changed evidence module; historical acceptance is not rebound to this patch.

All adapters consume the shared quality result. A malformed source stays readable
as `missing_or_invalid`, loses retest/compare eligibility, produces incomparable
pairs instead of recovery claims, and cannot be exported with evidence included.
An independently assembled incoming ZIP is also retained only for limited reading;
activation, revalidation and source-fact recomputation cannot restore eligibility.
Complete valid before/after proof still yields the legitimate recovery conclusion.

### Observed checks

All product execution used the existing Linux ARM64/Python 3.12.15 Dev Container,
offline with locked dependencies. Evidence root:
`artifacts/review-fixes-20261020/f02/`.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Initial regression construction | 4 failed, 3 passed; nested mutation helper needed correction because production JSON conversion copies objects | `red.xml` |
| Corrected independent mutations, before implementation | All 6 negative variants failed because quality was incorrectly verified; healthy recovery control passed | `red-2.xml` |
| Core closure/source/comparison tests | 26 passed; zero failures/errors/skips | `green.xml` |
| Related import/export/recovered-report/review/CLI/handoff tests | 60 passed; zero failures/errors/skips | `related.xml` |
| Fast verification | All 8 gates passed, unchanged source; 475 Python unit/harness tests passed | `fast/check-result.json`, `fast/unit.xml`, `fast/frontend-static/` |

The six independent mutations remove body, event or response files, contradict a
capture's declared file hash, remove a PASS assertion's reference, or substitute
another case's proof. Tests bind all enclosing result/context hashes after the
intentional mutation, so rejection cannot rely on an accidentally stale envelope.
They exercise real execution, source reading, comparison, guarded export,
independently assembled ZIP import/activation, repeated baseline reads and comparison
against the imported source. Original delivery bytes remain unchanged throughout.
The first test-construction attempt remains retained and is not counted as the
complete six-variant RED result. Expectations were not weakened.

Fast observed the uncommitted patch on base `6ea328d`, with source fingerprint
`db07c022a13e94c4b03607ddce07bc1046d9239f9b1e6b952580892896ad2e9e`.
This is local correction verification, not clean-source whole-stage acceptance.
No full browser graph, installation/multi-architecture image rebuild, remote CI
or live model/client workflow was run. Existing runtime images and preview data
were not updated. F03 and F04 remain pending for separately resumed turns.

After all checks completed, the existing development container was restored to its
original stopped state. `container-final-state.json` records `exited`,
`running=false`, exit code 0. No test/build task remains running; no replacement
container, network or volume was created. Pause after the local F02 commit.

## F03: derive replay tail facts from retained bytes

Base: `fe5b4ad`. The owner resumed on 2026-10-21 and authorized F03 only. The
one-fix stopping rule remains in effect; F04 is not included.

Root cause: `load_capture` reconstructed SSE framing from retained bytes, then
overwrote the computed `pending_data` with a cached metadata flag. Identical raw
EOF bytes could consequently change between PASS and FAIL without any body change.

Correction: for complete, untransformed captures, retain the decoder's pending
state. For transformed or incomplete captures, conservatively combine decoded and
cached pending signals; a false cache cannot hide decoded unfinished data, and
rechunking/redaction cannot erase an existing uncertainty signal. Existing UTF-8
recomputation, resource-limit metadata, capture-end semantics and cancellation
exit code 130 remain intact. No source capture is rewritten, and no schema,
golden, assertion identity or catalog change is introduced. The existing execution
implementation identity includes the changed evidence module.

### Observed checks

All product execution used the existing Linux ARM64/Python 3.12.15 Dev Container,
offline with locked dependencies. Evidence root:
`artifacts/review-fixes-20261021/f03/`.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Initial regression run | 7 failed, 1 passed; one failure was an incorrect test expectation of exit 3 for a cancelled replay, whose existing contract is 130 | `red.xml` |
| Corrected regression before implementation | 6 failed, 2 conservative controls passed | `red-2.xml` |
| Evidence, CLI and historical review regressions after implementation | 31 passed; zero failures/errors/skips | `green.xml` |
| F02 closure and comparison service regressions | 11 passed; zero failures/errors/skips | `related.xml` |
| Fast verification | All 8 gates passed, unchanged source; 475 Python unit/harness tests passed | `fast/check-result.json`, `fast/unit.xml`, `fast/frontend-static/` |

The complete-capture tests cover both schema 1.0 and 1.1, valid and undispatched
SSE tails, and the opposite cached flag in each case. Actual replay controls and
mutated captures must retain literal exit codes 0 or 1 and matching framing
assertions; body bytes and the deliberately mutated metadata stay unchanged on
read. Four conservative cases cover redacted or cancelled captures with opposing
byte/cache signals. Their case result stays INDETERMINATE; transformed EOF replay
returns 3 and cancelled replay returns 130. The initial test expectation correction
is retained separately and does not change product behavior or old expectations.

Fast observed the uncommitted patch on base `fe5b4ad`, with source fingerprint
`f37b863df69ae8ee7e3bb68d8abb01ca8b71940c7610d9ed75fb7966337b4cd3`.
This is local correction verification, not clean-source whole-stage acceptance.
No full browser graph, installation/multi-architecture image rebuild, remote CI
or real endpoint/client workflow ran. Existing images, preview data and historical
acceptance records remain tied to their original source. F04 remains pending.

After all checks completed, the existing development container was restored to its
original stopped state. `container-final-state.json` records `exited`,
`running=false`, exit code 0. No test/build process remains running; no replacement
container, network or volume was created. Pause after the local F03 commit.

## F04: validate derived dimensions and execution counts

Base: `575f279`. The owner authorized F04 after F03's clean local checkpoint.
This turn closes the fourth finding without restarting the whole-stage review.

Root cause: result semantics validated overall assertion/attempt/case status but
trusted the separately declared dimension map. Request accounting required only
agreement among totals, so all captured live attempts could be changed to zero
without creating a detected contradiction.

Correction: move the existing dimension reduction to the pure models module and
share it between the runner and semantic reader. All four declared dimension
states must equal aggregation of the required assertions in each category,
including preconditions and not_evaluated states. Reject missing/empty maps rather
than silently rewriting them. For the shipped single-request attempt model, live
counts must be one, or zero for an indeterminate EXECUTION-COMPLETE failure without
any declared capture evidence for that attempt. Existing replay-zero and
aggregate-total checks remain intact. Future
multi-call attempts require deliberately versioned accounting rather than silently
relaxing this rule. No schema, assertion identity or versioned golden was changed;
valid writer output remains the same, and execution identity includes these source
changes. Partial checkpoint validation is unchanged by this final-result fix.

The same final-result entry point protects direct rehydration, report source
loading, evidence-inclusive export and ZIP import. Rejection preserves the
original and intentionally mutated input bytes and does not activate a baseline.
Independent ZIP mutations update enclosing hashes, preventing a stale-envelope
error from masquerading as detection of the semantic contradiction.

### Observed checks and explicit rulings

All product execution used the existing Linux ARM64/Python 3.12.15 Dev Container,
offline with locked dependencies. Evidence root:
`artifacts/review-fixes-20261021/f04/`.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Initial RED construction | 8 negative variants reproduced acceptance; an additional failure came from an overbroad request-builder fault affecting the final plan snapshot | `red.xml` |
| Corrected transient fault, before implementation | 8 negative variants failed as expected; unsent-failure zero-request control passed | `red-2.xml` |
| First post-fix core run | 22 passed, 1 failed: an old hand-written positive sample had an empty dimension map despite a BLOCKED environment assertion | `green-attempt.xml` |
| Corrected positive input, original assertions retained | 23 passed | `green.xml` |
| First fast graph | 7 gates passed; lint found two redundant list comprehensions in the new test | `fast/check-result.json`, `fast/lint.log` |
| Core run after equivalent list-style correction, before added proof guard | 23 passed; zero failures/errors/skips | `green-2.xml` |
| Related regressions before added proof guard | 81 passed; zero failures/errors/skips | `related.xml` |
| Fast graph after lint correction, before added proof guard | All 8 gates passed, unchanged source; 475 Python unit/harness tests passed | `fast-2/check-result.json` |
| Added captured-attempt/zero-request boundary, before guard | One coherent negative input still accepted; new regression failed as expected | `zero-proof-red.xml` |
| Final core run after proof guard | 24 passed; zero failures/errors/skips | `green-3.xml` |
| Final evidence/import/comparison/report/review/handoff/CLI regressions | 81 passed; zero failures/errors/skips | `related-2.xml` |
| Final fast graph after proof guard | All 8 gates passed, unchanged source; 475 Python unit/harness tests passed | `fast-3/check-result.json`, `fast-3/unit.xml`, `fast-3/frontend-static/` |

The initial eight independent variants contradict protocol, behavior, client or environment
states; remove one/all dimensions; or declare coherent but false zero/two-request
counts. The failed streaming case's four correct dimensions are asserted against
literal expected values before mutation, independently of the shared reducer.
The positive control raises a transient error before the send, confirms zero
transport calls and preserves a valid zero-request indeterminate result. Related
tests cover missing credentials, exclusions, deadlines, internal errors, replay
zero requests, redaction and cancellation without weakening their expectations.

Final boundary analysis added a ninth variant: a captured attempt is relabeled
as an indeterminate execution failure, with zero count and matching case/profile
states, while its capture inventory remains present. The intermediate exception
incorrectly accepted it. The added guard requires absence of declared capture
evidence before admitting a zero-request unsent failure; the new regression was
observed RED first, and final core/fast/related suites were rerun on that source.

The old synthetic unit input was explicitly corrected from an empty dimension map
to protocol/behavior/client not_evaluated and environment BLOCKED. Its roundtrip
and inconsistent-readiness assertions remain unchanged. This repairs a positive
test fixture that did not model actual runner output; it does not update frozen
result/capture goldens or excuse a contradictory input. All failed attempts above
remain retained. The final test-only list() cleanup changes no expectation.

Final fast observed the uncommitted patch on base `575f279`, with fingerprint
`78b67246eaae373f7b5932a767a4f053e3767239ba3e69559e1bb0bfa0968985`.
Focused counts overlap fast and are not summed as unique whole-stage tests. No
full browser graph, installation/multi-architecture image rebuild, remote CI or
live endpoint/client workflow ran. Existing runtime images and historical W2
acceptance records remain tied to their old source. All four original findings
are now corrected and locally verified; this is not whole-stage recertification.

After every check completed, the development container was restored to its original
stopped state. `container-final-state.json` records `exited`, `running=false`,
exit code 0. No test/build task remains running; no replacement container, network
or volume was created. Stop after the local F04 commit. A later full/container
acceptance is a separate resumed task, not an implied outcome of this correction.

## Full source verification after all four corrections — 2026-10-21

The owner approved the proposed next step: run the complete source graph before
another bounded review or Docker rebuild. This turn adds no product behavior,
test expectation, dependency, schema or image change. The existing container was
initially stopped and was started only for this offline verification.

Verified source: `9a3056707560c991449c1ae4988781f335b0add7`, clean working tree,
branch `codex/local-web-console`. `uv sync --locked --offline` succeeded using
the prepared Linux ARM64/Python 3.12.15 environment. The actual full command was:

```sh
UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite full \
  --out artifacts/review-fixes-20261021/full-9a30567
```

All thirteen required gates completed with exit 0: lock, format, lint, strict type,
architecture, packaged schemas, unit/harness, frontend static, Chromium browser,
integration, acceptance, installed-package checks and documentation. The actual
run took about 11.5 minutes. Source remained unchanged throughout.

| Executed suite | Actual test cases | Outcome |
| --- | ---: | --- |
| Python unit/harness | 475 | Passed |
| Python integration | 241 | Passed |
| Python acceptance | 84 | Passed |
| Installed-package checks | 5 | Passed |
| Node | 20 | Passed |
| Chromium | 78 | Passed |

Python total: 805. Every referenced JUnit report contains actual cases and zero
failures, errors or skipped cases. These are full-run counts, not sums of prior
focused runs. The retained `verify_observation.py` independently parses the actual
JUnit files, requires all thirteen executed gates, checks the clean recorded Git
identity, and matches current source bytes to the observed fingerprint. Its
exclusive `observed-summary.json` records the same outcomes without changing the
original check result.

Evidence root: `artifacts/review-fixes-20261021/full-9a30567/`.
Main record: `check-result.json`, SHA-256
`9532fdf7759865e2994cfb9f5e75afea31e84a628488afcc640001d4aca36e26`.
Source fingerprint:
`78b67246eaae373f7b5932a767a4f053e3767239ba3e69559e1bb0bfa0968985`.
Per-gate logs, JUnit XML and actual browser artifacts remain in that directory.
The documentation-only closeout does not replace or rebind any previous result.

This establishes a new complete source verification baseline for the corrected
implementation. The main record deliberately keeps `stage_readiness=incomplete`:
updated container acceptance, remote CI and a new independent review are not_run.
No Docker image build, registry write, real model endpoint, Claude Code workflow
or Python 3.11/native AMD64 verification was performed in this turn. Existing W2
image and whole-stage records still apply only to their original source. A bounded
diff review and current-source Docker acceptance are separate next steps.

After documentation and fingerprint checks completed, the development container
was restored to its original stopped state. `container-final-state.json` records
`exited`, `running=false`, exit code 0. No test/build task remains running; no
replacement container, network or volume was created. This turn ends with a local
documentation-only commit and a clean working tree, without any remote write.

## Bounded independent correction review — 2026-10-21

The owner approved one read-only review before updated image acceptance. One
fresh-context reviewer inspected only the F01-F04 product/test diff and direct
supporting paths. Its first dispatch failed before review because the selected
model was at capacity. A single retry of the same reviewer completed; the failed
dispatch is not a review or passing check. No second reviewer was dispatched.

Immutable diff identity:

- Base: `0ac72c6be5ac3d16ea76abf487026e3efb55c2be`.
- Head: `9a3056707560c991449c1ae4988781f335b0add7`.
- Checkout at dispatch: documentation-only `a8c1f4da43647ed680fa20e0110bd94182ad9c17`.
- Scope: six product files and five test files under `src/` and `tests/`.
- `review.diff` SHA-256:
  `fc2a20e3b96c4040dfac0dfb72b27c9ece28d0dfa707068f75a158aa0f6d8f61`.

Evidence root:
`artifacts/review-fixes-20261021/bounded-review-9a30567/`.
The original `REPORT.md` is retained without editing, SHA-256
`87ef09989dc2d41ce51c6bbab278b7f5e99829102aaa5ef73179684e764a122c`.
Verdict: **With fixes** for readiness to proceed to the next container verification,
with two Important findings and no reported Critical/Minor findings. This is not
whole-product certification.

### Author rulings and next corrections

| Reviewer item | Tracking ID | Author ruling | Observed boundary |
| --- | --- | --- | --- |
| R01, `report_sources.py:73` | F05 | Accepted, Important | Increasing `retained_bytes` by one preserves verified eligibility, although `load_capture` rejects the same capture. |
| R02, `report_sources.py:80` | F06 | Accepted, Important | An observed response/protocol PASS can cite only its own attempt's `request.json` and retain verified comparison eligibility. |

The author inspected the actual probe, its summary, the report-source helper,
`load_capture`'s length check and `runner._bind`'s response-proof rules. Both are
concrete integrity/binding gaps within F02's intended boundary. F05 requires
applicable cross-file capture consistency checks; F06 requires proof kind/location
in addition to attempt ownership. Fix them in separate bounded turns, F05 first,
before building updated runtime images. Preserve F03's intentional byte-derived
handling of cached EOF-tail flags and all submitted evidence bytes. Add meaningful
failing regressions without silently relaxing old expectations.

One offline synthetic probe ran two mutation variants in the prepared Linux/Python
3.12 container. Both returned `evidence_verification.status=verified`,
`retest=true`, `compare=true`, `comparable=true` and
`all_previous_failures_passed=true`; reading preserved input bytes. The length
variant failed `load_capture` with `capture_integrity:retained_bytes`; the
request-only variant retained a valid capture. The actual summary is
`probe-output/summary.json`, SHA-256
`4fdb383f17ef9a7c69f5c35936990c514af78f5870d6311abf78bbcf1b10db4a`.
An initial Docker socket denial did not execute the probe; the same authorized
command then succeeded under escalation, exit 0. No API/network transport ran.

Both bodies are valid synthetic controls. This demonstrates improper admission
of inconsistent/misbound proof, not an invalid protocol response being classified
PASS or a proven false underlying repair. Unmodified before/after sources remain
retained, but no separate healthy-comparison control was executed in this review;
existing positive tests were inspected only. No broad suite or image ran.

Accepted declined-to-judge boundaries:

- Other capture contradictions and general assertion authenticity: unexercised.
  Cover directly related consistency variants during F05/F06; hashes do not
  authenticate an author, and no general trust-system redesign is authorized.
- ZIP/export propagation: direct source-reading/comparison was dynamically probed.
  Exercise relevant downstream boundaries during fixes; no new dynamic import or
  export result is claimed here.
- Partial-checkpoint dimensions/counts: outside F04's final-result scope; do not
  promote to another finding without a concrete separate trigger.
- UI, images, remote CI, platform matrices and real clients: excluded for scope
  and quota. Image verification is later; the other checks remain unrun.

No new actionable F01/F03/F04 issue was established in this bounded pass; this is
not proof of absence. The parent reran only retained `verify_observation.py`,
confirming the existing 805 Python / 20 Node / 78 Chromium record and unchanged
source fingerprint. Those tests were not executed again. The original full-run
record's `independent_review=not_run` remains its historical state at creation;
this section separately records the later review.

No source, test, dependency or schema changed. The parent restored the development
container to stopped after the reviewer finished; `container-final-state.json`
records `exited`, `running=false`, exit code 0. No test/build task remains running;
no replacement container, network or volume was created. Stop with a local
documentation-only commit. No Docker build, endpoint call, remote write, fix
implementation or automatic follow-on review is part of this turn.

## F05: align report evidence with existing capture integrity checks — 2026-10-21

The owner authorized one F05 correction turn from clean `46da8c6`. F06, image
acceptance and another review are outside this turn. Work uses the existing
Linux ARM64/Python 3.12.15 Dev Container; offline locked sync succeeded.

Root cause: `attempt_evidence_errors` checked the capture schema, complete local
inventory and enclosing hashes, but omitted relational checks already enforced
by `load_capture`. A package could therefore be invalid for replay but retain
verified report quality, controlled retest/comparison and recovery claims.

Correction: after inventory binding, call that same capture reader on the safe
response path. Existing read/parse/integrity failures enter the existing readable
evidence-limitation path. No duplicate integrity implementation, protocol
revalidation, new contract/schema version or broader assertion-proof rule is
introduced. F03's byte-derived EOF tail and conservative incomplete/transformed
handling remain unchanged. This aligns the existing reader checks; it is not a
claim of author authenticity or exhaustive validation of every capture field.

New negative variants change only retained length, the embedded request, original
body hash, original length or structural digest. Enclosing result/context and
response hashes remain coherent. Each is first confirmed invalid by the existing
capture reader, then tested through source facts, comparison, evidence export,
independently assembled ZIP import and repeated stored-baseline reads. All five
failed before implementation because report quality was still `verified`.
After correction they remain readable with `missing_or_invalid` proof, without
controlled permissions or recovery; evidence export rejects the invalid source.
All submitted bytes remain unchanged on read. No old expectation was weakened.

Positive controls preserve healthy recovery and admit complete valid captures
with an obsolete pending-tail cache flag in both capture schema versions 1.0/1.1.
The existing evidence tests also exercise transformed data, partial/cancelled
captures and both directions of byte/cache disagreement. No golden was rewritten.

| Executed check | Observed result | Retained evidence under `artifacts/review-fixes-20261021/f05/` |
| --- | --- | --- |
| Initial core RED | 5 failures, 9 passed; no errors/skips | `red.log`, `red.xml` |
| Core after correction, including replay/evidence | 27 passed; no failures/errors/skips | `green.log`, `green.xml` |
| Initial related command | Exit 4, no tests ran: nonexistent `tests/acceptance/test_review.py` | `related.log` |
| Corrected report/import/export/comparison/accounting/runner/review regression command | 102 passed; no failures/errors/skips | `related-2.log`, `related-2.xml` |
| Fast graph | All 8 gates passed on unchanged source; 475 Python unit/harness and 20 Node tests | `fast/check-result.json`, JUnit files |
| Documentation contracts and links | Exit 0 | `documentation.log` |

The initial related-command typo was corrected to the existing
`test_review_regressions.py`; its failed log remains retained and does not count
as a passing test. Focused counts overlap prior verification and are not summed
into a whole-stage claim. No new broad browser, installed-package, image, remote
CI or real endpoint/client workflow verification ran.

Fast observed the uncommitted patch on base
`46da8c6c42cf19dc814fb6ec7640a3ca28828833`, with source fingerprint
`01205080ed51dcdce39ad1da4c4f51de533938481cf83868d4f57bdcfbeaa90b`.
Main record SHA-256:
`ae0db57bd351831b5bb3bc775233295d5793f08c096b6e858148838e073def85`.
The exact source/test `correction.diff` has SHA-256
`b630fbdabf23ef1fc85d37663a473ceb66676d0ef04f668b00dd7ebb09150308`.
`verify_observation.py` checks actual JUnit cases, RED failures, executed fast
gates and current fingerprint, retaining a separate `observed-summary.json`.
Original full-source and review records remain unchanged and tied to their
original source; fast still reports stage readiness incomplete.

After documentation checks, the container was restored to its original stopped
state. `container-final-state.json` records `exited`, `running=false`, exit code 0.
Stop after the local F05 commit with no test/build task running.
No replacement container/network/volume, remote write,
F06 implementation or automatic follow-on review/build is part of this delivery.

## F06: enforce assertion evidence kind and location — 2026-10-21

The owner authorized F06 only from clean `12f9217`. Work remains in the prepared
Linux ARM64/Python 3.12.15 Dev Container; offline locked sync succeeded. No new
reviewer, full graph, image rebuild or real endpoint call is part of this turn.

Root cause: nonempty observed PASS references were checked for attempt ownership
and hashes, but any file in that capture could qualify. An outgoing request could
therefore masquerade as proof of a response observation. Even intact response
files elsewhere in the inventory did not make that assertion's reference correct.

Correction: writer and reader share pure `assertion_evidence_file` in `models.py`.
HTTP/capture assertions select `response.json`; other assertions select indexed
`events.jsonl` or `body.bin`. Report validation checks every supplied observation
reference against that expected file under its own attempt. Existing verification
still checks hashes and resolves event/pointer locations. A mismatch follows the
readable `missing_or_invalid` path, removing controlled eligibility and recovery
claims; it is not silently rebound to another reference. Existing missing-PASS
proof rules and uncaptured internal-failure exceptions remain unchanged.

Initial extraction retained the old writer's event-first precedence. Eight
wrong-file regressions passed after this first correction, but boundary analysis
identified that an untrusted HTTP/capture reference could add an event index to
select stream data. Two focused regressions reproduced this bypass before the
final change. Transport/capture metadata now takes precedence regardless of that
index. The shipped validator never emits HTTP/capture assertions with an event
index, so actual valid writer output remains unchanged. No schema/versioned golden
or existing assertion expectation was changed. All intermediate runs are retained.

Ten negative variants cover request-only proof for all PASS checks, HTTP/body and
capture/body substitutions, message/response-metadata substitution, stream/request
proof, an unindexed event file, mixed valid/request references, nonstream/request
proof, and both transport event-index bypasses. Enclosing result/context hashes
remain coherent. All now lose verified quality and comparison/retest eligibility,
cannot claim recovery or pass evidence-inclusive export, and remain limited after
independently assembled ZIP import and repeated baseline reads. Input bytes remain
unchanged. Literal positive checks exercise the actual writer's metadata/body
selection and indexed failure-event references, without deriving expectations
from the shared helper. Healthy recovery, F05 metadata checks and both old capture
formats' cached-tail controls remain passing.

| Executed check | Observed result | Evidence under `artifacts/review-fixes-20261021/f06/` |
| --- | --- | --- |
| Initial core RED | 8 failures, 14 passed; no errors/skips | `red.log`, `red.xml` |
| Initial core after extraction | 35 passed | `green.log`, `green.xml` |
| Initial fast graph | All 8 gates passed on the intermediate source | `fast/check-result.json` |
| Added event-index bypass RED | 2 failures, 22 deselected; no errors/skips | `red-event.log`, `red-event.xml` |
| Final core including evidence/replay controls | 37 passed; no failures/errors/skips | `green-2.log`, `green-2.xml` |
| Final report/import/export/comparison/accounting/runner/review regressions | 102 passed; no failures/errors/skips | `related.log`, `related.xml` |
| Final fast graph | All 8 gates passed, unchanged source; 475 Python unit/harness and 20 Node tests | `fast-2/check-result.json`, JUnit files |
| Documentation contracts and links | Exit 0 | `documentation.log` |

Final fast observed the uncommitted patch on base
`12f9217ae44ff028db5ac0c80fc17209b2201658`, fingerprint
`8f501bbe8282195e311ea47128023c02c610ae7f20e22613dec22896a0bbfac5`.
Main record SHA-256:
`a8ce60a45483d44ea7d800b2a4051b839540d9f0994128f522e1dff1b3a22c9a`.
The exact source/test `correction.diff` has SHA-256
`faab5c111423783b6e40d89252240a6c1a786b9570471092712559665f21442e`.
`verify_observation.py` independently checks actual final JUnit cases, both RED
runs, executed gates and current source fingerprint, retaining a separate
`observed-summary.json`. Focused counts are not whole-stage acceptance counts.

This validates proof-file binding and existing location/hash checks; it does not
authenticate an archive's author or independently rerun validators to prove every
submitted assertion's truth. No broader trust-system claim is introduced. The
historical full-source record, bounded review and W2 handoff remain unchanged and
bound to their original sources. Current source still needs complete source and
updated image verification; remote CI and endpoint/client checks remain unrun.

After documentation checks, the container was restored to its original stopped
state. `container-final-state.json` records `exited`, `running=false`, exit code 0.
Stop after the local F06 commit with no test/build task running.
No replacement container/network/volume, remote write
or automatic follow-on verification/review/build is part of this turn.

## Full source verification after F05/F06 — 2026-10-21

The owner approved one full-source verification turn from clean
`cd955f78cd8ec0938455da1d7df37c2ef66712df`. No source, tests, harness, dependencies,
assertions or goldens changed. The existing Linux ARM64/Python 3.12.15 container
started from stopped; `uv sync --locked --offline` succeeded.

The first invocation exited before any check because its output directory had
already been created for the log, while the harness creates its output directory
exclusively. Its traceback remains `full.log`. The corrected invocation used a
fresh subdirectory, without deleting or replacing that failed attempt:

```sh
UV_OFFLINE=1 uv run --frozen python scripts/check.py --suite full \
  --out artifacts/review-fixes-20261021/full-cd955f7/run-1
```

The complete graph returned exit 1 after about 11.4 minutes. Twelve required gates
passed; the required integration gate was `blocked`, reason `timeout`, at
300.0526 seconds. It produced no `integration.xml`. The overall record correctly
reports `status=blocked` and `stage_readiness=incomplete`. No assertion failure is
visible in the partial integration log, but the cause of its runtime and the
outcome of its remaining cases are not established. This is not a passing run.

| Completed suite | Actual JUnit cases | Observation |
| --- | ---: | --- |
| Python unit/harness | 475 | Passed, no failures/errors/skips |
| Python acceptance | 84 | Passed, no failures/errors/skips |
| Installed-package | 5 | Passed, no failures/errors/skips |
| Node | 20 | Passed, no failures/errors/skips |
| Chromium | 78 | Passed, no failures/errors/skips |
| Integration | Unavailable | Timed out; no complete test report |

The twelve passing gates are lock, format, lint, strict type, architecture,
packaged schemas, unit/harness, frontend static, browser, acceptance, packaging
and documentation. No incomplete integration cases are counted as passed or
summed into a whole-source test total. Prior focused F05/F06 checks and the old
fully passing `9a30567` record do not replace this missing result.

Evidence root: `artifacts/review-fixes-20261021/full-cd955f7/`.
Authoritative record: `run-1/check-result.json`, SHA-256
`1f8a1011e14ec0045ecbb97031180dae383f6f28b6b9728238aaeae3b7ad2266`.
Unchanged source fingerprint:
`8f501bbe8282195e311ea47128023c02c610ae7f20e22613dec22896a0bbfac5`.
The actual command log is `full-run.log`; per-gate logs, completed JUnit reports
and browser artifacts remain under `run-1/`. `verify_observation.py` checks the
clean recorded Git identity, exact blocked gate, twelve executed passes, actual
completed test cases, absence of an integration report and current source
fingerprint. Its separate `observed-summary.json` retains the blocked status.

Next task: diagnose the integration runtime and determine whether its budget or
test organization needs a justified change, before another full-source run and
updated image acceptance. Do not silently raise limits, remove cases, weaken
assertions or relabel this timeout as PASS. No new broad review, Docker build,
remote CI, real endpoint/client workflow or independent review ran in this turn.
Old records and external not_run statuses remain unchanged.

The post-closeout documentation check passed. After documentation and observation
checks, the container was restored to its original stopped state;
`container-final-state.json` records `exited`, `running=false`, exit code 0.
Stop with a local documentation-only commit, without any test/build task left
running. No replacement container/network/volume or remote write is part of this turn.
