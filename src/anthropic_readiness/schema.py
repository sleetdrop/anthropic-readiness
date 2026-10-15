"""Offline structural and relational document validation."""

from __future__ import annotations

from importlib.resources import files

from jsonschema import Draft202012Validator

from anthropic_readiness.models import (
    EvidenceRef,
    JsonObject,
    JsonValue,
    RunResult,
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
    planned_cases = {str(c["id"]): c for c in _objects(plan.get("cases", []))}
    actual_requests = 0
    for case in cases:
        expected_case = planned_cases.get(str(case.get("id")), {})
        if expected_case and (
            case.get("version") != expected_case.get("version")
            or case.get("required") != expected_case.get("required")
        ):
            errors.append(f"case_contract:{case.get('id')}")
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
            actual_by_id = {str(a["id"]): a for a in assertions}
            for expected in _objects(expected_case.get("assertions", [])):
                actual = actual_by_id.get(str(expected["id"]))
                if actual is None:
                    if expected.get("required") is True and attempt.get("status") == "PASS":
                        errors.append(f"missing_assertion:{expected['id']}")
                elif actual.get("required") != expected.get("required") or actual.get(
                    "version"
                ) != expected.get("version"):
                    errors.append(f"assertion_contract:{expected['id']}")
            assertion_ids = [a.get("id") for a in assertions]
            if len(assertion_ids) != len({str(a) for a in assertion_ids}):
                errors.append("duplicate_assertion_id")
            required = [Status(str(a["status"])) for a in assertions if a.get("required") is True]
            status = aggregate_required(required)
            if attempt.get("status") != status.value:
                errors.append(f"attempt_status:{attempt_id}")
            statuses.append(status)
        if not statuses:
            if case.get("status") == "PASS":
                errors.append("unexecuted_case_pass")
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
    profile_records = _objects(value.get("profiles", []))
    planned_profiles = {str(p["id"]): p for p in _objects(plan.get("profiles", []))}
    if planned_profiles and (
        len(profile_records) != len(planned_profiles)
        or {str(p["id"]) for p in profile_records} != set(planned_profiles)
    ):
        errors.append("profile_inventory")
    for profile in profile_records:
        expected_profile = planned_profiles.get(str(profile.get("id")))
        if expected_profile is not None and expected_profile.get("cases") != profile.get("cases"):
            errors.append(f"profile_cases:{profile.get('id')}")
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


def result_from_document(document: JsonObject) -> RunResult:
    """Rehydrate only after structural and relational validation."""
    validate_document(document, load_schema("result"))
    if errors := validate_result_semantics(document):
        raise ValueError("result_semantics:" + ";".join(errors))

    def text(value: JsonValue) -> str:
        if not isinstance(value, str):
            raise ValueError("expected_string")
        return value

    limitations = document["limitations"]
    if not isinstance(limitations, list):
        raise ValueError("invalid_limitations")
    evidence: list[EvidenceRef] = []
    for ref in _objects(document["evidence"]):
        event = ref.get("event")
        pointer = ref.get("pointer")
        evidence.append(
            EvidenceRef(
                text(ref["path"]),
                text(ref["sha256"]),
                event if type(event) is int else None,
                text(pointer) if pointer is not None else None,
            )
        )
    return RunResult(
        text(document["run_id"]),
        text(document["assessment_id"]),
        "live" if document["mode"] == "live" else "replay",
        text(document["started_at"]),
        text(document["finished_at"]),
        object_value(document["tool"]),
        object_value(document["execution_environment"]),
        object_value(document["contract"]),
        object_value(document["target"]),
        object_value(document["plan"]),
        tuple(_objects(document["profiles"])),
        tuple(_objects(document["cases"])),
        tuple(evidence),
        object_value(document["report_context"]),
        tuple(text(item) for item in limitations),
        text(document["source_run_id"]) if document["source_run_id"] is not None else None,
    )
