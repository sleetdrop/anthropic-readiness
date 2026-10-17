"""Exports preserve selected verified bytes and never discover unrelated files."""

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from anthropic_readiness import exports
from anthropic_readiness.exports import ExportPolicy, ExportService
from anthropic_readiness.models import object_value
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.report_sources import source_bytes
from tests.export_fixtures import prepared_run


def test_export_preserves_sources_and_manifest_hashes(tmp_path: Path) -> None:
    run_id = prepared_run(tmp_path)
    source = tmp_path / "runs" / run_id / "assessment"
    before = {
        path.relative_to(source): path.read_bytes() for path in source.rglob("*") if path.is_file()
    }
    service = ExportService(tmp_path)
    preview = service.preview(run_id, ExportPolicy(("zip",), True))
    assert "evidence/" in str(preview.get("files"))
    created = service.create(run_id, ExportPolicy(("zip",), True))
    assert created.get("run_id") == run_id
    archive = service.resolve(run_id, str(created["export_id"]))
    with ZipFile(archive) as package:
        manifest = object_value(json.loads(package.read("manifest.json")))
        validate_operational(manifest, "export-manifest")
        assert manifest["partial"] is False
        inventory = objects(manifest["files"])
        assert {item["path"] for item in inventory} == set(package.namelist()) - {"manifest.json"}
        for item in inventory:
            data = package.read(str(item["path"]))
            assert len(data) == item["bytes"]
            assert hashlib.sha256(data).hexdigest() == item["sha256"]
        for path, data in before.items():
            assert package.read(path.as_posix()) == data
        assert b'"status": "FAIL"' in package.read("result.json")
        assert "阅读 Agent" in package.read("README.md").decode()
    assert all((source / path).read_bytes() == data for path, data in before.items())
    another = service.create(run_id, ExportPolicy(("zip",), True))
    assert another["export_id"] != created["export_id"]
    assert service.resolve(run_id, str(created["export_id"])).read_bytes() == archive.read_bytes()


def test_report_only_and_partial_exports_disclose_omissions(tmp_path: Path) -> None:
    run_id = prepared_run(tmp_path / "complete")
    service = ExportService(tmp_path / "complete")
    created = service.create(run_id, ExportPolicy(("html", "json"), False))
    assert created.get("export_id")
    with ZipFile(service.resolve(run_id, str(created["export_id"]))) as package:
        assert not any(name.startswith("evidence/") for name in package.namelist())
        manifest = object_value(json.loads(package.read("manifest.json")))
        assert manifest["include_evidence"] is False
        assert manifest["omissions"]
        report = package.read("report.html").decode()
        assert "未附证据文件" in report
        assert "无法独立复核" in report
        assert "随附证据的路径、哈希与引用已核验" not in report
    partial_id = prepared_run(tmp_path / "partial", partial=True)
    partial = ExportService(tmp_path / "partial")
    created_partial = partial.create(partial_id, ExportPolicy(("zip",), True))
    assert created_partial.get("export_id")
    with ZipFile(partial.resolve(partial_id, str(created_partial["export_id"]))) as package:
        assert "result.json" not in package.namelist()
        assert "operations/execution.json" in package.namelist()
        assert (
            len([name for name in package.namelist() if name.startswith("operations/checkpoints/")])
            == 1
        )
        assert object_value(json.loads(package.read("manifest.json")))["partial"] is True
        assert object_value(json.loads(package.read("report-view.json")))["status"] == "partial"
        assert b'"status": "FAIL"' in package.read("operations/checkpoints/ANT-MESSAGE-001.json")


def test_export_rejects_changed_source_between_verification_and_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_id = prepared_run(tmp_path)
    original = source_bytes
    changed = [False]

    def replace_before_copy(root: Path, relative: str) -> bytes:
        if relative.endswith("body.bin") and not changed[0]:
            (root / relative).write_bytes(b"changed between verification and copy")
            changed[0] = True
        return original(root, relative)

    monkeypatch.setattr(exports, "source_bytes", replace_before_copy)
    with pytest.raises(ValueError, match="export_integrity"):
        ExportService(tmp_path).create(run_id, ExportPolicy(("zip",), True))
    assert changed[0]
    assert not list((tmp_path / "runs" / run_id / "exports").glob("*/record.json"))


