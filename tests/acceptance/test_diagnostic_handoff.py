"""Public CLI repair handoff across two isolated local environments."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Literal
from zipfile import ZipFile

from anthropic_readiness.config import load_target
from anthropic_readiness.models import JsonObject, object_value, strict_json
from anthropic_readiness.operations.reduction import objects

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/contracts/core-1.0.0"
CASE_IDS = {"ANT-MESSAGE-001", "ANT-TEXT-SSE-001", "ANT-TEXT-SSE-002", "ANT-TOOL-FORCED-001"}


@dataclass
class Peer:
    url: str
    server: ThreadingHTTPServer
    thread: threading.Thread
    requests: list[JsonObject] = field(default_factory=list)
    closed: bool = False

    def close(self) -> None:
        if not self.closed:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=2)
            self.closed = True


@contextmanager
def peer(phase: Literal["before", "after"], key: str) -> Iterator[Peer]:
    calls: list[JsonObject] = []

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: object) -> None:
            pass

        def do_POST(self) -> None:
            payload = object_value(
                strict_json(self.rfile.read(int(self.headers["Content-Length"])).decode())
            )
            calls.append(
                {
                    "path": self.path,
                    "body": payload,
                    "credential_matches": self.headers.get("x-api-key") == key,
                }
            )
            if self.path != "/v1/messages":
                self.send_error(404)
                return
            if payload.get("stream"):
                data = (
                    (FIXTURES / "stream-valid.sse")
                    .read_bytes()
                    .replace(b'"example-model"', b'"synthetic-upstream-model"')
                )
                counting = "Count" in str(payload["messages"])
                if counting:
                    data = data.replace(b"Hello.", b"1 2 3 4 5")
                if phase == "before":
                    lines = []
                    for line in data.decode().splitlines():
                        if line.startswith("data: "):
                            event = object_value(strict_json(line[6:]))
                            for name in ("message", "delta"):
                                value = event.get(name)
                                if isinstance(value, dict):
                                    value.pop("stop_sequence", None)
                            line = "data: " + json.dumps(event)
                        lines.append(line)
                    data = ("\n".join(lines) + "\n\n").encode()
                elif counting:
                    first = data.split(b"\n\n", 1)[0] + b"\n\n"
                    data = first + data
                content_type = "text/event-stream"
            else:
                name = "message-valid-tool.json" if "tools" in payload else "message-valid.json"
                message = object_value(strict_json((FIXTURES / name).read_text()))
                message["model"] = "synthetic-upstream-model"
                if phase == "before":
                    message.pop("stop_sequence", None)
                data = json.dumps(message).encode()
                content_type = "application/json"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    value = Peer(f"http://127.0.0.1:{server.server_port}", server, thread, calls)
    thread.start()
    try:
        yield value
    finally:
        value.close()


def invoke(
    cwd: Path, *args: str, credential: tuple[str, str] | None = None, expected: int = 0
) -> JsonObject:
    environment = {
        "PATH": os.defpath,
        "LANG": "C.UTF-8",
        "PYTHONNOUSERSITE": "1",
        "UV_OFFLINE": "1",
    }
    if credential:
        environment[credential[0]] = credential[1]
    result = subprocess.run(
        [sys.executable, "-m", "anthropic_readiness", *args],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == expected, result.stderr
    return object_value(strict_json(result.stdout))


def snapshots(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def target_file(root: Path, endpoint: str, reference: str) -> Path:
    document = load_target(ROOT / "examples/target.yaml").to_json()
    document.update(
        {
            "name": "Synthetic " + reference,
            "delivery_id": "synthetic-" + reference.lower(),
            "model": "synthetic-repair",
            "messages_url": endpoint + "/v1/messages",
            "auth": {"mode": "api_key", "credential_env": reference},
        }
    )
    path = root / "target.json"
    path.write_text(json.dumps(document))
    return path


def test_portable_repair_handoff_preserves_original_scope_and_visible_regression(
    tmp_path: Path,
) -> None:
    a_root, b_root = tmp_path / "environment-a", tmp_path / "environment-b"
    a_root.mkdir()
    b_root.mkdir()
    a_key, b_key = "synthetic-key-a-only", "synthetic-key-b-only"
    with peer("before", a_key) as a, peer("after", b_key) as b:
        a_target = target_file(a_root, a.url, "SYNTHETIC_A_AUTH")
        a_output = a_root / "assessment"
        a_result = invoke(
            a_root,
            "run",
            "--target",
            str(a_target),
            "--profile",
            "anthropic-basic",
            "--profile",
            "anthropic-tools-smoke",
            "--out",
            str(a_output),
            "--allow-live",
            credential=("SYNTHETIC_A_AUTH", a_key),
            expected=1,
        )
        assert a_result["actual_requests"] == len(a.requests) == 4
        original_a = snapshots(a_output)
        archive = a_root / "handoff.zip"
        inventory = invoke(
            a_root,
            "diagnostics",
            "export",
            "--input",
            str(a_output),
            "--out",
            str(archive),
            "--include-evidence",
        )
        assert inventory["archive_sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()
        assert len(a.requests) == 4
        a.close()
        transferred = b_root / "received.zip"
        shutil.copy2(archive, transferred)
        assert transferred.read_bytes() == archive.read_bytes()
        b_data = b_root / "local-data"
        imported = invoke(
            b_root,
            "diagnostics",
            "import",
            "--package",
            str(transferred),
            "--data-dir",
            str(b_data),
        )
        assert object_value(imported["eligibility"])["retest"] is True
        baseline = str(imported["id"])
        inspected = invoke(
            b_root, "diagnostics", "inspect", "--baseline", baseline, "--data-dir", str(b_data)
        )
        assert inspected == imported
        assert not b.requests
        b_target = target_file(b_root, b.url, "SYNTHETIC_B_AUTH")
        preview = invoke(
            b_root,
            "diagnostics",
            "retest",
            "--baseline",
            baseline,
            "--data-dir",
            str(b_data),
            "--target",
            str(b_target),
            "--out",
            str(b_root / "preview"),
            "--dry-run",
        )
        plan = object_value(preview["plan"])
        assert plan["planned_requests"] == 4
        assert {case["id"] for case in objects(plan["cases"])} == CASE_IDS
        assert not b.requests
        b_output = b_root / "assessment"
        b_result = invoke(
            b_root,
            "diagnostics",
            "retest",
            "--baseline",
            baseline,
            "--data-dir",
            str(b_data),
            "--target",
            str(b_target),
            "--out",
            str(b_output),
            "--allow-live",
            "--language",
            "en",
            "--theme",
            "light",
            credential=("SYNTHETIC_B_AUTH", b_key),
            expected=1,
        )
        assert b_result["actual_requests"] == len(b.requests) == 4
        assert all(request["credential_matches"] is True for request in b.requests)
        result = object_value(strict_json((b_output / "result.json").read_text()))
        assert {case["id"] for case in objects(result["cases"])} == CASE_IDS
        assert all(
            object_value(case["dimensions"])["behavior"] == "PASS"
            for case in objects(result["cases"])
        )
        original_b = snapshots(b_output)
        comparison_path = b_root / "paired.json"
        comparison = invoke(
            b_root,
            "diagnostics",
            "compare",
            "--baseline",
            baseline,
            "--data-dir",
            str(b_data),
            "--input",
            str(b_output),
            "--out",
            str(comparison_path),
        )
        assert comparison["comparable"] is True
        assert object_value(comparison["coverage"])["matched_cases"] == 4
        pairs = {
            (row["case_id"], row["assertion_id"]): row["transition"]
            for row in objects(comparison["pairs"])
        }
        for case_id in CASE_IDS:
            assert pairs[case_id, "MSG-MODEL"] == "persistent"
            assert pairs[case_id, "MSG-CORE"] == "recovered"
        assert pairs["ANT-TEXT-SSE-002", "STR-START"] == "new_failure"
        assert comparison["all_previous_failures_passed"] is False
        assert any(
            change["field"] == "messages_url" and change["kind"] == "context"
            for change in objects(comparison["condition_changes"])
        )
        exported = b_root / "retest.zip"
        invoke(
            b_root,
            "diagnostics",
            "export",
            "--input",
            str(b_output),
            "--out",
            str(exported),
            "--include-evidence",
            "--comparison",
            str(comparison_path),
            "--language",
            "en",
            "--theme",
            "dark",
        )
        with ZipFile(exported) as package:
            assert package.read("result.json") == original_b["result.json"]
            assert object_value(strict_json(package.read("comparison.json").decode())) == comparison
            manifest = object_value(strict_json(package.read("manifest.json").decode()))
            assert manifest["presentation_version"] == "3.0"
            for entry in objects(manifest["files"]):
                content = package.read(str(entry["path"]))
                assert len(content) == entry["bytes"]
                assert hashlib.sha256(content).hexdigest() == entry["sha256"]
                assert a_key.encode() not in content
                assert b_key.encode() not in content
        assert len(b.requests) == 4
        assert snapshots(a_output) == original_a
        assert snapshots(b_output) == original_b
        assert all(a_key.encode() not in content for content in snapshots(b_root).values())
        assert not (b_root / "presets").exists()
