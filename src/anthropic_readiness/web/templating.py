"""Escaped request-local templates over shared presentation choices and catalogs."""

from typing import cast

from fastapi import Request
from jinja2 import Environment, PackageLoader, select_autoescape
from starlette.responses import HTMLResponse

from anthropic_readiness.localization import load_catalog, translate
from anthropic_readiness.models import JsonObject, object_value
from anthropic_readiness.presentation import LOCALES
from anthropic_readiness.web.security import preferences_for
from anthropic_readiness.web.ui_assets import UIAssets

ENVIRONMENT = Environment(
    loader=PackageLoader("anthropic_readiness", "resources/web"),
    autoescape=select_autoescape(("html",)),
)
STATE_KEYS = {
    "queued": "run.queued",
    "running": "run.running",
    "cancelling": "run.cancelling",
    "completed": "run.completed",
    "cancelled": "run.cancelled",
    "interrupted": "run.interrupted",
    "error": "run.error",
    "pending": "run.pending",
    "PASS": "check.pass",
    "FAIL": "check.fail",
    "INDETERMINATE": "check.indeterminate",
    "BLOCKED": "check.blocked",
    "SKIP": "check.skip",
    "not_evaluated": "check.unassessed",
    "missing": "check.missing",
}
CASE_KEYS = {
    "ANT-MESSAGE-001": "case.message",
    "ANT-TEXT-SSE-001": "case.sse_greeting",
    "ANT-TEXT-SSE-002": "case.sse_count",
    "ANT-TOOL-FORCED-001": "case.forced_tool",
    "ANT-TOOL-LOOP-001": "case.tool_loop",
}


def page(name: str, context: dict[str, object], *, request: Request) -> HTMLResponse:
    ui_assets = cast(UIAssets, request.app.state.ui_assets)
    options = preferences_for(request)
    catalog = load_catalog(options.locale)

    def text(key: str, **params: str | int | float) -> str:
        return translate(catalog, key, params)

    def case_name(identifier: str) -> str:
        return text(CASE_KEYS[identifier]) if identifier in CASE_KEYS else identifier

    def profile_name(identifier: str) -> str:
        key = {
            "anthropic-basic": "profile.basic",
            "anthropic-tools-smoke": "profile.tools",
            "anthropic-tool-loop": "profile.tool_loop",
        }.get(identifier)
        return text(key) if key else identifier

    def phase_name(phase: str) -> str:
        key = "phase." + phase
        return text(key) if key in catalog else phase

    catalogs: JsonObject = {}
    for locale in LOCALES:
        messages: JsonObject = {}
        messages.update(load_catalog(locale))
        catalogs[locale] = messages
    bootstrap = object_value(context.get("bootstrap", {}))
    bootstrap.update(
        presentation=options.to_json(), catalogs=catalogs, ui_revision=ui_assets.revision
    )
    values = {
        **context,
        "bootstrap": bootstrap,
        "ui_revision": ui_assets.revision,
        "asset_url": ui_assets.url,
        "presentation": options.to_json(),
        "catalogs": catalogs,
        "t": text,
        "case_name": case_name,
        "profile_name": profile_name,
        "phase_name": phase_name,
        "state_names": {state: text(key) for state, key in STATE_KEYS.items()},
    }
    if isinstance(context.get("title_key"), str):
        values["title"] = text(str(context["title_key"]))
    return HTMLResponse(ENVIRONMENT.get_template(name).render(**values))