def test_export_ignores_unrelated_files_and_secret_values(tmp_path: Path) -> None:
    run_id = prepared_run(tmp_path)
    root = tmp_path / "runs" / run_id
    secret = b"synthetic-private-unrelated-value"
    for name in (".env", "server.log", "assessment/unrelated.txt", "operations/private.txt"):
        (root / name).write_bytes(secret)
    service = ExportService(tmp_path)
    created = service.create(run_id, ExportPolicy(("zip",), True))
    assert created.get("export_id")
    with ZipFile(service.resolve(run_id, str(created["export_id"]))) as package:
        assert all(secret not in package.read(name) for name in package.namelist())
        assert all(
            "private" not in name and "server.log" not in name and ".env" not in name
            for name in package.namelist()
        )
    archive = service.resolve(run_id, str(created["export_id"]))
    archive.write_bytes(b"modified published artifact")
    with pytest.raises(ValueError, match="export_integrity"):
        service.resolve(run_id, str(created["export_id"]))


@pytest.mark.parametrize(
    "bad", ["../../outside", "unknown", "00000000-0000-0000-0000-000000000000"]
)
def test_export_lookup_is_scoped(tmp_path: Path, bad: str) -> None:
    run_id = prepared_run(tmp_path)
    with pytest.raises(ValueError, match=r"export_not_found|invalid_identifier"):
        ExportService(tmp_path).resolve(run_id, bad)


def test_preview_matches_published_selection_and_omissions(tmp_path: Path) -> None:
    run_id = prepared_run(tmp_path)
    service = ExportService(tmp_path)
    policy = ExportPolicy(("zip",), True)
    preview = service.preview(run_id, policy)
    created = service.create(run_id, policy)
    manifest = object_value(created["manifest"])
    assert preview["omissions"] == manifest["omissions"]
    assert preview["evidence_verification"] == manifest["evidence_verification"]
    names = preview["files"]
    assert isinstance(names, list)
    with ZipFile(service.resolve(run_id, str(created["export_id"]))) as package:
        assert {str(name) for name in names} == set(package.namelist())


def test_damaged_evidence_allows_only_qualified_report_delivery(tmp_path: Path) -> None:
    run_id = prepared_run(tmp_path)
    body = next((tmp_path / "runs" / run_id / "assessment/evidence").rglob("body.bin"))
    body.write_bytes(b"damaged fixture")
    service = ExportService(tmp_path)
    with pytest.raises(ValueError, match="export_evidence_invalid"):
        service.create(run_id, ExportPolicy(("zip",), True))
    created = service.create(run_id, ExportPolicy(("zip",), False))
    with ZipFile(service.resolve(run_id, str(created["export_id"]))) as package:
        manifest = object_value(json.loads(package.read("manifest.json")))
        assert object_value(manifest["evidence_verification"])["status"] == "missing_or_invalid"
        assert "来源证据未完整核验" in package.read("report.html").decode()
        assert 'class="comparison"' not in package.read("report.html").decode()


def test_selected_download_rejects_changed_bytes_and_unselected_format(tmp_path: Path) -> None:
    run_id = prepared_run(tmp_path)
    service = ExportService(tmp_path)
    created = service.create(run_id, ExportPolicy(("html",), False))
    export_id = str(created["export_id"])
    assert b"<html" in service.read(run_id, export_id, format="html")
    with pytest.raises(ValueError, match="export_format_unavailable"):
        service.read(run_id, export_id, format="markdown")
    path = tmp_path / "runs" / run_id / "exports" / export_id / "report.html"
    path.write_bytes(b"modified standalone report")
    with pytest.raises(ValueError, match="export_integrity"):
        service.read(run_id, export_id, format="html")


def test_failed_publication_never_becomes_downloadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from anthropic_readiness.evidence import atomic_write

    run_id = prepared_run(tmp_path)

    def fail_record(path: Path, data: bytes) -> None:
        if path.name == "record.json":
            raise OSError("synthetic publication failure")
        atomic_write(path, data)

    monkeypatch.setattr(exports, "atomic_write", fail_record)
    service = ExportService(tmp_path)
    with pytest.raises(OSError, match="synthetic publication failure"):
        service.create(run_id, ExportPolicy(("zip",), True))
    directory = next((tmp_path / "runs" / run_id / "exports").iterdir())
    assert (directory / "bundle.zip").exists()
    assert not (directory / "record.json").exists()
    with pytest.raises(ValueError, match="export_not_found"):
        service.resolve(run_id, directory.name)
