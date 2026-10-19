"""Paired check observations never hide changed conditions or verification gaps."""

from copy import deepcopy

import pytest

from anthropic_readiness.diagnostics.comparison import compare_assessments
from anthropic_readiness.diagnostics.contracts import validate_diagnostic
from anthropic_readiness.models import JsonObject, JsonValue, object_value
from tests.diagnostic_contract_fixtures import contract_documents


def facts(status: str) -> JsonObject:
    documents = contract_documents()
    recipe = documents["retest-recipe"]
    return {
        "schema_version": "1.0",
        "source": object_value(documents["diagnostic-package"]["source"]),
        "plan": {"cases": recipe["cases"]},
        "recipe": recipe,
        "context": documents["assessment-context"],
        "target": {"name": "synthetic", "messages_url": "http://synthetic.invalid/v1/messages"},
        "cases": [{"id": "ANT-MESSAGE-001", "version": 1, "required": True, "status": status}],
        "checks": [
            {
                "case_id": "ANT-MESSAGE-001",
                "case_version": 1,
                "assertion_id": "MSG-CORE",
                "assertion_version": 1,
                "category": "protocol",
                "required": True,
                "status": status,
                "reason": "synthetic_observation",
                "expected": "required fields",
                "actual": "synthetic data",
                "evidence_refs": [],
            }
        ],
        "eligibility": {"read": True, "retest": True, "compare": True, "reasons": []},
        "evidence_verification": {"status": "verified", "errors": [], "delivery": "external_files"},
    }


def rows(value: JsonValue) -> list[JsonObject]:
    assert isinstance(value, list)
    return [object_value(item) for item in value]


@pytest.mark.parametrize(
    ("before_status", "after_status", "transition"),
    [
        ("FAIL", "PASS", "recovered"),
        ("FAIL", "FAIL", "persistent"),
        ("PASS", "FAIL", "new_failure"),
        ("PASS", "PASS", "passed_both"),
        ("missing", "PASS", "newly_evaluated"),
        ("SKIP", "FAIL", "newly_evaluated"),
        ("FAIL", "missing", "gap"),
        ("PASS", "INDETERMINATE", "gap"),
        ("FAIL", "BLOCKED", "gap"),
        ("PASS", "SKIP", "gap"),
    ],
)
def test_transition_table(before_status: str, after_status: str, transition: str) -> None:
    before, after = facts(before_status), facts(after_status)
    originals = deepcopy((before, after))
    comparison = compare_assessments(before, after).document
    validate_diagnostic(comparison, "comparison")
    assert rows(comparison["pairs"])[0]["transition"] == transition
    assert object_value(comparison["summary"])[transition] == 1
    assert comparison["all_previous_failures_passed"] is (transition == "recovered")
    assert (before, after) == originals


@pytest.mark.parametrize("field", ["model", "protocol", "limits", "capabilities", "profiles"])
def test_changed_conditions_have_no_recovery_badge(field: str) -> None:
    before, after = facts("FAIL"), facts("PASS")
    recipe = object_value(after["recipe"])
    if field == "profiles":
        profile = rows(recipe[field])[0]
        profile["version"] = 2
        recipe[field] = [profile]
    else:
        changed = object_value(recipe[field])
        changes: dict[str, tuple[str, JsonValue]] = {
            "model": ("requested", "changed-model"),
            "protocol": ("api_version", "2099-01-01"),
            "limits": ("max_tokens", 256),
            "capabilities": ("tools", False),
        }
        key, value = changes[field]
        changed[key] = value
        recipe[field] = changed
    after["recipe"] = recipe
    value = compare_assessments(before, after).document
    assert value["comparable"] is False
    assert value["all_previous_failures_passed"] is False
    assert object_value(value["summary"])["recovered"] == 0
    assert any(row["field"] == field for row in rows(value["condition_changes"]))


def test_same_label_changed_implementation_incomparable() -> None:
    before, after = facts("FAIL"), facts("PASS")
    recipe = object_value(after["recipe"])
    identity = object_value(recipe["implementation"])
    identity["file_hashes"] = {"validation/messages.py": "b" * 64}
    recipe["implementation"] = identity
    after["recipe"] = recipe
    value = compare_assessments(before, after).document
    assert value["comparable"] is False
    assert not value["pairs"]
    assert len(rows(value["unmatched_before"])) == len(rows(value["unmatched_after"])) == 1
    assert object_value(value["summary"])["recovered"] == 0


