"""Versioned local operations; no route discovers endpoints or retries model calls."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from fastapi import APIRouter, Request
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse, Response, StreamingResponse

from anthropic_readiness.cases import PROFILES, list_cases
from anthropic_readiness.config import strings
from anthropic_readiness.contracts import SUPPORTED, resolve_contract
from anthropic_readiness.credentials import MemoryCredentials
from anthropic_readiness.evidence import safe_path, verify_evidence
from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.models import EvidenceRef, JsonObject, object_value
from anthropic_readiness.operations.checkpoints import CheckpointStore, checkpoint_refs
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.operations.models import JobState
from anthropic_readiness.operations.storage import MAX_DOCUMENT_BYTES, read_document
from anthropic_readiness.schema import result_from_document
from anthropic_readiness.web.contracts import request_contract, response_contract
from anthropic_readiness.web.events import event_stream
from anthropic_readiness.web.security import LocalSession, api_response, error_response

ERRORS = {
    "plan_expired": 410,
    "plan_not_found": 404,
    "job_not_found": 404,
    "idempotency_mismatch": 409,
    "queue_full": 429,
    "plan_integrity": 409,
    "job_state_conflict": 409,
    "active_job_exists": 409,
    "service_unavailable": 503,
    "evidence_not_found": 404,
    "evidence_invalid": 409,
    "invalid_event_cursor": 422,
    "invalid_identifier": 422,
    "invalid_history_limit": 422,
    "invalid_history_cursor": 422,
    "invalid_history_filter": 422,
}


class LocalRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[object, object, Response]]:
        original = super().get_route_handler()

        async def handle(request: Request) -> Response:
            try:
                return await original(request)
            except ValueError as exc:
                # Only known codes are reflected; schema errors can contain secrets.
                code = str(exc).split(":", 1)[0]
                return (
                    error_response(code, ERRORS[code])
                    if code in ERRORS
                    else error_response("invalid_request", 422)
                )
            except OSError:
                return error_response("service_unavailable", 503)

        return handle


router = APIRouter(prefix="/api/v1", route_class=LocalRoute)


def utc_now() -> datetime:
    return datetime.now(UTC)


def manager_for(request: Request) -> JobManager:
    return cast(JobManager, request.app.state.manager)


def body(request: Request, kind: str) -> JsonObject:
    document = object_value(request.state.document)
    validate_operational({"kind": kind, "data": document}, "web-api")
    return document


def owner(request: Request) -> str:
    return cast(LocalSession, request.state.session).binding


def evidence_id(ref: EvidenceRef) -> str:
    return hashlib.sha256((ref.path + "\0" + ref.sha256).encode()).hexdigest()


def evidence_refs(manager: JobManager, run_id: str) -> tuple[Path, tuple[EvidenceRef, ...]]:
    manager.store.get_job(run_id)
    root = safe_path(manager.store.root, "runs/" + run_id)
    evidence_root = safe_path(root, "assessment")
    result_path = safe_path(evidence_root, "result.json")
    try:
        if result_path.exists():
            result = result_from_document(read_document(result_path))
            frozen = manager.store.get_admitted_plan(run_id)
            expected = {**frozen.plan, "actual_requests": result.plan["actual_requests"]}
            snapshot = manager.snapshot(run_id)["execution"]
            if (
                result.run_id != run_id
                or result.mode != "live"
                or result.target != frozen.target
                or result.plan != expected
            ):
                raise ValueError("result_identity")
            if (
                isinstance(snapshot, dict)
                and snapshot["result_sha256"] is not None
                and hashlib.sha256(result_path.read_bytes()).hexdigest()
                != snapshot["result_sha256"]
            ):
                raise ValueError("result_hash_mismatch")
            refs = result.evidence
        elif safe_path(root, "operations/execution.json").exists():
            checkpoints = CheckpointStore(
                root / "operations", run_id, evidence_root=evidence_root
            ).load_verified()
            refs = tuple(ref for checkpoint in checkpoints for ref in checkpoint_refs(checkpoint))
        else:
            refs = ()
        unique = {(ref.path, ref.sha256): EvidenceRef(ref.path, ref.sha256) for ref in refs}
        return evidence_root, tuple(unique.values())
    except (ValueError, OSError) as exc:
        raise ValueError("evidence_invalid") from exc


def run_document(manager: JobManager, run_id: str) -> JsonObject:
    snapshot = manager.snapshot(run_id)
    inventory: list[JsonObject] = []
    try:
        root, refs = evidence_refs(manager, run_id)
        inventory = [
            {
                "id": evidence_id(ref),
                "path": ref.path,
                "sha256": ref.sha256,
                "verified": not verify_evidence(root, (ref,)),
            }
            for ref in refs
        ]
    except ValueError:
        pass
    return {
        **snapshot,
        "plan": manager.store.get_admitted_plan(run_id).to_json(),
        "report": None,
        "evidence": list(inventory),
    }


@router.get("/catalog", responses=response_contract("catalog_response"))
def catalog(request: Request) -> JSONResponse:
    titles = {
        "ANT-MESSAGE-001": "基础消息",
        "ANT-TEXT-SSE-001": "流式消息",
        "ANT-TEXT-SSE-002": "流式任务完成",
        "ANT-TOOL-FORCED-001": "强制工具调用",
    }
    profile_titles = {
        "anthropic-basic": "基础消息与流式输出",
        "anthropic-tools-smoke": "强制工具调用",
    }
    cases = list_cases()
    return api_response(
        "catalog_response",
        {
            "contracts": [
                {**resolve_contract(name, revision).manifest, "version_semantics": "unverified"}
                for name, revision in SUPPORTED
            ],
            "profiles": [
                {
                    "id": profile,
                    "version": 1,
                    "title": profile_titles[profile],
                    "cases": [case.id for case in cases if profile in case.profiles],
                }
                for profile in PROFILES
            ],
            "cases": [
                {
                    "id": case.id,
                    "version": case.version,
                    "title": titles[case.id],
                    "streaming": case.streaming,
                    "behavior": case.behavior,
                    "profiles": list(case.profiles),
                    "capabilities": list(case.capabilities),
                }
                for case in cases
            ],
            "credential_refs": list(manager_for(request).credential_references),
        },
    )


@router.post(
    "/plans",
    status_code=201,
    responses=response_contract("plan_response", 201),
    openapi_extra=request_contract("plan_request"),
)
def create_plan(request: Request) -> JSONResponse:
    document = body(request, "plan_request")
    plan = manager_for(request).store.create_plan(
        object_value(document["target"]),
        strings(document["profiles"]),
        owner(request),
        now=utc_now(),
    )
    return api_response("plan_response", plan.to_json(), status=201)


@router.get("/plans/{plan_id}", responses=response_contract("plan_response"))
def get_plan(plan_id: str, request: Request) -> JSONResponse:
    return api_response(
        "plan_response",
        manager_for(request).store.get_plan(plan_id, owner(request), now=utc_now()).to_json(),
    )


@router.post(
    "/runs",
    status_code=202,
    responses=response_contract("job_response", 202),
    openapi_extra=request_contract("start_request"),
)
def start_run(request: Request) -> JSONResponse:
    document = body(request, "start_request")
    manager = manager_for(request)
    credentials = (
        manager.credentials_for_reference(str(document["credential_ref"]))
        if "credential_ref" in document
        else MemoryCredentials(str(document["credential"]) if "credential" in document else None)
    )
    job = manager.submit(
        str(document["plan_id"]), owner(request), str(document["idempotency_key"]), credentials
    )
    return api_response("job_response", job.to_json(), status=202)


@router.get("/runs", responses=response_contract("history_response"))
def history(
    request: Request,
    cursor: str | None = None,
    limit: int = 50,
    state: JobState | None = None,
    target_name: str | None = None,
    model: str | None = None,
    profile: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
) -> JSONResponse:
    if set(request.query_params) - {
        "cursor",
        "limit",
        "state",
        "target_name",
        "model",
        "profile",
        "created_after",
        "created_before",
    }:
        raise ValueError("invalid_history_filter")
    filters: JsonObject = {
        key: value
        for key, value in {
            "state": state,
            "target_name": target_name,
            "model": model,
            "profile": profile,
            "created_after": created_after,
            "created_before": created_before,
        }.items()
        if value is not None
    }
    return api_response(
        "history_response", manager_for(request).store.history(filters, cursor, limit)
    )


@router.get("/runs/{run_id}", responses=response_contract("run_response"))
def get_run(run_id: str, request: Request) -> JSONResponse:
    return api_response("run_response", run_document(manager_for(request), run_id))


@router.post(
    "/runs/{run_id}/cancel",
    responses=response_contract("job_response"),
    openapi_extra=request_contract("cancel_request"),
)
def cancel_run(run_id: str, request: Request) -> JSONResponse:
    body(request, "cancel_request")
    return api_response("job_response", manager_for(request).cancel(run_id).to_json())


@router.get("/runs/{run_id}/events", response_class=StreamingResponse)
def progress(run_id: str, request: Request, after: str = "0") -> StreamingResponse:
    values = request.headers.getlist("last-event-id")
    value = values[0] if values else after
    if len(values) > 1 or not re.fullmatch(r"[0-9]{1,18}", value):
        raise ValueError("invalid_event_cursor")
    manager = manager_for(request)
    manager.store.get_job(run_id)
    return StreamingResponse(
        event_stream(run_id, int(value), manager),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )


@router.get("/runs/{run_id}/evidence/{reference}")
def evidence(run_id: str, reference: str, request: Request) -> Response:
    if not re.fullmatch(r"[0-9a-f]{64}", reference):
        raise ValueError("invalid_identifier")
    root, refs = evidence_refs(manager_for(request), run_id)
    ref = next((item for item in refs if evidence_id(item) == reference), None)
    if ref is None:
        raise ValueError("evidence_not_found")
    try:
        path = safe_path(root, ref.path)
        with path.open("rb") as stream:
            data = stream.read(MAX_DOCUMENT_BYTES + 1)
        if len(data) > MAX_DOCUMENT_BYTES or hashlib.sha256(data).hexdigest() != ref.sha256:
            raise ValueError("evidence_invalid")
    except (OSError, ValueError) as exc:
        raise ValueError("evidence_invalid") from exc
    return Response(
        data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": 'attachment; filename="evidence-' + reference + '.bin"'},
    )


@router.get("/presets", responses=response_contract("presets_response"))
def presets(request: Request) -> JSONResponse:
    return api_response("presets_response", {"items": list(manager_for(request).store.presets())})


@router.post(
    "/presets",
    status_code=201,
    responses=response_contract("preset_response", 201),
    openapi_extra=request_contract("preset_request"),
)
def create_preset(request: Request) -> JSONResponse:
    document = body(request, "preset_request")
    identifier = manager_for(request).store.save_preset(None, object_value(document["target"]))
    return api_response("preset_response", {"id": identifier}, status=201)


@router.put(
    "/presets/{preset_id}",
    responses=response_contract("preset_response"),
    openapi_extra=request_contract("preset_request"),
)
def update_preset(preset_id: str, request: Request) -> JSONResponse:
    document = body(request, "preset_request")
    identifier = manager_for(request).store.save_preset(preset_id, object_value(document["target"]))
    return api_response("preset_response", {"id": identifier})
