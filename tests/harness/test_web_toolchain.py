"""The prepared development toolchain is reproducible; Web stays optional."""

import json
import subprocess
import sys
from importlib.resources import files
from pathlib import Path

from scripts.check_package import verify_wheel_resources

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = (
    "plan",
    "job",
    "execution",
    "checkpoint",
    "progress-event",
    "report-view",
    "export-manifest",
    "web-api",
    "web-console-acceptance",
    "web-console-handoff",
)


def test_web_extra_is_optional() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import anthropic_readiness.cli; assert 'fastapi' not in sys.modules; assert 'uvicorn' not in sys.modules",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_every_operational_schema_is_a_packaged_resource() -> None:
    resources = files("anthropic_readiness").joinpath("resources/schemas")
    missing = [name for name in SCHEMAS if not resources.joinpath(name + ".schema.json").is_file()]
    assert missing == []


def test_prepared_node_matches_the_checked_toolchain() -> None:
    record_path = ROOT / "docs/harness/web-toolchain.json"
    assert record_path.is_file(), "prepared toolchain record is missing"
    record = json.loads(record_path.read_text())
    node = subprocess.run(["node", "--version"], capture_output=True, text=True, check=False)
    assert node.returncode == 0
    assert node.stdout.strip() == "v" + record["node_version"]
    assert record["node_version"].startswith("24.")
    assert set(record["archives"]) == {"arm64", "x64"}
    assert all(len(value["sha256"]) == 64 for value in record["archives"].values())


def test_wheel_inventory_rejects_a_missing_operational_schema(tmp_path: Path) -> None:
    import zipfile

    root = tmp_path / "source"
    resources = root / "src/anthropic_readiness/resources/schemas"
    resources.mkdir(parents=True)
    (resources / "job.schema.json").write_text("{}")
    wheel = tmp_path / "empty.whl"
    with zipfile.ZipFile(wheel, "w"):
        pass
    assert verify_wheel_resources(wheel, root) == [
        "missing_resource:anthropic_readiness/resources/schemas/job.schema.json"
    ]
