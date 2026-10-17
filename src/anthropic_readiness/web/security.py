"""Exact local request boundaries, process-local sessions and safe ASGI errors."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlsplit

from starlette.datastructures import Headers, MutableHeaders
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from anthropic_readiness.models import JsonObject, strict_json
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.web.settings import WebSettings

COOKIE_NAME = "readiness_session"
SESSION_TTL_S = 28800
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
MESSAGES = {
    "invalid_host": "请通过本机地址访问此服务。",
    "origin_forbidden": "请求来源不匹配，请从本机页面操作。",
    "session_required": "会话已失效，请刷新页面恢复连接；现有任务仍会保留。",
    "csrf_invalid": "页面校验已失效，请刷新页面后重试。",
    "body_too_large": "请求内容超过本机服务允许的大小。",
    "invalid_json": "请求必须是有效、无重复字段且深度有限的 JSON 对象。",
    "unsupported_content_type": "请使用 JSON 请求。",
    "internal_error": "本机服务未能完成操作，请查看任务状态后再处理。",
    "not_found": "未找到请求的资源。",
    "invalid_request": "请求参数不符合接口约定。",
    "export_not_terminal": "任务结束后才能冻结并导出报告；现有任务仍在执行。",
    "export_not_found": "未找到已发布的导出，请重新生成。",
    "export_integrity": "导出文件已变化或无法核验，请重新生成；原始失败记录会保留。",
    "export_source_invalid": "来源记录无法绑定到本次任务，不能生成完整报告。",
    "export_evidence_invalid": "证据存在缺失或损坏，可选择不附证据导出带诊断说明的报告。",
    "export_format_unavailable": "本次导出未选择该文件格式。",
    "export_size_limit": "导出超过 256 MiB 的本机处理上限，可缩小所选内容后重试。",
}


def api_response(kind: str, document: JsonObject, *, status: int = 200) -> JSONResponse:
    validate_operational({"kind": kind, "data": document}, "web-api")
    return JSONResponse(document, status_code=status)


def error_response(code: str, status: int) -> JSONResponse:
    return api_response(
        "error",
        {"error": {"code": code, "message": MESSAGES.get(code, MESSAGES["invalid_request"])}},
        status=status,
    )


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
            await error_response(code, status)(scope, receive, protected_send)

        headers = Headers(scope=scope)
        if len(headers.getlist("host")) != 1 or not self.security.valid_host(
            headers.get("host", "")
        ):
            await reject("invalid_host", 403)
            return
        request = Request(scope)
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
            if (
                headers.get("content-type", "").split(";", 1)[0].strip().lower()
                != "application/json"
            ):
                await reject("unsupported_content_type", 415)
                return
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

        async def replay_receive() -> Message:
            nonlocal consumed
            if body is not None and not consumed:
                consumed = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        try:
            await self.app(scope, replay_receive, protected_send)
        except Exception:
            # Route exceptions can include private payloads. Prevent both reflection
            # and the outer server middleware's traceback logging.
            if not started:
                await reject("internal_error", 500)
            elif not finished:
                await protected_send(
                    {"type": "http.response.body", "body": b"", "more_body": False}
                )
