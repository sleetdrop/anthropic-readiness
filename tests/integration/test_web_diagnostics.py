"""Only the authenticated ZIP route streams binary input; all other mutations stay JSON."""

import asyncio
import shutil
import time
from collections.abc import AsyncIterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event, Lock
from types import SimpleNamespace
from typing import cast

import httpx
import pytest
from fastapi import FastAPI
from starlette.types import Message, Scope

from anthropic_readiness.config import load_target
from anthropic_readiness.diagnostics.contracts import validate_storage
from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.models import JsonObject, object_value
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.presentation import parse_preferences
from anthropic_readiness.web.settings import WebSettings
from tests.diagnostic_fixtures import portable_archive
from tests.http_server import SyntheticServer
from tests.web_fixtures import ORIGIN, csrf_headers, wait_run
from tests.web_fixtures import anyio_backend as anyio_backend
from tests.web_fixtures import client as client
from tests.web_fixtures import web_app as web_app

pytestmark = pytest.mark.anyio
UPLOAD = "/api/v1/diagnostics/imports/preview"
ROOT = Path(__file__).resolve().parents[2]


async def chunks(data: bytes) -> AsyncIterator[bytes]:
    for offset in range(0, len(data), 1024):
        yield data[offset : offset + 1024]
        await asyncio.sleep(0)


async def uploaded(client: httpx.AsyncClient, headers: dict[str, str], archive: Path) -> JsonObject:
    response = await client.post(
        UPLOAD,
        headers={**headers, "Content-Type": "application/zip"},
        content=chunks(archive.read_bytes()),
    )
    assert response.status_code == 200, response.text
    return object_value(response.json())


async def test_chunked_import_retest_preview_and_comparison_use_normal_start(
    client: httpx.AsyncClient, web_app: FastAPI, tmp_path: Path, server: SyntheticServer
) -> None:
    archive, _ = portable_archive(tmp_path / "producer")
    headers = await csrf_headers(client)
    preview = await uploaded(client, headers, archive)
    assert preview["eligibility"]
    committed = await client.post(
        "/api/v1/diagnostics/imports/commit",
        json={"preview_id": preview["preview_id"]},
        headers=headers,
    )
    assert committed.status_code == 201, committed.text
    baseline = committed.json()
    baseline_id = baseline["id"]
    read = await client.get(f"/api/v1/diagnostics/baselines/{baseline_id}")
    assert read.status_code == 200
    assert read.json()["baseline"]["id"] == baseline_id
    assert "<script>" not in read.text
    target = replace(load_target(ROOT / "examples/target.yaml"), messages_url=server.url + "/cases")
    prepared = await client.post(
        "/api/v1/diagnostics/retests/preview",
        json={"baseline_id": baseline_id, "target": target.to_json()},
        headers=headers,
    )
    assert prepared.status_code == 201, prepared.text
    plan = prepared.json()["plan"]
    assert plan["plan"]["planned_requests"] == 4
    manager = cast(JobManager, web_app.state.manager)
    context = manager.store.get_plan_context(plan["id"])
    assert context is not None
    assert object_value(context["baseline"])["baseline_id"] == baseline_id
    assert not server.requests
    response = await client.post(
        "/api/v1/runs",
        json={"plan_id": plan["id"], "live_consent": True, "idempotency_key": "diagnostic-retest"},
        headers=headers,
    )
    assert response.status_code == 202
    run_id = response.json()["id"]
    await wait_run(client, run_id)
    assert len(server.requests) == 4
    compared = await client.post(
        "/api/v1/diagnostics/comparisons",
        json={
            "before": {"kind": "baseline", "id": baseline_id},
            "after": {"kind": "run", "id": run_id},
        },
        headers=headers,
    )
    assert compared.status_code == 200, compared.text
    assert compared.json()["comparable"] is True
    assert compared.json()["after"]["run_id"] == run_id
    assert len(server.requests) == 4
    bad = await client.post(
        "/api/v1/diagnostics/comparisons",
        json={
            "before": {"kind": "path", "id": "/private/target"},
            "after": {"kind": "run", "id": run_id},
        },
        headers=headers,
    )
    assert bad.status_code == 422
    _, foreign = portable_archive(tmp_path / "foreign")
    assessment = tmp_path / "runs" / run_id / "assessment"
    assessment.rename(assessment.with_name("assessment-original"))
    shutil.copytree(foreign, assessment)
    substituted = await client.post(
        "/api/v1/diagnostics/comparisons",
        json={
            "before": {"kind": "baseline", "id": baseline_id},
            "after": {"kind": "run", "id": run_id},
        },
        headers=headers,
    )
    assert substituted.status_code == 409
    assert substituted.json()["error"]["code"] == "export_source_invalid"


