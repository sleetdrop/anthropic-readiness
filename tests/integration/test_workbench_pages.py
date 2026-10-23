"""New workbench pages use checked facts, normal links and escaped localization."""

import hashlib
import multiprocessing
import time
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import httpx
import pytest
from fastapi import FastAPI

from anthropic_readiness.config import load_target
from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.jobs.manager import JobManager, OwnedWorker
from anthropic_readiness.models import JsonObject, object_value
from anthropic_readiness.web import api
from tests.diagnostic_fixtures import portable_archive
from tests.export_fixtures import prepared_run
from tests.http_server import SyntheticServer
from tests.integration.test_web_api import preview, start_body
from tests.web_fixtures import anyio_backend as anyio_backend
from tests.web_fixtures import client as client
from tests.web_fixtures import csrf_headers, wait_run
from tests.web_fixtures import web_app as web_app

pytestmark = pytest.mark.anyio
ROOT = Path(__file__).resolve().parents[2]


async def test_console_list_search_and_occurrence_links_use_checked_facts(
    client: httpx.AsyncClient, seeded_run: str
) -> None:
    path = "/runs/" + seeded_run
    listing = await client.get(path, params={"view": "issues"})
    assert listing.status_code == 200
    assert 'class="issues-table"' in listing.text
    assert 'id="issue-inspector"' not in listing.text
    assert 'id="completion-bar"' in listing.text
    assert 'id="language-toggle"' in listing.text
    found = await client.get(path, params={"view": "issues", "q": "stop_sequence"})
    assert found.status_code == 200
    assert "stop_sequence" in found.text
    absent = await client.get(path, params={"view": "issues", "q": "never-in-fixture"})
    assert absent.status_code == 200
    assert "data-issue-key=" not in absent.text
    escaped = await client.get(path, params={"view": "issues", "q": '<img src=x onerror="bad">'})
    assert '<img src=x onerror="bad">' not in escaped.text
    assert (await client.get(path, params={"view": "issues", "q": "x" * 201})).status_code == 422


@pytest.fixture(autouse=True)
def seeded_run(tmp_path: Path, request: pytest.FixtureRequest) -> str:
    scenario = getattr(request, "param", "complete")
    target = load_target(ROOT / "examples/target.yaml")
    if scenario == "larger-cap":
        target = replace(target, limits=replace(target.limits, max_requests=7))
    if scenario == "hostile":
        target = replace(target, model='model <img src=x onerror="window.unsafe=1"> & co')
    return prepared_run(
        tmp_path,
        partial=scenario == "partial",
        keep_unpublished=scenario == "partial",
        target=target,
    )


async def test_run_uses_independent_workbench_views_and_neutral_completion(
    client: httpx.AsyncClient, tmp_path: Path, seeded_run: str
) -> None:
    run_id = seeded_run
    response = await client.get("/runs/" + run_id)
    assert response.status_code == 200
    html = response.text
    assert 'data-workbench-version="2.0"' in html
    assert 'data-lifecycle="completed"' in html
    assert 'data-lifecycle-tone="neutral"' in html
    assert 'id="report-panel"' not in html
    assert 'href="/assets/report-v2.css"' not in html
    for view in ("overview", "issues", "cases", "compare", "activity"):
        assert f"view={view}" in html
        page = await client.get("/runs/" + run_id, params={"view": view})
        assert page.status_code == 200
        assert f'data-active-view="{view}"' in page.text
    cases = await client.get("/runs/" + run_id, params={"view": "cases"})
    assert "通过 / 已评估" in cases.text
    assert "Claude Code 工作流未评估" in html


async def test_checked_theme_and_language_are_applied_before_css(
    client: httpx.AsyncClient, tmp_path: Path, seeded_run: str
) -> None:
    run_id = seeded_run
    client.cookies.set("readiness_preferences", "v1.en.dark", domain="localhost.local", path="/")
    response = await client.get("/runs/" + run_id)
    html = response.text
    assert '<html lang="en" data-theme="dark">' in html
    assert ">Overview<" in html
    assert "Claude Code workflows not assessed" in html
    assert '"zh-CN"' in html
    assert '"en"' in html
    assert 'id="language-toggle"' in html
    assert 'id="theme-toggle"' in html


@pytest.mark.parametrize("seeded_run", ["partial"], indirect=True)
async def test_partial_workbench_keeps_unfinished_records_visible(
    client: httpx.AsyncClient, tmp_path: Path, seeded_run: str
) -> None:
    run_id = seeded_run
    response = await client.get("/runs/" + run_id, params={"view": "cases"})
    assert response.status_code == 200
    assert "部分记录" in response.text
    assert "已中断" in response.text
    assert "ANT-TEXT-SSE-002" in response.text
    assert not (tmp_path / "runs" / run_id / "exports").exists()


