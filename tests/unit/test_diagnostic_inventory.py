"""Diagnostic categorization enriches, never rewrites, the frozen execution plan."""

from copy import deepcopy

import pytest

from anthropic_readiness.diagnostics.inventory import categorized_cases
from anthropic_readiness.models import JsonValue, object_value
from anthropic_readiness.requirements import CASE_IDS, assertion_plan


def test_categories_are_explicit_and_original_requirements_are_unchanged() -> None:
    original: JsonValue = [
        {
            "id": "ANT-MESSAGE-001",
            "version": 1,
            "required": True,
            "assertions": [
                {"id": "HTTP-STATUS", "version": 1, "required": True},
                {"id": "CAPTURE-COMPLETE", "version": 1, "required": True},
                {"id": "TASK-COMPLETE", "version": 1, "required": True},
            ],
        }
    ]
    before = deepcopy(original)
    result = categorized_cases(original)
    checks = object_value(result[0])["assertions"]
    assert isinstance(checks, list)
    assert checks == [
        {"id": "HTTP-STATUS", "version": 1, "required": True, "category": "protocol"},
        {"id": "CAPTURE-COMPLETE", "version": 1, "required": True, "category": "environment"},
        {"id": "TASK-COMPLETE", "version": 1, "required": True, "category": "behavior"},
    ]
    assert original == before


def test_all_installed_checks_have_categories_and_unknown_checks_are_rejected() -> None:
    for case_id in CASE_IDS:
        categorized_cases([{"id": case_id, "assertions": assertion_plan(case_id, True)}])
    with pytest.raises(ValueError, match="unsupported_diagnostic_assertion"):
        categorized_cases([{"assertions": [{"id": "UNREVIEWED-CHECK"}]}])