@pytest.mark.parametrize("missing", ["origin", "csrf", "session"])
async def test_zip_requires_all_existing_mutation_guards(
    client: httpx.AsyncClient, missing: str
) -> None:
    headers = await csrf_headers(client)
    if missing == "origin":
        headers.pop("Origin")
    elif missing == "csrf":
        headers.pop("X-CSRF-Token")
    else:
        client.cookies.clear()
    consumed = False

    async def body() -> AsyncIterator[bytes]:
        nonlocal consumed
        consumed = True
        yield b"private-upload"

    response = await client.post(
        UPLOAD, headers={**headers, "Content-Type": "application/zip"}, content=body()
    )
    assert response.status_code in {401, 403}
    assert consumed is False


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/plans",
        "/api/v1/runs",
        "/api/v1/preferences",
        "/api/v1/diagnostics/imports/commit",
        "/api/v1/diagnostics/retests/preview",
        "/api/v1/diagnostics/comparisons",
        UPLOAD + "/",
    ],
)
async def test_zip_is_not_a_general_content_type_bypass(
    client: httpx.AsyncClient, path: str
) -> None:
    headers = await csrf_headers(client)
    response = await client.post(
        path, headers={**headers, "Content-Type": "application/zip"}, content=b"PK"
    )
    assert response.status_code == 415


async def test_upload_media_length_and_actual_limits_clean_staging(
    client: httpx.AsyncClient, web_app: FastAPI, tmp_path: Path
) -> None:
    headers = await csrf_headers(client)
    settings = replace(cast(WebSettings, web_app.state.settings), max_import_bytes=16)
    web_app.state.settings = settings
    web_app.state.security.settings = settings
    for extra, data, expected in [
        ({"Content-Type": "text/plain"}, b"PK", 415),
        ({"Content-Type": "application/zip", "Content-Length": "17"}, b"PK", 413),
        ({"Content-Type": "application/zip", "Content-Length": "-1"}, b"PK", 422),
        ({"Content-Type": "application/zip", "Content-Length": "1"}, b"PK", 422),
        ({"Content-Type": "application/zip"}, b"x" * 17, 413),
    ]:
        response = await client.post(UPLOAD, headers={**headers, **extra}, content=chunks(data))
        assert response.status_code == expected, response.text
    uploads = tmp_path / "diagnostics/uploads"
    assert not uploads.exists() or not list(uploads.iterdir())
    json_response = await client.post(
        "/api/v1/plans",
        headers={**headers, "Content-Type": "application/json"},
        content=b'{"x":"' + b"x" * 65536 + b'"}',
    )
    assert json_response.status_code == 413
    assert json_response.json()["error"]["code"] == "body_too_large"


