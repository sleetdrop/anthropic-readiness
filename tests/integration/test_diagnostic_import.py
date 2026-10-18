"""Untrusted delivery imports preserve source bytes, isolation and limited eligibility."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from anthropic_readiness.diagnostics import identity
from anthropic_readiness.diagnostics import store as store_module
from anthropic_readiness.diagnostics.archive import ArchiveLimits
from anthropic_readiness.diagnostics.importing import validate_import
from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.diagnostics.store import DiagnosticStore
from anthropic_readiness.evidence import json_bytes
from anthropic_readiness.models import JsonObject, object_value, strict_json
from anthropic_readiness.report_models import ReportSource
from tests.diagnostic_fixtures import portable_archive, rewrite_archive

NOW = datetime(2026, 11, 1, tzinfo=UTC)
ALICE = "a" * 64
BOB = "b" * 64


def activate(store: DiagnosticStore, archive: Path) -> str:
    preview = store.preview(archive, ALICE, now=NOW)
    return str(store.commit(str(preview["preview_id"]), ALICE, now=NOW).document["id"])


@pytest.mark.parametrize(
    ("variant", "expected"),
    [
        ("complete", True),
        ("legacy", False),
        ("partial", False),
        ("omitted", False),
    ],
)
def test_complete_legacy_partial_and_omitted_eligibility(
    tmp_path: Path, variant: str, expected: bool
) -> None:
    archive, _ = portable_archive(
        tmp_path / "producer",
        legacy=variant == "legacy",
        partial=variant == "partial",
        include_evidence=variant != "omitted",
    )
    store = DiagnosticStore(tmp_path / "diagnostics")
    preview = store.preview(archive, ALICE, now=NOW)
    assert object_value(preview["eligibility"])["read"] is True
    assert object_value(preview["eligibility"])["retest"] is expected
    baseline = store.commit(str(preview["preview_id"]), ALICE, now=NOW).document
    assert baseline["imported_at"] == NOW.isoformat()
    assert object_value(baseline["eligibility"])["compare"] is expected
    source = store.load_source(str(baseline["id"]))
    assert (source.result is None) is (variant == "partial")
    assert source.result is None or source.result.finished_at != baseline["imported_at"]
    assert not (tmp_path / "diagnostics/jobs.sqlite3").exists()
    assert not (tmp_path / "diagnostics/runs").exists()
    original = archive.read_bytes()
    assert store.get(str(baseline["id"])).document["source"] == baseline["source"]
    assert archive.read_bytes() == original


def test_duplicate_archive_deduplicates_and_survives_index_rebuild(tmp_path: Path) -> None:
    archive, _ = portable_archive(tmp_path / "producer")
    root = tmp_path / "diagnostics"
    store = DiagnosticStore(root)
    first = activate(store, archive)
    preview = store.preview(archive, BOB, now=NOW)
    assert object_value(preview["relationship"])["kind"] == "identical"
    second = store.commit(str(preview["preview_id"]), BOB, now=NOW).document
    assert second["id"] == first
    assert len(list((root / "baselines").iterdir())) == 1
    (root / "index.sqlite3").unlink()
    assert DiagnosticStore(root).get(first).document == second


def test_external_id_collision_stays_separate(tmp_path: Path) -> None:
    run_id = "11111111-1111-4111-8111-111111111111"
    first, _ = portable_archive(tmp_path / "first", run_id=run_id)
    other, _ = portable_archive(tmp_path / "other", run_id=run_id)
    store = DiagnosticStore(tmp_path / "diagnostics")
    baseline_id = activate(store, first)
    preview = store.preview(other, ALICE, now=NOW)
    assert object_value(preview["relationship"])["kind"] == "conflict"
    assert object_value(preview["relationship"])["baseline_ids"] == [baseline_id]
    second_id = str(store.commit(str(preview["preview_id"]), ALICE, now=NOW).document["id"])
    assert second_id != baseline_id
    assert store.get(baseline_id).document["source"] != store.get(second_id).document["source"]


def test_localized_exports_are_variants_not_conflicts(tmp_path: Path) -> None:
    first, source = portable_archive(tmp_path / "zh", locale="zh-CN")
    english, _ = portable_archive(tmp_path / "en", source_dir=source, locale="en")
    store = DiagnosticStore(tmp_path / "diagnostics")
    baseline_id = activate(store, first)
    preview = store.preview(english, ALICE, now=NOW)
    assert object_value(preview["relationship"]) == {
        "kind": "variant",
        "baseline_ids": [baseline_id],
    }
    second = store.commit(str(preview["preview_id"]), ALICE, now=NOW).document
    assert second["id"] != baseline_id
    assert second["source"] == store.get(baseline_id).document["source"]


def test_variant_evidence_is_not_merged(tmp_path: Path) -> None:
    first, source = portable_archive(tmp_path / "full")
    omitted, _ = portable_archive(tmp_path / "omitted", source_dir=source, include_evidence=False)
    store = DiagnosticStore(tmp_path / "diagnostics")
    full_id = activate(store, first)
    limited_id = activate(store, omitted)
    assert object_value(store.get(full_id).document["eligibility"])["compare"] is True
    assert object_value(store.get(limited_id).document["eligibility"])["compare"] is False
    assert store.load_source(limited_id).evidence_verification["status"] != "verified"


def test_activation_crash_is_not_visible(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    archive, _ = portable_archive(tmp_path / "producer")
    root = tmp_path / "diagnostics"
    store = DiagnosticStore(root)
    preview = store.preview(archive, ALICE, now=NOW)

    def crash(*args: object, **kwargs: object) -> None:
        raise OSError("synthetic_activation_crash")

    monkeypatch.setattr(store, "_publish_commit", crash)
    with pytest.raises(OSError, match="synthetic_activation_crash"):
        store.commit(str(preview["preview_id"]), ALICE, now=NOW)
    assert not list((root / "baselines").glob("*/committed.json"))
    (root / "index.sqlite3").unlink()
    restarted = DiagnosticStore(root)
    new_preview = restarted.preview(archive, ALICE, now=NOW)
    assert object_value(new_preview["relationship"])["kind"] == "new"


@pytest.mark.parametrize("target", ["source/result.json", "archive.zip"])
def test_changed_import_bytes_revoke_eligibility(tmp_path: Path, target: str) -> None:
    archive, _ = portable_archive(tmp_path / "producer")
    root = tmp_path / "diagnostics"
    store = DiagnosticStore(root)
    baseline_id = activate(store, archive)
    path = root / "baselines" / baseline_id / target
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="diagnostic_baseline_integrity"):
        store.get(baseline_id)
    with pytest.raises(ValueError, match="diagnostic_baseline_integrity"):
        store.load_source(baseline_id)


def test_previews_are_owned_expire_and_have_a_local_cap(tmp_path: Path) -> None:
    archive, _ = portable_archive(tmp_path / "producer")
    root = tmp_path / "diagnostics"
    store = DiagnosticStore(root)
    alice = store.preview(archive, ALICE, now=NOW)
    bob = store.preview(archive, BOB, now=NOW + timedelta(minutes=14))
    with pytest.raises(ValueError, match="diagnostic_preview_owner"):
        store.commit(str(alice["preview_id"]), BOB, now=NOW)
    with pytest.raises(ValueError, match="diagnostic_preview_limit"):
        store.preview(archive, ALICE, now=NOW + timedelta(minutes=14))
    later = NOW + timedelta(minutes=16)
    with pytest.raises(ValueError, match="diagnostic_preview_expired"):
        store.commit(str(alice["preview_id"]), ALICE, now=later)
    fresh = store.preview(archive, ALICE, now=later)
    assert (root / "previews" / str(bob["preview_id"])).is_dir()
    baseline = store.commit(str(fresh["preview_id"]), ALICE, now=later)
    store.preview(archive, ALICE, now=NOW + timedelta(days=1))
    assert store.get(str(baseline.document["id"])).document["id"] == baseline.document["id"]


def test_import_and_read_use_only_data_no_sockets_or_uploaded_html(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, _ = portable_archive(tmp_path / "producer", partial=True)

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("import_must_not_connect")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    service = DiagnosticService(tmp_path / "application-data")
    preview = service.preview(archive, ALICE, now=NOW)
    baseline = service.commit(str(preview["preview_id"]), ALICE, now=NOW)
    source_dir = tmp_path / "application-data/diagnostics" / str(baseline.document["artifact_root"])
    before = {
        path.relative_to(source_dir): path.read_bytes()
        for path in source_dir.rglob("*")
        if path.is_file()
    }
    assert not any(path.name == "writer.lock" for path in before)
    source = service.load_source(str(baseline.document["id"]))
    assert source.result is None
    assert before == {
        path.relative_to(source_dir): path.read_bytes()
        for path in source_dir.rglob("*")
        if path.is_file()
    }
    assert "uploaded" not in str(preview)
    disclosures = preview["disclosures"]
    assert isinstance(disclosures, list)
    assert "source_contains_target_context" in disclosures


def test_archive_is_copied_and_not_reused_from_an_external_path(tmp_path: Path) -> None:
    archive, _ = portable_archive(tmp_path / "producer")
    store = DiagnosticStore(tmp_path / "diagnostics")
    preview = store.preview(archive, ALICE, now=NOW)
    archive.unlink()
    baseline = store.commit(str(preview["preview_id"]), ALICE, now=NOW)
    assert store.get(str(baseline.document["id"])).document == baseline.document


def test_uncommitted_orphan_is_not_rebuilt_as_a_baseline(tmp_path: Path) -> None:
    root = tmp_path / "diagnostics"
    DiagnosticStore(root)
    orphan = root / "baselines/11111111-1111-4111-8111-111111111111"
    orphan.mkdir()
    (orphan / "baseline.json").write_text("{}")
    (root / "index.sqlite3").unlink()
    restarted = DiagnosticStore(root)
    with pytest.raises(ValueError, match="diagnostic_baseline_not_found"):
        restarted.get(orphan.name)
    assert orphan.is_dir()


@pytest.mark.parametrize(
    ("relative", "field", "replacement", "code"),
    [
        (
            "manifest.json",
            "run_id",
            "22222222-2222-4222-8222-222222222222",
            "diagnostic_source_mismatch",
        ),
        ("manifest.json", "include_evidence", False, "diagnostic_evidence_delivery_mismatch"),
        (
            "assessment-context-verification.json",
            "result_sha256",
            "0" * 64,
            "diagnostic_context_mismatch",
        ),
        (
            "assessment-context.json",
            "run_id",
            "22222222-2222-4222-8222-222222222222",
            "diagnostic_context_mismatch",
        ),
    ],
)
def test_cross_document_conflicts_are_rejected(
    tmp_path: Path, relative: str, field: str, replacement: str | bool, code: str
) -> None:
    archive, _ = portable_archive(tmp_path / "producer")

    def mutation(data: dict[str, bytes]) -> None:
        document = object_value(strict_json(data[relative].decode()))
        document[field] = replacement
        data[relative] = json_bytes(document)

    rewrite_archive(archive, mutation)
    store = DiagnosticStore(tmp_path / "diagnostics")
    with pytest.raises(ValueError, match=code):
        store.preview(archive, ALICE, now=NOW)
    assert not list((tmp_path / "diagnostics/baselines").iterdir())


def test_conflicting_optional_execution_snapshot_cannot_gain_verification(tmp_path: Path) -> None:
    archive, source = portable_archive(tmp_path / "producer")
    from anthropic_readiness.report_sources import load_report_source

    loaded = load_report_source(source)
    assert loaded.execution is not None
    wrong = {**loaded.execution, "run_id": "22222222-2222-4222-8222-222222222222"}
    rewrite_archive(
        archive, lambda data: data.update({"operations/execution.json": json_bytes(wrong)})
    )
    with pytest.raises(ValueError, match="diagnostic_source_mismatch"):
        DiagnosticStore(tmp_path / "diagnostics").preview(archive, ALICE, now=NOW)


def test_local_identity_change_revokes_operations_without_modifying_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, _ = portable_archive(tmp_path / "producer")
    store = DiagnosticStore(tmp_path / "diagnostics")
    baseline_id = activate(store, archive)
    record_path = store.root / "baselines" / baseline_id / "baseline.json"
    before = record_path.read_bytes()
    copied = tmp_path / "installed"
    shutil.copytree(identity._package_root(), copied, ignore=shutil.ignore_patterns("__pycache__"))
    file = copied / "validation/messages.py"
    file.write_text(file.read_text() + "\n# Synthetic changed validator.\n")
    monkeypatch.setattr(identity, "_package_root", lambda: copied)
    record = store.get(baseline_id).document
    eligibility = object_value(record["eligibility"])
    assert eligibility["read"] is True
    assert eligibility["retest"] is False
    assert eligibility["compare"] is False
    reasons = eligibility["reasons"]
    assert isinstance(reasons, list)
    assert "implementation_files_changed" in reasons
    assert record_path.read_bytes() == before


def test_nonregular_archive_input_cannot_block_preparation(tmp_path: Path) -> None:
    fifo = tmp_path / "not-an-archive"
    os.mkfifo(fifo)
    code = """
