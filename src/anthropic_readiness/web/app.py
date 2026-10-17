"""Create the optional local application without starting a server on import."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import HTMLResponse, JSONResponse

from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.web.api import router
from anthropic_readiness.web.contracts import ContractApplication
from anthropic_readiness.web.security import (
    COOKIE_NAME,
    SESSION_TTL_S,
    LocalBoundary,
    LocalSecurity,
    api_response,
    error_response,
)
from anthropic_readiness.web.settings import WebSettings


def create_app(*, data_root: Path, settings: WebSettings) -> FastAPI:
    security = LocalSecurity(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        manager = JobManager(
            JobStore(data_root),
            credential_allowlist={
                name: os.environ[name]
                for name in settings.credential_env_allowlist
                if name in os.environ
            },
        )
        manager.start()
        app.state.manager = manager
        try:
            yield
        finally:
            manager.close()

    app = ContractApplication(
        title="Anthropic Readiness",
        version="1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.security = security
    app.state.settings = settings
    app.add_middleware(LocalBoundary, security=security)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return error_response(
            "not_found" if exc.status_code == 404 else "invalid_request", exc.status_code
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response("invalid_request", 422)

    @app.get("/health", include_in_schema=False)
    def health() -> JSONResponse:
        return api_response("health_response", {"status": "ok"})

    @app.get("/api/v1/session")
    async def session(request: Request) -> JSONResponse:
        cookie, value = security.bootstrap(request.cookies.get(COOKIE_NAME))
        response = api_response(
            "session_response", {"csrf_token": value.csrf_token, "expires_in_s": SESSION_TTL_S}
        )
        response.set_cookie(
            COOKIE_NAME, cookie, httponly=True, samesite="strict", max_age=SESSION_TTL_S, path="/"
        )
        return response

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def home() -> HTMLResponse:
        return HTMLResponse(
            '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Anthropic Readiness</title><body><main><h1>Anthropic Readiness</h1><p>本机兼容性测试控制台</p></main></body></html>'
        )

    app.include_router(router)
    return app
