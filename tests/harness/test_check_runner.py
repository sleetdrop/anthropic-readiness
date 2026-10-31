"""Check orchestration must not turn missing evidence into a green result."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.check import CheckSpec, run_checks

ROOT = Path(__file__).resolve().parents[2]


def run_check(
    tmp_path: Path, argv: list[str], kind: str = "command", timeout: float = 2
) -> dict[str, object]:
    config = tmp_path / "checks.json"
    config.write_text(
        json.dumps(
            [
                {
                    "check_id": "sample",
                    "argv": argv,
                    "timeout_s": timeout,
                    "check_kind": kind,
                    "required": True,
                    "junit_path": str(tmp_path / "empty.xml") if kind == "pytest" else None,
                }
            ]
        )
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/check.py"),
            "--checks",
            str(config),
            "--out",
            str(tmp_path / "output"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    output = tmp_path / "output/check-result.json"
    assert output.exists(), result.stderr
    value: dict[str, object] = json.loads(output.read_text())
    return value


def test_failed_command_fails_suite(tmp_path: Path) -> None:
    result = run_check(tmp_path, [sys.executable, "-c", "raise SystemExit(7)"])
    assert result["status"] == "failed"


def test_missing_command_is_blocked(tmp_path: Path) -> None:
    result = run_check(tmp_path, ["/nonexistent-readiness-check"])
    assert result["status"] == "blocked"


def test_timeout_is_not_pass(tmp_path: Path) -> None:
    result = run_check(tmp_path, [sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.05)
    assert result["status"] == "blocked"


def test_timeout_tolerates_transient_permission_error_from_group_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = os.killpg
    attempts = 0

    def probe(group: int, sig: int) -> None:
        nonlocal attempts
        if sig == 0 and attempts == 0:
            attempts += 1
            raise PermissionError("transient process group probe")
        original(group, sig)

    monkeypatch.setattr(os, "killpg", probe)
    result = run_checks(
        [CheckSpec("timeout", [sys.executable, "-c", "import time; time.sleep(5)"], 0.1)],
        tmp_path / "checks",
        root=tmp_path,
    )
    document = json.loads((tmp_path / "checks/check-result.json").read_text())
    assert attempts == 1
    assert result == 1
    assert document["status"] == "blocked"
    assert document["checks"][0]["reason"] == "timeout"


def test_zero_collected_tests_is_not_pass(tmp_path: Path) -> None:
    report = tmp_path / "empty.xml"
    report.write_text('<testsuites><testsuite tests="0" /></testsuites>')
    result = run_check(tmp_path, [sys.executable, "-c", "pass"], kind="pytest")
    assert result["status"] == "failed"
    checks = result["checks"]
    assert isinstance(checks, list)
    assert checks[0]["reason"] == "no_tests"
