"""Packaged server-rendered pages over the shared local job and report services."""

from __future__ import annotations

from importlib.resources import files
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from jinja2 import Environment, PackageLoader, select_autoescape
from markupsafe import Markup
from starlette.responses import HTMLResponse, Response

from anthropic_readiness.config import Limits
from anthropic_readiness.models import JsonObject, JsonValue, object_value
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.report_models import ReportView
from anthropic_readiness.report_reading import case_name
from anthropic_readiness.report_rendering import render_report_body
from anthropic_readiness.web.api import LocalRoute, catalog_document, manager_for, run_document

router = APIRouter(route_class=LocalRoute)
ENVIRONMENT = Environment(
    loader=PackageLoader("anthropic_readiness", "resources/web"),
    autoescape=select_autoescape(("html",)),
)
STATE_NAMES = {
    "queued": "排队中",
    "running": "执行中",
    "cancelling": "正在取消",
    "completed": "执行完成",
    "cancelled": "已取消",
    "interrupted": "已中断",
    "error": "执行错误",
    "pending": "待评估",
    "PASS": "通过",
    "FAIL": "未通过",
    "INDETERMINATE": "证据不足",
    "BLOCKED": "环境阻塞",
    "SKIP": "跳过",
}
ASSETS = {
    "web/app.css",
    "web/app.js",
    "web/forms.js",
    "web/progress.js",
    "web/report.js",
    "report-v2.css",
    "report-v2.js",
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


def page(name: str, context: dict[str, object]) -> HTMLResponse:
    return HTMLResponse(ENVIRONMENT.get_template(name).render(**context, state_names=STATE_NAMES))


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
        "capabilities": {"streaming": True, "tools": True},
        "response_model_policy": "request_or_alias",
        "response_model_aliases": [],
        "limits": Limits().to_json(),
    }


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
@router.get("/new", response_class=HTMLResponse, include_in_schema=False)
def configure(request: Request, copy: str | None = None) -> HTMLResponse:
    manager = manager_for(request)
    catalog = catalog_document(manager)
    target = initial_target(catalog)
    profiles = [str(profile["id"]) for profile in objects(catalog["profiles"])]
    if copy:
        frozen = manager.store.get_admitted_plan(copy)
        target, profiles = frozen.target, list(frozen.profiles)
    profile_values: list[JsonValue] = list(profiles)
    bootstrap: JsonObject = {
        "page": "configure",
        "catalog": catalog,
        "target": target,
        "profiles": profile_values,
        "copied": bool(copy),
        "presets": list(manager.store.presets()),
    }
    return page(
        "configure.html",
        {
            "title": "新建评估",
            "active": "new",
            "bootstrap": bootstrap,
            "target": target,
            "catalog": catalog,
            "profiles": profiles,
            "copied": bool(copy),
            "limits": target["limits"],
        },
    )


@router.get("/runs/{run_id}", response_class=HTMLResponse, include_in_schema=False)
def assessment(run_id: str, request: Request) -> HTMLResponse:
    document = run_document(manager_for(request), run_id)
    report = document["report"]
    rendered = render_report_body(ReportView(report)) if isinstance(report, dict) else ""
    if request.query_params.get("fragment") == "report":
        return HTMLResponse(rendered)
    frozen = object_value(document["plan"])
    planned = objects(object_value(frozen["plan"])["cases"])
    case_states = (
        {
            str(case["case_id"]): str(case["state"])
            for case in objects(object_value(document["execution"])["case_states"])
        }
        if isinstance(document["execution"], dict)
        else {}
    )
    cases: list[JsonObject] = [
        {
            "id": case["id"],
            "name": case_name(case["id"]),
            "state": case_states.get(str(case["id"]), "pending"),
        }
        for case in planned
    ]
    return page(
        "run.html",
        {
            "title": "评估记录",
            "active": "run",
            "bootstrap": {"page": "run", "run": document},
            "run": document,
            "cases": cases,
            "report_html": Markup(rendered),
            "target": frozen["target"],
            "plan": frozen["plan"],
            "job": document["job"],
            "execution": document["execution"],
        },
    )


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
            "active": "history",
            "bootstrap": {"page": "history"},
            "items": items,
            "filters": filters,
            "next_url": next_url,
        },
    )


@router.get("/assets/{asset:path}", include_in_schema=False)
def asset(asset: str) -> Response:
    if asset not in ASSETS:
        return Response(status_code=404)
    content = files("anthropic_readiness").joinpath("resources/" + asset).read_bytes()
    return Response(content, media_type="text/css" if asset.endswith(".css") else "text/javascript")
