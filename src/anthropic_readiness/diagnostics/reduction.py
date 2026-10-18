"""Conservative operation eligibility from explicitly verified metadata facts."""

from anthropic_readiness.models import JsonObject, JsonValue


def baseline_eligibility(metadata: JsonObject) -> JsonObject:
    reasons: list[JsonValue] = []
    read = metadata.get("source_valid") is True
    fields = {
        "source_valid": "diagnostic_source_invalid",
        "complete": "diagnostic_partial_source",
        "recipe_valid": "diagnostic_recipe_missing_or_invalid",
        "recipe_bound": "diagnostic_recipe_unbound",
        "context_verified": "diagnostic_context_unverified",
        "evidence_verified": "diagnostic_evidence_unavailable",
    }
    for field, code in fields.items():
        if metadata.get(field) is not True:
            reasons.append(code)
    identity_reasons = metadata.get("identity_reasons")
    if not isinstance(identity_reasons, list) or any(
        not isinstance(item, str) for item in identity_reasons
    ):
        reasons.append("diagnostic_identity_unverified")
    else:
        reasons.extend(item for item in identity_reasons if item not in reasons)
    return {"read": read, "retest": not reasons, "compare": not reasons, "reasons": reasons}