import sys
from datetime import UTC, datetime
from pathlib import Path
from anthropic_readiness.diagnostics.store import DiagnosticStore
try:
    DiagnosticStore(Path(sys.argv[1])).preview(Path(sys.argv[2]), 'local', now=datetime.now(UTC))
except ValueError as exc:
    assert str(exc) == 'archive_member_type'
    print('rejected')
else:
    raise AssertionError('nonregular_input_accepted')
"""
    process = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path / "diagnostics"), str(fifo)],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert process.returncode == 0
    assert process.stdout.strip() == "rejected"


def test_deadline_expiring_during_validation_cannot_publish_preview(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, _ = portable_archive(tmp_path / "producer")
    store = DiagnosticStore(tmp_path / "diagnostics")
    validated = False
    real_validate = validate_import
    real_remaining = store._remaining

    def slow_validation(
        root: Path, inventory: JsonObject, *, deadline: float
    ) -> tuple[ReportSource, JsonObject]:
        nonlocal validated
        result = real_validate(root, inventory, deadline=deadline)
        validated = True
        return result

    def remaining(deadline: float) -> ArchiveLimits:
        if validated:
            raise ValueError("archive_timeout")
        return real_remaining(deadline)

    monkeypatch.setattr(store_module, "validate_import", slow_validation)
    monkeypatch.setattr(store, "_remaining", remaining)
    with pytest.raises(ValueError, match="archive_timeout"):
        store.preview(archive, ALICE, now=NOW)
    assert not list((store.root / "previews").iterdir())
