"""Serve is optional, locally bounded and cleanly owns its service lifecycle."""

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

from tests.acceptance.test_cli import cli


def test_serve_help_does_not_require_web_imports() -> None:
    result = cli("serve", "--help")
    assert result.returncode == 0
    assert "--data-dir" in result.stdout
    assert "--credential-env" in result.stdout


def test_missing_web_extra_returns_actionable_error(tmp_path: Path) -> None:
    code = """
import builtins,sys
original=builtins.__import__
def without_web(name,*args,**kwargs):
    if name.split('.')[0] in {'fastapi','uvicorn','jinja2'}:
        raise ModuleNotFoundError(name)
    return original(name,*args,**kwargs)
builtins.__import__=without_web
from anthropic_readiness.cli import main
sys.exit(main(['serve','--data-dir',sys.argv[1]]))
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert result.returncode == 2
    assert "anthropic-readiness[web]" in result.stderr
    assert "Traceback" not in result.stderr


def test_real_serve_start_and_signal_shutdown(tmp_path: Path) -> None:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "anthropic_readiness",
            "serve",
            "--data-dir",
            str(tmp_path),
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        with httpx.Client(trust_env=False, timeout=0.2) as client:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                try:
                    response = client.get(f"http://127.0.0.1:{port}/health")
                    if response.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.02)
            else:
                raise AssertionError("serve_did_not_start")
        os.kill(process.pid, signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=8)
        # The locked Uvicorn replays SIGTERM only after lifespan shutdown.
        assert process.returncode == -signal.SIGTERM, (stdout, stderr)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=2)
