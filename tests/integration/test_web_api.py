"""HTTP adapters preserve explicit planning, request counts and evidence integrity."""

import asyncio
import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from anthropic_readiness.config import load_target
from anthropic_readiness.models import JsonObject, object_value
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.schema import load_schema
from anthropic_readiness.web import api
from tests.http_server import SyntheticServer
from tests.web_fixtures import anyio_backend as anyio_backend
from tests.web_fixtures import client as client
from tests.web_fixtures import csrf_headers, wait_run
from tests.web_fixtures import web_app as web_app

pytestmark = pytest.mark.anyio
ROOT = Path(__file__).resolve().parents[2]


async def preview(client: httpx.AsyncClient, headers: dict[str, str], url: str) -> JsonObject:
    target = replace(load_target(ROOT / "examples/target.yaml"), messages_url=url)
    response = await client.post(
        "/api/v1/plans",
        json={"target": target.to_json(), "profiles": ["anthropic-basic"]},
        headers=headers,
    )
    assert response.status_code == 201
    return object_value(response.json())


def start_body(plan: JsonObject, operation: str) -> JsonObject:
    return {"plan_id": plan["id"], "live_consent": True, "idempotency_key": operation}


async def test_preview_and_duplicate_start_request_counts(
    client: httpx.AsyncClient, server: SyntheticServer
) -> None:
    headers = await csrf_headers(client)
    catalog = await client.get("/api/v1/catalog")
    assert catalog.status_code == 200
    assert len(catalog.json()["cases"]) == 4
    plan = await preview(client, headers, server.url + "/cases")
    assert not server.requests
    assert (await client.get("/api/v1/plans/" + str(plan["id"]))).json() == plan
    response = await client.post(
        "/api/v1/runs", json=start_body(plan, "same-start"), headers=headers
    )
    assert response.status_code == 202
    run_id = str(response.json()["id"])
    assert (
        await client.post("/api/v1/runs", json=start_body(plan, "same-start"), headers=headers)
    ).json()["id"] == run_id
    completed = await wait_run(client, run_id)
    assert object_value(completed["job"])["state"] == "completed"
    assert object_value(completed["plan"])["config_sha256"] == plan["config_sha256"]
    assert len(server.requests) == 3
    for cursor in (0, 1, 1, 999999):
        stream = await client.get(f"/api/v1/runs/{run_id}/events", params={"after": cursor})
        assert stream.status_code == 200
        assert stream.headers["content-type"].startswith("text/event-stream")
    assert len(server.requests) == 3


async def test_plan_expiry_ownership_mismatch_and_consent_are_classified(
    client: httpx.AsyncClient, server: SyntheticServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = await csrf_headers(client)
    old_time = datetime.now(UTC) - timedelta(seconds=901)
    with monkeypatch.context() as temporal:
        temporal.setattr(api, "utc_now", lambda: old_time)
        expired = await preview(client, headers, server.url + "/cases")
        response = await client.post(
            "/api/v1/runs", json=start_body(expired, "expired"), headers=headers
        )
        assert response.status_code == 410
    plan = await preview(client, headers, server.url + "/cases")
    no_consent = {**start_body(plan, "not-consented"), "live_consent": False}
    assert (await client.post("/api/v1/runs", json=no_consent, headers=headers)).status_code == 422
    assert not server.requests
    first = await client.post("/api/v1/runs", json=start_body(plan, "operation"), headers=headers)
    another = await preview(client, headers, server.url + "/cases")
    conflict = await client.post(
        "/api/v1/runs", json=start_body(another, "operation"), headers=headers
    )
    assert conflict.status_code == 409
    await wait_run(client, str(first.json()["id"]))
    client.cookies.clear()
    await csrf_headers(client)
    assert (await client.get("/api/v1/plans/" + str(another["id"]))).status_code == 404


async def test_history_and_evidence_are_scoped_and_safe(
    client: httpx.AsyncClient, server: SyntheticServer, tmp_path: Path
) -> None:
    headers = await csrf_headers(client)
    plan = await preview(client, headers, server.url + "/cases")
    started = await client.post("/api/v1/runs", json=start_body(plan, "evidence"), headers=headers)
    run_id = str(started.json()["id"])
    completed = await wait_run(client, run_id)
    history = await client.get("/api/v1/runs", params={"state": "completed", "limit": 1})
    assert history.status_code == 200
    assert len(history.json()["items"]) == 1
    assert (await client.get("/api/v1/runs", params={"limit": 101})).status_code == 422
    evidence = objects(completed["evidence"])
    assert evidence
    item = next(item for item in evidence if str(item["path"]).endswith("body.bin"))
    route = f"/api/v1/runs/{run_id}/evidence/{item['id']}"
    response = await client.get(route)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-disposition"].startswith("attachment;")
    assert hashlib.sha256(response.content).hexdigest() == item["sha256"]
    assert (await client.get(f"/api/v1/runs/{run_id}/evidence/" + "0" * 64)).status_code == 404
    assert (await client.get(f"/api/v1/runs/{run_id}/evidence/..%2F..%2Foutside")).status_code in {
        404,
        422,
    }
    source = tmp_path / "runs" / run_id / "assessment" / str(item["path"])
    source.unlink()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"private unrelated file")
    source.symlink_to(outside)
    assert (await client.get(route)).status_code == 409
    assert len(server.requests) == 3


