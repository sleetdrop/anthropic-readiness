# llm-comply maturity and replacement assessment

Date: 2026-11-02 (Asia/Shanghai). Purpose: assess whether the existing candidate is
mature enough to replace this project, rather than infer maturity from its existence
or popularity. This is a compatibility/correctness review, not a security audit.

## Recommendation

Do not treat llm-comply as an exhaustive conformance authority. It is an actively
developed early utility with useful breadth and a usable CLI/Web surface, but
reproduced blind spots affect the meaning of its passing verdicts for our purpose.
The previous research established category existence, not a mature replacement;
the direct jump from those facts to assured replacement was too strong.

Nevertheless, do not restart our full independent product implementation now.
Retain this repository stopped, with its evidence and stricter rule controls.
Prefer adopting/contributing to, or narrowly forking, the candidate and correcting
its assessment semantics. That is an economic recommendation, not proof that a fork
has already met the product goal. Our current Node product also has only five cases,
no new GUI and unfinished version/client support. Finding defects in another tool
does not establish that our independent development route will deliver better value.

An independent continuation would need a concrete outcome that cannot reasonably
be achieved by extending that base, such as version-specific conformance/replay
requiring a substantially different result/evidence model. No implementation,
fork or expanded live trial is authorized or started by this analysis.

## Revision and inspection boundary

- Repository head inspected: 78421338385e69f6ae2b055074d03be2ff8739a4, committed
  2026-10-22. Pin all source links below to that revision.
- PyPI/GitHub latest release observed: 0.5.0, 2026-09-12. Head is 109 commits ahead
  of that release. Release documentation lists nine Anthropic cases; the actual
  inspected head contains 19. Installing the release does not establish head features.
- Repository metadata observed: four stars, zero forks. PyPI lists one maintainer
  and an Alpha classifier. These are maintenance/adoption signals, not correctness
  scores, nor proof that nobody else uses or reviews the code.
- Read source, workflows, bundled manifest, recent issues/PRs and CI results. Did
  not infer current defects from stale unchecked issue boxes; tested head paths.
- Downloaded selected pinned source into a disposable directory. Used an existing
  local Python/jsonschema installation solely for offline candidate evaluation;
  added no dependency or Python requirement to our active Node application.
- No third-party installation, network test peer, real model/API request, browser
  usability test or complete upstream test suite execution. Transport was replaced
  by deterministic in-memory return values during probes.

## Maturity dimensions

| Dimension | Evidence and judgment |
| --- | --- |
| Packaging and usability | Published wheel/releases, local CLI/Web and progress exist. A real usable utility, rather than just an idea. GUI usability was not exercised here. |
| Release discipline | Significant head/release gap and Alpha designation. Current source improvements are not all in the last packaged release. |
| Engineering checks | Head CI succeeded on 2026-10-22; workflow runs lint and Python 3.10-3.13 checks, schema/CLI/validator/fixture scripts and pytest. Meaningful work exists beyond listing cases. No claim of full correctness follows from green CI. |
| Protocol verdict accuracy | Counterexamples below pass through real selected runner paths; unsuitable as the sole strict conformance verdict. |
| Self-hosted applicability | Custom URLs/models/headers work by design; thinking probe skips non-Claude names. Capability inference by name is inadequate for arbitrary compatible APIs. |
| Evidence/reporting | CLI JSON serializes statuses/errors/warnings, omitting request/response/events even when captured in verbose mode. Source objects/UI details exist, but this is not a portable raw evidence archive. |
| Version maintenance | A hashed manifest and refresh/check mechanisms exist. Anthropic spec version is recorded as unknown; custom API headers do not establish a selectable version-specific rules matrix. |
| Maintenance sustainability | Development and public checks are visible; independent adoption and a broad maintainer base were not established. Low stars alone do not justify rejection. |

The scheduled spec-update run on 2026-10-26 failed after refresh at validation:
the Google Interactions schema-count assertion failed and the PR step was skipped.
This is not an Anthropic network failure or proof that the shipped snapshot is
broken. It demonstrates that cross-format refresh can block publication of an
update; unattended reliable protocol maintenance has not been established.

## Reproduced offline behavior at head

Used actual candidate test definitions and TestRunner with synthetic transport.
The selected SSE/error tests disable schema validation in their own definitions;
SpecLoader() therefore needs no bundled schema for these paths. No validator,
test setting or assertion was weakened for these probes. Valid stream passed;
removing its message_stop failed, confirming that the normal runner was active.

| Input / probe | Actual candidate result | Assessment |
| --- | --- | --- |
| Legal text stream | PASSED | Positive control. |
| Same stream without message_stop | FAILED | Negative control detected. |
| Repeated message_start | PASSED | Missed lifecycle defect. |
| Text delta targeting unopened block index 99 | PASSED | Missed event/index defect. |
| Additional malformed JSON event with the parser's _parse_error marker | PASSED | Selected streaming path misses the recorded parse error. |
| Streaming usage output_tokens is a string | PASSED | Usage probe checks presence rather than numeric shape. |
| HTTP400 body with only an unrelated key | PASSED | Invalid error envelope is not checked by the error case. |
| Thinking probe using a non-Claude model name | SKIPPED | The model-name heuristic prevents capability assessment. |
| Wrong answer to system/multi-turn/tool-result prompts | No semantic-validator errors | Semantic checks do not prove instruction/context/result consumption. Only the semantic functions were exercised for these rows, not full response schemas. |
| Verbose successful stream serialized through to_dict | Captured request/events omitted | Confirmed CLI JSON evidence limitation; does not mean the Web UI has no details. |

The tool-result test supplies a fixed fabricated assistant tool call in one request;
it does not execute an observed first call and feed that returned call back. Its
positive result therefore establishes acceptance of that history shape, not a full
fresh end-to-end tool round trip. These concrete boundaries matter more than a
nineteen-case headline. They do not imply every case is ineffective.

## Evidence and primary sources

Reproducer, copied source and output remain ignored under
artifacts/llm-comply-maturity-20261102/. Run probe.py with a Python environment
containing jsonschema to reproduce the offline observations; network is stubbed.
This artifact is not a new product test harness or live endpoint outcome.

- [Release metadata](https://pypi.org/project/llm-comply/)
- [Release-to-head comparison](https://github.com/Oaklight/llm-comply/compare/v0.5.0...78421338385e69f6ae2b055074d03be2ff8739a4)
- [Test definitions](https://github.com/Oaklight/llm-comply/blob/78421338385e69f6ae2b055074d03be2ff8739a4/src/llm_comply/tests/anthropic.py)
- [Validators](https://github.com/Oaklight/llm-comply/blob/78421338385e69f6ae2b055074d03be2ff8739a4/src/llm_comply/validators.py)
- [Runner](https://github.com/Oaklight/llm-comply/blob/78421338385e69f6ae2b055074d03be2ff8739a4/src/llm_comply/runner.py)
- [Result serialization](https://github.com/Oaklight/llm-comply/blob/78421338385e69f6ae2b055074d03be2ff8739a4/src/llm_comply/result.py)
- [Spec manifest](https://github.com/Oaklight/llm-comply/blob/78421338385e69f6ae2b055074d03be2ff8739a4/src/llm_comply/specs/manifest.json)
- [Passing head CI](https://github.com/Oaklight/llm-comply/actions/runs/39753390126)
- [Failed scheduled refresh and validation log](https://github.com/Oaklight/llm-comply/actions/runs/40306470745/job/121516704223)

No remote publication, issue report or upstream modification was made. Project
development remains stopped pending the owner's choice; this assessment alone
does not resume it or delete/archive the existing work.