async def test_import_preview_owner_and_expiry(
    client: httpx.AsyncClient, web_app: FastAPI, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, _ = portable_archive(tmp_path / "producer")
    headers = await csrf_headers(client)
    preview = await uploaded(client, headers, archive)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url=ORIGIN
    ) as other:
        other_headers = await csrf_headers(other)
        response = await other.post(
            "/api/v1/diagnostics/imports/commit",
            json={"preview_id": preview["preview_id"]},
            headers=other_headers,
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "diagnostic_preview_owner"
    from anthropic_readiness.web import diagnostics

    monkeypatch.setattr(diagnostics, "utc_now", lambda: datetime.now(UTC) + timedelta(hours=1))
    expired = await client.post(
        "/api/v1/diagnostics/imports/commit",
        json={"preview_id": preview["preview_id"]},
        headers=headers,
    )
    assert expired.status_code == 410
    assert expired.json()["error"]["code"] == "diagnostic_preview_expired"


async def test_checked_preferences_cookie_and_request_local_errors(
    client: httpx.AsyncClient,
) -> None:
    headers = await csrf_headers(client)
    default = await client.get("/api/v1/diagnostics/baselines/not-an-id")
    assert default.status_code == 422
    assert any("\u4e00" <= char <= "\u9fff" for char in default.json()["error"]["message"])
    selected = await client.post(
        "/api/v1/preferences", json={"locale": "en", "theme": "dark"}, headers=headers
    )
    assert selected.status_code == 200
    cookie = selected.headers["set-cookie"].lower()
    assert "readiness_preferences=v1.en.dark" in cookie
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert "max-age=31536000" in cookie
    assert "path=/" in cookie
    translated = await client.get("/api/v1/diagnostics/baselines/not-an-id")
    assert translated.json()["error"]["code"] == default.json()["error"]["code"]
    assert translated.json()["error"]["message"] != default.json()["error"]["message"]
    invalid = await client.post(
        "/api/v1/preferences", json={"locale": "en-US", "theme": "dark"}, headers=headers
    )
    assert invalid.status_code == 422
    assert parse_preferences(client.cookies.get("readiness_preferences")).locale == "en"
    response = await client.post("/api/v1/preferences", json={"locale": "zh-CN", "theme": "light"})
    assert response.status_code == 403
    client.cookies.set("readiness_preferences", "obsolete", domain="localhost.local", path="/")
    fallback = await client.get("/api/v1/diagnostics/baselines/not-an-id")
    assert fallback.json()["error"]["message"] == default.json()["error"]["message"]


async def test_openapi_binary_declaration_and_closed_export_variants(web_app: FastAPI) -> None:
    document = web_app.openapi()
    paths = object_value(document["paths"])
    operation = object_value(object_value(paths[UPLOAD])["post"])
    content = object_value(object_value(operation["requestBody"])["content"])
    assert set(content) == {"application/zip"}
    assert object_value(object_value(content["application/zip"])["schema"])["format"] == "binary"
    value: JsonObject = {
        "schema_version": "2.0",
        "formats": ["zip"],
        "include_evidence": False,
        "presentation": {"schema_version": "1.0", "locale": "en", "theme": "dark"},
    }
    validate_operational({"kind": "diagnostic_export_request", "data": value}, "web-api")
    with pytest.raises(ValueError, match="schema"):
        validate_operational({"kind": "export_request", "data": value}, "web-api")


async def test_disconnected_upload_removes_owned_staging(
    client: httpx.AsyncClient, web_app: FastAPI, tmp_path: Path
) -> None:
    headers = await csrf_headers(client)
    scope: Scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": UPLOAD,
        "raw_path": UPLOAD.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"host", b"localhost:8765"),
            (b"origin", ORIGIN.encode()),
            (b"content-type", b"application/zip"),
            (
                b"cookie",
                ("readiness_session=" + str(client.cookies.get("readiness_session"))).encode(),
            ),
            (b"x-csrf-token", headers["X-CSRF-Token"].encode()),
        ],
    }
    received: list[Message] = [
        {"type": "http.request", "body": b"PK-private-upload", "more_body": True},
        {"type": "http.disconnect"},
    ]
    sent: list[Message] = []

    async def receive() -> Message:
        return received.pop(0) if received else {"type": "http.disconnect"}

    async def send(message: Message) -> None:
        sent.append(message)

    await web_app(scope, receive, send)
    assert not received
    uploads = tmp_path / "diagnostics/uploads"
    assert not uploads.exists() or not list(uploads.iterdir())
    previews = tmp_path / "diagnostics/previews"
    assert not previews.exists() or not list(previews.iterdir())


