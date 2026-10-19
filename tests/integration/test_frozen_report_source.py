"""Immutable imported snapshots are read without creating a live writer journal."""

from pathlib import Path
from zipfile import ZipFile

import pytest

from anthropic_readiness.models import object_value, strict_json
from anthropic_readiness.operations.checkpoints import (
    validate_checkpoint,
    validate_declared_checkpoint,
)
from anthropic_readiness.report_sources import load_report_source
from tests.diagnostic_fixtures import portable_archive


def test_frozen_source_creates_no_lock_or_journal(tmp_path: Path) -> None:
    archive, _ = portable_archive(tmp_path / "producer", partial=True)
    directory = tmp_path / "frozen"
    directory.mkdir()
    with ZipFile(archive) as package:
        # Trusted synthetic fixture only; production extraction is bounded separately.
        for name in package.namelist():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(package.read(name))
    before = {
        path.relative_to(directory): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }
    source = load_report_source(directory, frozen_operations=True)
    assert source.result is None
    assert len(source.case_records) == 1
    assert before == {
        path.relative_to(directory): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


def test_declared_checkpoint_reader_keeps_accounting_without_granting_proof(tmp_path: Path) -> None:
    _, source = portable_archive(tmp_path / "producer", partial=True)
    context = object_value(strict_json((source / "operations/execution.json").read_text()))
    path = next((source / "operations/checkpoints").glob("*.json"))
    checkpoint = object_value(strict_json(path.read_text()))
    missing = tmp_path / "no-captures"
    with pytest.raises(ValueError, match="checkpoint_evidence_invalid"):
        validate_checkpoint(checkpoint, context, missing)
    validate_declared_checkpoint(checkpoint, context)
    case = object_value(checkpoint["case_record"])
    case["status"] = "PASS" if case["status"] != "PASS" else "FAIL"
    checkpoint["case_record"] = case
    with pytest.raises(ValueError, match="checkpoint_case_status"):
        validate_declared_checkpoint(checkpoint, context)
