"""Create the optional local application without starting a server on import."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from threading import BoundedSemaphore

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.web.api import router
from anthropic_readiness.web.contracts import ContractApplication
from anthropic_readiness.web.diagnostics import router as diagnostics_router
from anthropic_readiness.web.pages import router as pages_router
from anthropic_readiness.web.security import (
    COOKIE_NAME,
    SESSION_TTL_S,
    LocalBoundary,
    LocalSecurity,
    api_response,
    error_response,
    preferences_for,
)
from anthropic_readiness.web.settings import WebSettings
from anthropic_readiness.web.workbench import router as workbench_router


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
    app.state.diagnostics = DiagnosticService(data_root)
    app.state.import_slots = BoundedSemaphore(2)
    app.add_middleware(LocalBoundary, security=security)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return error_response(
            "not_found" if exc.status_code == 404 else "invalid_request",
            exc.status_code,
            options=preferences_for(request),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response("invalid_request", 422, options=preferences_for(request))

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

    app.include_router(router)
    app.include_router(diagnostics_router)
    app.include_router(pages_router)
    app.include_router(workbench_router)
    return app