async def test_upload_concurrency_is_bounded_without_blocking_the_event_loop(
    client: httpx.AsyncClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, _ = portable_archive(tmp_path / "producer")
    headers = {**await csrf_headers(client), "Content-Type": "application/zip"}
    original = DiagnosticService.preview
    entered, release, lock = Event(), Event(), Lock()
    active = 0

    def delayed(
        self: DiagnosticService,
        archive: Path,
        owner: str,
        *,
        now: datetime,
        deadline: float | None = None,
    ) -> JsonObject:
        nonlocal active
        with lock:
            active += 1
            if active == 2:
                entered.set()
        assert release.wait(10), "synthetic_import_gate_timed_out"
        return original(self, archive, owner, now=now, deadline=deadline)

    monkeypatch.setattr(DiagnosticService, "preview", delayed)
    tasks = [
        asyncio.create_task(client.post(UPLOAD, content=archive.read_bytes(), headers=headers))
        for _ in range(2)
    ]
    try:
        assert await asyncio.to_thread(entered.wait, 5)
        rejected = await client.post(UPLOAD, content=b"PK", headers=headers)
        assert rejected.status_code == 429
        assert rejected.json()["error"]["code"] == "diagnostic_import_busy"
        assert (await client.get("/health")).status_code == 200
    finally:
        release.set()
        responses = await asyncio.gather(*tasks)
    assert [response.status_code for response in responses] == [200, 200]
    assert not list((tmp_path / "diagnostics/uploads").iterdir())


async def test_stalled_upload_times_out_and_releases_staging(
    client: httpx.AsyncClient, web_app: FastAPI, tmp_path: Path
) -> None:
    headers = await csrf_headers(client)
    settings = replace(cast(WebSettings, web_app.state.settings), import_timeout_s=0.02)
    web_app.state.settings = settings
    web_app.state.security.settings = settings

    async def slow() -> AsyncIterator[bytes]:
        yield b"PK"
        await asyncio.sleep(0.1)
        yield b"x"

    response = await client.post(
        UPLOAD, content=slow(), headers={**headers, "Content-Type": "application/zip"}
    )
    assert response.status_code == 408
    assert response.json()["error"]["code"] == "archive_timeout"
    assert not list((tmp_path / "diagnostics/uploads").iterdir())


async def test_upload_and_validation_share_one_processing_deadline(
    client: httpx.AsyncClient, web_app: FastAPI, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, _ = portable_archive(tmp_path / "producer")
    headers = await csrf_headers(client)
    settings = replace(cast(WebSettings, web_app.state.settings), import_timeout_s=1)
    web_app.state.settings = settings
    web_app.state.security.settings = settings
    original = DiagnosticService.preview

    def delayed(
        self: DiagnosticService,
        archive: Path,
        owner: str,
        *,
        now: datetime,
        deadline: float | None = None,
    ) -> JsonObject:
        time.sleep(1.1)
        if deadline is None:
            return original(self, archive, owner, now=now)
        return original(self, archive, owner, now=now, deadline=deadline)

    monkeypatch.setattr(DiagnosticService, "preview", delayed)
    response = await client.post(
        UPLOAD, content=archive.read_bytes(), headers={**headers, "Content-Type": "application/zip"}
    )
    assert response.status_code == 408
    assert response.json()["error"]["code"] == "archive_timeout"
    assert not list((tmp_path / "diagnostics/uploads").iterdir())
    assert not list((tmp_path / "diagnostics/previews").iterdir())


async def test_deadline_expiring_during_preview_encoding_cannot_publish(
    client: httpx.AsyncClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from anthropic_readiness.diagnostics import store

    archive, _ = portable_archive(tmp_path / "producer")
    headers = await csrf_headers(client)
    clock = [time.monotonic()]
    monkeypatch.setattr(store, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    original = validate_storage

    def expires(document: JsonObject, name: str) -> None:
        original(document, name)
        if name == "diagnostic-import-preview":
            clock[0] += 61

    monkeypatch.setattr(store, "validate_storage", expires)
    response = await client.post(
        UPLOAD, content=archive.read_bytes(), headers={**headers, "Content-Type": "application/zip"}
    )
    assert response.status_code == 408
    assert not list((tmp_path / "diagnostics/uploads").iterdir())
    assert not list((tmp_path / "diagnostics/previews").iterdir())
