"""Offline structural and relational document validation."""

from __future__ import annotations

from importlib.resources import files

from jsonschema import Draft202012Validator

from anthropic_readiness.models import (
    JsonObject,
    JsonValue,
    Status,
    aggregate_required,
    object_value,
    readiness,
    strict_json,
)


def load_schema(name: str) -> JsonObject:
    if name not in {"result", "capture", "target", "contract", "check-result", "acceptance"}:
        raise ValueError("unknown_schema")
    return object_value(
        strict_json(
            files("anthropic_readiness")
            .joinpath(f"resources/schemas/{name}.schema.json")
            .read_text()
        )
    )


def validate_document(value: object, schema: JsonValue) -> None:
    def check_refs(node: JsonValue) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if (
                    key in {"$ref", "$dynamicRef"}
                    and isinstance(child, str)
                    and not child.startswith("#")
                ):
                    raise ValueError("external_schema_reference")
                check_refs(child)
        elif isinstance(node, list):
            for child in node:
                check_refs(child)

    check_refs(schema)
    if not isinstance(schema, (dict, bool)):
        raise ValueError("invalid_schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(e.path))
    if errors:
        raise ValueError("schema:" + "; ".join(f"{list(e.path)}:{e.message}" for e in errors))


def _objects(value: JsonValue) -> list[JsonObject]:
    return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def validate_result_semantics(value: JsonObject) -> list[str]:
    errors: list[str] = []
    plan = object_value(value.get("plan", {}))
    cases = _objects(value.get("cases", []))
    by_id = {str(c.get("id")): c for c in cases}
    if len(by_id) != len(cases):
        errors.append("duplicate_case_id")
    planned = plan.get("cases", [])
    if isinstance(planned, list):
        ids = [str(v.get("id")) if isinstance(v, dict) else str(v) for v in planned]
        if len(ids) != len(set(ids)):
            errors.append("duplicate_planned_case")
        for case_id in ids:
            if case_id not in by_id:
                errors.append(f"missing_case:{case_id}")
        for case_id in by_id:
            if case_id not in ids:
                errors.append(f"unplanned_case:{case_id}")
    attempt_ids: set[str] = set()
    actual_requests = 0
    for case in cases:
        statuses: list[Status] = []
        for attempt in _objects(case.get("attempts", [])):
            attempt_id = str(attempt.get("id"))
            if attempt_id in attempt_ids:
                errors.append("duplicate_attempt_id")
            attempt_ids.add(attempt_id)
            count = attempt.get("actual_requests", 0)
            if type(count) is int:
                actual_requests += count
            assertions = _objects(attempt.get("assertions", []))
            assertion_ids = [a.get("id") for a in assertions]
            if len(assertion_ids) != len({str(a) for a in assertion_ids}):
                errors.append("duplicate_assertion_id")
            required = [Status(str(a["status"])) for a in assertions if a.get("required") is True]
            status = aggregate_required(required)
            if attempt.get("status") != status.value:
                errors.append(f"attempt_status:{attempt_id}")
            statuses.append(status)
        if not statuses:
            statuses = [
                Status(str(p["status"]))
                for p in _objects(case.get("preconditions", []))
                if p.get("required") is True
            ]
        if case.get("status") != aggregate_required(statuses).value:
            errors.append(f"case_status:{case.get('id')}")
    if plan.get("actual_requests", actual_requests) != actual_requests:
        errors.append("request_count")
    if value.get("mode") == "replay" and actual_requests != 0:
        errors.append("replay_request_count")
    for profile in _objects(value.get("profiles", [])):
        required_ids = profile.get("cases", [])
        profile_statuses = (
            [
                Status(str(by_id[c]["status"])) if c in by_id else Status.INDETERMINATE
                for c in required_ids
                if isinstance(c, str)
            ]
            if isinstance(required_ids, list)
            else []
        )
        if profile.get("readiness") != readiness(aggregate_required(profile_statuses)):
            errors.append(f"profile_readiness:{profile.get('id')}")
    return errors