def test_omitted_evidence_no_verified_headline() -> None:
    before, after = facts("FAIL"), facts("PASS")
    before["eligibility"] = {
        "read": True,
        "retest": False,
        "compare": False,
        "reasons": ["diagnostic_evidence_unavailable"],
    }
    before["evidence_verification"] = {
        "status": "missing_or_invalid",
        "errors": ["missing"],
        "delivery": "omitted",
    }
    value = compare_assessments(before, after).document
    assert value["comparable"] is False
    assert value["all_previous_failures_passed"] is False
    assert rows(value["pairs"])[0]["transition"] == "incomparable"
    assert rows(value["pairs"])[0]["before"] == "FAIL"
    assert "diagnostic_evidence_unavailable" in str(value["reasons"])


def test_missing_required_check_not_hidden_in_denominator() -> None:
    before, after = facts("FAIL"), facts("PASS")
    after["checks"] = []
    after["cases"] = []
    value = compare_assessments(before, after).document
    assert value["coverage"] == {
        "before_checks": 1,
        "after_checks": 0,
        "matched_checks": 0,
        "missing_required_checks": 1,
        "before_cases": 1,
        "after_cases": 0,
        "matched_cases": 0,
        "missing_required_cases": 1,
    }
    assert len(rows(value["unmatched_before"])) == 1
    assert value["all_previous_failures_passed"] is False


def test_unmatched_new_checks_are_enumerated_without_regression_claim() -> None:
    before, after = facts("FAIL"), facts("FAIL")
    checks = rows(after["checks"])
    checks[0]["assertion_version"] = 2
    after["checks"] = list(checks)
    value = compare_assessments(before, after).document
    assert not value["pairs"]
    assert len(rows(value["unmatched_before"])) == len(rows(value["unmatched_after"])) == 1
    assert object_value(value["summary"])["new_failure"] == 0


def test_new_failure_remains_beside_recovery_and_blocks_clean_headline() -> None:
    before, after = facts("FAIL"), facts("PASS")
    before_extra = {**rows(before["checks"])[0], "assertion_id": "MSG-MODEL", "status": "PASS"}
    after_extra = {**rows(after["checks"])[0], "assertion_id": "MSG-MODEL", "status": "FAIL"}
    before["checks"] = [*rows(before["checks"]), before_extra]
    after["checks"] = [*rows(after["checks"]), after_extra]
    value = compare_assessments(before, after).document
    assert object_value(value["summary"])["recovered"] == 1
    assert object_value(value["summary"])["new_failure"] == 1
    assert value["all_previous_failures_passed"] is False


def test_endpoint_change_is_declared_and_presentation_is_irrelevant() -> None:
    before, after = facts("FAIL"), facts("PASS")
    after["target"] = {"name": "fixed", "messages_url": "http://fixed.invalid/v1/messages"}
    first = compare_assessments(before, after).document
    after["presentation"] = {"locale": "en", "theme": "dark"}
    assert compare_assessments(before, after).document == first
    assert first["comparable"] is True
    assert {row["field"] for row in rows(first["condition_changes"])} == {"name", "messages_url"}


def test_checked_fact_projection_has_closed_packaged_schema() -> None:
    from anthropic_readiness.diagnostics.contracts import validate_projection

    value = facts("FAIL")
    validate_projection(value, "diagnostic-comparison-facts")
    with pytest.raises(ValueError, match="schema"):
        validate_projection({**value, "uploaded_html": "untrusted"}, "diagnostic-comparison-facts")
    checks = rows(value["checks"])
    checks[0]["required"] = "yes"
    value["checks"] = list(checks)
    with pytest.raises(ValueError, match="schema"):
        validate_projection(value, "diagnostic-comparison-facts")


def test_evidence_omission_cannot_borrow_a_prior_verification_status() -> None:
    before, after = facts("FAIL"), facts("PASS")
    before["evidence_verification"] = {"status": "verified", "errors": [], "delivery": "omitted"}
    value = compare_assessments(before, after).document
    assert value["comparable"] is False
    assert value["all_previous_failures_passed"] is False


def test_unmatched_unresolved_check_is_a_gap_not_newly_evaluated() -> None:
    before, after = facts("PASS"), facts("BLOCKED")
    before["checks"] = []
    value = compare_assessments(before, after).document
    assert object_value(value["summary"])["gap"] == 1
    assert object_value(value["summary"])["newly_evaluated"] == 0
