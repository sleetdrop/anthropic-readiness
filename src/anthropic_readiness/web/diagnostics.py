"""Owned local diagnostic routes; imported content never becomes executable pages."""

import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import BoundedSemaphore
from typing import BinaryIO, cast

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.evidence import safe_path
from anthropic_readiness.exports import ExportService
from anthropic_readiness.models import object_value
from anthropic_readiness.presentation import (
    LOCALES,
    THEMES,
    PresentationOptions,
    serialize_preferences,
)
from anthropic_readiness.web.api import LocalRoute, body, manager_for, owner, utc_now
from anthropic_readiness.web.contracts import (
    binary_request_contract,
    request_contract,
    response_contract,
)
from anthropic_readiness.web.security import PREFERENCES_COOKIE, api_response

router = APIRouter(prefix="/api/v1", route_class=LocalRoute)


def service_for(request: Request) -> DiagnosticService:
    return cast(DiagnosticService, request.app.state.diagnostics)


@dataclass
class UploadStaging:
    directory: TemporaryDirectory[str]
    stream: BinaryIO
    path: Path

    def close(self) -> None:
        try:
            self.stream.close()
        finally:
            self.directory.cleanup()


def _staging(root: Path) -> UploadStaging:
    uploads = safe_path(root, "uploads")
    uploads.mkdir(mode=0o700, exist_ok=True)
    directory = TemporaryDirectory(prefix="upload-", dir=uploads)
    try:
        path = Path(directory.name) / "archive.zip"
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        return UploadStaging(directory, os.fdopen(descriptor, "wb"), path)
    except BaseException:
        directory.cleanup()
        raise


def _finish(staging: UploadStaging) -> None:
    staging.stream.flush()
    os.fsync(staging.stream.fileno())
    staging.stream.close()


@router.post(
    "/diagnostics/imports/preview",
    responses=response_contract("diagnostic_import_preview"),
    openapi_extra=binary_request_contract(),
)
async def import_preview(request: Request) -> JSONResponse:
    slots = cast(BoundedSemaphore, request.app.state.import_slots)
    if not slots.acquire(blocking=False):
        raise ValueError("diagnostic_import_busy")
    staging: UploadStaging | None = None
    try:
        service = service_for(request)
        staging = await run_in_threadpool(_staging, service.store.root)
        async for chunk in request.stream():
            if chunk:
                await run_in_threadpool(staging.stream.write, chunk)
        await run_in_threadpool(_finish, staging)
        preview = await run_in_threadpool(
            service.preview,
            staging.path,
            owner(request),
            now=utc_now(),
            deadline=request.state.import_deadline,
        )
        return api_response("diagnostic_import_preview", preview)
    finally:
        try:
            if staging is not None:
                await run_in_threadpool(staging.close)
        finally:
            slots.release()


@router.post(
    "/diagnostics/imports/commit",
    status_code=201,
    responses=response_contract("diagnostic_import_commit_response", 201),
    openapi_extra=request_contract("diagnostic_import_commit_request"),
)
def import_commit(request: Request) -> JSONResponse:
    document = body(request, "diagnostic_import_commit_request")
    record = service_for(request).commit(str(document["preview_id"]), owner(request), now=utc_now())
    return api_response("diagnostic_import_commit_response", record.document, status=201)


@router.get(
    "/diagnostics/baselines/{baseline_id}",
    responses=response_contract("diagnostic_baseline_response"),
)
def baseline(baseline_id: str, request: Request) -> JSONResponse:
    service = service_for(request)
    record = service.get(baseline_id).document
    facts = service.source_facts(safe_path(service.store.root, str(record["artifact_root"])))
    return api_response("diagnostic_baseline_response", {"baseline": record, "facts": facts})


@router.post(
    "/diagnostics/retests/preview",
    status_code=201,
    responses=response_contract("diagnostic_retest_response", 201),
    openapi_extra=request_contract("diagnostic_retest_request"),
)
def retest_preview(request: Request) -> JSONResponse:
    document = body(request, "diagnostic_retest_request")
    assessment, context, differences = service_for(request).prepare_retest(
        str(document["baseline_id"]), object_value(document["target"])
    )
    plan = manager_for(request).store.create_plan(
        assessment.target.to_json(),
        assessment.profiles,
        owner(request),
        now=utc_now(),
        context=context.document,
    )
    return api_response(
        "diagnostic_retest_response",
        {"plan": plan.to_json(), "conditions": differences},
        status=201,
    )


def _owned_source(request: Request, reference: object) -> Path:
    value = object_value(reference)
    if value["kind"] == "baseline":
        service = service_for(request)
        record = service.get(str(value["id"])).document
        return safe_path(service.store.root, str(record["artifact_root"]))
    manager = manager_for(request)
    run_id = str(value["id"])
    ExportService(manager.store.root).verified_source(run_id)
    return safe_path(manager.store.root, "runs/" + run_id)


@router.post(
    "/diagnostics/comparisons",
    responses=response_contract("diagnostic_comparison_response"),
    openapi_extra=request_contract("diagnostic_comparison_request"),
)
def comparison(request: Request) -> JSONResponse:
    document = body(request, "diagnostic_comparison_request")
    result = service_for(request).compare_sources(
        _owned_source(request, document["before"]), _owned_source(request, document["after"])
    )
    return api_response("diagnostic_comparison_response", result.document)


@router.post(
    "/preferences",
    responses=response_contract("preferences_response"),
    openapi_extra=request_contract("preferences_request"),
)
def preferences(request: Request) -> JSONResponse:
    document = body(request, "preferences_request")
    locale = next(value for value in LOCALES if value == document["locale"])
    theme = next(value for value in THEMES if value == document["theme"])
    options = PresentationOptions(locale, theme)
    response = api_response("preferences_response", options.to_json())
    response.set_cookie(
        PREFERENCES_COOKIE,
        serialize_preferences(options),
        httponly=True,
        samesite="strict",
        path="/",
        max_age=31536000,
    )
    return response
