"""A reversed dependency must fail the actual architecture command."""

from pathlib import Path

import pytest

from scripts.check import build_checks, run_checks


def test_reversed_dependency_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package = tmp_path / "src/demo"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "core.py").write_text("import demo.io\n")
    (package / "io.py").write_text("")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.importlinter]\nroot_package = "demo"\n[[tool.importlinter.contracts]]\nname="core must stay pure"\ntype="forbidden"\nsource_modules=["demo.core"]\nforbidden_modules=["demo.io"]\n'
    )
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "src"))
    output = tmp_path / "check"
    gate = next(c for c in build_checks(tmp_path, output, "fast") if c.check_id == "architecture")
    assert run_checks([gate], output, root=tmp_path) == 1
    assert "BROKEN" in (output / "architecture.log").read_text()
