# CI timing diagnosis

## Scope and conclusion

The owner requested investigation after one unchanged CI retry also failed.
Source baseline: `fe5e5017b63f32a914a2c8f659a8c69118c76e6c`. Product source,
tests, dependencies, workflows, assertions and timeouts were not changed. No new
remote job, real endpoint request or independent repository review ran.

Measured implementation overhead contributes to the timing failures: repeated
execution-identity construction and repeated JSON Schema meta-validation consume
most of the profiled comparison path. A slower CI environment exposes the limited
headroom of a composite 40-second browser test and the 300-second browser suite.
This is more specific than a transient runner/network explanation. It does not
prove a protocol/report-value defect or exclude every other performance cause.

## Evidence chain

1. The local passing full baseline took 230.25 seconds for 78 browser cases;
   its mixed-comparison case took 29.864 seconds. The first CI completed browser
   suite took 291.57 seconds and that case timed out at 40.374 seconds. The retry's
   completed browser suite took 281.71 seconds and the same case timed out at
   40.310 seconds. Other CI browser runs hit the 300-second whole-suite limit.
   These observations are across machines, not a controlled hardware benchmark.
2. In both failed traces, the test consumed approximately 38–39.5 seconds before
   waiting for export. That wait lasted approximately 0.8–2 seconds before the
   global deadline/teardown. Comparison page requests took about 3.2–6.7 seconds;
   export preview returned 200 in about 1.57 seconds. No content assertion failed.
   SSE response durations include intentional open-stream waiting and are not
   treated as CPU or network-outage evidence.
3. Read-only local Linux ARM64/Python 3.12 profiling used the exact synthetic
   before/after assessment files retained by the retry. One comparison called
   `installed_identity()` four times: two source facts, each computing identity
   directly and again through recipe binding. Its profile attributed about 1.42
   of 2.39 seconds to those calls and 0.57 seconds to schema checking/construction.
   Profiler overhead is substantial: these are attribution measurements, not
   normal request latency. The combined comparison/export profile shows the same
   hotspots. Comparison page composition also rereads baseline facts.
4. A separate existing integration case,
   `test_complete_response_proof_can_establish_recovery`, passed under profiling.
   Its profiled test body took 10.30 seconds; identity was constructed 18 times,
   consuming 6.45 seconds, and schema checking/construction ran 69 times for
   1.63 seconds. This confirms the same overhead in integration work; it does not
   extrapolate one case into an exact whole-suite saving.

Implementation locations:

- `diagnostics/service.py`: `compare_sources`, `source_facts` and repeated source reads.
- `diagnostics/recipes.py`: `validate_recipe_binding` computes installed identity again.
- `diagnostics/identity.py`: installed identity rebuilds its file/import/resource/
  dependency closure, parsing and walking source ASTs on every invocation.
- `json_validation.py`: `validate_document` rebuilds a checked validator, including
  meta-schema validation. The immutable operational/diagnostic adapters already
  reuse compiled schemas; generic result/target/capture reads do not.
- `web/workbench.py`: comparison composition obtains both a comparison and baseline
  facts separately, adding repeated work. Export preview also renders package files.

## Controlled diagnostic experiment

Only the disposable diagnostic process was patched, never tracked code. All modes
executed real comparison, source/evidence verification and export-file generation.
Each mode ran three times on the same synthetic input pair, in the same environment.
The baseline was warmed before measurement. The identity experiment recomputed a
real identity once per operation, not once for the entire process. Schema reuse
cached compiled validators by complete schema content, not document results.

| Experimental mode | Median seconds | Identity constructions per operation |
| --- | --- | --- |
| Current implementation | 0.9053 | 4 |
| Reuse schema compilation only | 0.7308 | 4 |
| One identity evaluation per operation only | 0.5605 | 1 |
| Both | 0.3848 | 1 |

Every comparison object, evidence-verification value and generated export file
matched byte-for-byte/digest-for-digest across all modes. Output digest:
`a7d2d26e1d72c0c36cb8a9b1f20d69d62180a5b7697e8b9e7379204888ad5fa5`.
All 699 retained fixture files were checked against their original artifact ZIP;
none changed. Source fingerprint remained
`8c93fbb11a42050d945a43ae29ca2b5751fac3575a6797d3788a554245ff9423`.

The approximately 57% saving establishes avoidable repeated work in this local
experiment. It is not a production patch, tamper-safety proof, full benchmark,
remote CI pass or prediction of remote timings. Fixed experiment order and three
samples limit the performance claim.

## Recommended bounded correction

Optimize redundant work before deciding on longer limits:

1. Reuse compilation of immutable packaged schemas while validating every incoming
   document in full. Do not cache evidence eligibility or document verdicts.
2. Reduce repeated identity/AST analysis while preserving detection of changed
   source bytes, module inventory, resources and dependency versions. A permanent
   process-wide identity result would hide changes and is not justified by this
   experiment. Evaluate content-keyed parsing and explicitly scoped reuse, with
   mutation/corruption regression coverage before implementation.
3. Re-measure the existing mixed-comparison browser case and representative
   integration cases with unchanged assertions and deadlines. If budget/test
   restructuring remains necessary, base it on the measured remaining cost and
   retain every existing behavior/evidence assertion.

No optimization has been implemented. A later correction needs meaningful failing
regressions, strict source/evidence semantics, appropriate full verification and
one new remote CI observation after a justified change. Do not keep retrying
unchanged code or treat this experiment as a green release.

## Retained observations

Ignored root: `artifacts/ci-timing-20261022/`. It contains raw pstats/text, the
controlled experiment and output digests, source pair, remote timing extraction,
one-case JUnit and original command logs. It references only synthetic public CI
artifacts. Original remote failed attempts remain under their separate roots.

| Record | SHA-256 |
| --- | --- |
| profile-summary.json | 4ea461cd72c6bc896b162dd67be3748d1cd3ed5095e681aaf83ead22f93d67a4 |
| controlled-work-summary.json | c3a4bcc673499a098dbb5b650150eeb768e3e7fc8fa31409944141636a351ffb |
| remote-timing-summary.json | 8bcec4fb7526fb87673179f69d85cdde4beeb3276293ce398953ac1ad027ccbb |
| integration-profile-summary.json | 509a79ccc7cd298c11bbb60cdbbeb5692c3435e28be7964333920678a8160e6c |
| evidence-case.xml | b7955928696a95f13781c75f25e9f8bd7310059ed170454a027287158bc05783 |

Linux documentation/evidence checks passed. The prepared developer container was
restored to stopped, exit 0; no diagnostic/test process remains running. Stop
after the local documentation commit. No remote write or new CI run is included.
