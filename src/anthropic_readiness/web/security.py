"""Exact local request boundaries, process-local sessions and safe ASGI errors."""

from __future__ import annotations

import asyncio
import hashlib
import json
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlsplit

from starlette.datastructures import Headers, MutableHeaders
from starlette.requests import ClientDisconnect, Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from anthropic_readiness.localization import load_catalog, translate
from anthropic_readiness.models import JsonObject, strict_json
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.presentation import PresentationOptions, parse_preferences
from anthropic_readiness.web.settings import WebSettings

COOKIE_NAME = "readiness_session"
PREFERENCES_COOKIE = "readiness_preferences"
IMPORT_PATH = "/api/v1/diagnostics/imports/preview"
SESSION_TTL_S = 28800
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"


def api_response(kind: str, document: JsonObject, *, status: int = 200) -> JSONResponse:
    validate_operational({"kind": kind, "data": document}, "web-api")
    return JSONResponse(document, status_code=status)


def error_response(
    code: str, status: int, *, options: PresentationOptions | None = None
) -> JSONResponse:
    catalog = load_catalog((options or PresentationOptions()).locale)
    key = "error." + code
    message = translate(catalog, key if key in catalog else "error.invalid_request")
    return api_response(
        "error",
        {"error": {"code": code, "message": message}},
        status=status,
    )


def preferences_for(request: Request) -> PresentationOptions:
    return parse_preferences(request.cookies.get(PREFERENCES_COOKIE))


class ImportBoundaryError(Exception):
    def __init__(self, code: str, status: int) -> None:
        self.code = code
        self.status = status
        super().__init__(code)


@dataclass(frozen=True)
class LocalSession:
    binding: str
    csrf_token: str
    expires: float


