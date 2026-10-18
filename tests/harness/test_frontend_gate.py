"""Frontend gates must prove executed cases and prepared, fingerprinted tools."""

import json
import os
import signal
import subprocess
import sys
import time
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
        "start_ticks": Path("/proc/self/stat").read_text().split()[21],
        "stopped": stopped,
        "web_port": 18765,
        "peer_port": 18766,
    }
    (tmp_path / "process.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match=r"fixture_.*"):
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


def test_gate_timeout_stops_owned_descendants(tmp_path: Path) -> None:
    child_file = tmp_path / "child.json"
    script = (
        "import subprocess,sys,json,time; from pathlib import Path; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        "stat=Path('/proc/'+str(p.pid)+'/stat').read_text().split(); "
        "Path(sys.argv[1]).write_text(json.dumps({'pid':p.pid,'start':stat[21]})); "
        "time.sleep(60)"
    )
    run_checks(
        [CheckSpec("timeout", [sys.executable, "-c", script, str(child_file)], 0.3)],
        tmp_path / "checks",
        root=tmp_path,
    )
    child = json.loads(child_file.read_text())
    stat = Path(f"/proc/{child['pid']}/stat")

    def alive() -> bool:
        try:
            parts = stat.read_text().split()
            return parts[21] == child["start"] and parts[2] != "Z"
        except FileNotFoundError:
            return False

    try:
        deadline = time.monotonic() + 2
        while alive() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert not alive(), "check timeout left an owned child running"
    finally:
        if alive():
            os.kill(child["pid"], signal.SIGTERM)


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
