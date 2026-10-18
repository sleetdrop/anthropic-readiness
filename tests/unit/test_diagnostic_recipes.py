"""Portable recipes regenerate installed cases; imported bodies are never executed."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from anthropic_readiness.application import build_plan, prepare_assessment
from anthropic_readiness.config import fingerprint, load_target
from anthropic_readiness.diagnostics import recipes
from anthropic_readiness.diagnostics.context import context_for_plan
from anthropic_readiness.diagnostics.identity import installed_identity
from anthropic_readiness.diagnostics.models import ImplementationIdentity, RetestRecipe
from anthropic_readiness.diagnostics.recipes import (
    build_recipe,
    prepare_retest,
    validate_recipe_binding,
)
from anthropic_readiness.diagnostics.reduction import baseline_eligibility
from anthropic_readiness.evidence import json_bytes
from anthropic_readiness.models import EvidenceRef, JsonObject, object_value, strict_json
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.report_sources import load_report_source
from anthropic_readiness.runner import RunPlan, execute_run
from tests.acceptance.test_runner import FixtureTransport

ROOT = Path(__file__).resolve().parents[2]
PROFILES = ("anthropic-basic", "anthropic-tools-smoke")


def plan_fixture() -> RunPlan:
    return build_plan(load_target(ROOT / "examples/target.yaml").to_json(), PROFILES)


def resign(document: JsonObject) -> RetestRecipe:
    document["content_sha256"] = fingerprint(
        {key: value for key, value in document.items() if key != "content_sha256"}
    )
    return RetestRecipe(document)


def test_recipe_contains_no_endpoint_or_auth() -> None:
    plan = plan_fixture()
    plan = replace(
        plan,
        target=replace(plan.target, auth_mode="api_key", credential_env="PRIVATE_TOKEN_REFERENCE"),
    )
    recipe = build_recipe(plan, installed_identity())
    serialized = json.dumps(recipe.document)
    for private in (
        plan.target.messages_url,
        "credential_env",
        "messages_url",
        '"auth"',
        "PRIVATE_TOKEN_REFERENCE",
    ):
        assert private not in serialized
    requests = objects(recipe.document["requests"])
    assert len(requests) == 4
    assert requests[0]["body"] == {
        "model": "example-model",
        "max_tokens": 512,
        "stream": False,
        "messages": [{"role": "user", "content": "Say hello in one short sentence."}],
    }
    assert recipe.document["repeat"] == 1
    assert recipe.document["retry"] == 0
    assert all(
        check["required"] is True
        for case in objects(recipe.document["cases"])
        for check in objects(case["assertions"])
    )


def test_retest_preserves_all_profiles_and_required_cases() -> None:
    plan = plan_fixture()
    recipe = build_recipe(plan, installed_identity())
    target = {**plan.target.to_json(), "messages_url": "http://127.0.0.1:9000/v1/messages"}
    retest, differences = prepare_retest(recipe, target, installed_identity())
    assert retest.profiles == PROFILES
    assert [case.id for case in retest.cases] == [case.id for case in plan.cases]
    assert retest.to_json()["cases"] == plan.to_json()["cases"]
    assert differences["comparable"] is True
    assert all(change["kind"] == "context" for change in objects(differences["changes"]))
    assert recipe.document == build_recipe(plan, installed_identity()).document


def test_missing_revision_never_selects_latest() -> None:
    plan = plan_fixture()
    value = deepcopy(build_recipe(plan, installed_identity()).document)
    value["contract"] = {**object_value(value["contract"]), "revision": "missing-99"}
    with pytest.raises(ValueError, match="unsupported_contract"):
        prepare_retest(resign(value), plan.target.to_json(), installed_identity())


@pytest.mark.parametrize("field", ["model", "response_model_aliases", "limits", "capabilities"])
def test_changed_alias_model_or_limit_is_declared(field: str) -> None:
    plan = plan_fixture()
    target = plan.target.to_json()
    if field == "model":
        target[field] = "different-model"
    elif field == "response_model_aliases":
        target[field] = ["declared-alias"]
    elif field == "limits":
        target[field] = {**object_value(target[field]), "max_tokens": 256}
    else:
        target[field] = {**object_value(target[field]), "streaming": False, "tools": False}
    retest, differences = prepare_retest(
        build_recipe(plan, installed_identity()), target, installed_identity()
    )
    assert len(retest.cases) == 4
    assert differences["comparable"] is False
    semantic = [
        change for change in objects(differences["changes"]) if change["kind"] == "semantic"
    ]
    assert semantic
    assert all(change["before"] != change["after"] for change in semantic)
    assert differences["reasons"] == ["semantic_conditions_changed"]


def test_redacted_semantic_input_blocks_exact_retest() -> None:
    plan = plan_fixture()
    value = deepcopy(build_recipe(plan, installed_identity()).document)
    requests = objects(value["requests"])
    requests[0]["body"] = {**object_value(requests[0]["body"]), "model": "[REDACTED]"}
    requests[0]["sha256"] = fingerprint(
        {key: item for key, item in requests[0].items() if key not in {"case_id", "sha256"}}
    )
    value["requests"] = list(requests)
    with pytest.raises(ValueError, match="diagnostic_recipe_regeneration"):
        prepare_retest(resign(value), plan.target.to_json(), installed_identity())


def test_preview_and_rebinding_send_no_requests_and_do_not_drop_budgeted_cases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("planning_must_not_send")

    monkeypatch.setattr("anthropic_readiness.transport.HttpTransport.send", forbidden)
    plan, context = prepare_assessment(plan_fixture().target.to_json(), PROFILES)
    assert context.document["run_id"] is None
    recipe = RetestRecipe(object_value(context.document["recipe"]))
    prepare_retest(recipe, plan.target.to_json(), installed_identity())
    small = plan.target.to_json()
    small["limits"] = {**object_value(small["limits"]), "max_requests": 3}
    with pytest.raises(ValueError, match="request_budget_insufficient"):
        prepare_retest(recipe, small, installed_identity())


def test_identity_mismatch_blocks_same_test() -> None:
    plan = plan_fixture()
    current = deepcopy(installed_identity().document)
    current["dependencies"] = {**object_value(current["dependencies"]), "httpx": "999.0"}
    current["content_sha256"] = fingerprint(
        {key: value for key, value in current.items() if key != "content_sha256"}
    )
    with pytest.raises(ValueError, match="dependency_versions_changed"):
        prepare_retest(
            build_recipe(plan, installed_identity()),
            plan.target.to_json(),
            ImplementationIdentity(current),
        )


def test_binding_checks_actual_result_plan_and_target(tmp_path: Path) -> None:
    plan = plan_fixture()
    recipe = build_recipe(plan, installed_identity())
    output = tmp_path / "original"
    execute_run(plan, FixtureTransport(), output)
    source = load_report_source(output)
    assert validate_recipe_binding(recipe, source) == ()
    altered = replace(source, plan={**source.plan, "retry": 1})
    assert "diagnostic_source_plan_mismatch" in validate_recipe_binding(recipe, altered)
    value = deepcopy(recipe.document)
    value["model"] = {**object_value(value["model"]), "requested": "another-model"}
    assert validate_recipe_binding(resign(value), source)


def test_recipe_keeps_skipped_cases_and_full_retest_scope(tmp_path: Path) -> None:
    plan = plan_fixture()
    target = plan.target.to_json()
    target["capabilities"] = {
        **object_value(target["capabilities"]),
        "streaming": False,
        "tools": False,
    }
    excluded = build_plan(target, PROFILES)
    output = tmp_path / "excluded"
    result = execute_run(excluded, FixtureTransport(), output)
    assert [case["status"] for case in result.cases] == ["PASS", "SKIP", "SKIP", "SKIP"]
    recipe = build_recipe(excluded, installed_identity())
    assert validate_recipe_binding(recipe, load_report_source(output)) == ()
    retest, _ = prepare_retest(recipe, target, installed_identity())
    assert len(retest.cases) == 4


def test_eligibility_requires_positive_proof_and_preserves_reason_codes() -> None:
    verified: JsonObject = {
        "source_valid": True,
        "complete": True,
        "recipe_valid": True,
        "recipe_bound": True,
        "context_verified": True,
        "evidence_verified": True,
        "identity_reasons": [],
    }
    assert baseline_eligibility(verified) == {
        "read": True,
        "retest": True,
        "compare": True,
        "reasons": [],
    }
    legacy = baseline_eligibility({"source_valid": True})
    assert legacy["read"] is True
    assert legacy["retest"] is False
    assert legacy["compare"] is False
    omitted = baseline_eligibility({**verified, "evidence_verified": False})
    assert omitted["compare"] is False
    mismatched = baseline_eligibility({**verified, "identity_reasons": ["python_runtime_changed"]})
    assert mismatched["retest"] is False
    reasons = mismatched["reasons"]
    assert isinstance(reasons, list)
    assert "python_runtime_changed" in reasons
    assert baseline_eligibility({})["read"] is False


def test_context_refuses_a_recipe_with_different_request_semantics() -> None:
    plan = plan_fixture()
    value = deepcopy(build_recipe(plan, installed_identity()).document)
    requests = objects(value["requests"])
    requests[0]["body"] = {**object_value(requests[0]["body"]), "max_tokens": 7}
    value["requests"] = list(requests)
    with pytest.raises(ValueError, match="diagnostic_recipe_plan"):
        context_for_plan(plan, resign(value))


def test_recipe_binds_hashed_request_captures_and_rejects_redaction(tmp_path: Path) -> None:
    plan = plan_fixture()
    output = tmp_path / "captured"
    execute_run(plan, FixtureTransport(), output)
    source = load_report_source(output)
    recipe = build_recipe(plan, installed_identity())
    assert recipes.validate_recipe_evidence(recipe, source, output) == ()
    reference = next(ref for ref in source.evidence_refs if ref.path.endswith("request.json"))
    request = object_value(strict_json((output / reference.path).read_text()))
    request["body"] = {**object_value(request["body"]), "model": "[REDACTED]"}
    data = json_bytes(request)
    (output / reference.path).write_bytes(data)
    rebound = replace(
        source,
        evidence_refs=tuple(
            EvidenceRef(ref.path, hashlib.sha256(data).hexdigest()) if ref == reference else ref
            for ref in source.evidence_refs
        ),
    )
    assert "diagnostic_request_capture_mismatch" in recipes.validate_recipe_evidence(
        recipe, rebound, output
    )
    assert "diagnostic_request_capture_invalid" in recipes.validate_recipe_evidence(
        recipe, source, output
    )


def test_request_inventory_cannot_substitute_an_unrecorded_attempt(tmp_path: Path) -> None:
    plan = plan_fixture()
    output = tmp_path / "inventory"
    execute_run(plan, FixtureTransport(), output)
    source = load_report_source(output)
    reference = next(ref for ref in source.evidence_refs if ref.path.endswith("request.json"))
    directory = (output / reference.path).parent.parent / "unrecorded-attempt"
    directory.mkdir()
    (directory / "request.json").write_bytes((output / reference.path).read_bytes())
    replacement = EvidenceRef(
        (directory / "request.json").relative_to(output).as_posix(), reference.sha256
    )
    rebound = replace(
        source,
        evidence_refs=tuple(
            replacement if ref == reference else ref for ref in source.evidence_refs
        ),
    )
    assert recipes.validate_recipe_evidence(
        build_recipe(plan, installed_identity()), rebound, output
    ) == ("diagnostic_request_capture_missing",)
