"""Bounded SSE framing, with no knowledge of HTTP or Anthropic messages."""

from __future__ import annotations

import codecs

from anthropic_readiness.models import DecodeTail, SSEFrame


class SSEDecoder:
    def __init__(self, max_event_bytes: int, max_events: int):
        if max_event_bytes <= 0 or max_events <= 0:
            raise ValueError("invalid_sse_limit")
        self.max_event_bytes = max_event_bytes
        self.max_events = max_events
        self._line = bytearray()
        self._size = 0
        self._skip_lf = False
        self._first_line = True
        self._data: list[str] = []
        self._event = ""
        self._id = ""
        self._retry: int | None = None
        self._sequence = 0
        self._encoding_errors = 0
        self._limit: str | None = None
        self._finished = False
        self._tail: DecodeTail | None = None

    @property
    def limit_kind(self) -> str | None:
        return self._limit

    def _text(self, raw: bytes) -> str:
        if self._first_line:
            raw = raw.removeprefix(b"\xef\xbb\xbf")
            self._first_line = False
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            self._encoding_errors += 1
            return raw.decode("utf-8", errors="replace")

    def _process_line(self, received_ms: float) -> SSEFrame | None:
        line = self._text(bytes(self._line))
        self._line.clear()
        if not line:
            self._size = 0
            frame = None
            if self._data:
                if self._sequence >= self.max_events:
                    self._limit = "max_events"
                else:
                    frame = SSEFrame(
                        self._sequence,
                        self._event or "message",
                        "\n".join(self._data),
                        received_ms,
                        self._id,
                        self._retry,
                    )
                    self._sequence += 1
            self._data.clear()
            self._event = ""
            return frame
        if line.startswith(":"):
            return None
        name, colon, value = line.partition(":")
        if colon and value.startswith(" "):
            value = value[1:]
        if name == "data":
            self._data.append(value)
        elif name == "event":
            self._event = value
        elif name == "id" and "\x00" not in value:
            self._id = value
        elif name == "retry" and value and value.isascii() and value.isdigit():
            # Very long decimal fields must stay bounded without Python's int digit limit.
            self._retry = int(value) if len(value) <= 18 else None
        return None

    def feed(self, chunk: bytes, received_ms: float) -> list[SSEFrame]:
        if self._finished:
            raise ValueError("decoder_already_finished")
        frames: list[SSEFrame] = []
        for byte in chunk:
            if self._limit:
                break
            if self._skip_lf:
                self._skip_lf = False
                if byte == 10:
                    continue
            self._size += 1
            if self._size > self.max_event_bytes:
                self._limit = "max_event_bytes"
                break
            if byte in (10, 13):
                frame = self._process_line(received_ms)
                if frame is not None:
                    frames.append(frame)
                self._skip_lf = byte == 13
            else:
                self._line.append(byte)
        return frames

    def finish(self, *, complete: bool = True) -> DecodeTail:
        if self._tail is None:
            pending = bool(self._data)
            if self._line:
                if complete:
                    last = self._text(bytes(self._line))
                else:
                    try:
                        last = codecs.getincrementaldecoder("utf-8")().decode(
                            bytes(self._line), final=False
                        )
                    except UnicodeDecodeError:
                        self._encoding_errors += 1
                        last = bytes(self._line).decode("utf-8", errors="replace")
                pending = pending or last.partition(":")[0] == "data"
            self._tail = DecodeTail(pending, self._encoding_errors, self._limit)
            self._finished = True
        return self._tail
