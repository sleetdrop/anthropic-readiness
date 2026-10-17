"""Installed minimal CLI and Web extras work away from the source checkout."""

import json
import socket
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

from scripts.check_package import verify_wheel_resources
from tests.acceptance.test_installed_package import run

ROOT = Path(__file__).resolve().parents[2]


def install(tmp_path: Path, *, web: bool) -> tuple[Path, Path, Path]:
    dist = tmp_path / "dist"
    run(["uv", "build", "--offline", "--no-build-isolation", "--out-dir", str(dist)], ROOT)
    wheel = next(dist.glob("*.whl"))
    environment = tmp_path / "venv"
    run(
        [
            "uv",
            "sync",
            "--locked",
            "--no-dev",
            "--no-install-project",
            "--project",
            str(ROOT),
            *(["--extra", "web"] if web else []),
        ],
        tmp_path,
        environment,
    )
    python = environment / "bin/python"
    run(
        ["uv", "pip", "install", "--offline", "--no-deps", "--python", str(python), str(wheel)],
        tmp_path,
    )
    run(["uv", "pip", "check", "--python", str(python)], tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    return python, outside, wheel


def test_cli_install_works_without_web_extra(tmp_path: Path) -> None:
    python, outside, _ = install(tmp_path, web=False)
    run(
        [
            str(python),
            "-c",
            "import importlib.util; import anthropic_readiness.cli; assert importlib.util.find_spec('fastapi') is None; assert importlib.util.find_spec('uvicorn') is None",
        ],
        outside,
    )
    command = str(python.parent / "anthropic-readiness")
    run([command, "contracts", "list"], outside)
    result = subprocess.run(
        [command, "serve", "--data-dir", str(outside / "data")],
        cwd=outside,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 2
    assert "anthropic-readiness[web]" in result.stderr
    assert not (outside / "data").exists()


def test_web_install_contains_templates_schemas_and_assets(tmp_path: Path) -> None:
    python, outside, wheel = install(tmp_path, web=True)
    assert verify_wheel_resources(wheel, ROOT) == []
    imported = run(
        [str(python), "-c", "import anthropic_readiness; print(anthropic_readiness.__file__)"],
        outside,
    )
    assert Path(imported.stdout.strip()).is_relative_to(python.parent.parent)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    with (outside / "server.log").open("wb") as log:
        process = subprocess.Popen(
            [
                str(python.parent / "anthropic-readiness"),
                "serve",
                "--data-dir",
                str(outside / "data"),
                "--port",
                str(port),
            ],
            cwd=outside,
            stdout=log,
            stderr=log,
        )
        try:
            url = f"http://127.0.0.1:{port}"
            deadline = time.monotonic() + 10
            while True:
                try:
                    with urllib.request.urlopen(url + "/health", timeout=1) as response:
                        assert json.load(response)["status"] == "ok"
                    break
                except OSError:
                    if process.poll() is not None or time.monotonic() > deadline:
                        raise AssertionError("installed_web_start_failed") from None
                    time.sleep(0.02)
            with urllib.request.urlopen(url + "/new", timeout=2) as response:
                page = response.read().decode()
            assert page.count("data-case-id=") == 4
            for asset in ("web/app.js", "web/app.css", "report-v2.js", "report-v2.css"):
                with urllib.request.urlopen(url + "/assets/" + asset, timeout=2) as response:
                    assert len(response.read()) > 100
        finally:
            process.terminate()
            process.wait(timeout=12)
    assert process.returncode in (0, -15)


def test_missing_web_asset_fails_wheel_inventory(tmp_path: Path) -> None:
    resources = tmp_path / "source/src/anthropic_readiness/resources/web"
    resources.mkdir(parents=True)
    (resources / "app.js").write_text("export {};")
    wheel = tmp_path / "missing.whl"
    with zipfile.ZipFile(wheel, "w"):
        pass
    assert verify_wheel_resources(wheel, tmp_path / "source") == [
        "missing_resource:anthropic_readiness/resources/web/app.js"
    ]