async def test_imported_baseline_and_retest_configuration_do_not_reuse_endpoint(
    client: httpx.AsyncClient, tmp_path: Path
) -> None:
    archive, source = portable_archive(tmp_path / "producer")
    service = DiagnosticService(tmp_path)
    now = datetime.now(UTC)
    preview = service.preview(archive, "a" * 64, now=now)
    record = service.commit(str(preview["preview_id"]), "a" * 64, now=now)
    baseline_id = str(record.document["id"])
    imported = await client.get("/baselines/" + baseline_id)
    assert imported.status_code == 200
    assert 'data-read-only="true"' in imported.text
    assert 'throw Error("uploaded")' not in imported.text
    configuration = await client.get("/new", params={"baseline": baseline_id})
    assert configuration.status_code == 200
    assert 'id="endpoint"' in configuration.text
    assert 'data-baseline-id="' + baseline_id + '"' in configuration.text
    assert 'value="http://127.0.0.1:8000/v1/messages"' not in configuration.text
    assert (await client.get("/imports")).status_code == 200
    assert (source / "result.json").exists()


@pytest.mark.parametrize("seeded_run", ["hostile"], indirect=True)
async def test_localized_metadata_is_literal_text_at_the_real_template_boundary(
    client: httpx.AsyncClient, tmp_path: Path, seeded_run: str
) -> None:
    run_id = seeded_run
    response = await client.get("/runs/" + run_id)
    assert response.status_code == 200
    assert "&lt;img" in response.text
    assert "&amp; co" in response.text
    assert "&amp;amp; co" not in response.text
    assert '<img src=x onerror="window.unsafe=1">' not in response.text


async def test_worker_observation_reports_owned_process_without_a_heartbeat(
    web_app: FastAPI, client: httpx.AsyncClient, tmp_path: Path, seeded_run: str
) -> None:
    run_id = seeded_run
    manager = cast(JobManager, web_app.state.manager)
    observed = manager.worker_observation(run_id)
    assert observed["state"] == "not_running"
    assert observed["observed_at"]


async def test_owned_worker_observation_does_not_follow_completed_job_state(
    web_app: FastAPI, client: httpx.AsyncClient, seeded_run: str
) -> None:
    active_manager = cast(JobManager, web_app.state.manager)
    manager = JobManager(active_manager.store, credential_allowlist={})
    process = multiprocessing.get_context("spawn").Process(target=time.sleep, args=(5,))
    control, control_peer = multiprocessing.Pipe()
    observations, observation_peer = multiprocessing.Pipe()
    try:
        process.start()
        manager._active = OwnedWorker(seeded_run, process, control, observations)
        assert manager.store.get_job(seeded_run).state == "completed"
        assert manager.worker_observation(seeded_run)["state"] == "running"
        process.terminate()
        process.join(timeout=5)
        assert manager.worker_observation(seeded_run)["state"] == "not_running"
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        process.close()
        for connection in (control, control_peer, observations, observation_peer):
            connection.close()


async def test_workbench_terminal_projection_rejects_an_earlier_generation(
    client: httpx.AsyncClient,
    web_app: FastAPI,
    tmp_path: Path,
    server: SyntheticServer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = await csrf_headers(client)
    planned = await preview(client, headers, server.url + "/cases")
    started = await client.post(
        "/api/v1/runs", headers=headers, json=start_body(planned, "workbench-generation")
    )
    run_id = str(started.json()["id"])
    await wait_run(client, run_id)
    result_path = tmp_path / "runs" / run_id / "assessment/result.json"
    original_bytes = result_path.read_bytes()
    original = api._report_document
    sent_stale = False

    def stale_once(manager: JobManager, identifier: str) -> JsonObject | None:
        nonlocal sent_stale
        current = original(manager, identifier)
        if current is not None and not sent_stale:
            sent_stale = True
            stale = deepcopy(current)
            stale.update(status="partial", source_result_sha256=None)
            return stale
        return current

    monkeypatch.setattr(api, "_report_document", stale_once)
    response = await client.get(f"/api/v1/runs/{run_id}/workbench")
    assert response.status_code == 200, response.text
    document = object_value(response.json())
    assert sent_stale
    assert object_value(document["job"])["state"] == "completed"
    facts = object_value(document["facts"])
    assert facts["status"] == "complete"
    assert facts["source_result_sha256"] == hashlib.sha256(original_bytes).hexdigest()
    assert result_path.read_bytes() == original_bytes


@pytest.mark.parametrize("seeded_run", ["larger-cap"], indirect=True)
async def test_request_denominator_uses_admitted_cap_not_selected_case_count(
    client: httpx.AsyncClient, seeded_run: str
) -> None:
    response = await client.get("/runs/" + seeded_run)
    assert response.status_code == 200
    assert 'id="request-progress">3 / 7</strong>' in response.text


async def test_matrix_filter_is_closed_and_opens_only_matching_dimension_members(
    client: httpx.AsyncClient, seeded_run: str
) -> None:
    path = "/runs/" + seeded_run
    matrix = await client.get(path, params={"view": "cases"})
    assert "filter=matrix%3Astreaming%3Aprotocol%3AFAIL" in matrix.text
    filtered = await client.get(
        path, params={"view": "cases", "filter": "matrix:streaming:protocol:FAIL"}
    )
    assert filtered.status_code == 200
    assert filtered.text.count('class="case-item"') == 2
    assert 'data-case-id="ANT-MESSAGE-001"' not in filtered.text
    assert 'data-case-id="ANT-TEXT-SSE-001"' in filtered.text
    for invalid in (
        "matrix:streaming:unknown:FAIL",
        "matrix:../../outside:protocol:FAIL",
        "matrix:streaming:protocol:unknown",
    ):
        response = await client.get(path, params={"view": "cases", "filter": invalid})
        assert response.status_code == 422
