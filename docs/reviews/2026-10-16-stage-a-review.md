# Independent Stage A review

Reviewer: fresh-context gpt-6-astra, xhigh. Read-only whole-stage review of
`676f105203a50c270a43bad3d2ad3c824d7a88a2..ad4e131e6514438a00aca08c3f98a4a89ea16870`.
No implementer agents or second review. The reviewer independently ran the
existing 152 tests in the Linux Dev Container: 152 passed in 26.00 seconds.
No real endpoint, dependency download or remote publication was involved.

## Findings and author verification

No Critical findings. All six Important findings were reproduced by the author.
The first regression run produced nine failures and one legal control pass;
fixes were then checked against the same cases. Two profile identity edge cases
and one tool-JSON depth control were also observed failing before correction.

| Finding in reviewed revision | Final behavior | Regression |
| --- | --- | --- |
| Self-reduced basic profile could pass | Shared pure registry enforces complete case/assertion/version requirements; imported contract must match packaged immutable manifest; capture replay stays one explicit case | test_reduced_profile_and_assertion_contract_cannot_certify_pass; test_report_profile_identity_cannot_disagree_with_plan |
| Any redaction erased known lifecycle FAIL | Capture 1.1 binds a lifecycle projection digest before/after redaction and verifies it on replay; proven lifecycle assertions survive, uncertain body semantics remain indeterminate | test_transformed_replay_preserves_only_proven_structure, including structural-token redaction control |
| Deep JSON erased prior failure and bytes | Parser exhaustion is indeterminate, not a target syntax defect; previous assertions remain; sanitized capture persists before validation | test_deep_json_keeps_known_failure_and_persisted_capture; test_capture_is_retained_even_if_validator_crashes; test_tool_json_parser_limit_is_not_invalid_tool_input |
| Report trusted only top-level files | All assertion/precondition refs must belong to inventory and pass hash/event/pointer verification; missing/invalid evidence cannot be labeled verified | test_report_checks_assertion_refs_not_only_inventory, hash/event/pointer variants |
| Timeout UTF-8 prefix caused false FAIL | Framing finalization distinguishes EOF from interrupted capture; valid incomplete suffixes are not invalid bytes; completed and irrecoverably invalid controls remain distinct | test_timeout_utf8_prefix_is_not_a_proven_encoding_defect; test_legacy_partial_capture_rechecks_utf8_suffix; existing transport/stream suite |
| Wheel borrowed unrelated parent Git SHA | Git is consulted only for this module's proven source-checkout layout; installed code records null when provenance is unavailable | test_installed_layout_never_borrows_parent_repository_provenance; installed-wheel acceptance |

The reviewer called the README missing `--out` and incorrect status names Minor.
The author graded both Important: the primary onboarding command deterministically
failed, and the domain documentation gave readers/Agents incorrect enum names.
Both were corrected in the same pass; the complete README dry-run command is
executed in final validation. No deferred minors remain.

## Scope rulings

The reviewer set aside tool loops/parallel live cases (B); matrices and
repeat/retry/comparison/rescoring (later stages); real Claude Code/client readiness
(C); protocol-update Agent command and remote/registry/account setup (D or separate
authorization); and actual endpoint/remote CI/published-image outcomes (unrun).
The author retains each boundary and its cost in the implementation ledger.
Local synthetic acceptance cannot establish those capabilities or outcomes.

Capture writers now use schema 1.1 for the projection proof. Schema 1.0 captures
remain readable, including conservative transformed replay without such proof.
Historical files are untouched. The API rule bundle, prompts and required case
set are unchanged. The additive evidence format is versioned explicitly.

Final full/floor/image results and exact source/lock/contract fingerprints are
recorded in [the handoff manifest](../harness/handoff.json). The independent review
found issues; author RED-to-GREEN verification, rather than a second review, closes
them. The review is not a service compatibility certificate.
