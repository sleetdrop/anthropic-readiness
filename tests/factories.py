"""Small synthetic domain fixtures."""

from pathlib import Path

from anthropic_readiness.models import Capture, ReadRecord, RequestSpec
from anthropic_readiness.sse import SSEDecoder


def capture(body: bytes | None = None, streaming: bool = False) -> Capture:
    if body is None:
        body = (
            Path(__file__).parent / "fixtures/contracts/core-1.0.0/message-valid.json"
        ).read_bytes()
    request = RequestSpec(
        "http://127.0.0.1:8000/v1/messages",
        (("content-type", "application/json"),),
        {"model": "example-model"},
        streaming,
    )
    decoder = SSEDecoder(262144, 10000)
    frames = decoder.feed(body, 1) if streaming else []
    return Capture(
        request,
        200,
        (("content-type", "text/event-stream" if streaming else "application/json"),),
        body,
        (ReadRecord(len(body), 1),),
        tuple(frames),
        "message_stop" if streaming else "none",
        tail=decoder.finish(),
        observed_bytes=len(body),
        duration_ms=2,
    )
