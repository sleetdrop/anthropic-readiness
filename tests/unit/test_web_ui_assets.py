"""UI identity tracks packaged interface content, never local run data."""

from pathlib import Path

import pytest

from anthropic_readiness.web import ui_assets


def test_ui_identity_changes_with_resource_bytes_not_directory_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resources = tmp_path / "resources"
    (resources / "web").mkdir(parents=True)
    (resources / "locales").mkdir()
    (resources / "themes.css").write_text("body{}")
    style = resources / "web" / "console.css"
    style.write_text("th{padding:12px}")
    catalog = resources / "locales" / "en.json"
    catalog.write_text('{"reload":"Refresh"}')
    monkeypatch.setattr(ui_assets, "files", lambda package: tmp_path)
    first = ui_assets.load_ui_assets()
    assert first == ui_assets.load_ui_assets()
    assert first.url("web/console.css").endswith(first.versions["web/console.css"])
    (resources / "web" / ".DS_Store").write_bytes(b"ignored operating system metadata")
    assert first == ui_assets.load_ui_assets()
    catalog.write_text('{"reload":"Reload"}')
    translated = ui_assets.load_ui_assets()
    assert translated.revision != first.revision
    assert translated.url("web/console.css") == first.url("web/console.css")
    style.write_text("th{padding:14px}")
    changed = ui_assets.load_ui_assets()
    assert changed.revision != translated.revision
    assert changed.url("web/console.css") != first.url("web/console.css")
