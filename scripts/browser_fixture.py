"""Disposable browser harness: local console plus a controllable synthetic Messages peer."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import FrameType
from unittest.mock import patch

import uvicorn

from anthropic_readiness import runner
from anthropic_readiness.application import build_plan
from anthropic_readiness.config import load_target
from anthropic_readiness.context import build_report_context
from anthropic_readiness.document_rendering import render_document_html
from anthropic_readiness.documents import build_document_view
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.models import JsonObject, object_value, strict_json
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.presentation import PresentationOptions
from anthropic_readiness.report_rendering import render_report_html
from anthropic_readiness.report_sources import load_report_source
from anthropic_readiness.report_view import build_report_view
from anthropic_readiness.web.app import create_app
from anthropic_readiness.web.settings import WebSettings
from scripts.check import ROOT
from tests.acceptance.test_readable_reports import MissingFieldsTransport
from tests.diagnostic_fixtures import portable_archive
from tests.export_fixtures import prepared_run
from tests.unit.test_report_view import source as mixed_report_source

FIXTURES = ROOT / "tests/fixtures/contracts/core-1.0.0"
HOSTILE = '</script><img src="https://invalid.example/escape" onerror="window.injected=true">'


def verify_cleanup(root: Path) -> None:
    """Conservatively verify the fixture PID and both listeners have stopped."""
    record = json.loads((root / "process.json").read_text())
    if record["stopped"] is not True:
        raise ValueError("fixture_cleanup_incomplete")
    try:
        os.kill(record["pid"], 0)
    except ProcessLookupError:
        pass
    except PermissionError as exc:
        raise ValueError("fixture_owner_unverifiable") from exc
    else:
        raise ValueError("fixture_owner_still_alive")
    for key in ("web_port", "peer_port"):
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", record[key]))
            except OSError as exc:
                raise ValueError("fixture_listener_still_alive") from exc
    print("owned fixture stopped; both listeners released")


class FixtureServer(uvicorn.Server):
    @contextmanager
    def capture_signals(self) -> Iterator[None]:
        """Let fixture cleanup finish; do not replay Uvicorn's captured SIGTERM."""

        def stop(signum: int, frame: FrameType | None) -> None:
            self.should_exit = True

        saved = {sig: signal.signal(sig, stop) for sig in (signal.SIGINT, signal.SIGTERM)}
        try:
            yield
        finally:
            for sig, handler in saved.items():
                signal.signal(sig, handler)


