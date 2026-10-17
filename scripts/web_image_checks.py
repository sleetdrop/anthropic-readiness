"""Host-side stdlib HTTP observations of installed Web images and their owned volumes."""

from __future__ import annotations

import hashlib
import io
import json
import platform
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scripts.check_images import Acceptance

ROOT = Path(__file__).resolve().parents[1]
TERMINAL = {"completed", "cancelled", "interrupted", "error"}


class WebClient:
    def __init__(self, base: str) -> None:
        self.base = base
        self.cookie = ""
        self.csrf = ""

    def request(self, path: str, body: dict[str, Any] | None = None) -> bytes:
        headers = {"Host": "127.0.0.1:8765", "Origin": "http://127.0.0.1:8765"}
        if self.cookie:
            headers["Cookie"] = self.cookie
        if body is not None:
            headers.update({"Content-Type": "application/json", "X-CSRF-Token": self.csrf})
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            cookie = response.headers.get("Set-Cookie")
            if cookie:
                self.cookie = cookie.split(";", 1)[0]
            return bytes(response.read())

    def json(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        value: dict[str, Any] = json.loads(self.request(path, body))
        return value

    def bootstrap(self) -> None:
        deadline = time.monotonic() + 45
        while True:
            try:
                self.csrf = str(self.json("/api/v1/session")["csrf_token"])
                return
            except OSError:
                if time.monotonic() >= deadline:
                    raise RuntimeError("web_start_timeout") from None
                time.sleep(0.1)

    def start(self, url: str) -> str:
        # This file is an acceptance harness, never a provider configuration.
        target: dict[str, Any] = {
            "schema_version": "1.0",
            "name": "synthetic-container-peer",
            "delivery_id": "synthetic",
            "protocol": "anthropic.messages",
            "messages_url": url,
            "model": "example-model",
            "api_version": "2023-06-01",
            "beta_headers": [],
            "protocol_contract": {"id": "anthropic-messages-2023-06-01-core", "revision": "1.0.0"},
            "auth": {"mode": "none"},
            "capabilities": {
                "streaming": True,
                "tools": True,
                "thinking": False,
                "parallel_tools": False,
            },
            "response_model_policy": "request_or_alias",
            "response_model_aliases": [],
            "limits": {
                "max_requests": 4,
                "run_timeout_s": 30,
                "attempt_timeout_s": 15,
                "read_timeout_s": 5,
            },
        }
        frozen = self.json(
            "/api/v1/plans",
            {"target": target, "profiles": ["anthropic-basic", "anthropic-tools-smoke"]},
        )
        return str(
            self.json(
                "/api/v1/runs",
                {
                    "plan_id": frozen["id"],
                    "live_consent": True,
                    "idempotency_key": str(frozen["id"]),
                },
            )["id"]
        )

    def wait(self, run_id: str) -> dict[str, Any]:
        deadline = time.monotonic() + 45
        while True:
            record = self.json("/api/v1/runs/" + run_id)
            if record["job"]["state"] in TERMINAL:
                return record
            if time.monotonic() > deadline:
                raise RuntimeError("web_job_timeout")
            time.sleep(0.05)


def request_count(acceptance: Acceptance) -> int:
    path = acceptance.peer_state / "requests.jsonl"
    return len(path.read_text().splitlines()) if path.is_file() else 0


def wait_count(acceptance: Acceptance, expected: int) -> None:
    deadline = time.monotonic() + 30
    while request_count(acceptance) != expected:
        if time.monotonic() >= deadline:
            raise RuntimeError("synthetic_request_count_timeout")
        time.sleep(0.05)


def run_web_checks(a: Acceptance, host_url: str) -> None:
    def passed(name: str, observations: dict[str, Any]) -> None:
        path = a.output / (name + ".json")
        path.write_text(json.dumps(observations, indent=2) + "\n")
        a.records.append({"id": name, "status": "passed", "log": path.name})

    image = json.loads(
        a.docker("web-image-inspect", ["image", "inspect", a.web, "--format", "{{json .}} "])
    )
    if image["Config"]["Labels"].get("io.anthropic-readiness.image-context") != a.image_context:
        raise RuntimeError("web_image_context_mismatch")
    a.docker(
        "web-default-nonroot",
        [
            "run",
            "--rm",
            "--platform",
            a.platform,
            "--network",
            "none",
            "--read-only",
            "--entrypoint",
            "python",
            a.web,
            "-c",
            "import os,shutil,importlib.util; from importlib.resources import files; from anthropic_readiness.web.pages import ASSETS,ENVIRONMENT; assert os.getuid()==10001; assert not any(shutil.which(x) for x in ('uv','git','node','npm','pytest','chromium')); assert importlib.util.find_spec('pytest') is None; assert not os.path.exists('/build'); [ENVIRONMENT.get_template(n) for n in ('base.html','configure.html','run.html','history.html')]; assert all(files('anthropic_readiness').joinpath('resources/'+n).is_file() for n in ASSETS); print('installed Web resources and nonroot isolation verified')",
        ],
    )
    volume = a.token + "-web-data"
    a.volumes.append(volume)
    a.docker("web-volume-create", ["volume", "create", volume])

    def start(suffix: str) -> tuple[str, WebClient]:
        name = a.token + "-web-" + suffix
        a.containers.append(name)
        args = [
            "run",
            "-d",
            "--name",
            name,
            "--platform",
            a.platform,
            "--read-only",
            "--tmpfs",
            "/tmp:rw,nosuid,noexec,size=64m",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--network",
            a.web_network,
            "-p",
            "127.0.0.1::8765",
            "-v",
            volume + ":/data",
        ]
        if platform.system() == "Linux":
            args.extend(["--add-host", "host.docker.internal:host-gateway"])
        a.docker("web-start-" + suffix, [*args, a.web])
        port = a.docker("web-port-" + suffix, ["port", name, "8765/tcp"]).strip().split(":")[-1]
        client = WebClient("http://127.0.0.1:" + port)
        client.bootstrap()
        return name, client

    name, client = start("first")
    page = client.request("/new").decode()
    if page.count("data-case-id=") != 4 or "预览计划" not in page:
        raise RuntimeError("web_page_scope")
    for asset in ("web/app.js", "web/app.css", "report-v2.js", "report-v2.css"):
        if len(client.request("/assets/" + asset)) < 100:
            raise RuntimeError("web_asset_missing")
    passed("web-pages", {"cases": 4, "installed_assets": True})
    before = request_count(a)
    run_id = client.start("http://synthetic-peer:8080/cases")
    record = client.wait(run_id)
    (a.output / "web-completed-response.json").write_text(json.dumps(record, indent=2) + "\n")
    if record["job"]["state"] != "completed" or record["execution"]["actual_requests"] != 4:
        raise RuntimeError("web_assessment_accounting")
    if any(case["status"] != "PASS" for case in record["report"]["cases"]):
        raise RuntimeError("web_synthetic_verdict")
    if request_count(a) != before + 4:
        raise RuntimeError("web_peer_accounting")
    passed(
        "web-assessment",
        {"run_id": run_id, "actual_requests": 4, "cases": 4, "data_kind": "synthetic"},
    )
    policy = {"formats": ["html", "markdown", "json"], "include_evidence": True}
    client.json(f"/api/v1/runs/{run_id}/exports/preview", policy)
    created = client.json(f"/api/v1/runs/{run_id}/exports", policy)
    raw = client.request(f"/api/v1/runs/{run_id}/exports/{created['export_id']}")
    (a.output / "web-synthetic-export.zip").write_bytes(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        if set(archive.namelist()) != {item["path"] for item in manifest["files"]} | {
            "manifest.json"
        }:
            raise RuntimeError("web_export_inventory")
        for entry in manifest["files"]:
            data = archive.read(entry["path"])
            if hashlib.sha256(data).hexdigest() != entry["sha256"] or len(data) != entry["bytes"]:
                raise RuntimeError("web_export_hash")
        original = archive.read("result.json")
    result_hash = hashlib.sha256(original).hexdigest()
    if result_hash != manifest["source_result_sha256"] or request_count(a) != before + 4:
        raise RuntimeError("web_export_source_or_requests")
    passed(
        "web-exports",
        {"source_sha256": result_hash, "files": len(manifest["files"]), "extra_requests": 0},
    )
    if a.scope != "full":
        return
    before = request_count(a)
    cancelled = client.start("http://synthetic-peer:8080/pings")
    wait_count(a, before + 1)
    client.json(f"/api/v1/runs/{cancelled}/cancel", {})
    cancelled_record = client.wait(cancelled)
    if (
        cancelled_record["job"]["state"] not in {"cancelled", "interrupted"}
        or request_count(a) != before + 1
    ):
        raise RuntimeError("web_cancellation_accounting")
    passed("web-cancellation", {"state": cancelled_record["job"]["state"], "actual_requests": 1})
    before = request_count(a)
    active = client.start("http://synthetic-peer:8080/pings")
    wait_count(a, before + 1)
    queued = client.start("http://synthetic-peer:8080/cases")
    if client.json("/api/v1/runs/" + queued)["job"]["state"] != "queued":
        raise RuntimeError("web_queue_before_shutdown")
    a.docker("web-stop-active", ["stop", "--time", "15", name], timeout=30)
    a.docker("web-remove-first", ["rm", name])
    name, client = start("replacement")
    restored = client.json("/api/v1/runs/" + run_id)
    (a.output / "web-restored-response.json").write_text(json.dumps(restored, indent=2) + "\n")
    if restored["job"]["state"] != "completed" or restored["report"] != record["report"]:
        raise RuntimeError("web_completed_source_changed")
    for interrupted_id in (active, queued):
        if client.json("/api/v1/runs/" + interrupted_id)["job"]["state"] not in TERMINAL:
            raise RuntimeError("web_restart_resumed_job")
    if request_count(a) != before + 1:
        raise RuntimeError("web_restart_sent_request")
    history = client.json("/api/v1/runs")["items"]
    if run_id not in {item["job"]["id"] for item in history}:
        raise RuntimeError("web_history_not_retained")
    passed(
        "web-volume-restart",
        {"original_run": run_id, "active": active, "queued": queued, "extra_requests": 0},
    )
    a.docker("web-enable-host-route", ["network", "connect", "bridge", name])
    before = request_count(a)
    host_run = client.start(host_url)
    host_record = client.wait(host_run)
    if (
        host_record["job"]["state"] != "completed"
        or host_record["execution"]["actual_requests"] != 4
        or request_count(a) != before + 4
    ):
        raise RuntimeError("web_host_path_failed")
    if any(case["status"] != "PASS" for case in host_record["report"]["cases"]):
        raise RuntimeError("web_host_path_verdict")
    passed("web-host-path", {"actual_requests": 4, "data_kind": "synthetic", "host": host_url})
