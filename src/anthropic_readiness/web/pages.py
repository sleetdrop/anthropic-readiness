"""Packaged server-rendered pages over the shared local job and report services."""

from __future__ import annotations

from importlib.resources import files
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse, Response

from anthropic_readiness.cases import list_cases
from anthropic_readiness.config import Limits
from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.models import JsonObject, JsonValue, object_value
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.report_models import ReportView
from anthropic_readiness.report_rendering import render_report_body
from anthropic_readiness.web.api import LocalRoute, catalog_document, manager_for, run_document
from anthropic_readiness.web.templating import page

router = APIRouter(route_class=LocalRoute)
ASSETS = {
    "web/workbench-links.js",
    "web/workbench.js",
    "web/diagnostics.js",
    "web/app.css",
    "web/app.js",
    "web/forms.js",
    "web/progress.js",
    "web/report.js",
    "report-v2.css",
    "report-v2.js",
    "themes.css",
    "web/icons/document-text.svg",
    "web/icons/plus.svg",
    "web/icons/arrow-up-tray.svg",
    "web/icons/stop.svg",
    "web/icons/chevron-right.svg",
}
FILTERS = {
    "state",
    "target_name",
    "model",
    "profile",
    "created_after",
    "created_before",
    "contract_id",
    "contract_revision",
    "api_version",
}


def initial_target(catalog: JsonObject) -> JsonObject:
    contract = objects(catalog["contracts"])[0]
    return {
        "schema_version": "1.0",
        "name": "local-assessment",
        "delivery_id": "local-web",
        "protocol": "anthropic.messages",
        "messages_url": "",
        "model": "",
        "api_version": contract["api_version"],
        "beta_headers": contract["beta_headers"],
        "protocol_contract": {"id": contract["id"], "revision": contract["revision"]},
        "auth": {"mode": "none"},
        "capabilities": {
            "streaming": True,
            "tools": True,
            "thinking": False,
            "parallel_tools": False,
        },
        "response_model_policy": "request_or_alias",
        "response_model_aliases": [],
        "limits": Limits(max_requests=sum(case.request_count for case in list_cases())).to_json(),
    }


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
@router.get("/new", response_class=HTMLResponse, include_in_schema=False)
def configure(
    request: Request, copy: str | None = None, baseline: str | None = None
) -> HTMLResponse:
    manager = manager_for(request)
    catalog = catalog_document(manager)
    target = initial_target(catalog)
    profiles = [str(profile["id"]) for profile in objects(catalog["profiles"])]
    if copy:
        frozen = manager.store.get_admitted_plan(copy)
        target, profiles = frozen.target, list(frozen.profiles)
    reference: JsonObject | None = None
    retest_id: str | None = None
    if baseline:
        if copy:
            raise ValueError("invalid_request")
        service = DiagnosticService(manager.store.root)
        record = service.get(baseline).document
        source = service.load_source(baseline)
        original_target = (
            source.result.target
            if source.result is not None
            else object_value(source.execution["target"])
            if source.execution is not None
            else {}
        )
        reference = {
            "baseline_id": baseline,
            "target": original_target,
            "eligibility": record["eligibility"],
        }
        target = {**original_target, "messages_url": "", "auth": {"mode": "none"}}
        profiles = [str(profile["id"]) for profile in objects(source.plan["profiles"])]
        if object_value(record["eligibility"])["retest"] is True:
            retest_id = baseline
    profile_values: list[JsonValue] = list(profiles)
    bootstrap: JsonObject = {
        "page": "configure",
        "catalog": catalog,
        "target": target,
        "profiles": profile_values,
        "copied": bool(copy),
        "presets": list(manager.store.presets()),
        "baseline_id": retest_id,
        "reference": reference,
    }
    return page(
        "configure.html",
        {
            "title": "新建评估",
            "title_key": "form.title",
            "active": "new",
            "bootstrap": bootstrap,
            "target": target,
            "catalog": catalog,
            "profiles": profiles,
            "copied": bool(copy),
            "limits": target["limits"],
            "reference": reference,
            "baseline_id": retest_id,
        },
        request=request,
    )


@router.get("/runs/{run_id}", response_class=HTMLResponse, include_in_schema=False)
def assessment(run_id: str, request: Request) -> HTMLResponse:
    if request.query_params.get("fragment") == "report":
        document = run_document(manager_for(request), run_id)
        report = document["report"]
        return HTMLResponse(
            render_report_body(ReportView(report)) if isinstance(report, dict) else ""
        )
    from anthropic_readiness.web.workbench import workbench_page

    return workbench_page(request, run_id)


@router.get("/history", response_class=HTMLResponse, include_in_schema=False)
def history(request: Request, cursor: str | None = None) -> HTMLResponse:
    if set(request.query_params) - {*FILTERS, "cursor"}:
        raise ValueError("invalid_history_filter")
    filters: JsonObject = {
        key: value for key, value in request.query_params.items() if key in FILTERS and value
    }
    manager = manager_for(request)
    document = manager.store.history(filters, cursor, 25)
    items = objects(document["items"])
    for item in items:
        try:
            item["execution"] = manager.snapshot(str(object_value(item["job"])["id"]))["execution"]
        except (OSError, ValueError):
            item["execution"] = None
    next_url = (
        "/history?" + urlencode({**filters, "cursor": document["next_cursor"]})
        if document["next_cursor"]
        else None
    )
    return page(
        "history.html",
        {
            "title": "评估历史",
            "title_key": "history.title",
            "active": "history",
            "bootstrap": {"page": "history"},
            "items": items,
            "filters": filters,
            "next_url": next_url,
        },
        request=request,
    )


@router.get("/assets/{asset:path}", include_in_schema=False)
def asset(asset: str) -> Response:
    if asset not in ASSETS:
        return Response(status_code=404)
    content = files("anthropic_readiness").joinpath("resources/" + asset).read_bytes()
    media = (
        "image/svg+xml"
        if asset.endswith(".svg")
        else "text/css"
        if asset.endswith(".css")
        else "text/javascript"
    )
    return Response(content, media_type=media)
