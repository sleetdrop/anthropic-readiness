"""Local sessions, exact origins and bounded strict JSON protect every mutation."""

from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, Request

from anthropic_readiness.web.app import create_app
from anthropic_readiness.web.settings import WebSettings

ORIGIN = "http://localhost:8765"
pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def web_app(tmp_path: Path) -> FastAPI:
    app = create_app(data_root=tmp_path, settings=WebSettings())

    @app.post("/api/v1/probe")
    def probe(request: Request) -> dict[str, bool]:
        if request.state.document.get("fail"):
            raise RuntimeError("synthetic-private-route-error")
        return {"accepted": True}

    return app


@pytest.fixture
async def client(web_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with (
        web_app.router.lifespan_context(web_app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=web_app), base_url=ORIGIN) as value,
    ):
        yield value


async def bootstrap(client: httpx.AsyncClient) -> str:
    response = await client.get("/api/v1/session")
    assert response.status_code == 200
    token: object = response.json()["csrf_token"]
    assert isinstance(token, str)
    return token


async def test_cross_origin_mutation_and_rebinding_host_rejected(client: httpx.AsyncClient) -> None:
    token = await bootstrap(client)
    cases = [
        ({}, "origin_forbidden"),
        ({"Origin": "https://attacker.invalid", "X-CSRF-Token": token}, "origin_forbidden"),
        ({"Origin": "http://localhost:8766", "X-CSRF-Token": token}, "origin_forbidden"),
        ({"Origin": "null", "X-CSRF-Token": token}, "origin_forbidden"),
        ({"Origin": ORIGIN}, "csrf_invalid"),
        ({"Origin": ORIGIN, "X-CSRF-Token": "wrong"}, "csrf_invalid"),
        (
            {"Origin": ORIGIN, "X-CSRF-Token": token, "Host": "attacker.invalid:8765"},
            "invalid_host",
        ),
    ]
    for headers, code in cases:
        response = await client.post("/api/v1/probe", json={}, headers=headers)
        assert response.status_code == 403
        assert response.json()["error"]["code"] == code
        assert "access-control-allow-origin" not in response.headers
    accepted = await client.post(
        "/api/v1/probe", json={}, headers={"Origin": ORIGIN, "X-CSRF-Token": token}
    )
    assert accepted.status_code == 200
    assert accepted.json() == {"accepted": True}
    client.cookies.clear()
    rejected = await client.post(
        "/api/v1/probe", json={}, headers={"Origin": ORIGIN, "X-CSRF-Token": token}
    )
    assert rejected.status_code == 401


async def test_cookie_and_response_headers_are_local_and_private(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/session")
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert "domain=" not in cookie
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert "csrf_token" not in str(response.request.url)


async def test_expired_session_can_bootstrap_without_restarting_job(
    client: httpx.AsyncClient, web_app: FastAPI
) -> None:
    first = await bootstrap(client)
    manager = web_app.state.manager
    web_app.state.security.clock = lambda: 10**12
    expired = await client.get("/api/v1/private-probe")
    assert expired.status_code == 401
    renewed = await bootstrap(client)
    assert renewed != first
    assert web_app.state.manager is manager
    response = await client.post(
        "/api/v1/probe", json={}, headers={"Origin": ORIGIN, "X-CSRF-Token": renewed}
    )
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("body", "code", "status"),
    [
        (b'{"x":"' + b"x" * 65536 + b'"}', "body_too_large", 413),
        (b"[" * 2000 + b"0" + b"]" * 2000, "invalid_json", 422),
        (b'{"x":1,"x":2}', "invalid_json", 422),
        (b'{"x":NaN}', "invalid_json", 422),
        (b'{"x":1e999}', "invalid_json", 422),
        (b"\xff", "invalid_json", 422),
    ],
    ids=["oversized", "deep", "duplicate", "nan", "infinite-number", "invalid-utf8"],
)
async def test_oversized_and_nested_body_rejected_before_dispatch(
    client: httpx.AsyncClient, body: bytes, code: str, status: int
) -> None:
    token = await bootstrap(client)
    response = await client.post(
        "/api/v1/probe",
        content=body,
        headers={"Origin": ORIGIN, "X-CSRF-Token": token, "Content-Type": "application/json"},
    )
    assert response.status_code == status
    assert response.json()["error"]["code"] == code


async def test_private_exception_text_is_not_returned_or_logged(
    client: httpx.AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    token = await bootstrap(client)
    response = await client.post(
        "/api/v1/probe", json={"fail": True}, headers={"Origin": ORIGIN, "X-CSRF-Token": token}
    )
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    captured = capsys.readouterr()
    assert "synthetic-private-route-error" not in response.text + captured.out + captured.err


async def test_non_ascii_csrf_is_rejected_without_an_internal_error(
    client: httpx.AsyncClient,
) -> None:
    await bootstrap(client)
    response = await client.post(
        "/api/v1/probe", json={}, headers=[(b"Origin", ORIGIN.encode()), (b"X-CSRF-Token", b"\xff")]
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_invalid"


async def test_another_port_derives_only_exact_loopback_origins() -> None:
    settings = WebSettings(port=9345, host="0.0.0.0")
    assert set(settings.allowed_origins) == {
        "http://localhost:9345",
        "http://127.0.0.1:9345",
        "http://[::1]:9345",
    }
    assert "http://0.0.0.0:9345" not in settings.allowed_origins
