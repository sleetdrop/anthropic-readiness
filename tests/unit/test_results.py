"""Required coverage and observed failures control readiness."""

from anthropic_readiness.models import Status, aggregate_required
from anthropic_readiness.schema import validate_result_semantics


def test_fail_survives_incomplete_capture() -> None:
    assert aggregate_required([Status.PASS, Status.FAIL, Status.INDETERMINATE]) == Status.FAIL


def test_empty_required_set_never_passes() -> None:
    assert aggregate_required([]) == Status.INDETERMINATE


def test_missing_required_case_is_incomplete() -> None:
    errors = validate_result_semantics(
        {"plan": {"cases": ["missing"]}, "cases": [], "profiles": []}
    )
    assert "missing_case:missing" in errors


def test_precedence() -> None:
    ordered = [Status.FAIL, Status.BLOCKED, Status.INDETERMINATE, Status.SKIP, Status.PASS]
    for index, expected in enumerate(ordered):
        assert aggregate_required(ordered[index:]) == expected


def test_mixed_result_roundtrip_and_inconsistent_readiness() -> None:
    import json
    from dataclasses import replace

    from anthropic_readiness.models import AssertionResult, JsonObject, RunResult, object_value
    from anthropic_readiness.schema import load_schema, validate_document

    assertion = AssertionResult("precondition", "environment", Status.BLOCKED, "missing_key")
    case: JsonObject = {
        "id": "example",
        "version": 1,
        "required": True,
        "status": "BLOCKED",
        "preconditions": [assertion.to_json()],
        "attempts": [],
        "dimensions": {},
    }
    profile: JsonObject = {
        "id": "basic",
        "version": 1,
        "cases": ["example"],
        "readiness": "incomplete",
    }
    plan: JsonObject = {
        "cases": [
            {
                "id": "example",
                "version": 1,
                "required": True,
                "assertions": [{"id": "TASK-COMPLETE", "version": 1, "required": True}],
            }
        ],
        "profiles": [{"id": "basic", "version": 1, "cases": ["example"]}],
        "actual_requests": 0,
        "planned_requests": 1,
        "limits": {},
        "repeat": 1,
        "retry": 0,
        "config_fingerprint": "synthetic",
        "test_fingerprint": "synthetic",
    }
    result = RunResult(
        "run",
        "assessment",
        "replay",
        "2026-10-15",
        "2026-10-15",
        {},
        {},
        {},
        {},
        plan,
        (profile,),
        (case,),
        (),
        {},
        ("Synthetic data",),
    )
    document = object_value(json.loads(json.dumps(result.to_json())))
    validate_document(document, load_schema("result"))
    assert validate_result_semantics(document) == []
    inconsistent: JsonObject = {**profile, "readiness": "passed"}
    altered = replace(result, profiles=(inconsistent,)).to_json()
    validate_document(altered, load_schema("result"))
    assert validate_result_semantics(altered) == ["profile_readiness:basic"]
