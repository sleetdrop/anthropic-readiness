"""Conservative operation eligibility from explicitly verified metadata facts."""

from anthropic_readiness.diagnostics.inventory import categorized_cases
from anthropic_readiness.models import JsonObject, JsonValue, object_value


def _objects(value: JsonValue) -> list[JsonObject]:
    if not isinstance(value, list):
        raise ValueError("diagnostic_case_inventory")
    return [object_value(item) for item in value]


def comparison_inventory(
    plan: JsonObject, records: tuple[JsonObject, ...], recipe: JsonObject | None
) -> tuple[list[JsonValue], list[JsonValue]]:
    """Retain the entire selected inventory, including never-observed checks."""
    planned = recipe["cases"] if recipe is not None else categorized_cases(plan["cases"])
    observed = {str(case["id"]): case for case in records}
    cases: list[JsonValue] = []
    checks: list[JsonValue] = []
    for definition in _objects(planned):
        case_id = str(definition["id"])
        record = observed.get(case_id)
        cases.append(
            {
                "id": case_id,
                "version": definition["version"],
                "required": definition["required"],
                "status": record["status"] if record is not None else "missing",
            }
        )
        assertions: list[JsonObject] = []
        if record is not None:
            assertions.extend(_objects(record["preconditions"]))
            for attempt in _objects(record["attempts"]):
                assertions.extend(_objects(attempt["assertions"]))
        actual: dict[tuple[str, ...], JsonObject] = {}
        for assertion in assertions:
            key = tuple(
                str(assertion[field]) for field in ("id", "version", "category", "required")
            )
            if key in actual:
                # W2 supports one sample and no retry, never last-pass-wins.
                raise ValueError("diagnostic_repeated_comparison_check")
            actual[key] = assertion
        for expected in _objects(definition["assertions"]):
            key = tuple(str(expected[field]) for field in ("id", "version", "category", "required"))
            observed_assertion = actual.pop(key, None)
            checks.append(
                _comparison_check(case_id, definition["version"], expected, observed_assertion)
            )
        for assertion in actual.values():
            checks.append(_comparison_check(case_id, definition["version"], assertion, assertion))
    return cases, checks


def _comparison_check(
    case_id: str, case_version: JsonValue, definition: JsonObject, actual: JsonObject | None
) -> JsonObject:
    return {
        "case_id": case_id,
        "case_version": case_version,
        "assertion_id": definition["id"],
        "assertion_version": definition["version"],
        "category": definition["category"],
        "required": definition["required"],
        "status": actual["status"] if actual is not None else "missing",
        "reason": actual["reason_code"] if actual is not None else "not_observed",
        "expected": actual["expected"] if actual is not None else "",
        "actual": actual["actual"] if actual is not None else "",
        "evidence_refs": actual["evidence_refs"] if actual is not None else [],
    }


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
