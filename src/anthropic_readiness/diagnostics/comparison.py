"""Pure paired observations over checked facts, with explicit missing coverage."""

import json
from copy import deepcopy

from anthropic_readiness.diagnostics.models import Comparison
from anthropic_readiness.models import JsonObject, JsonValue, object_value

_RESOLVED = {"PASS", "FAIL"}
_SEMANTIC_FIELDS = (
    "implementation",
    "contract",
    "protocol",
    "model",
    "capabilities",
    "limits",
    "profiles",
    "cases",
    "requests",
    "repeat",
    "retry",
)
_TRANSITIONS = (
    "recovered",
    "persistent",
    "new_failure",
    "passed_both",
    "gap",
    "newly_evaluated",
    "incomparable",
)


def _objects(value: JsonValue) -> list[JsonObject]:
    if not isinstance(value, list):
        raise ValueError("diagnostic_comparison_inventory")
    return [object_value(item) for item in value]


def _canonical(value: JsonValue) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _case_key(facts: JsonObject, case_id: JsonValue, version: JsonValue) -> tuple[str, ...]:
    recipe = facts["recipe"]
    identity: JsonValue = None
    request: JsonValue = None
    if isinstance(recipe, dict):
        identity = {"implementation": recipe["implementation"], "contract": recipe["contract"]}
        request = next(
            (row for row in _objects(recipe["requests"]) if row["case_id"] == case_id), None
        )
    return str(case_id), str(version), _canonical(identity), _canonical(request)


def _check_key(facts: JsonObject, row: JsonObject) -> tuple[str, ...]:
    return (
        *_case_key(facts, row["case_id"], row["case_version"]),
        str(row["assertion_id"]),
        str(row["assertion_version"]),
        str(row["category"]),
        str(row["required"]),
    )


def _indexed(facts: JsonObject) -> dict[tuple[str, ...], JsonObject]:
    result: dict[tuple[str, ...], JsonObject] = {}
    for row in _objects(facts["checks"]):
        key = _check_key(facts, row)
        if key in result:
            raise ValueError("diagnostic_duplicate_comparison_check")
        result[key] = row
    return result


def check_transition(before: str, after: str) -> str:
    if after not in _RESOLVED:
        return "gap"
    if before not in _RESOLVED:
        return "newly_evaluated"
    return {
        ("FAIL", "PASS"): "recovered",
        ("FAIL", "FAIL"): "persistent",
        ("PASS", "FAIL"): "new_failure",
        ("PASS", "PASS"): "passed_both",
    }[(before, after)]


def _conditions(before: JsonObject, after: JsonObject) -> list[JsonValue]:
    changes: list[JsonValue] = []
    left, right = before["recipe"], after["recipe"]
    if isinstance(left, dict) and isinstance(right, dict):
        for field in _SEMANTIC_FIELDS:
            if left[field] != right[field]:
                changes.append(
                    {
                        "field": field,
                        "before": left[field],
                        "after": right[field],
                        "kind": "semantic",
                    }
                )
    for field in ("name", "delivery_id", "messages_url", "auth"):
        left_target, right_target = object_value(before["target"]), object_value(after["target"])
        if left_target.get(field) != right_target.get(field):
            changes.append(
                {
                    "field": field,
                    "before": left_target.get(field),
                    "after": right_target.get(field),
                    "kind": "context",
                }
            )
    return changes


def _pair(before: JsonObject, after: JsonObject, comparable: bool) -> JsonObject:
    result: JsonObject = {
        key: before[key]
        for key in ("case_id", "assertion_id", "assertion_version", "category", "required")
    }
    result.update(
        before=before["status"],
        after=after["status"],
        transition=check_transition(str(before["status"]), str(after["status"]))
        if comparable
        else "incomparable",
    )
    for prefix, row in (("before", before), ("after", after)):
        for field in ("reason", "expected", "actual"):
            result[prefix + "_" + field] = row[field]
        result[prefix + "_evidence"] = row["evidence_refs"]
    return result


