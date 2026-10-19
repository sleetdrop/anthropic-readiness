"""Documents preserve judgments while excluding private routing context."""

import json
from copy import deepcopy
from dataclasses import replace

import pytest

from anthropic_readiness.diagnostics.comparison import compare_assessments
from anthropic_readiness.diagnostics.contracts import validate_diagnostic
from anthropic_readiness.models import JsonObject, object_value
from anthropic_readiness.presentation import Locale, PresentationOptions
from anthropic_readiness.report_view import build_report_view
from tests.unit.test_diagnostic_comparison import facts
from tests.unit.test_report_view import source


def test_document_is_independent_checked_presentation_without_rejudgment() -> None:
    from anthropic_readiness.documents import build_document_view

    original = source()
    before = deepcopy(original)
    view = build_document_view(original).document
    validate_diagnostic(view, "document-view")
    assert view["presentation_version"] == "3.0"
    assert object_value(view["presentation"])["locale"] == "zh-CN"
    assert view["available_locales"] == ["zh-CN", "en"]
    value = object_value(view["facts"])
    assert object_value(value["summary"])["planned_cases"] == 3
    assert value["cases"] == build_report_view(original).document["cases"]
    assert original == before


@pytest.mark.parametrize("locale", ["zh-CN", "en"])
def test_private_route_and_auth_reference_do_not_enter_any_document_field(locale: Locale) -> None:
    from anthropic_readiness.documents import build_document_view

    original = source()
    assert original.result is not None
    result = replace(
        original.result,
        target={
            **original.result.target,
            "messages_url": "http://private-route.invalid/v1/messages",
            "auth": {"mode": "api_key", "credential_env": "PRIVATE_AUTH_REFERENCE"},
        },
    )
    original = replace(original, result=result)
    view = build_document_view(original, presentation=PresentationOptions(locale, "dark")).document
    encoded = json.dumps(view)
    assert "private-route.invalid" not in encoded
    assert "PRIVATE_AUTH_REFERENCE" not in encoded
    assert "messages_url" not in encoded
    assert object_value(view["facts"])["identity"]
    assert result.target["messages_url"] == "http://private-route.invalid/v1/messages"


def test_comparison_keeps_transitions_but_hides_context_values() -> None:
    from anthropic_readiness.documents import build_document_view

    original_source = source()
    assert original_source.result is not None
    before, after = facts("FAIL"), facts("PASS")
    after["source"] = {
        **object_value(after["source"]),
        "run_id": original_source.result.run_id,
        "assessment_id": original_source.result.assessment_id,
        "result_sha256": original_source.result_sha256,
    }

    before["target"] = {
        "name": "before",
        "messages_url": "http://old-private.invalid/v1/messages",
        "auth": {"mode": "api_key", "credential_env": "OLD_PRIVATE_AUTH"},
    }
    after["target"] = {
        "name": "after",
        "messages_url": "http://new-private.invalid/v1/messages",
        "auth": {"mode": "api_key", "credential_env": "NEW_PRIVATE_AUTH"},
    }
    comparison = compare_assessments(before, after)
    original = deepcopy(comparison.document)
    view = build_document_view(original_source, comparison=comparison).document
    assert object_value(view["comparison"])["summary"] == comparison.document["summary"]
    encoded = json.dumps(view)
    for private in (
        "old-private.invalid",
        "new-private.invalid",
        "OLD_PRIVATE_AUTH",
        "NEW_PRIVATE_AUTH",
    ):
        assert private not in encoded
    assert comparison.document == original


def test_projection_has_no_resource_io(monkeypatch: pytest.MonkeyPatch) -> None:
    from anthropic_readiness import schema
    from anthropic_readiness.documents import build_document_view

    original = source()

    def forbidden(name: str) -> JsonObject:
        raise AssertionError(name)

    monkeypatch.setattr(schema, "load_schema", forbidden)
    assert build_document_view(original).document


def test_foreign_comparison_cannot_be_presented_as_this_source() -> None:
    from anthropic_readiness.documents import build_document_view

    comparison = compare_assessments(facts("FAIL"), facts("PASS"))
    with pytest.raises(ValueError, match="document_comparison_source_mismatch"):
        build_document_view(source(), comparison=comparison)


def test_identical_field_excerpts_share_space_without_losing_case_evidence() -> None:
    from anthropic_readiness.documents import group_observations

    observations: list[JsonObject] = [
        {
            "case_id": "case-a",
            "expected_excerpt": '{"model":"requested"}',
            "actual_excerpt": '{"model":"observed"}',
            "reference": {"path": "evidence/a.json"},
        },
        {
            "case_id": "case-b",
            "expected_excerpt": '{"model":"requested"}',
            "actual_excerpt": '{"model":"observed"}',
            "reference": {"path": "evidence/b.json"},
        },
        {
            "case_id": "case-c",
            "expected_excerpt": '{"model":"requested"}',
            "actual_excerpt": "{}",
            "reference": {"path": "evidence/c.json"},
        },
    ]
    original = deepcopy(observations)
    groups = group_observations(observations)
    assert len(groups) == 2
    assert groups[0]["case_ids"] == ["case-a", "case-b"]
    assert [
        observation
        for group in groups
        for observation in (
            group["observations"] if isinstance(group["observations"], list) else []
        )
    ] == original
    assert observations == original


@pytest.mark.parametrize("reference", ["FAIL", "example"])
def test_credential_reference_collisions_preserve_verdicts_and_model_identity(
    reference: str,
) -> None:
    from anthropic_readiness.documents import build_document_view

    original = source()
    assert original.result is not None
    result = replace(
        original.result,
        target={**original.result.target, "auth": {"mode": "api_key", "credential_env": reference}},
    )
    original = replace(original, result=result)
    view = build_document_view(original).document
    value = object_value(view["facts"])
    assert value["cases"] == build_report_view(original).document["cases"]
    assert object_value(value["identity"])["model"] == result.target["model"]
    assert "credential_env" not in json.dumps(view)
    validate_diagnostic(view, "document-view")
