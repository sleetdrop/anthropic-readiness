"""Operational composition preserves checked facts and observes no invented liveness."""

from copy import deepcopy

import pytest

from anthropic_readiness.diagnostics.contracts import validate_diagnostic
from anthropic_readiness.models import JsonObject, JsonValue, object_value
from anthropic_readiness.report_view import build_report_view
from anthropic_readiness.workbench import build_workbench_view
from tests.operation_fixtures import NOW, context
from tests.unit.test_report_view import source


def run_frame(state: str = "completed") -> JsonObject:
    original = source()
    assert original.result is not None
    result = original.result
    job: JsonObject = {
        "schema_version": "1.0",
        "id": result.run_id,
        "plan_id": "22222222-2222-4222-8222-222222222222",
        "state": state,
        "created_at": NOW,
        "updated_at": NOW,
        "last_sequence": 3,
        "result_path": "assessment/result.json" if state == "completed" else None,
    }
    return {
        "job": job,
        "execution": None,
        "plan": {"target": result.target, "plan": {**result.plan, "actual_requests": 0}},
        "report": build_report_view(original).document if state == "completed" else None,
        "evidence": [],
    }


def test_complete_workbench_is_a_separate_composition_without_rescoring() -> None:
    run = run_frame()
    before = deepcopy(run)
    worker: JsonObject = {"state": "not_running", "observed_at": NOW}
    value = build_workbench_view(run, worker_observation=worker).document
    validate_diagnostic(value, "workbench-view")
    assert value["facts"] == run["report"]
    assert value["job"] == run["job"]
    assert value["worker"] == worker
    assert value["comparison"] is None
    assert value["presentation_version"] == "1.0"
    assert run == before
    facts = object_value(value["facts"])
    cases = facts["cases"]
    assert isinstance(cases, list)
    assert all(
        object_value(object_value(case)["dimensions"])["client"] == "not_evaluated"
        for case in cases
    )


@pytest.mark.parametrize("state", ["queued", "running", "interrupted", "error"])
def test_missing_verified_records_keep_the_whole_plan_without_fake_timestamps(state: str) -> None:
    run = run_frame(state)
    value = build_workbench_view(
        run, worker_observation={"state": "unknown", "observed_at": None}
    ).document
    validate_diagnostic(value, "workbench-view")
    facts = object_value(value["facts"])
    summary = object_value(facts["summary"])
    assert summary["planned_cases"] == 3
    assert summary["completed_cases"] == summary["actual_requests"] == 0
    assert summary["started_at"] is summary["finished_at"] is summary["duration_ms"] is None
    assert facts["execution"] is None
    assert facts["source_result_sha256"] is None
    assert object_value(summary["counts"])["pending"] == 3


def test_recorded_upstream_activity_is_not_worker_observation_or_service_connectivity() -> None:
    run = run_frame("running")
    execution = context()
    run["execution"] = execution
    job = object_value(run["job"])
    job["id"] = execution["run_id"]
    run["job"] = job
    run["plan"] = {"target": execution["target"], "plan": execution["plan"]}
    worker: JsonObject = {"state": "not_running", "observed_at": "2026-10-19T10:00:00+00:00"}
    value = build_workbench_view(run, worker_observation=worker).document
    facts = object_value(value["facts"])
    assert object_value(facts["execution"])["updated_at"] == NOW
    assert value["worker"] == worker
    assert "connected" not in value


def test_mixed_projection_generation_cannot_be_displayed() -> None:
    run = run_frame()
    run["execution"] = context()
    with pytest.raises(ValueError, match="workbench_generation_mismatch"):
        build_workbench_view(run, worker_observation={"state": "unknown", "observed_at": None})


def test_presentation_choices_do_not_change_facts_or_semantic_generation() -> None:
    run = run_frame()
    worker: JsonObject = {"state": "unknown", "observed_at": None}
    initial = build_workbench_view(run, worker_observation=worker).document
    run["presentation"] = {"schema_version": "1.0", "locale": "en", "theme": "dark"}
    changed = build_workbench_view(run, worker_observation=worker).document
    assert initial["facts"] == changed["facts"]
    assert initial["generation"] == changed["generation"]
    assert object_value(changed["presentation"])["locale"] == "en"


def test_projection_performs_no_resource_io(monkeypatch: pytest.MonkeyPatch) -> None:
    from anthropic_readiness import report_models

    frames = [run_frame(), run_frame("queued")]

    def forbidden(name: str) -> JsonObject:
        raise AssertionError("workbench_projection_resource_io")

    monkeypatch.setattr(report_models, "load_schema", forbidden)
    for frame in frames:
        assert build_workbench_view(
            frame, worker_observation={"state": "unknown", "observed_at": None}
        ).document["facts"]


def test_comparison_groups_preserve_check_counts_case_overlap_and_raw_members() -> None:
    from anthropic_readiness.workbench import group_comparison

    pairs: list[JsonValue] = [
        {
            "case_id": "case-one",
            "assertion_id": "MSG-CORE",
            "transition": "recovered",
            "before": "FAIL",
            "after": "PASS",
        },
        {
            "case_id": "case-one",
            "assertion_id": "MSG-MODEL",
            "transition": "persistent",
            "before": "FAIL",
            "after": "FAIL",
        },
        {
            "case_id": "case-two",
            "assertion_id": "MSG-MODEL",
            "transition": "persistent",
            "before": "FAIL",
            "after": "FAIL",
        },
        {
            "case_id": "case-two",
            "assertion_id": "STR-STOP",
            "transition": "new_failure",
            "before": "PASS",
            "after": "FAIL",
        },
        {
            "case_id": "case-three",
            "assertion_id": "MSG-CORE",
            "transition": "gap",
            "before": "FAIL",
            "after": "missing",
        },
        {
            "case_id": "case-three",
            "assertion_id": "TOOL-NAME",
            "transition": "gap",
            "before": "PASS",
            "after": "missing",
        },
        {
            "case_id": "case-one",
            "assertion_id": "HTTP-STATUS",
            "transition": "passed_both",
            "before": "PASS",
            "after": "PASS",
        },
    ]
    original = deepcopy(pairs)
    groups = group_comparison({"pairs": list(pairs)})
    assert len(groups) == 4
    assert sum(int(str(group["check_count"])) for group in groups) == 6
    persistent = next(group for group in groups if group["transition"] == "persistent")
    assert persistent["family"] == "model"
    assert persistent["affected_cases"] == 2
    gap = next(group for group in groups if group["transition"] == "gap")
    assert gap["check_count"] == 2
    assert gap["affected_cases"] == 1
    assert gap["before_states"] == ["FAIL", "PASS"]
    assert gap["after_states"] == ["missing"]
    assert pairs == original
    assert group_comparison({"pairs": list(reversed(pairs))}) == groups
