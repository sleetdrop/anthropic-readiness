"""Real plan inputs for provenance tests; production recipe generation is separate."""

from anthropic_readiness.cases import build_request
from anthropic_readiness.config import fingerprint
from anthropic_readiness.diagnostics.core_contracts import validate_core
from anthropic_readiness.diagnostics.identity import installed_identity
from anthropic_readiness.diagnostics.inventory import categorized_cases
from anthropic_readiness.diagnostics.models import RetestRecipe
from anthropic_readiness.models import JsonObject, JsonValue
from anthropic_readiness.runner import RunPlan


def recipe_fixture(plan: RunPlan) -> RetestRecipe:
    requests: list[JsonValue] = []
    beta_headers: list[JsonValue] = list(plan.target.beta_headers)
    aliases: list[JsonValue] = []
    aliases.extend(sorted(set(plan.target.response_model_aliases)))
    for case in plan.cases:
        request = build_request(case, plan.target)
        normalized: JsonObject = {
            "method": "POST",
            "headers": dict(request.headers),
            "body": request.body,
            "streaming": request.streaming,
        }
        requests.append({"case_id": case.id, **normalized, "sha256": fingerprint(normalized)})
    value: JsonObject = {
        "schema_version": "1.0",
        "implementation": installed_identity().document,
        "contract": {
            "id": plan.target.contract_id,
            "revision": plan.target.contract_revision,
            "content_sha256": plan.bundle.content_sha256,
        },
        "protocol": {
            "name": "anthropic.messages",
            "api_version": plan.target.api_version,
            "beta_headers": beta_headers,
        },
        "model": {
            "requested": plan.target.model,
            "policy": plan.target.response_model_policy,
            "aliases": aliases,
        },
        "capabilities": dict(plan.target.capabilities),
        "limits": plan.target.limits.to_json(),
        "profiles": plan.to_json()["profiles"],
        "cases": categorized_cases(plan.to_json()["cases"]),
        "requests": requests,
        "repeat": 1,
        "retry": 0,
    }
    value["content_sha256"] = fingerprint(value)
    validate_core(value, "retest-recipe")
    return RetestRecipe(value)
