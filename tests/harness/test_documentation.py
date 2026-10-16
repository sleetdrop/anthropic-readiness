"""Documentation references and collaboration definitions are executable contracts."""

from pathlib import Path

from scripts.check_docs import broken_links, validate_collaboration

ROOT = Path(__file__).resolve().parents[2]


def test_missing_local_link_is_reported(tmp_path: Path) -> None:
    document = tmp_path / "README.md"
    document.write_text("[missing](docs/missing.md)\n[official](https://example.com)\n")
    assert broken_links(tmp_path, [document]) == ["README.md:docs/missing.md"]
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/missing.md").write_text("available")
    assert broken_links(tmp_path, [document]) == []


def test_collaboration_files_are_valid_and_use_no_publish_credentials() -> None:
    assert validate_collaboration(ROOT) == []
