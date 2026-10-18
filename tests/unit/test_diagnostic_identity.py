"""Execution identity follows actual code/resources/dependencies, not release labels."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from importlib.metadata import PackageNotFoundError
from pathlib import Path

import pytest

from anthropic_readiness.diagnostics import identity
from anthropic_readiness.diagnostics.identity import check_identity, installed_identity
from anthropic_readiness.models import object_value, strict_json


@pytest.fixture
def installed_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "anthropic_readiness"
    shutil.copytree(identity._package_root(), root, ignore=shutil.ignore_patterns("__pycache__"))
    monkeypatch.setattr(identity, "_package_root", lambda: root)
    return root


def test_same_label_changed_bytes_rejects(installed_copy: Path) -> None:
    before = installed_identity()
    source = installed_copy / "validation/messages.py"
    source.write_text(source.read_text() + "\n# Synthetic identity mutation.\n")
    after = installed_identity()
    assert before.document["semantic_revision"] == after.document["semantic_revision"]
    assert "implementation_files_changed" in check_identity(before, after)
    assert before.document["content_sha256"] != after.document["content_sha256"]
    assert str(installed_copy) not in json.dumps(after.document)


def test_missing_transitive_dependency_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    real = identity._distribution_info

    def missing(name: str) -> identity.DistributionInfo:
        if name == "anyio":
            raise PackageNotFoundError(name)
        return real(name)

    monkeypatch.setattr(identity, "_distribution_info", missing)
    with pytest.raises(ValueError, match="identity_missing_distribution:anyio"):
        installed_identity()


def test_changed_dependency_version_changes_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    before = installed_identity()
    real = identity._distribution_info

    def changed(name: str) -> identity.DistributionInfo:
        info = real(name)
        return replace(info, version="0.28.2") if name == "httpx" else info

    monkeypatch.setattr(identity, "_distribution_info", changed)
    after = installed_identity()
    assert "dependency_versions_changed" in check_identity(before, after)


def test_unused_extra_is_not_required(monkeypatch: pytest.MonkeyPatch) -> None:
    before = installed_identity()
    real = identity._distribution_info

    def optional(name: str) -> identity.DistributionInfo:
        info = real(name)
        return (
            replace(
                info,
                requirements=(*info.requirements, "missing-diagnostic-extra; extra == 'unused'"),
            )
            if name == "httpx"
            else info
        )

    monkeypatch.setattr(identity, "_distribution_info", optional)
    assert installed_identity().document == before.document


def test_selected_transitive_extra_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    real = identity._distribution_info

    def selected(name: str) -> identity.DistributionInfo:
        info = real(name)
        if name == "httpx":
            return replace(info, requirements=(*info.requirements, "anyio[diagnostic-extra]"))
        if name == "anyio":
            return replace(
                info,
                requirements=(
                    *info.requirements,
                    "missing-diagnostic-extra; extra == 'diagnostic-extra'",
                ),
            )
        return info

    monkeypatch.setattr(identity, "_distribution_info", selected)
    with pytest.raises(ValueError, match="identity_missing_distribution:missing-diagnostic-extra"):
        installed_identity()


def test_presentation_only_project_dependency_is_not_part_of_core_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = installed_identity()
    real = identity._distribution_info

    def presentation_dependency(name: str) -> identity.DistributionInfo:
        info = real(name)
        return (
            replace(info, requirements=(*info.requirements, "missing-presentation-only-dependency"))
            if name == "anthropic-readiness"
            else info
        )

    monkeypatch.setattr(identity, "_distribution_info", presentation_dependency)
    assert installed_identity().document == before.document


@pytest.mark.parametrize(
    "relative",
    ["report_view.py", "resources/report-v2.css", "resources/schemas/report-view.schema.json"],
)
def test_report_only_change_preserves_identity(installed_copy: Path, relative: str) -> None:
    before = installed_identity()
    path = installed_copy / relative
    path.write_text(path.read_text() + "\n ")
    assert check_identity(before, installed_identity()) == ()


@pytest.mark.parametrize("relative", ["resources/locales/en.json", "resources/themes.css"])
def test_catalog_theme_changes_preserve_identity(installed_copy: Path, relative: str) -> None:
    before = installed_identity()
    path = installed_copy / relative
    path.write_text(path.read_text() + "\n ")
    assert installed_identity().document == before.document


def test_rule_resource_changes_alter_identity(installed_copy: Path) -> None:
    before = installed_identity()
    path = next((installed_copy / "resources/contracts").rglob("manifest.json"))
    path.write_text(path.read_text() + "\n ")
    assert "implementation_files_changed" in check_identity(before, installed_identity())


def test_new_reachable_module_requires_manifest_entry(installed_copy: Path) -> None:
    added = installed_copy / "identity_extra.py"
    added.write_text('VALUE = "synthetic"\n')
    root = installed_copy / "validation/messages.py"
    root.write_text(root.read_text() + "\nimport anthropic_readiness.identity_extra\n")
    with pytest.raises(ValueError, match=r"identity_unlisted_module:identity_extra\.py"):
        installed_identity()


def test_new_resource_requires_manifest_entry(installed_copy: Path) -> None:
    source = installed_copy / "validation/messages.py"
    source.write_text(
        source.read_text()
        + "\nfrom importlib.resources import files\n"
        + 'EXTRA = files("anthropic_readiness").joinpath("resources/new-rule.json")\n'
    )
    (installed_copy / "resources/new-rule.json").write_text("{}")
    with pytest.raises(ValueError, match=r"identity_unlisted_resource:resources/new-rule\.json"):
        installed_identity()


def test_undeclared_dynamic_local_import_blocks(installed_copy: Path) -> None:
    source = installed_copy / "validation/messages.py"
    source.write_text(source.read_text() + '\n__import__("anthropic_readiness.identity_extra")\n')
    with pytest.raises(ValueError, match="identity_dynamic_import"):
        installed_identity()


@pytest.mark.parametrize("target", ["math", "anthropic_readiness.models"])
def test_dynamic_import_exception_is_explicit_and_stdlib_only(
    installed_copy: Path, target: str
) -> None:
    source = installed_copy / "validation/messages.py"
    source.write_text(source.read_text() + f"\n__import__({target!r})\n")
    with pytest.raises(ValueError, match="identity_dynamic_import"):
        installed_identity()
    path = installed_copy / "resources/diagnostic-identity.json"
    manifest = object_value(strict_json(path.read_text()))
    manifest["dynamic_imports"] = [
        {"module": "validation/messages.py", "function": "__import__", "target": target}
    ]
    path.write_text(json.dumps(manifest))
    if target == "math":
        assert installed_identity().document["semantic_revision"] == "1"
    else:
        with pytest.raises(ValueError, match="identity_dynamic_import"):
            installed_identity()


@pytest.mark.parametrize(
    "statement",
    [
        'exec("pass")',
        'eval("1")',
        'compile("pass", "synthetic", "exec")',
        'import builtins as b\nb.exec("pass")',
    ],
)
def test_builtin_code_execution_is_rejected(installed_copy: Path, statement: str) -> None:
    source = installed_copy / "validation/messages.py"
    source.write_text(source.read_text() + "\n" + statement + "\n")
    with pytest.raises(ValueError, match="identity_dynamic_import"):
        installed_identity()


def test_type_only_import_does_not_pull_rendering_into_execution(installed_copy: Path) -> None:
    source = installed_copy / "validation/messages.py"
    source.write_text(
        source.read_text()
        + "\nfrom typing import TYPE_CHECKING\nif TYPE_CHECKING:\n"
        + "    from anthropic_readiness.report_models import ReportSource\n"
    )
    value = installed_identity()
    hashes = object_value(value.document["file_hashes"])
    assert "report_models.py" not in hashes


def test_rebound_type_checking_flag_is_not_ignored(installed_copy: Path) -> None:
    source = installed_copy / "validation/messages.py"
    source.write_text(
        source.read_text()
        + "\nfrom typing import TYPE_CHECKING\nTYPE_CHECKING = True\nif TYPE_CHECKING:\n"
        + "    import anthropic_readiness.identity_extra\n"
    )
    (installed_copy / "identity_extra.py").write_text("VALUE = 1\n")
    with pytest.raises(ValueError, match=r"identity_unlisted_module:identity_extra\.py"):
        installed_identity()


def test_identity_includes_actual_runtime_dependencies_only() -> None:
    value = installed_identity()
    dependencies = object_value(value.document["dependencies"])
    assert {"httpx", "httpcore", "anyio", "jsonschema", "pyyaml", "packaging"} <= set(dependencies)
    assert not {"fastapi", "jinja2", "pytest"} & set(dependencies)
    assert "resources/diagnostic-identity.json" in object_value(value.document["file_hashes"])


def test_tampered_identity_digest_cannot_certify_itself() -> None:
    from anthropic_readiness.diagnostics.models import ImplementationIdentity

    before = installed_identity()
    altered = object_value(before.document)
    altered["content_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="identity_digest"):
        check_identity(ImplementationIdentity(altered), before)


def test_unknown_manifest_version_is_rejected(installed_copy: Path) -> None:
    path = installed_copy / "resources/diagnostic-identity.json"
    document = object_value(strict_json(path.read_text()))
    document["schema_version"] = "999"
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="schema"):
        installed_identity()


def test_identity_in_fresh_process_needs_no_git(installed_copy: Path) -> None:
    expected = installed_identity().document
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json; from anthropic_readiness.diagnostics.identity import installed_identity; "
            "print(json.dumps(installed_identity().document, sort_keys=True))",
        ],
        cwd=installed_copy.parent,
        env={**os.environ, "PYTHONPATH": str(installed_copy.parent)},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == expected
    assert not (installed_copy.parent / ".git").exists()
