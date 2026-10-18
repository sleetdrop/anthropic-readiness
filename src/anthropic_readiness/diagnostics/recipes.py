"""Regenerate portable recipes from installed code, never imported executable input."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from anthropic_readiness.cases import build_request
from anthropic_readiness.config import fingerprint, target_from_document
from anthropic_readiness.contracts import resolve_contract
from anthropic_readiness.diagnostics.core_contracts import validate_core
from anthropic_readiness.diagnostics.identity import check_identity, installed_identity
from anthropic_readiness.diagnostics.inventory import categorized_cases
from anthropic_readiness.diagnostics.models import ImplementationIdentity, RetestRecipe
from anthropic_readiness.evidence import safe_path
from anthropic_readiness.models import JsonObject, JsonValue, object_value, strict_json
from anthropic_readiness.operations.storage import MAX_DOCUMENT_BYTES
from anthropic_readiness.runner import RunPlan, plan_run

if TYPE_CHECKING:
    from anthropic_readiness.report_models import ReportSource


def _objects(value: JsonValue) -> list[JsonObject]:
    if not isinstance(value, list):
        raise ValueError("diagnostic_expected_array")
    return [object_value(item) for item in value]


def build_recipe(plan: RunPlan, identity: ImplementationIdentity) -> RetestRecipe:
    check_identity(identity, identity)
    requests: list[JsonValue] = []
    for case in plan.cases:
        request = build_request(case, plan.target)
        normalized: JsonObject = {
            "method": "POST",
            "headers": dict(request.headers),
            "body": request.body,
            "streaming": request.streaming,
        }
        requests.append({"case_id": case.id, **normalized, "sha256": fingerprint(normalized)})
    raw: dict[str, object] = {
        "schema_version": "1.0",
        "implementation": identity.document,
        "contract": {
            "id": plan.target.contract_id,
            "revision": plan.target.contract_revision,
            "content_sha256": plan.bundle.content_sha256,
        },
        "protocol": {
            "name": "anthropic.messages",
            "api_version": plan.target.api_version,
            "beta_headers": list(plan.target.beta_headers),
        },
        "model": {
            "requested": plan.target.model,
            "policy": plan.target.response_model_policy,
            "aliases": sorted(set(plan.target.response_model_aliases)),
        },
        "capabilities": dict(plan.target.capabilities),
        "limits": plan.target.limits.to_json(),
        "profiles": plan.to_json()["profiles"],
        "cases": categorized_cases(plan.to_json()["cases"]),
        "requests": requests,
        "repeat": 1,
        "retry": 0,
    }
    document = object_value(raw)
    document["content_sha256"] = fingerprint(document)
    validate_core(document, "retest-recipe")
    return RetestRecipe(document)


def _plan(target: JsonObject, profiles: Sequence[str]) -> RunPlan:
    config = target_from_document(target)
    return plan_run(
        config, resolve_contract(config.contract_id, config.contract_revision), profiles
    )


def _profiles(recipe: RetestRecipe) -> tuple[str, ...]:
    return tuple(str(item["id"]) for item in _objects(recipe.document["profiles"]))


def _check_recipe(recipe: RetestRecipe, identity: ImplementationIdentity) -> None:
    validate_core(recipe.document, "retest-recipe")
    value = recipe.document
    if (
        fingerprint({key: item for key, item in value.items() if key != "content_sha256"})
        != value["content_sha256"]
    ):
        raise ValueError("diagnostic_recipe_integrity")
    reasons = check_identity(
        ImplementationIdentity(object_value(value["implementation"])), identity
    )
    if reasons:
        raise ValueError("diagnostic_identity_changed:" + ",".join(reasons))


def _original_plan(recipe: RetestRecipe, local: JsonObject) -> RunPlan:
    value = recipe.document
    contract = object_value(value["contract"])
    protocol = object_value(value["protocol"])
    model = object_value(value["model"])
    original: JsonObject = {
        **local,
        "model": model["requested"],
        "response_model_policy": model["policy"],
        "response_model_aliases": model["aliases"],
        "api_version": protocol["api_version"],
        "beta_headers": protocol["beta_headers"],
        "protocol_contract": {"id": contract["id"], "revision": contract["revision"]},
        "capabilities": value["capabilities"],
        "limits": value["limits"],
    }
    return _plan(original, _profiles(recipe))


def prepare_retest(
    recipe: RetestRecipe, target: JsonObject, identity: ImplementationIdentity
) -> tuple[RunPlan, JsonObject]:
    _check_recipe(recipe, identity)
    original = _original_plan(recipe, target)
    if build_recipe(original, identity).document != recipe.document:
        raise ValueError("diagnostic_recipe_regeneration")
    retest = _plan(target, _profiles(recipe))
    current = build_recipe(retest, identity).document
    changes: list[JsonValue] = []
    for field in (
        "contract",
        "protocol",
        "model",
        "capabilities",
        "limits",
        "profiles",
        "cases",
        "requests",
    ):
        if recipe.document[field] != current[field]:
            changes.append(
                {
                    "field": field,
                    "before": recipe.document[field],
                    "after": current[field],
                    "kind": "semantic",
                }
            )
    semantic = bool(changes)
    # Endpoint/auth/display context is deliberately absent from a portable recipe.
    for field in ("name", "delivery_id", "messages_url"):
        changes.append({"field": field, "before": None, "after": target[field], "kind": "context"})
    return retest, {
        "schema_version": "1.0",
        "comparable": not semantic,
        "changes": changes,
        "reasons": ["semantic_conditions_changed"] if semantic else [],
    }


def validate_recipe_binding(recipe: RetestRecipe, source: ReportSource) -> tuple[str, ...]:
    try:
        identity = installed_identity()
        _check_recipe(recipe, identity)
        target = (
            source.result.target
            if source.result is not None
            else (
                object_value(source.execution["target"]) if source.execution is not None else None
            )
        )
        if target is None:
            return ("diagnostic_source_target_missing",)
        regenerated = _plan(target, _profiles(recipe))
        if build_recipe(regenerated, identity).document != recipe.document:
            return ("diagnostic_recipe_source_mismatch",)
        expected = regenerated.to_json()
        recorded = {**source.plan, "actual_requests": 0}
        if recorded != expected:
            return ("diagnostic_source_plan_mismatch",)
        if source.result is not None and (
            source.result.mode != "live"
            or source.result.contract.get("content_sha256") != regenerated.bundle.content_sha256
        ):
            return ("diagnostic_source_contract_mismatch",)
        return ()
    except (ValueError, KeyError) as exc:
        return (
            str(exc).split(":", 1)[0]
            if isinstance(exc, ValueError)
            else "diagnostic_source_binding",
        )


def validate_recipe_evidence(
    recipe: RetestRecipe, source: ReportSource, root: Path
) -> tuple[str, ...]:
    """Verify bounded captured requests against the regenerated semantic inventory."""
    requests = {str(item["case_id"]): item for item in _objects(recipe.document["requests"])}
    references = {
        ref.path: ref for ref in source.evidence_refs if ref.path.endswith("/request.json")
    }
    expected_paths = {
        "evidence/" + str(case["id"]) + "/" + str(attempt["id"]) + "/request.json"
        for case in source.case_records
        for attempt in _objects(case.get("attempts", []))
    }
    if set(references) != expected_paths:
        return ("diagnostic_request_capture_missing",)
    reasons: list[str] = []
    for relative, ref in references.items():
        try:
            parts = relative.split("/")
            if len(parts) != 4 or parts[0] != "evidence" or parts[1] not in requests:
                raise ValueError("request_inventory")
            with safe_path(root, relative).open("rb") as stream:
                data = stream.read(MAX_DOCUMENT_BYTES + 1)
            if len(data) > MAX_DOCUMENT_BYTES or hashlib.sha256(data).hexdigest() != ref.sha256:
                raise ValueError("request_integrity")
            capture = object_value(strict_json(data.decode()))
            if set(capture) != {"url", "headers", "body", "streaming"}:
                raise ValueError("request_fields")
            headers = {
                key.lower(): value
                for key, value in object_value(capture["headers"]).items()
                if key.lower() not in {"authorization", "x-api-key"}
            }
            normalized: JsonObject = {
                "method": "POST",
                "headers": headers,
                "body": capture["body"],
                "streaming": capture["streaming"],
            }
            expected = {
                key: value
                for key, value in requests[parts[1]].items()
                if key not in {"case_id", "sha256"}
            }
            if normalized != expected:
                reasons.append("diagnostic_request_capture_mismatch")
        except (OSError, ValueError, KeyError):
            reasons.append("diagnostic_request_capture_invalid")
    return tuple(dict.fromkeys(reasons))
