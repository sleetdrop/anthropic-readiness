"""Frontend gates must prove executed cases and prepared, fingerprinted tools."""

import json
import os
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path

import pytest

from scripts.browser_fixture import verify_cleanup
from scripts.check import CheckSpec, build_checks, run_checks, source_fingerprint

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("report", "code", "expected"),
    [
        (None, 2, "blocked"),
        (None, 0, "failed"),
        ('<testsuites><testsuite tests="0"/></testsuites>', 0, "failed"),
        ('<testsuites><testsuite tests="1"/></testsuites>', 0, "failed"),
        (
            '<testsuite tests="1"><testcase name="omitted"><skipped/></testcase></testsuite>',
            0,
            "failed",
        ),
        (
            '<testsuite tests="1"><testcase name="broken"><failure/></testcase></testsuite>',
            0,
            "failed",
        ),
        ('<testsuite tests="1"><testcase name="executed"/></testsuite>', 0, "passed"),
    ],
)
def test_frontend_gate_cannot_pass_with_missing_browser_or_zero_cases(
    tmp_path: Path, report: str | None, code: int, expected: str
) -> None:
    junit = tmp_path / "browser.xml"
    if report is not None:
        junit.write_text(report)
    output = tmp_path / "checks"
    gate = CheckSpec(
        "frontend-browser",
        [sys.executable, "-c", f"raise SystemExit({code})"],
        5,
        "junit",
        junit_path=junit,
        blocked_exit_codes=(2,),
    )
    result = run_checks([gate], output, root=tmp_path)
    document = json.loads((output / "check-result.json").read_text())
    assert document["status"] == expected
    assert result == (0 if expected == "passed" else 1)


def test_frontend_is_required_in_each_designated_graph(tmp_path: Path) -> None:
    for suite in ("fast", "full"):
        checks = {item.check_id: item for item in build_checks(ROOT, tmp_path, suite)}
        assert checks["frontend-static"].required
        if suite == "full":
            assert checks["frontend-browser"].required
            assert checks["frontend-browser"].check_kind == "junit"
            assert checks["frontend-browser"].junit_path is not None


@pytest.mark.parametrize(
    "name",
    [
        "package-lock.json",
        "playwright.config.js",
        ".prettierrc.json",
        "docs/harness/web-toolchain.json",
    ],
)
def test_frontend_preparation_is_part_of_source_fingerprint(tmp_path: Path, name: str) -> None:
    before = source_fingerprint(tmp_path)
    file = tmp_path / name
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("synthetic change")
    assert source_fingerprint(tmp_path) != before


def test_full_ci_prepares_locked_node_and_browser() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "scripts/prepare_frontend.py" in workflow
    assert "playwright install --with-deps chromium" in workflow


