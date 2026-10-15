"""User commands perform only explicit actions and preserve exit codes."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.http_server import SyntheticServer

ROOT = Path(__file__).resolve().parents[2]


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "anthropic_readiness", *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


def target_file(tmp_path: Path, url: str | None = None) -> Path:
    path = tmp_path / "target.yaml"
    text = (ROOT / "examples/target.yaml").read_text()
    if url:
        text = text.replace("http://127.0.0.1:8000/v1/messages", url)
    path.write_text(text)
    return path


def test_validate_contracts_and_dry_run(tmp_path: Path) -> None:
    target = target_file(tmp_path)
    assert cli("validate", "--target", str(target)).returncode == 0
    assert cli("contracts", "list").returncode == 0
    shown = cli("contracts", "show", "anthropic-messages-2023-06-01-core", "--revision", "1.0.0")
    assert shown.returncode == 0
    assert json.loads(shown.stdout)["api_version"] == "2023-06-01"
    out = tmp_path / "dry"
    dry = cli("run", "--target", str(target), "--out", str(out), "--dry-run")
    assert dry.returncode == 0
    assert json.loads(dry.stdout)["planned_requests"] == 3
    assert not out.exists()


def test_run_requires_opt_in_and_budget_before_output(tmp_path: Path) -> None:
    target = target_file(tmp_path)
    out = tmp_path / "run"
    assert cli("run", "--target", str(target), "--out", str(out)).returncode == 2
    assert not out.exists()
    target.write_text(target.read_text().replace("limits: {}", "limits: {max_requests: 2}"))
    assert cli("run", "--target", str(target), "--out", str(out), "--allow-live").returncode == 2
    assert not out.exists()


def test_actual_request_counts(server: SyntheticServer, tmp_path: Path) -> None:
    target = target_file(tmp_path, server.url + "/cases")
    out = tmp_path / "run"
    result = cli("run", "--target", str(target), "--out", str(out), "--allow-live")
    assert result.returncode == 0, result.stderr
    document = json.loads((out / "result.json").read_text())
    assert document["plan"]["actual_requests"] == len(server.requests) == 3
    assert len(document["cases"]) == 3
    assert document["profiles"][0]["readiness"] == "passed"


@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
def test_signal_preserves_partial_results(
    server: SyntheticServer, tmp_path: Path, sig: signal.Signals
) -> None:
    target = target_file(tmp_path, server.url + "/pings")
    out = tmp_path / "run"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "anthropic_readiness",
            "run",
            "--target",
            str(target),
            "--out",
            str(out),
            "--allow-live",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 5
        while not server.requests and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert server.requests
        os.kill(process.pid, sig)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 128 + sig, (stdout, stderr)
        document = json.loads((out / "result.json").read_text())
        assert len(document["cases"]) == 3
        assert document["execution_environment"]["interruption"] == sig
        assert document["cases"][0]["attempts"][0]["termination"]["capture_end"] == "cancelled"
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=2)