def _unmatched(row: JsonObject, reason: str) -> JsonObject:
    return {
        "case_id": row["case_id"],
        "assertion_id": row["assertion_id"],
        "assertion_version": row["assertion_version"],
        "reason": reason,
    }


def _missing_required(
    left: dict[tuple[str, ...], JsonObject], right: dict[tuple[str, ...], JsonObject]
) -> int:
    return sum(
        any(row is not None and row["required"] is True for row in (left.get(key), right.get(key)))
        and any(
            row is None or row["status"] not in _RESOLVED for row in (left.get(key), right.get(key))
        )
        for key in left.keys() | right.keys()
    )


def compare_assessments(before: JsonObject, after: JsonObject) -> Comparison:
    changes = _conditions(before, after)
    reasons: list[str] = []
    for facts in (before, after):
        eligibility = object_value(facts["eligibility"])
        if eligibility["compare"] is not True:
            declared = eligibility["reasons"]
            if not isinstance(declared, list):
                raise ValueError("diagnostic_comparison_eligibility")
            reasons.extend(str(reason) for reason in declared)
            reasons.append("diagnostic_source_not_comparable")
        if facts["recipe"] is None:
            reasons.append("diagnostic_recipe_missing_or_invalid")
        quality = object_value(facts["evidence_verification"])
        if quality["status"] != "verified" or quality.get("delivery") == "omitted":
            reasons.append("diagnostic_evidence_unavailable")
    if any(object_value(change)["kind"] == "semantic" for change in changes):
        reasons.append("semantic_conditions_changed")
    comparable = not reasons
    left, right = _indexed(before), _indexed(after)
    common = left.keys() & right.keys()
    pairs = [_pair(left[key], right[key], comparable) for key in sorted(common)]
    removed, added = sorted(left.keys() - common), sorted(right.keys() - common)
    summary: JsonObject = {"unit": "checks", **dict.fromkeys(_TRANSITIONS, 0)}
    for pair in pairs:
        transition = str(pair["transition"])
        summary[transition] = int(str(summary[transition])) + 1
    for _key in removed:
        field = "gap" if comparable else "incomparable"
        summary[field] = int(str(summary[field])) + 1
    for key in added:
        field = (
            ("newly_evaluated" if right[key]["status"] in _RESOLVED else "gap")
            if comparable
            else "incomparable"
        )
        summary[field] = int(str(summary[field])) + 1
    left_cases = {
        (*_case_key(before, row["id"], row["version"]), str(row["required"])): row
        for row in _objects(before["cases"])
    }
    right_cases = {
        (*_case_key(after, row["id"], row["version"]), str(row["required"])): row
        for row in _objects(after["cases"])
    }
    coverage: JsonObject = {
        "before_checks": len(left),
        "after_checks": len(right),
        "matched_checks": len(common),
        "missing_required_checks": _missing_required(left, right),
        "before_cases": len(left_cases),
        "after_cases": len(right_cases),
        "matched_cases": len(left_cases.keys() & right_cases.keys()),
        "missing_required_cases": _missing_required(left_cases, right_cases),
    }
    failures = {key for key, row in left.items() if row["status"] == "FAIL"}
    clean = (
        comparable
        and bool(failures)
        and all(key in right and right[key]["status"] == "PASS" for key in failures)
        and not removed
        and not added
        and coverage["missing_required_checks"] == 0
        and coverage["missing_required_cases"] == 0
        and summary["new_failure"] == 0
        and summary["gap"] == 0
    )
    result: JsonObject = {
        "schema_version": "1.0",
        "before": before["source"],
        "after": after["source"],
        "comparable": comparable,
        "reasons": list(dict.fromkeys(reasons)),
        "condition_changes": changes,
        "pairs": list(pairs),
        "unmatched_before": [
            _unmatched(left[key], "missing_semantic_match_after") for key in removed
        ],
        "unmatched_after": [
            _unmatched(right[key], "missing_semantic_match_before") for key in added
        ],
        "coverage": coverage,
        "summary": summary,
        "all_previous_failures_passed": clean,
    }
    return Comparison(deepcopy(result))
