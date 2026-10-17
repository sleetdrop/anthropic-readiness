"""Shared asynchronous HTTP application fixtures without a deprecated test client."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from anthropic_readiness.models import JsonObject, object_value
from anthropic_readiness.web.app import create_app
from anthropic_readiness.web.settings import WebSettings

ORIGIN = "http://localhost:8765"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def web_app(tmp_path: Path) -> FastAPI:
    return create_app(data_root=tmp_path, settings=WebSettings())


@pytest.fixture
async def client(web_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with (
        web_app.router.lifespan_context(web_app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=web_app), base_url=ORIGIN) as client,
    ):
        yield client


async def csrf_headers(client: httpx.AsyncClient) -> dict[str, str]:
    response = await client.get("/api/v1/session")
    assert response.status_code == 200
    return {"Origin": ORIGIN, "X-CSRF-Token": str(response.json()["csrf_token"])}


async def wait_run(client: httpx.AsyncClient, run_id: str) -> JsonObject:
    for _ in range(500):
        response = await client.get("/api/v1/runs/" + run_id)
        assert response.status_code == 200
        document = object_value(response.json())
        if object_value(document["job"])["state"] in {
            "completed",
            "cancelled",
            "interrupted",
            "error",
        }:
            return document
        await asyncio.sleep(0.02)
    raise AssertionError("run_did_not_finish")
