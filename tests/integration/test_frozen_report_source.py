"""Immutable imported snapshots are read without creating a live writer journal."""

from pathlib import Path
from zipfile import ZipFile

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
