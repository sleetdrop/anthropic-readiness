"""Conservative operation eligibility from explicitly verified metadata facts."""

from anthropic_readiness.diagnostics.inventory import categorized_cases
from anthropic_readiness.models import (
    JsonObject,
    JsonValue,
    RunResult,
    Status,
    aggregate_required,
    object_value,
)
from anthropic_readiness.tool_loop import CASE_ID as TOOL_LOOP_CASE_ID


def controlled_result_complete(result: RunResult | None) -> bool:
    """A persisted result alone does not establish completed live execution."""
    return (
        result is not None
        and result.mode == "live"
        and result.execution_environment.get("interruption") is None
        and result.execution_environment.get("internal_error") is None
    )


def _objects(value: JsonValue) -> list[JsonObject]:
    if not isinstance(value, list):
        raise ValueError("diagnostic_case_inventory")
    return [object_value(item) for item in value]


def _loop_assertions(record: JsonObject) -> list[JsonObject]:
    """Project both fixed exchanges conservatively; never use last-pass-wins."""
    attempts = _objects(record["attempts"])
    if len(attempts) > 2 or [row["index"] for row in attempts] != list(range(1, len(attempts) + 1)):
        raise ValueError("diagnostic_tool_loop_exchange_order")
    groups: list[tuple[int, list[JsonObject]]] = [(0, _objects(record["preconditions"]))]
    groups.extend((int(str(row["index"])), _objects(row["assertions"])) for row in attempts)
    buckets: dict[tuple[str, ...], list[tuple[int, JsonObject]]] = {}
    for step, assertions in groups:
        seen: set[tuple[str, ...]] = set()
        for assertion in assertions:
            key = tuple(
                str(assertion[field]) for field in ("id", "version", "category", "required")
            )
            if key in seen:
                raise ValueError("diagnostic_repeated_comparison_check")
            seen.add(key)
            buckets.setdefault(key, []).append((step, assertion))
    result: list[JsonObject] = []
    for rows in buckets.values():
        if len(rows) == 1:
            result.append(rows[0][1])
            continue
        status = aggregate_required([Status(str(row["status"])) for _, row in rows])
        lead = next(row for _, row in rows if row["status"] == status.value)
        refs: list[JsonValue] = []
        for _, row in rows:
            refs.extend(_objects(row["evidence_refs"]))
        result.append(
            {
                **lead,
                "status": status.value,
                "expected": "; ".join(
                    f"exchange {step}: {row['expected']}" for step, row in rows if row["expected"]
                ),
                "actual": "; ".join(
                    f"exchange {step}: {row['actual']}" for step, row in rows if row["actual"]
                ),
                "evidence_refs": refs,
            }
        )
    return result


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
            if case_id == TOOL_LOOP_CASE_ID:
                assertions = _loop_assertions(record)
            else:
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
