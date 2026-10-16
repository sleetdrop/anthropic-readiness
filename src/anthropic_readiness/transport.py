"""Bounded application-byte capture with independent absolute deadlines."""

from __future__ import annotations

import asyncio
import time
import zlib
from collections.abc import Callable

import httpx

from anthropic_readiness.config import Limits
from anthropic_readiness.models import (
    Capture,
    CaptureEnd,
    DecodeTail,
    ProtocolEnd,
    ReadRecord,
    RequestSpec,
    SSEFrame,
)
from anthropic_readiness.sse import SSEDecoder


class HttpTransport:
    def __init__(
        self,
        clock: Callable[[], float] = time.monotonic,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.clock = clock
        self.transport = transport
        self._cancel: Callable[[], None] | None = None

    def cancel(self) -> None:
        if self._cancel is not None:
            self._cancel()

    def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
        return asyncio.run(self._send(request, limits, deadline))

    async def _send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
        task = asyncio.current_task()
        loop = asyncio.get_running_loop()

        def cancel_current() -> None:
            if task is not None:
                loop.call_soon_threadsafe(task.cancel)

        self._cancel = cancel_current
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
        decoder = SSEDecoder(limits.max_event_bytes, limits.max_events)

        def accept(data: bytes) -> bool:
            nonlocal observed, protocol_end, capture_end, error
            observed += len(data)
            remaining = limits.max_response_bytes - len(body)
            kept = data[:remaining]
            body.extend(kept)
            received_ms = (self.clock() - started) * 1000
            if data:
                reads.append(ReadRecord(len(data), received_ms))
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
            if expires <= started:
                raise TimeoutError
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
        tail = (
            decoder.finish(complete=capture_end == "eof")
            if request.streaming and code == 200
            else DecodeTail()
        )
        self._cancel = None
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
