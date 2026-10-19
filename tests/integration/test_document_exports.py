"""Versioned presentation choices are honored at the authenticated export boundary."""

import json
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from anthropic_readiness.models import JsonObject, object_value
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.web.app import create_app
from anthropic_readiness.web.settings import WebSettings
from tests.export_fixtures import prepared_run
from tests.web_fixtures import anyio_backend as anyio_backend
from tests.web_fixtures import client as client
from tests.web_fixtures import csrf_headers

pytestmark = pytest.mark.anyio


@pytest.fixture
def web_app(tmp_path: Path) -> FastAPI:
    run_id = prepared_run(tmp_path)
    app = create_app(data_root=tmp_path, settings=WebSettings())
    app.state.fixture_run_id = run_id
    return app


async def test_versioned_export_uses_explicit_presentation_and_validates_response(
    client: httpx.AsyncClient, web_app: FastAPI
) -> None:
    run_id = web_app.state.fixture_run_id
    headers = await csrf_headers(client)
    policy: JsonObject = {
        "schema_version": "2.0",
        "formats": ["zip"],
        "include_evidence": False,
        "presentation": {"schema_version": "1.0", "locale": "en", "theme": "dark"},
    }
    preview = await client.post(
        f"/api/v1/runs/{run_id}/exports/preview", json=policy, headers=headers
    )
    assert preview.status_code == 200, preview.text
    value = preview.json()
    validate_operational({"kind": "diagnostic_export_preview", "data": value}, "web-api")
    assert value["presentation"] == policy["presentation"]
    assert "document-view.json" in value["files"]
    created = await client.post(f"/api/v1/runs/{run_id}/exports", json=policy, headers=headers)
    assert created.status_code == 201, created.text
    record = created.json()
    validate_operational({"kind": "diagnostic_export_response", "data": record}, "web-api")
    assert record["manifest"]["presentation"] == policy["presentation"]
    for format in ("html", "json"):
        response = await client.get(
            f"/api/v1/runs/{run_id}/exports/{record['export_id']}?format={format}"
        )
        assert response.status_code == 200
        if format == "html":
            assert '<html lang="en" data-theme="dark"' in response.text
        else:
            assert 'filename="document-view.json"' in response.headers["content-disposition"]
            assert json.loads(response.content)["presentation_version"] == "3.0"
    rejected = await client.post(
        f"/api/v1/runs/{run_id}/exports",
        json={
            **policy,
            "presentation": {**object_value(policy["presentation"]), "theme": "invalid"},
        },
        headers=headers,
    )
    assert rejected.status_code == 422


async def test_selected_comparison_is_exported_without_starting_requests(
    client: httpx.AsyncClient, web_app: FastAPI
) -> None:
    run_id = web_app.state.fixture_run_id
    headers = await csrf_headers(client)
    response = await client.post(
        f"/api/v1/runs/{run_id}/exports",
        json={
            "schema_version": "2.0",
            "formats": ["zip"],
            "include_evidence": False,
            "presentation": {"schema_version": "1.0", "locale": "en", "theme": "light"},
            "baseline": {"kind": "run", "id": run_id},
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    record = response.json()
    document = await client.get(f"/api/v1/runs/{run_id}/exports/{record['export_id']}?format=json")
    assert document.status_code == 200
    value = document.json()
    assert value["comparison"]["after"]["run_id"] == run_id
    assert value["comparison"]["comparable"] is False
    assert value["comparison"]["summary"]["incomparable"] > 0
    assert value["comparison"]["all_previous_failures_passed"] is False
