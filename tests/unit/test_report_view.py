"""Visual projection counts original facts without scoring or invented timing."""

from copy import deepcopy
from dataclasses import replace

import pytest

from anthropic_readiness.models import JsonObject, object_value
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.report_models import ReportSource, ReportView
from anthropic_readiness.report_view import build_report_view
from tests.acceptance.test_reports import mixed


def source() -> ReportSource:
    result = mixed()
    return ReportSource(
        result,
        "a" * 64,
        result.cases,
        None,
        {"status": "missing_or_invalid", "errors": ["missing_fixture_evidence"]},
        (),
        result.plan,
    )


def test_matrix_counts_all_original_states_without_rescoring() -> None:
    original = source()
    before = deepcopy(original.result.to_json()) if original.result else {}
    view = build_report_view(original).document
    groups = view.get("groups")
    assert isinstance(groups, list)
    assert len(groups) == 2
    streaming = next(
        object_value(group) for group in groups if object_value(group)["key"] == "streaming"
    )
    counts = object_value(object_value(streaming["dimensions"])["protocol"])
    assert counts == {
        "PASS": 1,
        "FAIL": 1,
        "INDETERMINATE": 0,
        "BLOCKED": 0,
        "SKIP": 0,
        "pending": 0,
        "running": 0,
        "not_evaluated": 0,
    }
    assert object_value(view["summary"])["planned_cases"] == 3
    for finding in objects(view["findings"]):
        members = finding["cases"]
        assert isinstance(members, list)
        assert finding["affected_cases"] == len({str(value) for value in members})
    assert original.result is not None
    assert original.result.to_json() == before


@pytest.mark.parametrize("state", ["PASS", "FAIL", "INDETERMINATE", "BLOCKED", "SKIP"])
def test_distribution_preserves_each_original_state(state: str) -> None:
    original = source()
    assert original.result is not None
    cases: tuple[JsonObject, ...] = tuple(
        {**case, "status": state} for case in original.case_records
    )
    projected = build_report_view(
        replace(original, result=replace(original.result, cases=cases), case_records=cases)
    ).document
    summary = projected.get("summary")
    assert isinstance(summary, dict)
    assert object_value(summary["counts"])[state] == 3
    assert [case["status"] for case in objects(projected["cases"])] == [state] * 3


def test_old_result_has_no_fabricated_timeline() -> None:
    view = build_report_view(source()).document
    figures = view.get("figures")
    assert isinstance(figures, list)
    assert figures
    assert all(object_value(figure)["kind"] != "timeline" for figure in figures)
    duration = next(
        object_value(figure) for figure in figures if object_value(figure)["kind"] == "duration"
    )
    assert "时序" in str(duration["caption"])
    assert view["execution"] is None
    assert {object_value(figure)["id"] for figure in figures} == {
        "fig-capabilities",
        "fig-status",
        "fig-impact",
        "fig-timing",
    }


def test_report_view_rejects_undeclared_contract_fields() -> None:
    with pytest.raises(ValueError, match=r"^schema:"):
        ReportView({"credential": "synthetic-secret"})


def test_projection_preserves_provenance_and_original_assertion_references() -> None:
    original = source()
    view = build_report_view(original).document
    provenance = view.get("provenance")
    assert isinstance(provenance, dict)
    assert original.result is not None
    assert provenance["assessment_id"] == original.result.assessment_id
    assert provenance["contract"] == original.result.contract
    assert provenance["report_context"] == original.result.report_context
    findings = view["findings"]
    assert isinstance(findings, list)
    assert all(
        "assertion_id" in object_value(finding) and "reason_code" in object_value(finding)
        for finding in findings
    )


def test_capability_groups_match_the_installed_case_catalog() -> None:
    from anthropic_readiness.cases import list_cases
    from anthropic_readiness.report_view import GROUPS

    grouped = [case_id for _, _, case_ids in GROUPS for case_id in case_ids]
    assert set(grouped) == {case.id for case in list_cases()}
    assert len(grouped) == 5
    forced = next(title for key, title, _ in GROUPS if key == "forced_tool")
    assert "非完整工具闭环" in forced


def test_projection_never_loads_resources_or_performs_io(monkeypatch: pytest.MonkeyPatch) -> None:
    from anthropic_readiness import report_models
    from anthropic_readiness.operations import contracts

    original = source()
    contracts._validator.cache_clear()

    def unavailable(name: str) -> JsonObject:
        raise AssertionError("projection attempted resource I/O")

    monkeypatch.setattr(contracts, "load_schema", unavailable)
    monkeypatch.setattr(report_models, "load_schema", unavailable)
    assert build_report_view(original).document["presentation_version"] == "2.0"
