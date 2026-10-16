"""Run the offline developer check graph; image acceptance is separate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    argv: list[str]
    timeout_s: float
    check_kind: str = "command"
    required: bool = True
    junit_path: Path | None = None
    cwd: Path | None = None

    def __post_init__(self) -> None:
        if (
            not re.fullmatch(r"[A-Za-z0-9_-]+", self.check_id)
            or not self.argv
            or any(not isinstance(a, str) for a in self.argv)
        ):
            raise ValueError("invalid_check_command")
        if (
            isinstance(self.timeout_s, bool)
            or not math.isfinite(self.timeout_s)
            or self.timeout_s <= 0
            or type(self.required) is not bool
            or self.check_kind not in {"command", "pytest"}
        ):
            raise ValueError("invalid_check_configuration")


def _utc() -> str:
    return datetime.now(UTC).isoformat()


def source_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    paths = [
        p
        for directory in ("src", "tests", "scripts", "examples", ".github", ".devcontainer")
        for p in (root / directory).rglob("*")
        if p.is_file()
        and not any(
            part in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
            for part in p.parts
        )
    ]
    paths.extend(
        root / p
        for p in (
            "pyproject.toml",
            "uv.lock",
            ".python-version",
            "Dockerfile",
            ".dockerignore",
            ".gitignore",
            ".pre-commit-config.yaml",
            "AGENTS.md",
            "README.md",
            "CONTRIBUTING.md",
            "docs/architecture.md",
            "docs/development.md",
            "docs/container-usage.md",
            "docs/harness/acceptance.json",
        )
        if (root / p).is_file()
    )
    for path in sorted(set(paths)):
        if path.suffix in {".pyc", ".pyo"}:
            continue
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


def _tool_versions() -> dict[str, str | None]:
    values: dict[str, str | None] = {"python": platform.python_version()}
    for name in ("ruff", "mypy", "pytest", "import-linter", "jsonschema", "hatchling"):
        try:
            values[name] = version(name)
        except PackageNotFoundError:
            values[name] = None
    try:
        result = subprocess.run(
            ["uv", "--version"], capture_output=True, text=True, timeout=5, check=False
        )
        values["uv"] = result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        values["uv"] = None
    return values


def _run_one(spec: CheckSpec, output_dir: Path) -> dict[str, object]:
    start = time.monotonic()
    started_at = _utc()
    status, reason, code = "blocked", "not_started", None
    log = output_dir / f"{spec.check_id}.log"
    with log.open("wb") as stream:
        try:
            completed = subprocess.run(
                spec.argv,
                cwd=spec.cwd,
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=spec.timeout_s,
                env=dict(os.environ, UV_OFFLINE="1"),
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
                        suites = list(tree.iter("testsuite"))
                        count = sum(int(node.get("tests", "0")) for node in suites)
                        skipped = sum(int(node.get("skipped", "0")) for node in suites)
                        defects = sum(
                            int(node.get("failures", "0")) + int(node.get("errors", "0"))
                            for node in suites
                        )
                        if count == 0:
                            status, reason = "failed", "no_tests"
                        elif defects:
                            status, reason = "failed", "test_report_failures"
                        elif count <= skipped:
                            status, reason = "failed", "no_executed_tests"
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
        "started_at": started_at,
        "finished_at": _utc(),
        "log": str(log),
    }


def _git_state(root: Path) -> dict[str, str | bool | None]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return {
            "commit": commit.stdout.strip() if commit.returncode == 0 else None,
            "dirty": bool(dirty.stdout.strip()) if dirty.returncode == 0 else None,
        }
    except (OSError, subprocess.TimeoutExpired):
        return {"commit": None, "dirty": None}


def run_checks(
    checks: Sequence[CheckSpec], output_dir: Path, *, root: Path = ROOT, scope: str = "custom"
) -> int:
    output_dir.mkdir(parents=True, exist_ok=False)
    started = _utc()
    before = source_fingerprint(root)
    results = [_run_one(spec, output_dir) for spec in checks]
    required = [r for r in results if r["required"]]
    status = (
        "failed"
        if any(r["status"] == "failed" for r in required)
        else "passed"
        if required and all(r["status"] == "passed" for r in required)
        else "blocked"
    )
    after = source_fingerprint(root)
    if before != after:
        status = "failed"
    payload = {
        "schema_version": "1.0",
        "scope": scope,
        "stage_readiness": "incomplete",
        "started_at": started,
        "finished_at": _utc(),
        "source_fingerprint": before,
        "source_unchanged": before == after,
        "lock_sha256": hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest()
        if (root / "uv.lock").is_file()
        else None,
        "tool_versions": _tool_versions(),
        "git": _git_state(root),
        "status": status,
        "checks": results,
        "external_checks": {
            "container_acceptance": "not_run",
            "remote_ci": "not_run",
            "independent_review": "not_run",
        },
    }
    (output_dir / "check-result.json").write_text(json.dumps(payload, indent=2) + "\n")
    for result in results:
        print(f"{result['check_id']}: {result['status']} ({result['reason']})")
    return 0 if status == "passed" else 1


def build_checks(root: Path, output: Path, suite: str) -> list[CheckSpec]:
    root, output = root.resolve(), output.resolve()

    def command(name: str, argv: list[str], timeout: float = 120) -> CheckSpec:
        return CheckSpec(name, argv, timeout, cwd=root)

    def pytest_check(name: str, paths: list[str], extra: list[str] | None = None) -> CheckSpec:
        junit = output / f"{name}.xml"
        return CheckSpec(
            name,
            [sys.executable, "-m", "pytest", "-q", *paths, *(extra or []), f"--junitxml={junit}"],
            300,
            "pytest",
            junit_path=junit,
            cwd=root,
        )

    checks = [
        command("lock", ["uv", "lock", "--check", "--offline"]),
        command("format", ["ruff", "format", "--check", "src", "tests", "scripts"]),
        command("lint", ["ruff", "check", "src", "tests", "scripts"]),
        command("type", ["mypy", "--config-file", str(root / "pyproject.toml")]),
        command(
            "architecture",
            ["lint-imports", "--config", str(root / "pyproject.toml"), "--no-cache", "--no-logo"],
        ),
        command(
            "schemas",
            [sys.executable, str(ROOT / "scripts/validate_resources.py"), "--root", str(root)],
        ),
        pytest_check(
            "unit",
            ["tests/unit", "tests/harness"],
            ["--cov=anthropic_readiness", f"--cov-report=xml:{output / 'coverage.xml'}"],
        ),
    ]
    if suite == "full":
        checks.extend(
            [
                pytest_check("integration", ["tests/integration"]),
                pytest_check(
                    "acceptance",
                    ["tests/acceptance", "--ignore=tests/acceptance/test_installed_package.py"],
                ),
                pytest_check("packaging", ["tests/acceptance/test_installed_package.py"]),
                command(
                    "documentation",
                    [sys.executable, str(ROOT / "scripts/check_docs.py"), "--root", str(root)],
                ),
            ]
        )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["fast", "full"], default="fast")
    parser.add_argument("--checks", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    out = (args.out or args.root / "artifacts/checks" / str(time.time_ns())).resolve()
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
        checks = build_checks(args.root, out, args.suite)
    return run_checks(checks, out, root=args.root, scope="custom" if args.checks else args.suite)


if __name__ == "__main__":
    raise SystemExit(main())