async def test_queue_exhaustion_is_429_without_dispatching_waiting_work(
    client: httpx.AsyncClient, server: SyntheticServer
) -> None:
    headers = await csrf_headers(client)
    active = await preview(client, headers, server.url + "/pings")
    started = await client.post("/api/v1/runs", json=start_body(active, "active"), headers=headers)
    assert started.status_code == 202
    for index in range(8):
        waiting = await preview(client, headers, server.url + "/cases")
        assert (
            await client.post(
                "/api/v1/runs", json=start_body(waiting, f"queued-{index}"), headers=headers
            )
        ).status_code == 202
    overflow = await preview(client, headers, server.url + "/cases")
    assert (
        await client.post("/api/v1/runs", json=start_body(overflow, "overflow"), headers=headers)
    ).status_code == 429
    assert all(path == "/pings" for path, _, _ in server.requests)


async def test_presets_and_start_only_credentials_keep_secrets_out_of_storage(
    client: httpx.AsyncClient, server: SyntheticServer, tmp_path: Path
) -> None:
    headers = await csrf_headers(client)
    target = load_target(ROOT / "examples/target.yaml").to_json()
    bad = {**target, "credential": "synthetic-private-config-key"}
    assert (
        await client.post("/api/v1/presets", json={"target": bad}, headers=headers)
    ).status_code == 422
    saved = await client.post("/api/v1/presets", json={"target": target}, headers=headers)
    assert saved.status_code == 201
    preset_id = str(saved.json()["id"])
    target["model"] = "modified-example-model"
    assert (
        await client.put("/api/v1/presets/" + preset_id, json={"target": target}, headers=headers)
    ).status_code == 200
    assert (await client.get("/api/v1/presets")).json()["items"][0]["target"] == target
    plan = await preview(client, headers, server.url + "/cases")
    body = {
        **start_body(plan, "ambiguous-auth"),
        "credential": "synthetic-private-browser-key",
        "credential_ref": "SYNTHETIC_KEY",
    }
    assert (await client.post("/api/v1/runs", json=body, headers=headers)).status_code == 422
    assert not server.requests
    assert all(
        b"synthetic-private" not in path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    )


async def test_generated_openapi_uses_packaged_closed_shapes(web_app: FastAPI) -> None:
    document = object_value(web_app.openapi())
    components = object_value(object_value(document["components"])["schemas"])
    packaged = load_schema("web-api")
    definitions = objects(packaged["oneOf"])
    for name in (
        "plan_request",
        "start_request",
        "plan_response",
        "run_response",
        "catalog_response",
    ):
        source = next(
            object_value(item["properties"])
            for item in definitions
            if object_value(object_value(item["properties"])["kind"])["const"] == name
        )
        expected = json.loads(
            json.dumps(source["data"]).replace(
                "#/$defs/", "#/components/schemas/contract_definitions/$defs/"
            )
        )
        assert components[name] == expected


async def test_start_credentials_are_private_and_duplicate_binding_is_lazy(
    client: httpx.AsyncClient, server: SyntheticServer, tmp_path: Path
) -> None:
    headers = await csrf_headers(client)
    secret = "synthetic-private-http-browser-credential"
    target = replace(
        load_target(ROOT / "examples/target.yaml"),
        messages_url=server.url + "/cases",
        auth_mode="api_key",
        credential_env="BROWSER_KEY",
    )
    planned = await client.post(
        "/api/v1/plans",
        json={"target": target.to_json(), "profiles": ["anthropic-basic"]},
        headers=headers,
    )
    assert planned.status_code == 201
    plan = object_value(planned.json())
    started = await client.post(
        "/api/v1/runs",
        json={**start_body(plan, "private-start"), "credential": secret},
        headers=headers,
    )
    assert started.status_code == 202
    run_id = str(started.json()["id"])
    complete = await wait_run(client, run_id)
    assert object_value(complete["job"])["state"] == "completed"
    assert len(server.requests) == 3
    assert all(values["x-api-key"] == secret for _, values, _ in server.requests)
    retry = await client.post(
        "/api/v1/runs",
        json={
            **start_body(plan, "private-start"),
            "credential_ref": "UNKNOWN_REFERENCE_MUST_NOT_RESOLVE",
        },
        headers=headers,
    )
    assert retry.status_code == 202
    assert retry.json()["id"] == run_id
    assert len(server.requests) == 3
    assert secret not in json.dumps(complete)
    assert all(
        secret.encode() not in path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    )


async def test_cancel_api_is_idempotent_and_does_not_dispatch_queued_work(
    client: httpx.AsyncClient, server: SyntheticServer
) -> None:
    headers = await csrf_headers(client)
    active = await preview(client, headers, server.url + "/pings")
    started = await client.post(
        "/api/v1/runs", json=start_body(active, "cancel-active"), headers=headers
    )
    active_id = str(started.json()["id"])
    queued = await preview(client, headers, server.url + "/cases")
    waiting = await client.post(
        "/api/v1/runs", json=start_body(queued, "cancel-queued"), headers=headers
    )
    waiting_id = str(waiting.json()["id"])
    cancelled = await client.post(f"/api/v1/runs/{waiting_id}/cancel", json={}, headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancelled"
    assert (
        await client.post(f"/api/v1/runs/{waiting_id}/cancel", json={}, headers=headers)
    ).json() == cancelled.json()
    for _ in range(500):
        if server.requests:
            break
        await asyncio.sleep(0.01)
    assert len(server.requests) == 1
    assert (
        await client.post(f"/api/v1/runs/{active_id}/cancel", json={}, headers=headers)
    ).status_code == 200
    assert object_value((await wait_run(client, active_id))["job"])["state"] == "cancelled"
    assert all(path == "/pings" for path, _, _ in server.requests)
