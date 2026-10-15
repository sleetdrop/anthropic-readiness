"""Run deterministic developer checks without concealing missing evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    argv: list[str]
    timeout_s: float
    check_kind: str = "command"
    required: bool = True
    junit_path: Path | None = None


def _run_one(spec: CheckSpec, output_dir: Path) -> dict[str, object]:
    start = time.monotonic()
    status, reason, code = "blocked", "not_started", None
    log = output_dir / f"{spec.check_id}.log"
    env = dict(os.environ, UV_OFFLINE="1")
    with log.open("wb") as stream:
        try:
            completed = subprocess.run(
                spec.argv,
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=spec.timeout_s,
                env=env,
                check=False,
            )
            code = completed.returncode
            status, reason = ("passed", "completed") if code == 0 else ("failed", "nonzero_exit")
            if status == "passed" and spec.check_kind == "pytest":
                if spec.junit_path is None or not spec.junit_path.is_file():
                    status, reason = "failed", "missing_test_report"
                else:
                    try:
                        tree = ET.parse(spec.junit_path)
                        count = sum(int(node.get("tests", "0")) for node in tree.iter("testsuite"))
                        if count == 0:
                            status, reason = "failed", "no_tests"
                    except (ET.ParseError, ValueError):
                        status, reason = "failed", "invalid_test_report"
        except FileNotFoundError:
            status, reason = "blocked", "missing_command"
        except subprocess.TimeoutExpired:
            status, reason = "blocked", "timeout"
    return {
        "check_id": spec.check_id,
        "argv": spec.argv,
        "required": spec.required,
        "status": status,
        "reason": reason,
        "returncode": code,
        "duration_s": time.monotonic() - start,
        "log": str(log),
    }


def run_checks(checks: Sequence[CheckSpec], output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=False)
    results = [_run_one(spec, output_dir) for spec in checks]
    required = [r for r in results if r["required"]]
    status = "passed"
    if any(r["status"] == "failed" for r in required):
        status = "failed"
    elif not required or any(r["status"] != "passed" for r in required):
        status = "blocked"
    fingerprint = hashlib.sha256()
    for path in sorted(Path("src").rglob("*.py")):
        fingerprint.update(str(path).encode())
        fingerprint.update(path.read_bytes())
    payload = {
        "schema_version": "1.0",
        "scope": "bootstrap",
        "stage_readiness": "incomplete",
        "started_at": datetime.now(UTC).isoformat(),
        "source_fingerprint": fingerprint.hexdigest(),
        "status": status,
        "checks": results,
    }
    (output_dir / "check-result.json").write_text(json.dumps(payload, indent=2) + "\n")
    for result in results:
        print(f"{result['check_id']}: {result['status']} ({result['reason']})")
    return 0 if status == "passed" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["fast", "full"], default="fast")
    parser.add_argument("--checks", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or Path("artifacts/checks") / str(time.time_ns())
    if args.checks:
        values = json.loads(args.checks.read_text())
        checks = [
            CheckSpec(
                v["check_id"],
                v["argv"],
                v["timeout_s"],
                v.get("check_kind", "command"),
                v.get("required", True),
                Path(v["junit_path"]) if v.get("junit_path") else None,
            )
            for v in values
        ]
    else:
        junit = out / "pytest.xml"
        checks = [
            CheckSpec("lock", ["uv", "lock", "--check", "--offline"], 60),
            CheckSpec("format", ["ruff", "format", "--check", "src", "tests", "scripts"], 60),
            CheckSpec("lint", ["ruff", "check", "src", "tests", "scripts"], 60),
            CheckSpec("type", ["mypy"], 120),
            CheckSpec(
                "unit",
                [sys.executable, "-m", "pytest", "-q", f"--junitxml={junit}"],
                180,
                "pytest",
                junit_path=junit,
            ),
        ]
    return run_checks(checks, out)


if __name__ == "__main__":
    raise SystemExit(main())
