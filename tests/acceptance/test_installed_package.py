"""The built wheel works away from source and carries runtime resources."""

import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.check_package import verify_wheel_resources
from tests.acceptance.test_cli import ROOT


def run(
    argv: list[str], cwd: Path, project_environment: Path | None = None
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "UV_OFFLINE": "1"}
    if project_environment is not None:
        env["UV_PROJECT_ENVIRONMENT"] = str(project_environment)
    result = subprocess.run(
        argv, cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=120
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def test_installed_wheel_outside_repository(tmp_path: Path) -> None:
    from anthropic_readiness.diagnostics.identity import installed_identity

    expected_identity = installed_identity().document
    dist = tmp_path / "dist"
    run(["uv", "build", "--offline", "--no-build-isolation", "--out-dir", str(dist)], ROOT)
    wheel = next(dist.glob("*.whl"))
    assert list(dist.glob("*.tar.gz"))
    assert verify_wheel_resources(wheel, ROOT) == []
    environment = tmp_path / "venv"
    run(["uv", "venv", str(environment), "--python", sys.executable], tmp_path)
    run(
        ["uv", "sync", "--locked", "--no-dev", "--no-install-project", "--project", str(ROOT)],
        tmp_path,
        environment,
    )
    run(
        [
            "uv",
            "pip",
            "install",
            "--offline",
            "--no-deps",
            "--python",
            str(environment / "bin/python"),
            str(wheel),
        ],
        tmp_path,
    )
    run(["uv", "pip", "check", "--python", str(environment / "bin/python")], tmp_path)
    command = str(environment / "bin/anthropic-readiness")
    outside = tmp_path / "outside"
    outside.mkdir()
    imported = run(
        [
            str(environment / "bin/python"),
            "-c",
            "import anthropic_readiness; print(anthropic_readiness.__file__)",
        ],
        outside,
    )
    assert Path(imported.stdout.strip()).is_relative_to(environment)
    identity_result = run(
        [
            str(environment / "bin/python"),
            "-c",
            "import json; from anthropic_readiness.diagnostics.identity import installed_identity; "
            "print(json.dumps(installed_identity().document, sort_keys=True))",
        ],
        outside,
    )
    assert json.loads(identity_result.stdout) == expected_identity
    run([command, "--help"], outside)
    shown = run(
        [command, "contracts", "show", "anthropic-messages-2023-06-01-core", "--revision", "1.0.0"],
        outside,
    )
    assert json.loads(shown.stdout)["api_version"] == "2023-06-01"
    run([command, "validate", "--target", str(ROOT / "examples/target.yaml")], outside)
    captured = (
        ROOT
        / "tests/fixtures/captures/valid/evidence/ANT-TEXT-SSE-001/fixture-attempt/response.json"
    )
    output = outside / "replay"
    run(
        [
            command,
            "replay",
            "--target",
            str(ROOT / "examples/target.yaml"),
            "--capture",
            str(captured),
            "--case",
            "ANT-TEXT-SSE-001",
            "--out",
            str(output),
        ],
        outside,
    )
    assert (output / "report.html").exists()
    assert (output / "report.md").exists()
    rerendered = outside / "report"
    run(
        [command, "report", "--input", str(output / "result.json"), "--out", str(rerendered)],
        outside,
    )
    assert (rerendered / "report.html").exists()
