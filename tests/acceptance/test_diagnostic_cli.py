"""Standalone diagnosis commands keep stdout structured and network use explicit."""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZipFile

from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.models import JsonObject, object_value, strict_json
from tests.acceptance.test_cli import target_file
from tests.diagnostic_fixtures import portable_archive
from tests.http_server import SyntheticServer


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "anthropic_readiness", "diagnostics", *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def document(output: subprocess.CompletedProcess[str]) -> JsonObject:
    assert output.returncode == 0, output.stderr
    return object_value(strict_json(output.stdout))


def baseline(root: Path, archive: Path) -> str:
    service = DiagnosticService(root)
    now = datetime.now(UTC)
    preview = service.preview(archive, "a" * 64, now=now)
    return str(service.commit(str(preview["preview_id"]), "a" * 64, now=now).document["id"])


def files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_import_inspect_export_compare_commands_preserve_sources(tmp_path: Path) -> None:
    archive, source = portable_archive(tmp_path / "source")
    original = files(source)
    data_dir = tmp_path / "data"
    record = document(cli("import", "--package", str(archive), "--data-dir", str(data_dir)))
    inspected = document(
        cli("inspect", "--baseline", str(record["id"]), "--data-dir", str(data_dir))
    )
    assert inspected == record
    exported = tmp_path / "export.zip"
    manifest = document(
        cli(
            "export",
            "--input",
            str(source / "result.json"),
            "--out",
            str(exported),
            "--include-evidence",
        )
    )
    assert manifest["archive_sha256"]
    with ZipFile(exported) as package:
        assert package.read("result.json") == original["result.json"]
        assert "diagnostic-package.json" in package.namelist()
    comparison_path = tmp_path / "comparison.json"
    comparison = document(
        cli(
            "compare",
            "--baseline",
            str(record["id"]),
            "--data-dir",
            str(data_dir),
            "--input",
            str(source / "result.json"),
            "--out",
            str(comparison_path),
        )
    )
    assert comparison["comparable"] is True
    assert comparison == object_value(strict_json(comparison_path.read_text()))
    assert files(source) == original


def test_retest_requires_opt_in_and_dry_run_creates_only_a_preview(
    tmp_path: Path, server: SyntheticServer
) -> None:
    archive, _ = portable_archive(tmp_path / "source")
    data_dir = tmp_path / "data"
    baseline_id = baseline(data_dir, archive)
    target = target_file(tmp_path, server.url + "/cases")
    output = tmp_path / "preview"
    args = (
        "retest",
        "--baseline",
        baseline_id,
        "--data-dir",
        str(data_dir),
        "--target",
        str(target),
        "--out",
        str(output),
    )
    rejected = cli(*args)
    assert rejected.returncode == 2
    assert "live_opt_in_required" in rejected.stderr
    assert not output.exists()
    preview = document(cli(*args, "--dry-run"))
    assert preview["kind"] == "retest_preview"
    assert object_value(preview["plan"])["planned_requests"] == 4
    assert {path.name for path in output.iterdir()} == {"retest-preview.json"}
    assert not server.requests


def test_live_retest_runs_all_four_cases_and_retains_lineage(
    tmp_path: Path, server: SyntheticServer
) -> None:
    archive, _ = portable_archive(tmp_path / "source")
    data_dir = tmp_path / "data"
    baseline_id = baseline(data_dir, archive)
    original = files(data_dir / "diagnostics/baselines" / baseline_id)
    target = target_file(tmp_path, server.url + "/cases")
    output = tmp_path / "retest"
    result = cli(
        "retest",
        "--baseline",
        baseline_id,
        "--data-dir",
        str(data_dir),
        "--target",
        str(target),
        "--out",
        str(output),
        "--allow-live",
    )
    # The shared synthetic peer does not implement tool responses; retain FAIL.
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)["actual_requests"] == len(server.requests) == 4
    source = object_value(strict_json((output / "result.json").read_text()))
    cases = source["cases"]
    assert isinstance(cases, list)
    assert len(cases) == 4
    context = object_value(strict_json((output / "assessment-context.json").read_text()))
    assert object_value(context["baseline"])["baseline_id"] == baseline_id
    assert "messages_url" in str(context["declared_changes"])
    assert (output / "assessment-context-verification.json").exists()
    assert all(
        (output / name).exists() for name in ("report.html", "report.md", "report-view.json")
    )
    assert files(data_dir / "diagnostics/baselines" / baseline_id) == original


def test_legacy_baseline_explains_manual_current_test(tmp_path: Path) -> None:
    archive, _ = portable_archive(tmp_path / "source", legacy=True)
    data_dir = tmp_path / "data"
    baseline_id = baseline(data_dir, archive)
    target = target_file(tmp_path)
    output = tmp_path / "retest"
    rejected = cli(
        "retest",
        "--baseline",
        baseline_id,
        "--data-dir",
        str(data_dir),
        "--target",
        str(target),
        "--out",
        str(output),
        "--dry-run",
    )
    assert rejected.returncode == 2
    assert "current test" in rejected.stderr
    assert not output.exists()


def test_incomparable_is_explicit_json_and_successful_representation(tmp_path: Path) -> None:
    archive, _ = portable_archive(tmp_path / "source", partial=True, include_evidence=False)
    _, after = portable_archive(tmp_path / "after")
    data_dir = tmp_path / "data"
    baseline_id = baseline(data_dir, archive)
    value = document(
        cli(
            "compare",
            "--baseline",
            baseline_id,
            "--data-dir",
            str(data_dir),
            "--input",
            str(after / "result.json"),
            "--out",
            str(tmp_path / "comparison.json"),
        )
    )
    assert value["comparable"] is False
    assert value["all_previous_failures_passed"] is False
    assert object_value(value["coverage"])["missing_required_cases"] == 3


def test_normal_run_creates_portable_context(tmp_path: Path, server: SyntheticServer) -> None:
    target = target_file(tmp_path, server.url + "/cases")
    output = tmp_path / "run"
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "anthropic_readiness",
            "run",
            "--target",
            str(target),
            "--out",
            str(output),
            "--allow-live",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert run.returncode == 0, run.stderr
    assert (output / "assessment-context.json").exists()
    assert (output / "assessment-context-verification.json").exists()
