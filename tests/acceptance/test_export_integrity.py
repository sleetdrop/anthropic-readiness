"""HTTP export is a session-protected local action with zero extra model calls."""

import hashlib
import json
import re
from io import BytesIO
from zipfile import ZipFile

import httpx
import pytest

from tests.http_server import SyntheticServer
from tests.integration.test_web_api import preview, start_body
from tests.web_fixtures import anyio_backend as anyio_backend
from tests.web_fixtures import client as client
from tests.web_fixtures import csrf_headers, wait_run
from tests.web_fixtures import web_app as web_app

pytestmark = pytest.mark.anyio


async def test_export_downloads_are_verified_and_make_zero_extra_requests(
    client: httpx.AsyncClient, server: SyntheticServer
) -> None:
    headers = await csrf_headers(client)
    plan = await preview(client, headers, server.url + "/cases")
    started = await client.post(
        "/api/v1/runs", json=start_body(plan, "export-fixture"), headers=headers
    )
    run_id = str(started.json()["id"])
    await wait_run(client, run_id)
    count = len(server.requests)
    policy = {"formats": ["zip"], "include_evidence": True}
    planned = await client.post(
        f"/api/v1/runs/{run_id}/exports/preview", json=policy, headers=headers
    )
    assert planned.status_code == 200
    assert planned.json()["files"]
    exported = await client.post(f"/api/v1/runs/{run_id}/exports", json=policy, headers=headers)
    assert exported.status_code == 201
    export_id = str(exported.json()["export_id"])
    response = await client.get(f"/api/v1/runs/{run_id}/exports/{export_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"].startswith("attachment;")
    assert hashlib.sha256(response.content).hexdigest() == exported.json()["artifact"]["sha256"]
    with ZipFile(BytesIO(response.content)) as package:
        assert "diagnostic-package.json" in package.namelist()
        html = package.read("report.html").decode()
        ids = set(re.findall(r'\bid="([^"]+)"', html))
        assert all(reference in ids for reference in re.findall(r'href="#([^"]+)"', html))
        assert json.loads(package.read("result.json"))["run_id"] == run_id
    standalone = await client.get(
        f"/api/v1/runs/{run_id}/exports/{export_id}", params={"format": "html"}
    )
    assert standalone.status_code == 200
    assert standalone.headers["content-type"].startswith("text/html")
    assert "<html" in standalone.text
    assert len(server.requests) == count == 3
    assert (await client.get(f"/api/v1/runs/{run_id}/exports/..%2F..%2Foutside")).status_code in {
        404,
        422,
    }