def seed(root: Path) -> JsonObject:
    original = build_report_context
    with patch.object(
        runner,
        "build_report_context",
        side_effect=lambda *args: {
            **original(*args),
            "data_kind": "synthetic",
        },
    ):
        partial_id = prepared_run(root, partial=True, keep_unpublished=True)
        store = JobStore(root)
        plan = store.create_plan(
            load_target(ROOT / "examples/target.yaml").to_json(),
            ("anthropic-basic", "anthropic-tools-smoke"),
            "b" * 64,
            now=datetime.now(UTC),
        )
        job = store.admit(plan.id, "b" * 64, "browser-fixture", now=datetime.now(UTC)).job
        store.transition(job.id, "queued", "running")
        output = root / "runs" / job.id / "assessment"
        runner.execute_run(
            build_plan(plan.target, plan.profiles),
            MissingFieldsTransport(),
            output,
            run_id=job.id,
            observer=DiskExecutionObserver(output.parent / "operations", output),
        )
    offline = root / "offline-report.html"
    offline.write_text(
        render_report_html(
            build_report_view(
                load_report_source(output, operations_root=output.parent / "operations")
            )
        )
    )
    document_paths: JsonObject = {}
    for locale in ("zh-CN", "en"):
        for theme in ("light", "dark", "system"):
            path = root / f"document-{locale}-{theme}.html"
            path.write_text(
                render_document_html(
                    build_document_view(
                        load_report_source(output, operations_root=output.parent / "operations"),
                        presentation=PresentationOptions(locale, theme),
                    )
                )
            )
            document_paths[f"{locale}-{theme}"] = str(path)
    mixed_path = root / "mixed-report.html"

    mixed_path.write_text(render_report_html(build_report_view(mixed_report_source())))
    archive, original_source = portable_archive(root / "portable-input")
    omitted, _ = portable_archive(
        root / "omitted-input", source_dir=original_source, include_evidence=False
    )
    legacy, _ = portable_archive(root / "legacy-input", source_dir=original_source, legacy=True)
    return {
        "import_path": str(archive),
        "omitted_path": str(omitted),
        "legacy_path": str(legacy),
        "completed_id": job.id,
        "partial_id": partial_id,
        "document_paths": document_paths,
        "offline_path": str(offline),
        "mixed_path": str(mixed_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--verify-cleanup", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.verify_cleanup:
        verify_cleanup(root)
        return
    if args.port is None:
        parser.error("--port is required when serving")
    root.mkdir(parents=True, exist_ok=False)
    info = seed(root)
    app = create_app(data_root=root, settings=WebSettings(port=args.port))
    elapsed = [0.0]
    app.state.security.clock = lambda: time.monotonic() + elapsed[0]
    lock = threading.Lock()
    calls: list[JsonObject] = []
    release = threading.Event()
    repair_phase = ["before"]

    def unfinished() -> list[str]:
        manager = app.state.manager
        return [
            str(object_value(item["job"])["id"])
            for state in ("queued", "running", "cancelling")
            for item in objects(manager.store.history({"state": state}, None, 50)["items"])
        ]

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: object) -> None:
            pass

        def reply(self, value: JsonObject) -> None:
            raw = json.dumps(value).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            if self.path == "/__fixture/info":
                self.reply(info)
            elif self.path == "/__fixture/state":
                with lock:
                    self.reply({"requests": list(calls), "count": len(calls)})
            else:
                self.send_error(404)

        def do_POST(self) -> None:
            nonlocal release
            if self.path.startswith("/__fixture/"):
                if self.path == "/__fixture/release":
                    release.set()
                elif self.path == "/__fixture/repair-after":
                    repair_phase[0] = "after"
                elif self.path == "/__fixture/expire":
                    elapsed[0] += 28801
                elif self.path == "/__fixture/reset":
                    manager = app.state.manager
                    for run_id in unfinished():
                        manager.cancel(run_id)
                    release.set()
                    deadline = time.monotonic() + 8
                    while unfinished() and time.monotonic() < deadline:
                        time.sleep(0.02)
                    if unfinished():
                        self.send_error(500, "fixture_cleanup_timeout")
                        return
                    repair_phase[0] = "before"
                    with lock:
                        calls.clear()
                        release = threading.Event()
                else:
                    self.send_error(404)
                    return
                self.reply({"ok": True})
                return
            if self.path != "/v1/messages":
                self.send_error(404)
                return
            payload = object_value(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            model = str(payload["model"])
            with lock:
                calls.append(
                    {
                        "model": model,
                        "stream": bool(payload.get("stream")),
                        "credential_seen": bool(self.headers.get("x-api-key")),
                    }
                )
                barrier = release
            visual = model == "synthetic-design"
            repair = model == "synthetic-repair"
            broken_fields = visual or (repair and repair_phase[0] == "before")
            if model == "synthetic-hold" or (visual and "Count" in str(payload.get("messages"))):
                barrier.wait(timeout=30)
            time.sleep(0.08)
            streaming = bool(payload.get("stream"))
            response_model = (
                HOSTILE
                if model == "synthetic-hostile"
                else "synthetic-upstream-model"
                if visual or repair
                else model
            )
            if streaming:
                data = (FIXTURES / "stream-valid.sse").read_bytes()
                data = data.replace(b'"example-model"', json.dumps(response_model).encode())
                if "Count" in str(payload.get("messages")):
                    data = data.replace(b"Hello.", b"1 2 3 4 5")
            else:
                name = "message-valid-tool.json" if "tools" in payload else "message-valid.json"
                message = object_value(json.loads((FIXTURES / name).read_bytes()))
                message["model"] = response_model
                if payload.get("tool_choice") == {"type": "none"}:
                    messages = payload["messages"]
                    assert isinstance(messages, list)
                    blocks = object_value(messages[-1])["content"]
                    assert isinstance(blocks, list)
                    result = object_value(strict_json(str(object_value(blocks[0])["content"])))
                    message = object_value(
                        json.loads((FIXTURES / "message-valid.json").read_bytes())
                    )
                    message["model"] = response_model
                    message["content"] = [{"type": "text", "text": result["verification_token"]}]
                if broken_fields:
                    message.pop("stop_sequence", None)
                if repair and repair_phase[0] == "after" and "tools" in payload:
                    message = {"error": {"type": "synthetic_missing_tool_result"}}
                data = json.dumps(message).encode()
            if broken_fields and streaming:
                lines = []
                for line in data.decode().splitlines():
                    if line.startswith("data: "):
                        value = object_value(json.loads(line[6:]))
                        if isinstance(value.get("message"), dict):
                            message_value = object_value(value["message"])
                            message_value.pop("stop_reason", None)
                            message_value.pop("stop_sequence", None)
                        if isinstance(value.get("delta"), dict):
                            object_value(value["delta"]).pop("stop_sequence", None)
                        line = "data: " + json.dumps(value)
                    lines.append(line)
                data = ("\n".join(lines) + "\n\n").encode()
            if (
                repair
                and repair_phase[0] == "after"
                and streaming
                and "Count" in str(payload.get("messages"))
            ):
                data += b'event: message_stop\ndata: {"type":"message_stop"}\n\n'
            try:
                self.send_response(
                    503 if repair and repair_phase[0] == "after" and "tools" in payload else 200
                )
                self.send_header(
                    "Content-Type", "text/event-stream" if streaming else "application/json"
                )
                if streaming:
                    self.send_header("Transfer-Encoding", "chunked")
                    self.end_headers()
                    for frame in data.split(b"\n\n"):
                        if frame:
                            chunk = frame + b"\n\n"
                            self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
                            self.wfile.flush()
                            time.sleep(0.03)
                    self.wfile.write(b"0\r\n\r\n")
                else:
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

    peer = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    peer.daemon_threads = True
    info.update(
        {
            "peer_url": f"http://127.0.0.1:{peer.server_port}",
            "web_url": f"http://127.0.0.1:{args.port}",
            "data_kind": "synthetic",
        }
    )
    identity = {
        "pid": os.getpid(),
        "stopped": False,
        "peer_port": peer.server_port,
        "web_port": args.port,
    }
    (root / "fixture.json").write_text(json.dumps(info))
    process_file = root / "process.json"
    process_file.write_text(json.dumps(identity))
    thread = threading.Thread(target=peer.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True)
    thread.start()
    try:
        FixtureServer(
            uvicorn.Config(
                app,
                host="127.0.0.1",
                port=args.port,
                access_log=False,
                proxy_headers=False,
                log_level="warning",
            )
        ).run()
    finally:
        release.set()
        peer.shutdown()
        peer.server_close()
        thread.join(timeout=2)
        identity["stopped"] = True
        process_file.write_text(json.dumps(identity))


if __name__ == "__main__":
    main()
