"""Fresh portable exports preserve exact source bytes and their independent proof."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZipFile

import pytest

from anthropic_readiness.diagnostics import packages
from anthropic_readiness.diagnostics.archive import ArchiveLimits, inspect_archive
from anthropic_readiness.diagnostics.packages import write_package
from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.models import object_value, strict_json
from tests.diagnostic_fixtures import portable_archive
from tests.export_fixtures import prepared_run

OWNER = "a" * 64


def files_under(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def imported(service: DiagnosticService, path: Path) -> str:
    now = datetime.now(UTC)
    preview = service.preview(path, OWNER, now=now)
    return str(service.commit(str(preview["preview_id"]), OWNER, now=now).document["id"])


def test_export_preserves_source_bytes_and_binds_recipe(tmp_path: Path) -> None:
    _, source = portable_archive(tmp_path / "source")
    before = files_under(source)
    service = DiagnosticService(tmp_path / "delivery")
    destination = tmp_path / "new.zip"
    exported = service.export(source, destination, include_evidence=True)
    assert files_under(source) == before
    assert exported["archive_sha256"] == hashlib.sha256(destination.read_bytes()).hexdigest()
    with ZipFile(destination) as package:
        assert package.read("result.json") == before["result.json"]
        assert package.read("assessment-context.json") == before["assessment-context.json"]
        assert (
            package.read("assessment-context-verification.json")
            == before["assessment-context-verification.json"]
        )
        for name, data in before.items():
            if name.startswith("evidence/"):
                assert package.read(name) == data
        assert "AGENT.md" in package.namelist()
        assert b"untrusted" in package.read("AGENT.md")
    baseline_id = imported(service, destination)
    assert object_value(service.get(baseline_id).document["eligibility"])["compare"] is True


def test_old_source_exports_as_legacy_not_verified(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    run_id = prepared_run(root)
    source = root / "runs" / run_id
    before = files_under(source)
    service = DiagnosticService(tmp_path / "delivery")
    destination = tmp_path / "legacy.zip"
    service.export(source, destination, include_evidence=True)
    with ZipFile(destination) as package:
        assert "diagnostic-package.json" not in package.namelist()
        assert package.read("result.json") == before["assessment/result.json"]
    assert files_under(source) == before
    baseline_id = imported(service, destination)
    assert object_value(service.get(baseline_id).document["eligibility"])["retest"] is False


@pytest.mark.parametrize(("partial", "evidence"), [(False, False), (True, True), (True, False)])
def test_evidence_omission_lowers_delivery(tmp_path: Path, partial: bool, evidence: bool) -> None:
    _, source = portable_archive(tmp_path / "source", partial=partial)
    before = files_under(source)
    service = DiagnosticService(tmp_path / "delivery")
    destination = tmp_path / "limited.zip"
    service.export(source, destination, include_evidence=evidence)
    baseline_id = imported(service, destination)
    baseline = service.get(baseline_id).document
    assert object_value(baseline["eligibility"])["compare"] is False
    assert files_under(source) == before
    with ZipFile(destination) as package:
        assert ("result.json" not in package.namelist()) is partial
        assert any(name.startswith("evidence/") for name in package.namelist()) is evidence
        marker = object_value(strict_json(package.read("diagnostic-package.json").decode()))
        assert marker["partial"] is partial


def test_source_url_is_disclosed_in_preview_without_upstream_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, source = portable_archive(tmp_path / "source")

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("export_must_not_send")

    monkeypatch.setattr("anthropic_readiness.transport.HttpTransport.send", forbidden)
    service = DiagnosticService(tmp_path / "delivery")
    preview = service.preview_export(source, include_evidence=False)
    disclosures = preview["disclosures"]
    assert isinstance(disclosures, list)
    assert "source_contains_target_context" in disclosures
    assert preview["include_evidence"] is False
    assert not (tmp_path / "never-written.zip").exists()


def test_package_export_import_limits_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    limits = replace(ArchiveLimits(), max_member_bytes=4, max_json_bytes=4, max_expanded_bytes=5)
    monkeypatch.setattr(packages, "ARCHIVE_LIMITS", limits)
    destination = tmp_path / "exact.zip"
    written = write_package({"a.bin": b"1234", "b.bin": b"x"}, destination)
    assert written == inspect_archive(destination, limits)
    too_large = tmp_path / "too-large.zip"
    with pytest.raises(ValueError, match="archive_member_limit"):
        write_package({"a.bin": b"12345"}, too_large)
    assert not too_large.exists()
    with pytest.raises(FileExistsError):
        write_package({"a.bin": b"1"}, destination)
    assert inspect_archive(destination, limits) == written


def test_reexport_never_reuses_uploaded_html(tmp_path: Path) -> None:
    archive, _ = portable_archive(tmp_path / "source")
    service = DiagnosticService(tmp_path / "delivery")
    baseline_id = imported(service, archive)
    baseline = service.get(baseline_id).document
    source = service.store.root / str(baseline["artifact_root"])
    destination = tmp_path / "fresh.zip"
    service.export(source, destination, include_evidence=True)
    with ZipFile(destination) as package:
        assert b'throw Error("uploaded")' not in package.read("report.html")
    assert (
        object_value(service.get(imported(service, destination)).document["eligibility"])["compare"]
        is True
    )


def test_reexport_partial_omitted_preserves_checkpoint_claims(tmp_path: Path) -> None:
    archive, _ = portable_archive(tmp_path / "source", partial=True, include_evidence=False)
    service = DiagnosticService(tmp_path / "delivery")
    baseline = service.get(imported(service, archive)).document
    source = service.store.root / str(baseline["artifact_root"])
    before = files_under(source)
    destination = tmp_path / "fresh.zip"
    service.export(source, destination, include_evidence=False)
    with ZipFile(destination) as package:
        for name, data in before.items():
            if name.startswith("operations/checkpoints/"):
                assert package.read(name) == data
    record = service.get(imported(service, destination)).document
    assert object_value(record["eligibility"])["compare"] is False
    assert files_under(source) == before


def test_export_keeps_noncanonical_legacy_result_bytes(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    run_id = prepared_run(root)
    source = root / "runs" / run_id / "assessment"
    path = source / "result.json"
    raw = json.dumps(json.loads(path.read_bytes()), separators=(",", ":")).encode()
    path.write_bytes(raw)
    service = DiagnosticService(tmp_path / "delivery")
    destination = tmp_path / "legacy.zip"
    service.export(source, destination, include_evidence=True)
    with ZipFile(destination) as package:
        assert package.read("result.json") == raw
    assert path.read_bytes() == raw
