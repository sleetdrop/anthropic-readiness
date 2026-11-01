"""Pure, explicit category enrichment of installed execution requirements."""

from anthropic_readiness.models import Category, JsonValue, object_value

_CATEGORIES: dict[str, Category] = {
    "HTTP-STATUS": "protocol",
    "HTTP-CONTENT-TYPE": "protocol",
    "CAPTURE-COMPLETE": "environment",
    "MSG-CORE": "protocol",
    "MSG-MODEL": "protocol",
    "MSG-STOP": "protocol",
    "MSG-STOP-SEQUENCE": "protocol",
    "MSG-JSON": "protocol",
    "TASK-COMPLETE": "behavior",
    "SSE-FRAMING": "protocol",
    "STR-JSON": "protocol",
    "STR-TYPE": "protocol",
    "STR-LIFECYCLE": "protocol",
    "STR-START": "protocol",
    "STR-DELTA": "protocol",
    "STR-STOP": "protocol",
    "MSG-TOOL-CALLS": "behavior",
    "MSG-TOOL-ID": "protocol",
    "MSG-TOOL-NAME": "behavior",
    "MSG-TOOL-INPUT": "behavior",
    "LOOP-STEP": "behavior",
}


def categorized_cases(value: JsonValue) -> list[JsonValue]:
    if not isinstance(value, list):
        raise ValueError("diagnostic_case_inventory")
    cases: list[JsonValue] = []
    for raw in value:
        case = object_value(raw)
        assertions = case.get("assertions")
        if not isinstance(assertions, list):
            raise ValueError("diagnostic_assertion_inventory")
        checks: list[JsonValue] = []
        for raw_check in assertions:
            check = object_value(raw_check)
            category = _CATEGORIES.get(str(check.get("id")))
            if category is None:
                raise ValueError("unsupported_diagnostic_assertion")
            checks.append({**check, "category": category})
        case["assertions"] = checks
        cases.append(case)
    return cases
