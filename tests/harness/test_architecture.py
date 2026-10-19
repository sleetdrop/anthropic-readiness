"""A reversed dependency must fail the actual architecture command."""

import shutil
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


@pytest.mark.parametrize(
    ("relative", "dependency", "contract"),
    [
        (
            "diagnostics/models.py",
            "diagnostics.core_contracts",
            "Diagnostic values stay independent",
        ),
        (
            "diagnostics/comparison.py",
            "diagnostics.service",
            "Diagnostic values stay independent",
        ),
        ("documents.py", "web", "Workbench composition stays independent of I/O adapters"),
        ("validation/messages.py", "presentation", "Pure domain, framing and validation"),
    ],
)
def test_real_pure_modules_reject_adapter_or_presentation_imports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative: str,
    dependency: str,
    contract: str,
) -> None:
    root = Path(__file__).resolve().parents[2]
    package = tmp_path / "src/anthropic_readiness"
    shutil.copytree(root / "src/anthropic_readiness", package)
    shutil.copy2(root / "pyproject.toml", tmp_path / "pyproject.toml")
    source = package / relative
    source.write_text(source.read_text() + f"\nimport anthropic_readiness.{dependency}\n")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "src"))
    output = tmp_path / "checks"
    gate = next(c for c in build_checks(tmp_path, output, "fast") if c.check_id == "architecture")
    assert run_checks([gate], output, root=tmp_path) == 1
    log = (output / "architecture.log").read_text()
    assert contract in log
    assert "BROKEN" in log
    assert f"anthropic_readiness.{dependency}" in log
