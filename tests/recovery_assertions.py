"""Check actual HTTP and ZIP access to retained interrupted-run evidence."""

import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx

from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.web.app import create_app
from anthropic_readiness.web.settings import WebSettings
from tests.web_fixtures import ORIGIN, csrf_headers


async def assert_recovered_interfaces(root: Path, run_id: str, manager: JobManager) -> None:
    app = create_app(data_root=root, settings=WebSettings())
    app.state.manager = manager
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=ORIGIN) as client:
        headers = await csrf_headers(client)
        response = await client.get("/api/v1/runs/" + run_id)
        assert response.status_code == 200
        document = response.json()
        report = document["report"]
        assert report["status"] == "partial"
        assert report["source_result_sha256"] is None
        assert report["summary"]["completed_cases"] == 1
        assert report["summary"]["planned_cases"] == 3
        assert report["summary"]["actual_requests"] == 1
        assert any("恢复" in note for note in report["limitations"])
        assert document["evidence"]
        for ref in document["evidence"]:
            copied = await client.get(f"/api/v1/runs/{run_id}/evidence/{ref['id']}")
            assert copied.status_code == 200
            assert hashlib.sha256(copied.content).hexdigest() == ref["sha256"]
        policy = {"formats": ["zip"], "include_evidence": True}
        preview = await client.post(
            f"/api/v1/runs/{run_id}/exports/preview", json=policy, headers=headers
        )
        assert preview.status_code == 200
        assert any(name.startswith("evidence/") for name in preview.json()["files"])
        created = await client.post(f"/api/v1/runs/{run_id}/exports", json=policy, headers=headers)
        assert created.status_code == 201
        export_id = created.json()["export_id"]
        download = await client.get(f"/api/v1/runs/{run_id}/exports/{export_id}")
        assert download.status_code == 200
        with ZipFile(BytesIO(download.content)) as package:
            assert "result.json" not in package.namelist()
            checkpoint = "operations/checkpoints/ANT-MESSAGE-001.json"
            assert json.loads(package.read(checkpoint))["run_id"] == run_id
            assert "恢复" in package.read("report.html").decode()
            manifest = json.loads(package.read("manifest.json"))
            for entry in manifest["files"]:
                assert hashlib.sha256(package.read(entry["path"])).hexdigest() == entry["sha256"]
