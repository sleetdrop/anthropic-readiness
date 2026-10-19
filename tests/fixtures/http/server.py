"""Standalone generic peer for disposable container acceptance; stdlib only."""

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    body = (args.fixtures / "contracts/core-1.0.0/stream-valid.sse").read_bytes()
    message = (args.fixtures / "contracts/core-1.0.0/message-valid.json").read_bytes()
    tool = (args.fixtures / "contracts/core-1.0.0/message-valid-tool.json").read_bytes()
    record_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *values: object) -> None:
            pass

        def do_POST(self) -> None:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            (args.state / "request").write_text(self.path)
            with record_lock, (args.state / "requests.jsonl").open("a") as record:
                record.write(
                    json.dumps(
                        {
                            "path": self.path,
                            "model": payload.get("model"),
                            "stream": bool(payload.get("stream")),
                            "credential_seen": bool(self.headers.get("x-api-key")),
                        }
                    )
                    + "\n"
                )
            self.send_response(200)
            streaming = bool(payload.get("stream")) or self.path == "/pings"
            self.send_header(
                "Content-Type", "text/event-stream" if streaming else "application/json"
            )
            if self.path == "/pings":
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                try:
                    for _ in range(600):
                        ping = b'event: ping\ndata: {"type":"ping"}\n\n'
                        self.wfile.write(f"{len(ping):x}\r\n".encode() + ping + b"\r\n")
                        self.wfile.flush()
                        time.sleep(0.1)
                except OSError:
                    pass
                return
            data = body if streaming else tool if "tools" in payload else message
            if streaming and "Count" in payload["messages"][0]["content"]:
                data = body.replace(b"Hello.", b"1 2 3 4 5")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    httpd = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    httpd.daemon_threads = True
    (args.state / "ready").write_text(str(httpd.server_port))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
