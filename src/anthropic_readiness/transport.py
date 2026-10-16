"""Bounded application-byte capture with independent absolute deadlines."""

from __future__ import annotations

import asyncio
import time
import zlib
from collections.abc import Callable
from datetime import UTC, datetime

import httpx

from anthropic_readiness.config import Limits
from anthropic_readiness.models import (
    Capture,
    CaptureEnd,
    DecodeTail,
    JsonObject,
    ProtocolEnd,
    ReadRecord,
    RequestSpec,
    SSEFrame,
)
from anthropic_readiness.operations.models import WorkerEvent
from anthropic_readiness.operations.ports import CancelToken, ExecutionObserver, emit_observation
from anthropic_readiness.sse import SSEDecoder


class HttpTransport:
    def __init__(
        self,
        clock: Callable[[], float] = time.monotonic,
        transport: httpx.AsyncBaseTransport | None = None,
        *,
        observer: ExecutionObserver | None = None,
        control: CancelToken | None = None,
    ):
        self.clock = clock
        self.transport = transport
        self._cancel: Callable[[], None] | None = None
        self._cancel_requested = False
        self.observer = observer
        self.control = control
        self._case_id: str | None = None
        self._attempt_id: str | None = None
        self._elapsed: Callable[[], float] = lambda: 0.0

    def bind_execution(
        self,
        case_id: str,
        attempt_id: str,
        *,
        observer: ExecutionObserver | None,
        control: CancelToken,
        elapsed_ms: Callable[[], float],
    ) -> None:
        self._case_id = case_id
        self._attempt_id = attempt_id
        self.observer = observer
        self.control = control
        self._elapsed = elapsed_ms

    def _phase(self, phase: str, received_bytes: int | None = None) -> None:
        if self._case_id is None or self._attempt_id is None:
            return
        payload: JsonObject = {
            "case_id": self._case_id,
            "attempt_id": self._attempt_id,
            "phase": phase,
        }
        if received_bytes is not None:
            payload["received_bytes"] = received_bytes
        emit_observation(
            self.observer,
            WorkerEvent("transport_phase", datetime.now(UTC).isoformat(), self._elapsed(), payload),
        )

    def cancel(self) -> None:
        self._cancel_requested = True
        if self._cancel is not None:
            self._cancel()

    def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
        return asyncio.run(self._send(request, limits, deadline))

    async def _send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
        task = asyncio.current_task()
        loop = asyncio.get_running_loop()

        def cancel_current() -> None:
            if task is not None and not task.done() and not loop.is_closed():
                try:
                    loop.call_soon_threadsafe(task.cancel)
                except RuntimeError:
                    if not loop.is_closed():
                        raise

        self._cancel = cancel_current
        unsubscribe = (
            self.control.register(cancel_current) if self.control is not None else lambda: None
        )
        started = self.clock()
        expires = min(deadline, started + limits.attempt_timeout_s)
        body = bytearray()
        reads: list[ReadRecord] = []
        frames: list[SSEFrame] = []
        protocol_end: ProtocolEnd = "none"
        capture_end: CaptureEnd = "eof"
        error: str | None = None
        code: int | None = None
        headers: tuple[tuple[str, str], ...] = ()
        headers_ms: float | None = None
        observed = 0
        last_activity = float("-inf")
        decoder = SSEDecoder(limits.max_event_bytes, limits.max_events)

        def accept(data: bytes) -> bool:
            nonlocal observed, protocol_end, capture_end, error, last_activity
            observed += len(data)
            remaining = limits.max_response_bytes - len(body)
            kept = data[:remaining]
            body.extend(kept)
            received_ms = (self.clock() - started) * 1000
            if data:
                reads.append(ReadRecord(len(data), received_ms))
                if self.clock() - last_activity >= 1:
                    self._phase("receiving", observed)
                    last_activity = self.clock()
            if request.streaming and code == 200:
                dispatched = decoder.feed(kept, received_ms)
                frames.extend(dispatched)
                for frame in dispatched:
                    if frame.event == "message_stop":
                        protocol_end = "message_stop"
                    elif frame.event == "error":
                        protocol_end = "error_event"
                if decoder.limit_kind:
                    capture_end, error = "capture_limit", decoder.limit_kind
                    return False
            if len(data) > remaining:
                capture_end, error = "capture_limit", "max_response_bytes"
                return False
            return True

        try:
            if self._cancel_requested or (self.control is not None and self.control.requested):
                raise asyncio.CancelledError
            if expires <= started:
                raise TimeoutError
            self._phase("awaiting_headers")
            if self._cancel_requested or (self.control is not None and self.control.requested):
                raise asyncio.CancelledError
            async with asyncio.timeout(expires - started):
                timeout = httpx.Timeout(
                    connect=limits.connect_timeout_s,
                    read=limits.read_timeout_s,
                    write=limits.connect_timeout_s,
                    pool=limits.connect_timeout_s,
                )
                async with httpx.AsyncClient(
                    timeout=timeout,
                    trust_env=False,
                    verify=True,
                    follow_redirects=False,
                    transport=self.transport,
                ) as client:
                    sent_headers = dict(request.headers)
                    sent_headers["accept-encoding"] = "gzip, deflate"
                    async with client.stream(
                        "POST", request.url, headers=sent_headers, json=request.body
                    ) as response:
                        code = response.status_code
                        headers = tuple(response.headers.multi_items())
                        headers_ms = (self.clock() - started) * 1000
                        self._phase("headers_received")
                        encoding = (
                            response.headers.get("content-encoding", "identity").lower().strip()
                        )
                        decompressor = None
                        if encoding in {"gzip", "deflate"}:
                            decompressor = zlib.decompressobj(
                                16 + zlib.MAX_WBITS if encoding == "gzip" else zlib.MAX_WBITS
                            )
                        elif encoding != "identity":
                            raise ValueError("unsupported_content_encoding")
                        async for raw in response.aiter_raw():
                            if self.clock() >= expires:
                                raise TimeoutError
                            if decompressor is None:
                                # httpcore limits raw reads; also bound injected transport streams.
                                if not accept(raw):
                                    break
                            else:
                                decoded = decompressor.decompress(
                                    raw, limits.max_response_bytes - len(body) + 1
                                )
                                if not accept(decoded):
                                    break
                                if decompressor.unused_data:
                                    raise ValueError("unsupported_compression_tail")
                        if (
                            capture_end == "eof"
                            and decompressor is not None
                            and not decompressor.eof
                        ):
                            raise ValueError("incomplete_compressed_response")
        except (TimeoutError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout):
            capture_end, error = "timeout", "deadline_or_io_timeout"
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            capture_end, error = "connection_error", type(exc).__name__
        except (httpx.HTTPError, ValueError, zlib.error) as exc:
            capture_end, error = "read_error", str(exc)
        except (asyncio.CancelledError, KeyboardInterrupt):
            capture_end, error = "cancelled", "cancelled"
        finally:
            unsubscribe()
            self._cancel = None
        tail = (
            decoder.finish(complete=capture_end == "eof")
            if request.streaming and code == 200
            else DecodeTail()
        )
        return Capture(
            request,
            code,
            headers,
            bytes(body),
            tuple(reads),
            tuple(frames),
            protocol_end,
            capture_end,
            tail,
            observed,
            (self.clock() - started) * 1000,
            headers_ms,
            error,
        )