@pytest.mark.parametrize("stopped", [False, True])
def test_browser_cleanup_rejects_unfinished_or_still_live_owner(
    tmp_path: Path, stopped: bool
) -> None:
    record = {
        "pid": os.getpid(),
        "stopped": stopped,
        "web_port": 18765,
        "peer_port": 18766,
    }
    (tmp_path / "process.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match=r"fixture_.*"):
        verify_cleanup(tmp_path)


def test_browser_cleanup_rejects_any_live_owner_without_proc(tmp_path: Path) -> None:
    record = {
        "pid": os.getpid(),
        "stopped": True,
        "web_port": 18765,
        "peer_port": 18766,
    }
    (tmp_path / "process.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match="fixture_owner_still_alive"):
        verify_cleanup(tmp_path)


def test_browser_cleanup_cannot_accept_unverifiable_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "process.json").write_text(
        json.dumps({"pid": 42, "stopped": True, "web_port": 18765, "peer_port": 18766})
    )

    def denied(pid: int, sig: int) -> None:
        raise PermissionError("process identity unavailable")

    monkeypatch.setattr(os, "kill", denied)
    with pytest.raises(ValueError, match="fixture_owner_unverifiable"):
        verify_cleanup(tmp_path)


def test_actual_missing_browser_produces_schema_valid_blocked_record(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.check_frontend",
            "--suite",
            "browser",
            "--out",
            str(tmp_path / "gate"),
        ],
        cwd=ROOT,
        env={**os.environ, "PLAYWRIGHT_BROWSERS_PATH": str(tmp_path / "unprepared")},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    document = json.loads((tmp_path / "gate/check-result.json").read_text())
    assert document["status"] == "blocked"
    assert document["checks"][0]["reason"] in {"missing_prerequisite", "missing_command"}
    assert not (tmp_path / "gate/browser.xml").exists()


def _descendant_code() -> str:
    return (
        "import errno,os,sys,time\n"
        "try:\n"
        " fd=os.open(sys.argv[1],os.O_WRONLY|os.O_NONBLOCK)\n"
        "except OSError as exc:\n"
        " if exc.errno == errno.ENXIO: sys.exit(0)\n"
        " raise\n"
        "try:\n"
        " os.write(fd,b'ready')\n"
        " while True:\n"
        "  time.sleep(0.05)\n"
        "  os.write(fd,b'x')\n"
        "except BrokenPipeError:\n"
        " pass\n"
    )


def test_descendant_fixture_exits_when_reader_is_closed(tmp_path: Path) -> None:
    fifo = tmp_path / "child-open"
    os.mkfifo(fifo)
    reader = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
    child = subprocess.Popen([sys.executable, "-c", _descendant_code(), str(fifo)])
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with suppress(BlockingIOError):
                if os.read(reader, 5) == b"ready":
                    break
            time.sleep(0.02)
        else:
            pytest.fail("descendant did not start")
        os.close(reader)
        reader = -1
        assert child.wait(timeout=5) == 0
    finally:
        if reader >= 0:
            os.close(reader)
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)


def test_descendant_fixture_exits_if_reader_closes_before_open(tmp_path: Path) -> None:
    fifo = tmp_path / "child-open"
    os.mkfifo(fifo)
    result = subprocess.run(
        [sys.executable, "-c", _descendant_code(), str(fifo)],
        capture_output=True,
        text=True,
        timeout=1,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_gate_timeout_stops_owned_descendants(tmp_path: Path) -> None:
    fifo = tmp_path / "child-open"
    os.mkfifo(fifo)
    reader = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
    script = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable,'-c',{_descendant_code()!r},sys.argv[1]]); "
        "time.sleep(60)"
    )
    try:
        run_checks(
            [CheckSpec("timeout", [sys.executable, "-c", script, str(fifo)], 2)],
            tmp_path / "checks",
            root=tmp_path,
        )
        document = json.loads((tmp_path / "checks/check-result.json").read_text())
        assert document["checks"][0]["reason"] == "timeout"
        assert os.read(reader, 5) == b"ready", "descendant did not start"
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                if os.read(reader, 4096) == b"":
                    break
            except BlockingIOError:
                pass
            time.sleep(0.02)
        else:
            pytest.fail("check timeout left an owned child running")
    finally:
        os.close(reader)


@pytest.mark.parametrize("kind", ["junit", "pytest"])
def test_selected_suite_with_any_unexpected_skip_is_not_green(tmp_path: Path, kind: str) -> None:
    junit = tmp_path / "mixed.xml"
    junit.write_text(
        '<testsuites><testsuite tests="2" skipped="1" failures="0" errors="0">'
        '<testcase name="executed"/><testcase name="omitted"><skipped/></testcase>'
        "</testsuite></testsuites>"
    )
    output = tmp_path / "checks"
    gate = CheckSpec("selected-suite", [sys.executable, "-c", "pass"], 5, kind, junit_path=junit)
    assert run_checks([gate], output, root=tmp_path) == 1
    document = json.loads((output / "check-result.json").read_text())
    assert document["status"] == "failed"
    assert document["checks"][0]["reason"] == "unexpected_skipped_tests"
