"""Disposable loopback HTTP server; no real endpoint credentials."""

import gzip
import json
import socket
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


@dataclass
class SyntheticServer:
    url: str = ""
    requests: list[tuple[str, dict[str, str], bytes]] = field(default_factory=list)


@pytest.fixture
def server() -> Iterator[SyntheticServer]:
    state = SyntheticServer()
    body = (
        Path(__file__).resolve().parent / "fixtures/contracts/core-1.0.0/stream-valid.sse"
    ).read_bytes()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: object) -> None:
            pass

        def do_POST(self) -> None:
            request_body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            state.requests.append(
                (self.path, {k.lower(): v for k, v in self.headers.items()}, request_body)
            )
            if self.path == "/redirect":
                self.send_response(307)
                self.send_header("Location", "/valid")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(503 if self.path == "/http-error" else 200)
            content_type = (
                "application/json"
                if self.path in {"/cases", "/tool-loop", "/tool-loop-ignored"}
                and not json.loads(request_body).get("stream")
                else "text/event-stream"
            )
            self.send_header("Content-Type", content_type)
            if self.path == "/gzip":
                packed = gzip.compress(b"x" * 1000000)
                self.send_header("Content-Encoding", "gzip")
                self.send_header("Content-Length", str(len(packed)))
                self.end_headers()
                self.wfile.write(packed)
                return
            if self.path in {"/pings", "/stop-open", "/reset"}:
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                try:
                    if self.path in {"/stop-open", "/reset"}:
                        self.wfile.write(f"{len(body):x}\r\n".encode() + body + b"\r\n")
                        self.wfile.flush()
                    if self.path == "/reset":
                        self.connection.shutdown(socket.SHUT_RDWR)
                        self.connection.close()
                        return
                    for _ in range(100):
                        ping = b'event: ping\ndata: {"type":"ping"}\n\n'
                        self.wfile.write(f"{len(ping):x}\r\n".encode() + ping + b"\r\n")
                        self.wfile.flush()
                        time.sleep(0.01)
                except OSError:
                    pass
                return
            if self.path == "/error":
                data = b'event: error\ndata: {"type":"error","error":{"type":"overloaded_error","message":"Synthetic"}}\n\n'
            elif self.path == "/early":
                data = body[: body.rfind(b"event: message_stop")]
            elif self.path == "/duplicate":
                first = body[: body.find(b"\n\n") + 2]
                data = first + body
            elif self.path == "/http-error":
                data = json.dumps({"error": "synthetic unavailable"}).encode()
            else:
                data = body
            if self.path == "/cases":
                payload = json.loads(request_body)
                if payload.get("stream"):
                    data = (
                        body.replace(b"Hello.", b"1 2 3 4 5")
                        if "Count" in payload["messages"][0]["content"]
                        else body
                    )
                else:
                    message = json.loads(
                        (
                            Path(__file__).resolve().parent
                            / "fixtures/contracts/core-1.0.0/message-valid.json"
                        ).read_bytes()
                    )
                    data = json.dumps(message).encode()
            if self.path in {"/tool-loop", "/tool-loop-ignored"}:
                payload = json.loads(request_body)
                message = json.loads(
                    (
                        Path(__file__).resolve().parent
                        / "fixtures/contracts/core-1.0.0/message-valid.json"
                    ).read_text()
                )
                if len(payload["messages"]) == 1:
                    message["stop_reason"] = "tool_use"
                    message["content"] = [
                        {
                            "type": "tool_use",
                            "id": "toolu_synthetic_loop",
                            "name": "get_weather",
                            "input": {"location": "Hanoi"},
                        }
                    ]
                else:
                    result = payload["messages"][2]["content"][0]
                    token = json.loads(result["content"])["verification_token"]
                    message["content"] = [
                        {
                            "type": "text",
                            "text": "ignored result" if self.path.endswith("ignored") else token,
                        }
                    ]
                data = json.dumps(message).encode()
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    httpd.daemon_threads = True
    state.url = f"http://127.0.0.1:{httpd.server_port}"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)
