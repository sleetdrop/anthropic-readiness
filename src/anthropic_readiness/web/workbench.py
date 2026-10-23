"""Independent operational pages and checked local workbench projections."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from anthropic_readiness.cases import list_cases
from anthropic_readiness.diagnostics.contracts import validate_diagnostic
from anthropic_readiness.diagnostics.models import WorkbenchView
from anthropic_readiness.evidence import safe_path, verify_evidence
from anthropic_readiness.localization import load_catalog, translate
from anthropic_readiness.models import JsonObject, JsonValue, object_value
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.operations.reduction import TERMINAL, objects
from anthropic_readiness.report_sources import source_bytes
from anthropic_readiness.report_view import DIMENSIONS, build_report_view
from anthropic_readiness.web.api import LocalRoute, evidence_id, manager_for, run_document
from anthropic_readiness.web.contracts import response_contract
from anthropic_readiness.web.diagnostics import _owned_source, service_for
from anthropic_readiness.web.security import api_response, preferences_for
from anthropic_readiness.web.templating import CASE_KEYS, STATE_KEYS, page
from anthropic_readiness.workbench import build_workbench_view, group_comparison

router = APIRouter(route_class=LocalRoute)
VIEWS = ("overview", "issues", "cases", "compare", "activity")
FILTERS = {"all", "FAIL", "unresolved", "PASS"}


def issue_key(finding: JsonObject) -> str:
    identity = [finding["assertion_id"], finding["reason_code"], finding["status"]]
    return hashlib.sha256(json.dumps(identity, separators=(",", ":")).encode()).hexdigest()


def _reference(value: str) -> JsonObject:
    kind, identifier = value.split(":", 1) if ":" in value else ("baseline", value)
    reference: JsonObject = {"kind": kind, "id": identifier}
    validate_operational(
        {
            "kind": "diagnostic_comparison_request",
            "data": {"before": reference, "after": reference},
        },
        "web-api",
    )
    return reference


def local_workbench(
    request: Request, run_id: str, baseline: str | None = None
) -> tuple[WorkbenchView, JsonObject]:
    manager = manager_for(request)
    document = run_document(manager, run_id)
    document["presentation"] = preferences_for(request).to_json()
    if baseline:
        reference = _reference(baseline)
        service = service_for(request)
        before = _owned_source(request, reference)
        after = _owned_source(request, {"kind": "run", "id": run_id})
        comparison = service.compare_sources(before, after)
        before_facts = service.source_facts(before)
        document["comparison"] = comparison.document
        document["baseline"] = {
            "id": reference["id"],
            "source": comparison.document["before"],
            "eligibility": before_facts["eligibility"],
        }
    view = build_workbench_view(document, worker_observation=manager.worker_observation(run_id))
    validate_diagnostic(view.document, "workbench-view")
    return view, document


@router.get("/api/v1/runs/{run_id}/workbench", responses=response_contract("workbench_response"))
def workbench_api(run_id: str, request: Request, baseline: str | None = None) -> JSONResponse:
    view, _ = local_workbench(request, run_id, baseline)
    return api_response("workbench_response", view.document)


def _issue_family(finding: JsonObject) -> str:
    identifier = str(finding["assertion_id"])
    if identifier == "MSG-MODEL":
        return "model_identity"
    if identifier == "MSG-CORE" and finding["observations"]:
        return "stop_fields"
    if finding["category"] == "environment":
        return "environment"
    if identifier.startswith(("STR-", "SSE-")):
        return "stream"
    if finding["category"] == "behavior":
        return "behavior"
    return "response"


def _matches(status: JsonValue, selection: str) -> bool:
    return (
        selection == "all"
        or status == selection
        or (selection == "unresolved" and status not in {"PASS", "FAIL"})
    )


def _scope_options(request: Request, current_id: str) -> list[JsonObject]:
    options: list[JsonObject] = []
    manager = manager_for(request)
    for item in objects(manager.store.history({}, None, 50)["items"]):
        identifier = str(object_value(item["job"])["id"])
        if identifier != current_id and str(object_value(item["job"])["state"]) in TERMINAL:
            options.append(
                {
                    "value": "run:" + identifier,
                    "label": str(item["target_name"]) + " · " + str(item["model"]),
                }
            )
    service = service_for(request)
    for record in service.store.stored_baselines():
        identifier = str(record.document["id"])
        label = "Imported · " + str(record.document["imported_at"])[:16] + " · " + identifier[:8]
        try:
            source = service.load_source(identifier)
            target = (
                source.result.target
                if source.result is not None
                else object_value(source.execution["target"])
                if source.execution is not None
                else {}
            )
            label = str(target.get("name", identifier[:8])) + " · " + str(target.get("model", ""))
        except (ValueError, OSError):
            pass
        options.append({"value": "baseline:" + identifier, "label": label})
    return options


def workbench_context(
    request: Request,
    view: WorkbenchView,
    original: JsonObject,
    *,
    base_url: str,
    selected_view: str,
    read_only: bool = False,
) -> dict[str, object]:
    value, options = view.document, preferences_for(request)
    catalog = load_catalog(options.locale)

    def text(key: str, **params: str | int | float) -> str:
        return translate(catalog, key, params)

    def case_name(identifier: JsonValue) -> str:
        return text(CASE_KEYS[str(identifier)]) if str(identifier) in CASE_KEYS else str(identifier)

    def link(selected: str, **query: str) -> str:
        if selected in {"issues", "overview"}:
            keep = selected_view in {"issues", "overview"}
            query = {
                "filter": selected_filter if keep else "all",
                "q": search if keep else "",
                **query,
            }
        return base_url + "?" + urlencode({"view": selected, **query})

    facts = object_value(value["facts"])
    cases = objects(facts["cases"])
    selected_filter = request.query_params.get("filter", "all")
    search = request.query_params.get("q", "")
    if len(search) > 200:
        raise ValueError("invalid_request")
    matrix_scope: tuple[str, str, str] | None = None
    matrix_members: set[str] = set()
    matrix_label: str | None = None
    if selected_filter not in FILTERS:
        parts = selected_filter.split(":")
        known_groups = {str(group["key"]): group for group in objects(facts["groups"])}
        if (
            selected_view != "cases"
            or len(parts) != 4
            or parts[0] != "matrix"
            or parts[1] not in known_groups
            or parts[2] not in DIMENSIONS
            or parts[3] not in STATE_KEYS
        ):
            raise ValueError("invalid_request")
        group_key, dimension, status = parts[1:]
        if status not in {
            "PASS",
            "FAIL",
            "INDETERMINATE",
            "BLOCKED",
            "SKIP",
            "pending",
            "running",
            "not_evaluated",
        }:
            raise ValueError("invalid_request")
        matrix_scope = (group_key, dimension, status)
        group_cases = known_groups[group_key]["case_ids"]
        matrix_members = (
            {str(item) for item in group_cases} if isinstance(group_cases, list) else set()
        )
        matrix_label = text(
            "filter.matrix_scope",
            group=text("group." + ("additional" if group_key == "other" else group_key)),
            dimension=text("dimension." + dimension),
            state=text(STATE_KEYS[status]),
        )

    def matrix_link(group: JsonObject, dimension: str, status: str) -> str:
        members = (
            [
                case
                for case in cases
                if case["case_id"] in group["case_ids"]
                and object_value(case["dimensions"])[dimension] == status
            ]
            if isinstance(group["case_ids"], list)
            else []
        )
        query = {"filter": "matrix:" + str(group["key"]) + ":" + dimension + ":" + status}
        if members:
            query["case"] = str(members[0]["case_id"])
        return link("cases", **query)

    target = object_value(object_value(facts["provenance"])["target"])
    summary = object_value(facts["summary"])
    findings: list[JsonObject] = []
    for finding in objects(facts["findings"]):
        family = _issue_family(finding)
        finding_members = finding.get("cases")
        member_names = (
            " / ".join(case_name(item) for item in finding_members)
            if isinstance(finding_members, list)
            else ""
        )
        findings.append(
            {
                **finding,
                "key": issue_key(finding),
                "label": text("issue." + family + ".title"),
                "explanation": text("issue." + family + ".impact"),
                "next_action": text("issue." + family + ".action"),
                "case_names": member_names,
            }
        )
    shown_findings = [
        finding
        for finding in findings
        if _matches(finding["status"], "all" if matrix_scope else selected_filter)
        and (not search or search.casefold() in json.dumps(finding, ensure_ascii=False).casefold())
    ]
    requested_issue = request.query_params.get("issue")
    selected_issue = (
        next(
            (finding for finding in findings if requested_issue in {finding["key"], finding["id"]}),
            None,
        )
        if requested_issue
        else None
    )
    requested_case = request.query_params.get("case")
    shown_cases = [
        case
        for case in cases
        if (
            case["case_id"] in matrix_members
            and object_value(case["dimensions"])[matrix_scope[1]] == matrix_scope[2]
            if matrix_scope
            else _matches(case["status"], selected_filter)
        )
    ]
    selected_case = (
        next((case for case in cases if case["case_id"] == requested_case), None)
        if requested_case
        else (shown_cases[0] if shown_cases else None)
    )
    if (requested_issue and selected_issue is None) or (requested_case and selected_case is None):
        raise ValueError("invalid_request")
    evidence = objects(original.get("evidence"))
    proof = {
        (str(item["path"]), str(item["sha256"])): item
        for item in evidence
        if item["verified"] is True
    }
    checks: list[JsonObject] = []
    for case in cases:
        assertions = [
            *objects(case["preconditions"]),
            *(
                assertion
                for attempt in objects(case["attempts"])
                for assertion in objects(attempt["assertions"])
            ),
        ]
        for assertion in assertions:
            links: list[JsonValue] = []
            for ref in objects(assertion["evidence_refs"]):
                item = proof.get((str(ref["path"]), str(ref["sha256"])))
                if item is not None:
                    links.append({"id": item["id"], **ref})
            checks.append(
                {
                    **assertion,
                    "case_id": case["case_id"],
                    "case_name": case_name(case["case_id"]),
                    "links": links,
                }
            )
    issue_checks = [
        check
        for check in checks
        if selected_issue is not None
        and all(
            check[left] == selected_issue[right]
            for left, right in (
                ("id", "assertion_id"),
                ("reason_code", "reason_code"),
                ("status", "status"),
            )
        )
    ]
    issue_members = tuple(dict.fromkeys(str(check["case_id"]) for check in issue_checks))
    issue_case = requested_case or (issue_members[0] if issue_members else None)
    if selected_view == "issues" and requested_case and requested_case not in issue_members:
        raise ValueError("invalid_request")
    issue_observations = (
        [
            observation
            for observation in objects(selected_issue.get("observations"))
            if observation["case_id"] == issue_case
        ]
        if selected_issue is not None
        else []
    )
    displayed_issue_checks = [check for check in issue_checks if check["case_id"] == issue_case]
    case_checks = [
        check
        for check in checks
        if selected_case is not None and check["case_id"] == selected_case["case_id"]
    ]
    groups: list[JsonObject] = []
    for group in objects(facts["groups"]):
        members = (
            [case for case in cases if case["case_id"] in group["case_ids"]]
            if isinstance(group["case_ids"], list)
            else []
        )
        completed = sum(
            case["status"] not in {"pending", "running", "not_evaluated"} for case in members
        )
        state = (
            "completed"
            if completed == len(members)
            else "running"
            if any(case["status"] == "running" for case in members)
            else "pending"
        )
        groups.append(
            {
                **group,
                "label": text(
                    "group." + ("additional" if group["key"] == "other" else str(group["key"]))
                ),
                "completed": completed,
                "total": len(members),
                "state": state,
            }
        )
    job = value["job"]
    terminal = not isinstance(job, dict) or str(job["state"]) in TERMINAL
    execution = facts["execution"]
    spans = objects(execution.get("spans")) if isinstance(execution, dict) else []
    active = next(
        (span for span in reversed(spans) if span["phase"] != "case" and span["end_ms"] is None),
        None,
    )
    elapsed = summary["duration_ms"]
    seconds = max(0, int(float(str(elapsed)) / 1000)) if elapsed is not None else None
    last_activity = str(execution["updated_at"]) if isinstance(execution, dict) else ""
    age_text = last_activity[:19].replace("T", " ") if last_activity else "—"
    observed = object_value(value["worker"])["observed_at"]
    if isinstance(observed, str) and last_activity:
        try:
            age = int(
                (
                    datetime.fromisoformat(observed) - datetime.fromisoformat(last_activity)
                ).total_seconds()
            )
            if age < 0:
                age_text = text("activity.clock_difference")
            else:
                unit, divisor = next(
                    (
                        (unit, divisor)
                        for unit, divisor in (
                            ("days", 86400),
                            ("hours", 3600),
                            ("minutes", 60),
                            ("seconds", 1),
                        )
                        if age >= divisor
                    ),
                    ("seconds", 1),
                )
                age_text = text("activity.age_" + unit, count=age // divisor)
        except ValueError:
            age_text = "—"
    comparison = value.get("comparison")
    baseline_ref = request.query_params.get("baseline", "")
    before_url = ""
    if isinstance(comparison, dict) and baseline_ref:
        reference = _reference(baseline_ref)
        before_url = ("/runs/" if reference["kind"] == "run" else "/baselines/") + str(
            reference["id"]
        )
    return {
        "title": str(target["name"]),
        "active": "run",
        "view": value,
        "facts": facts,
        "job": job,
        "target": target,
        "summary": summary,
        "groups": groups,
        "findings": shown_findings,
        "all_findings": findings,
        "attention": findings[:3],
        "cases": shown_cases,
        "all_cases": cases,
        "issue": selected_issue,
        "selected_case": selected_case,
        "issue_checks": issue_checks,
        "displayed_issue_checks": displayed_issue_checks,
        "issue_observations": issue_observations,
        "issue_cases": [{"case_id": member, "name": case_name(member)} for member in issue_members],
        "issue_case": issue_case,
        "case_checks": case_checks,
        "case_name": case_name,
        "view_url": link,
        "active_view": selected_view,
        "view_template": "workbench-" + selected_view + ".html",
        "selected_filter": selected_filter,
        "search": search,
        "matrix_label": matrix_label,
        "matrix_link": matrix_link,
        "read_only": read_only,
        "terminal": terminal,
        "installed_count": len(list_cases()),
        "elapsed_text": f"{seconds // 60:02}:{seconds % 60:02}" if seconds is not None else "—",
        "active_span": active,
        "last_activity": last_activity,
        "last_activity_text": age_text,
        "spans": spans,
        "recorded_case_states": {
            str(item["case_id"]): str(item["state"])
            for item in objects(execution.get("case_states"))
        }
        if isinstance(execution, dict)
        else {},
        "evidence_prefix": "/api/v1/runs/" + str(facts["run_id"]) + "/evidence/",
        "baseline_options": _scope_options(request, str(facts["run_id"]))
        if selected_view == "compare"
        else [],
        "baseline_ref": baseline_ref,
        "comparison_groups": group_comparison(comparison) if isinstance(comparison, dict) else [],
        "comparison_before_url": before_url,
        "behavior_pass": sum(
            object_value(case["dimensions"])["behavior"] == "PASS" for case in cases
        ),
        "protocol_fail": sum(
            object_value(case["dimensions"])["protocol"] == "FAIL" for case in cases
        ),
        "bootstrap": {
            "page": "workbench",
            "workbench": value,
            "run_id": facts["run_id"],
            "read_only": read_only,
        },
    }


def workbench_page(request: Request, run_id: str) -> HTMLResponse:
    selected = request.query_params.get("view", "overview")
    if selected not in VIEWS or set(request.query_params) - {
        "view",
        "issue",
        "case",
        "filter",
        "baseline",
        "q",
    }:
        raise ValueError("invalid_request")
    view, original = local_workbench(
        request, run_id, request.query_params.get("baseline") if selected == "compare" else None
    )
    context = workbench_context(
        request, view, original, base_url="/runs/" + run_id, selected_view=selected
    )
    return page("workbench.html", context, request=request)


@router.get("/imports", response_class=HTMLResponse, include_in_schema=False)
def imports_page(request: Request) -> HTMLResponse:
    return page(
        "import.html",
        {
            "title_key": "import.title",
            "active": "import",
            "baseline_options": [
                option
                for option in _scope_options(request, "")
                if str(option["value"]).startswith("baseline:")
            ],
            "bootstrap": {"page": "import"},
        },
        request=request,
    )


@router.get("/baselines/{baseline_id}", response_class=HTMLResponse, include_in_schema=False)
def baseline_page(baseline_id: str, request: Request) -> HTMLResponse:
    service = service_for(request)
    record = service.get(baseline_id).document
    source = service.load_source(baseline_id)
    facts = build_report_view(source).document
    frame: JsonObject = {
        "job": None,
        "execution": facts["execution"],
        "report": facts,
        "presentation": preferences_for(request).to_json(),
        "baseline": {key: record[key] for key in ("id", "source", "eligibility")},
        "evidence": [
            {
                "id": evidence_id(ref),
                "path": ref.path,
                "sha256": ref.sha256,
                "verified": not verify_evidence(
                    safe_path(service.store.root, str(record["artifact_root"])), (ref,)
                ),
            }
            for ref in source.evidence_refs
        ],
    }
    view = build_workbench_view(frame, worker_observation={"state": "unknown", "observed_at": None})
    validate_diagnostic(view.document, "workbench-view")
    selected = request.query_params.get("view", "overview")
    if selected not in VIEWS:
        raise ValueError("invalid_request")
    context = workbench_context(
        request,
        view,
        frame,
        base_url="/baselines/" + baseline_id,
        selected_view=selected,
        read_only=True,
    )
    context.update(
        record=record,
        active="import",
        evidence_prefix="/api/v1/diagnostics/baselines/" + baseline_id + "/evidence/",
    )
    return page("baseline.html", context, request=request)


@router.get("/api/v1/diagnostics/baselines/{baseline_id}/evidence/{identifier}")
def baseline_evidence(baseline_id: str, identifier: str, request: Request) -> Response:
    service = service_for(request)
    record, source = service.get(baseline_id).document, service.load_source(baseline_id)
    ref = next((ref for ref in source.evidence_refs if evidence_id(ref) == identifier), None)
    if ref is None:
        raise ValueError("evidence_not_found")
    root = safe_path(service.store.root, str(record["artifact_root"]))
    data = source_bytes(root, ref.path)
    if hashlib.sha256(data).hexdigest() != ref.sha256:
        raise ValueError("evidence_invalid")
    return Response(
        data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": 'attachment; filename="' + Path(ref.path).name + '"'},
    )
