"""Inject defects into disposable inputs and exercise production gate entry points."""

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from scripts.check import build_checks, run_checks
from scripts.check_package import verify_wheel_resources
from scripts.ci_required import required_jobs_pass
from scripts.validate_resources import validate_resources

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("gate_id", ["lint", "type"])
def test_static_violation_fails_designated_gate(tmp_path: Path, gate_id: str) -> None:
    for directory in ("src", "tests", "scripts"):
        (tmp_path / directory).mkdir()
    source = (
        "print(undefined_name)\n" if gate_id == "lint" else "def value() -> str:\n    return 1\n"
    )
    (tmp_path / "src/example.py").write_text(source)
    (tmp_path / "pyproject.toml").write_text('[tool.mypy]\nstrict=true\nfiles=["src"]\n')
    output = tmp_path / "check"
    gate = next(c for c in build_checks(tmp_path, output, "fast") if c.check_id == gate_id)
    assert run_checks([gate], output, root=tmp_path) == 1
    log = (output / f"{gate_id}.log").read_text()
    assert ("F821" if gate_id == "lint" else "return-value") in log


def test_invalid_schema_fails_schema_gate(tmp_path: Path) -> None:
    resource = tmp_path / "src/anthropic_readiness/resources/schemas"
    resource.mkdir(parents=True)
    (resource / "broken.schema.json").write_text('{"type":42}')
    errors = validate_resources(tmp_path)
    assert any("schema_invalid:broken.schema.json" in error for error in errors)


def test_missing_wheel_resource_is_rejected(tmp_path: Path) -> None:
    wheel = tmp_path / "synthetic.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("anthropic_readiness/__init__.py", "")
    assert any("missing_resource" in error for error in verify_wheel_resources(wheel, ROOT))


def test_required_job_missing_skipped_or_cancelled_never_passes() -> None:
    assert required_jobs_pass({"unit": {"result": "success"}}, ["unit"])
    for result in ("failure", "cancelled", "skipped"):
        assert not required_jobs_pass({"unit": {"result": result}}, ["unit"])
    assert not required_jobs_pass({}, ["unit"])
    assert not required_jobs_pass({}, [])


def test_all_skipped_or_failed_junit_is_not_green(tmp_path: Path) -> None:
    for name, attributes in [
        ("skipped", 'tests="2" skipped="2"'),
        ("failed", 'tests="1" failures="1"'),
    ]:
        junit = tmp_path / f"{name}.xml"
        junit.write_text(f"<testsuites><testsuite {attributes}/></testsuites>")
        config = tmp_path / f"{name}.json"
        import json

        config.write_text(
            json.dumps(
                [
                    {
                        "check_id": name,
                        "argv": [sys.executable, "-c", "pass"],
                        "timeout_s": 1,
                        "check_kind": "pytest",
                        "junit_path": str(junit),
                    }
                ]
            )
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/check.py"),
                "--checks",
                str(config),
                "--out",
                str(tmp_path / name),
            ],
            capture_output=True,
            check=False,
        )
        assert completed.returncode != 0


def test_resource_inventory_ignores_only_finder_metadata(tmp_path: Path) -> None:
    resources = tmp_path / "src/anthropic_readiness/resources"
    resources.mkdir(parents=True)
    (resources / ".DS_Store").write_bytes(b"finder metadata")
    (resources / ".required.json").write_text("{}")
    wheel = tmp_path / "resources.whl"
    with zipfile.ZipFile(wheel, "w"):
        pass
    assert verify_wheel_resources(wheel, tmp_path) == [
        "missing_resource:anthropic_readiness/resources/.required.json"
    ]
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("anthropic_readiness/resources/.required.json", "[]")
    assert verify_wheel_resources(wheel, tmp_path) == [
        "resource_content_mismatch:anthropic_readiness/resources/.required.json"
    ]


def test_source_identity_ignores_finder_metadata_but_tracks_resources(tmp_path: Path) -> None:
    from scripts.check import source_fingerprint

    resources = tmp_path / "src/anthropic_readiness/resources"
    resources.mkdir(parents=True)
    resource = resources / "required.json"
    resource.write_text("{}")
    before = source_fingerprint(tmp_path)
    (resources / ".DS_Store").write_bytes(b"finder metadata")
    assert source_fingerprint(tmp_path) == before
    resource.write_text("[]")
    assert source_fingerprint(tmp_path) != before
