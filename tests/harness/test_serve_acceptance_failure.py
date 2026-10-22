"""The startup acceptance probe must preserve failures without leaking pipes."""

import socket
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from tests.acceptance import test_serve_command


def test_healthy_cold_response_uses_the_remaining_startup_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = subprocess.Popen
    code = """
import http.server,sys,time
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.3)
        try:
            self.send_response(200)
            self.send_header('Content-Length','15')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        except (BrokenPipeError,ConnectionResetError):
            pass
    def log_message(self,*args):
        pass
http.server.HTTPServer(('127.0.0.1',int(sys.argv[1])),Handler).serve_forever()
"""

    def cold_health(argv: Sequence[str], **kwargs: Any) -> subprocess.Popen[str]:
        return original([sys.executable, "-c", code, argv[argv.index("--port") + 1]], **kwargs)

    monkeypatch.setattr(subprocess, "Popen", cold_health)
    test_serve_command.test_real_serve_start_and_signal_shutdown(tmp_path)


@pytest.mark.parametrize("contract", ["cleanup", "diagnostics"])
def test_startup_child_failure_preserves_diagnostics_and_closes_pipes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, contract: str
) -> None:
    original = subprocess.Popen
    children: list[subprocess.Popen[str]] = []
    with socket.socket() as reservation:

        def failed_child(argv: Sequence[str], **kwargs: Any) -> subprocess.Popen[str]:
            # Keep the selected address unavailable to unrelated services while
            # a real child exercises the acceptance probe's failure path.
            reservation.bind(("127.0.0.1", int(argv[argv.index("--port") + 1])))
            child: subprocess.Popen[str] = original(
                [
                    sys.executable,
                    "-c",
                    "import sys; print('synthetic-startup-exit',file=sys.stderr); sys.exit(23)",
                ],
                **kwargs,
            )
            children.append(child)
            return child

        monkeypatch.setattr(subprocess, "Popen", failed_child)
        try:
            with pytest.raises(AssertionError) as failure:
                test_serve_command.test_real_serve_start_and_signal_shutdown(tmp_path)
            assert len(children) == 1
            if contract == "cleanup":
                assert children[0].stdout is None or children[0].stdout.closed
                assert children[0].stderr is None or children[0].stderr.closed
                assert children[0].poll() == 23
            else:
                assert "23" in str(failure.value)
                assert "synthetic-startup-exit" in str(failure.value)
        finally:
            # Contain the known defect while observing RED; do not let this
            # regression itself poison later tests with unraisable warnings.
            for child in children:
                if child.poll() is None:
                    child.kill()
                child.wait(timeout=2)
                if child.stdout is not None:
                    child.stdout.close()
                if child.stderr is not None:
                    child.stderr.close()
