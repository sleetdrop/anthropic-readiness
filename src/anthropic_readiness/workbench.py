"""Pure operational composition over one checked source generation."""

import hashlib
import json
from copy import deepcopy

from anthropic_readiness.diagnostics.models import WorkbenchView
from anthropic_readiness.models import JsonObject, JsonValue, object_value
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.presentation import PresentationOptions
from anthropic_readiness.report_models import ReportSource
from anthropic_readiness.report_view import DIMENSIONS, GROUPS, build_report_view, counts


def _pending_facts(run: JsonObject) -> JsonObject:
    frozen, job = object_value(run["plan"]), object_value(run["job"])
    plan, target = object_value(frozen["plan"]), object_value(frozen["target"])
    contract = object_value(target["protocol_contract"])
    cases: list[JsonObject] = [
        {
            "case_id": case["id"],
            "name": case["id"],
            "required": case["required"],
            "status": "pending",
            "dimensions": {
                dimension: "not_evaluated" if dimension == "client" else "pending"
                for dimension in DIMENSIONS
            },
            "finding_ids": [],
            "attempts": [],
            "preconditions": [],
            "duration_ms": None,
        }
        for case in objects(plan["cases"])
    ]
    groups: list[JsonValue] = []
    known = {case_id for _, _, ids in GROUPS for case_id in ids}
    definitions = (
        *GROUPS,
        (
            "other",
            "Other selected cases",
            tuple(str(case["case_id"]) for case in cases if case["case_id"] not in known),
        ),
    )
    for key, name, ids in definitions:
        members = [case for case in cases if case["case_id"] in ids]
        if members:
            groups.append(
                {
                    "key": key,
                    "name": name,
                    "case_ids": [case["case_id"] for case in members],
                    "dimensions": {
                        dimension: counts(
                            [str(object_value(case["dimensions"])[dimension]) for case in members]
                        )
                        for dimension in DIMENSIONS
                    },
                }
            )
    return {
        "schema_version": "1.0",
        "presentation_version": "2.0",
        "run_id": job["id"],
        "mode": plan.get("mode", "live"),
        "status": "partial",
        "source_result_sha256": None,
        "identity": {
            "target_name": target["name"],
            "model": target["model"],
            "api_version": target["api_version"],
            "betas": target["beta_headers"],
            "contract_id": contract["id"],
            "contract_revision": contract["revision"],
        },
        "summary": {
            "title": "No verified case records",
            "description": "The selected plan is retained; no execution timestamp is inferred.",
            "planned_cases": len(cases),
            "executed_cases": 0,
            "completed_cases": 0,
            "actual_requests": 0,
            "request_cap": object_value(plan["limits"])["max_requests"],
            "duration_ms": None,
            "started_at": None,
            "finished_at": None,
            "counts": counts(["pending"] * len(cases)),
        },
        "cases": list(cases),
        "groups": groups,
        "findings": [],
        "figures": [],
        "evidence_verification": {"status": "no_evidence", "errors": []},
        "limitations": ["No verified case records or observed execution timestamps are available."],
        "references": [],
        "execution": None,
        "provenance": {
            "assessment_id": None,
            "source_run_id": job["id"],
            "tool": {},
            "execution_environment": {},
            "contract": contract,
            "target": target,
            "profiles": [
                {**profile, "readiness": "incomplete"} for profile in objects(plan["profiles"])
            ],
            "report_context": {},
        },
    }


def build_workbench_view(run: JsonObject, *, worker_observation: JsonObject) -> WorkbenchView:
    report, execution = run.get("report"), run.get("execution")
    if isinstance(report, dict):
        if report["execution"] != execution:
            raise ValueError("workbench_generation_mismatch")
        facts = deepcopy(report)
    elif isinstance(execution, dict):
        source = ReportSource(
            None,
            None,
            (),
            execution,
            {"status": "no_evidence", "errors": []},
            (),
            object_value(object_value(run["plan"])["plan"]),
        )
        facts = build_report_view(source).document
    else:
        facts = _pending_facts(run)
    semantic: JsonObject = {
        "job": run.get("job"),
        "facts": facts,
        "comparison": run.get("comparison"),
        "baseline": run.get("baseline"),
    }
    generation = hashlib.sha256(
        json.dumps(semantic, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    return WorkbenchView(
        deepcopy(
            {
                "schema_version": "1.0",
                "presentation_version": "1.0",
                "presentation": run.get("presentation", PresentationOptions().to_json()),
                "available_locales": ["zh-CN", "en"],
                "facts": facts,
                "generation": generation,
                "job": run.get("job"),
                "worker": worker_observation,
                "comparison": run.get("comparison"),
                "baseline": run.get("baseline"),
            }
        )
    )


def group_comparison(comparison: JsonObject) -> list[JsonObject]:
    """Group observed transitions for navigation without rejudging any check."""
    buckets: dict[tuple[str, str, str], list[JsonObject]] = {}
    transitions = (
        "recovered",
        "persistent",
        "new_failure",
        "gap",
        "newly_evaluated",
        "incomparable",
    )
    for pair in objects(comparison["pairs"]):
        transition, identifier = str(pair["transition"]), str(pair["assertion_id"])
        if transition == "passed_both":
            continue
        if transition not in transitions:
            raise ValueError("invalid_comparison_transition")
        scoped = transition in {"gap", "newly_evaluated", "incomparable"}
        family = (
            "gap"
            if scoped
            else "model"
            if identifier == "MSG-MODEL"
            else "fields"
            if identifier == "MSG-CORE"
            else "stream"
            if identifier.startswith(("STR-", "SSE-"))
            else "http"
            if identifier.startswith("HTTP-")
            else "capture"
            if identifier.startswith("CAPTURE-")
            else "behavior"
            if identifier.startswith(("TOOL-", "BHV-", "TASK-"))
            else "check"
        )
        bucket_key = family, transition, str(pair["case_id"]) if scoped else ""
        buckets.setdefault(bucket_key, []).append(pair)
    groups: list[JsonObject] = []
    for (family, transition, case_id), members in sorted(
        buckets.items(), key=lambda item: (transitions.index(item[0][1]), item[0][0], item[0][2])
    ):
        ordered = sorted(
            members, key=lambda pair: (str(pair["case_id"]), str(pair["assertion_id"]))
        )
        key = hashlib.sha256(json.dumps((family, transition, case_id)).encode()).hexdigest()
        case_ids: list[JsonValue] = []
        case_ids.extend(sorted({str(pair["case_id"]) for pair in members}))
        before_states: list[JsonValue] = []
        before_states.extend(sorted({str(pair["before"]) for pair in members}))
        after_states: list[JsonValue] = []
        after_states.extend(sorted({str(pair["after"]) for pair in members}))
        member_rows: list[JsonValue] = [deepcopy(pair) for pair in ordered]
        groups.append(
            {
                "key": key,
                "family": family,
                "transition": transition,
                "case_id": case_id or None,
                "check_count": len(members),
                "case_ids": case_ids,
                "affected_cases": len({str(pair["case_id"]) for pair in members}),
                "before_states": before_states,
                "after_states": after_states,
                "members": member_rows,
            }
        )
    return groups