class LocalSecurity:
    def __init__(
        self, settings: WebSettings, *, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.settings = settings
        self.clock = clock
        self._sessions: dict[str, LocalSession] = {}

    def session(self, cookie: str | None) -> LocalSession | None:
        value = self._sessions.get(cookie or "")
        return value if value is not None and value.expires > self.clock() else None

    def bootstrap(self, cookie: str | None) -> tuple[str, LocalSession]:
        existing = self.session(cookie)
        if existing is not None and cookie is not None:
            return cookie, existing
        self._sessions = {
            key: value for key, value in self._sessions.items() if value.expires > self.clock()
        }
        if len(self._sessions) >= 128:
            del self._sessions[next(iter(self._sessions))]
        identifier = secrets.token_urlsafe(32)
        value = LocalSession(
            hashlib.sha256(identifier.encode()).hexdigest(),
            secrets.token_urlsafe(32),
            self.clock() + SESSION_TTL_S,
        )
        self._sessions[identifier] = value
        return identifier, value

    def valid_host(self, value: str) -> bool:
        try:
            parsed = urlsplit("//" + value)
            host = parsed.hostname or ""
            normalized = "[" + host + "]" if ":" in host else host
            return (
                normalized in self.settings.allowed_hosts
                and parsed.port in {None, self.settings.port}
                and not parsed.username
                and not parsed.password
                and not parsed.path
                and not any(char in value for char in "?#")
                and not any(char.isspace() or ord(char) < 32 for char in value)
            )
        except ValueError:
            return False


class LocalBoundary:
    def __init__(self, app: ASGIApp, *, security: LocalSecurity) -> None:
        self.app = app
        self.security = security

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False
        finished = False

        async def protected_send(message: Message) -> None:
            nonlocal started, finished
            if message["type"] == "http.response.start":
                started = True
                headers = MutableHeaders(scope=message)
                headers["Cache-Control"] = "no-store"
                headers["X-Content-Type-Options"] = "nosniff"
                headers["Content-Security-Policy"] = CSP
                headers["Referrer-Policy"] = "no-referrer"
            elif message["type"] == "http.response.body" and not message.get("more_body", False):
                finished = True
            await send(message)

        async def reject(code: str, status: int) -> None:
            await error_response(code, status, options=options)(scope, receive, protected_send)

        headers = Headers(scope=scope)
        request = Request(scope)
        options = preferences_for(request)
        if len(headers.getlist("host")) != 1 or not self.security.valid_host(
            headers.get("host", "")
        ):
            await reject("invalid_host", 403)
            return
        session = self.security.session(request.cookies.get(COOKIE_NAME))
        state = scope.setdefault("state", {})
        state["session"] = session
        method, path = scope["method"], scope["path"]
        mutation = method not in {"GET", "HEAD", "OPTIONS"}
        if mutation and (
            len(headers.getlist("origin")) != 1
            or headers.get("origin") not in self.security.settings.allowed_origins
        ):
            await reject("origin_forbidden", 403)
            return
        if (mutation or path.startswith("/api/")) and path != "/api/v1/session" and session is None:
            await reject("session_required", 401)
            return
        body: bytes | None = None
        binary = False
        declared: int | None = None
        if mutation:
            if (
                session is None
                or len(headers.getlist("x-csrf-token")) != 1
                or not secrets.compare_digest(
                    headers.get("x-csrf-token", "").encode(), session.csrf_token.encode()
                )
            ):
                await reject("csrf_invalid", 403)
                return
            if method == "POST" and path == IMPORT_PATH:
                if (
                    len(headers.getlist("content-type")) != 1
                    or headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    != "application/zip"
                ):
                    await reject("unsupported_content_type", 415)
                    return
                lengths = headers.getlist("content-length")
                if lengths:
                    if (
                        len(lengths) != 1
                        or not lengths[0].isascii()
                        or not lengths[0].isdigit()
                        or len(lengths[0]) > 12
                    ):
                        await reject("invalid_request", 422)
                        return
                    declared = int(lengths[0])
                    if declared > self.security.settings.max_import_bytes:
                        await reject("archive_upload_limit", 413)
                        return
                binary = True
            elif (
                headers.get("content-type", "").split(";", 1)[0].strip().lower()
                != "application/json"
            ):
                await reject("unsupported_content_type", 415)
                return
            if not binary:
                parts: list[bytes] = []
                length = 0
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    part = message.get("body", b"")
                    length += len(part)
                    if length > self.security.settings.max_body_bytes:
                        await reject("body_too_large", 413)
                        return
                    parts.append(part)
                    if not message.get("more_body", False):
                        break
                body = b"".join(parts)
                try:
                    document = strict_json(body.decode())
                    if not isinstance(document, dict):
                        raise ValueError("expected_object")
                    json.dumps(document, allow_nan=False)
                    state["document"] = document
                except (ValueError, UnicodeError):
                    await reject("invalid_json", 422)
                    return
        consumed = False
        uploaded = 0
        upload_deadline = time.monotonic() + self.security.settings.import_timeout_s
        if binary:
            state["import_deadline"] = upload_deadline

        async def replay_receive() -> Message:
            nonlocal consumed, uploaded
            if binary:
                try:
                    async with asyncio.timeout(max(0, upload_deadline - time.monotonic())):
                        message = await receive()
                except TimeoutError as exc:
                    raise ImportBoundaryError("archive_timeout", 408) from exc
                if message["type"] == "http.request":
                    uploaded += len(message.get("body", b""))
                    if uploaded > self.security.settings.max_import_bytes:
                        raise ImportBoundaryError("archive_upload_limit", 413)
                    if declared is not None and (
                        uploaded > declared
                        or (not message.get("more_body", False) and uploaded != declared)
                    ):
                        raise ImportBoundaryError("invalid_request", 422)
                return message
            if body is not None and not consumed:
                consumed = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        try:
            await self.app(scope, replay_receive, protected_send)
        except ImportBoundaryError as exc:
            if not started:
                await reject(exc.code, exc.status)
        except ClientDisconnect:
            return
        except Exception:
            # Route exceptions can include private payloads. Prevent both reflection
            # and the outer server middleware's traceback logging.
            if not started:
                await reject("internal_error", 500)
            elif not finished:
                await protected_send(
                    {"type": "http.response.body", "body": b"", "more_body": False}
                )
