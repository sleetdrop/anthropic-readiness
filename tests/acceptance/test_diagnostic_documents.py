"""Standalone documents expose useful facts and remain inert offline artifacts."""

import hashlib
import json
from pathlib import Path

import pytest

from anthropic_readiness.models import object_value
from anthropic_readiness.presentation import Locale, PresentationOptions
from tests.acceptance.test_cli import ROOT, cli, target_file
from tests.http_server import SyntheticServer
from tests.http_server import server as server
from tests.unit.test_report_view import source


@pytest.mark.parametrize("locale", ["zh-CN", "en"])
def test_document_structure_counts_and_inert_source(locale: Locale) -> None:
    from anthropic_readiness.document_rendering import (
        render_agent_index,
        render_document_html,
        render_document_markdown,
    )
    from anthropic_readiness.documents import build_document_view

    view = build_document_view(source(), presentation=PresentationOptions(locale, "dark"))
    html = render_document_html(view)
    markdown = render_document_markdown(view)
    agent = render_agent_index(view)
    for identifier in ("conclusion", "scope", "findings", "method", "evidence"):
        assert f'id="{identifier}"' in html
    assert '<html lang="' + locale + '"' in html
    assert 'data-theme="dark"' in html
    assert 'id="document-data"' in html
    assert 'id="document-catalogs"' in html
    assert "<form" not in html
    assert "workbench" not in html
    assert "/api/v1/" not in html
    assert "https://" not in html.split("<style>")[1].split("</style>")[0]
    for text in ("ANT-MESSAGE-001", "STR-START", "FAIL", "INDETERMINATE"):
        assert text in html
        assert text in markdown
    for text in (
        "result.json",
        "retest-recipe.json",
        "comparison.json",
        "untrusted",
        "not authorization",
    ):
        assert text in agent
    assert "http://127." not in html + markdown
    assert "credential_env" not in html + markdown
    assert ("Passing / assessed" if locale == "en" else "通过 / 已评估") in html


@pytest.mark.parametrize(("locale", "theme"), [("en", "dark"), ("zh-CN", "light")])
def test_report_cli_flags_preserve_original_source(
    tmp_path: Path, locale: Locale, theme: str
) -> None:
    original = ROOT / "tests/fixtures/results/mixed.json"
    before = original.read_bytes()
    out = tmp_path / "report"
    result = cli(
        "report",
        "--input",
        str(original),
        "--out",
        str(out),
        "--language",
        locale,
        "--theme",
        theme,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert original.read_bytes() == before
    assert (out / "result.json").read_bytes() == before
    document = json.loads((out / "document-view.json").read_text())
    assert document["presentation"] == {"schema_version": "1.0", "locale": locale, "theme": theme}
    assert (out / "AGENT.md").exists()
    from anthropic_readiness.diagnostics.contracts import validate_projection

    validate_projection(
        object_value(json.loads((out / "report-manifest.json").read_text())), "document-manifest"
    )


@pytest.mark.parametrize(
    "command",
    [("run",), ("replay",), ("report",), ("diagnostics", "export"), ("diagnostics", "retest")],
)
def test_every_report_command_exposes_presentation_flags(command: tuple[str, ...]) -> None:
    result = cli(*command, "--help")
    assert result.returncode == 0
    assert "--language {zh-CN,en}" in result.stdout
    assert "--theme {light,dark,system}" in result.stdout


def test_diagnostic_export_is_versioned_and_retains_original_bytes(tmp_path: Path) -> None:
    from zipfile import ZipFile

    from anthropic_readiness.diagnostics.service import DiagnosticService
    from tests.diagnostic_fixtures import portable_archive

    _, root = portable_archive(tmp_path / "producer")
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    destination = tmp_path / "export.zip"
    service = DiagnosticService(tmp_path / "service")
    service.export(
        root, destination, include_evidence=True, presentation=PresentationOptions("en", "dark")
    )
    with ZipFile(destination) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema_version"] == "2.0"
        assert manifest["presentation_version"] == "3.0"
        assert manifest["presentation"]["locale"] == "en"
        assert archive.read("result.json") == before[Path("result.json")]
        assert "document-view.json" in archive.namelist()
        assert b'<html lang="en" data-theme="dark"' in archive.read("report.html")
    assert all((root / path).read_bytes() == data for path, data in before.items())


def test_versioned_web_export_keeps_legacy_manifest_and_artifacts_readable(tmp_path: Path) -> None:
    from anthropic_readiness.exports import ExportPolicy, ExportService
    from tests.export_fixtures import prepared_run

    run_id = prepared_run(tmp_path)
    service = ExportService(tmp_path)
    policy = ExportPolicy(("zip",), False)
    legacy = service.create(run_id, policy)
    assert object_value(legacy["manifest"])["presentation_version"] == "2.0"
    current = service.create(run_id, policy, presentation=PresentationOptions("en", "dark"))
    assert object_value(current["manifest"])["presentation_version"] == "3.0"
    assert b'<html lang="en" data-theme="dark"' in service.read(
        run_id, str(current["export_id"]), format="html"
    )
    assert (
        json.loads(service.read(run_id, str(current["export_id"]), format="json"))[
            "presentation_version"
        ]
        == "3.0"
    )
    assert service.read(run_id, str(legacy["export_id"]), format="json")


def test_explicit_comparison_is_included_in_report_and_diagnostic_package(tmp_path: Path) -> None:
    from zipfile import ZipFile

    from anthropic_readiness.diagnostics.service import DiagnosticService
    from tests.diagnostic_fixtures import portable_archive

    _, root = portable_archive(tmp_path / "producer")
    service = DiagnosticService(tmp_path / "service")
    comparison = service.compare_sources(root, root)
    comparison_path = tmp_path / "comparison.json"
    comparison_path.write_text(json.dumps(comparison.document))
    destination = tmp_path / "export.zip"
    service.export(root, destination, include_evidence=True, comparison=comparison)
    with ZipFile(destination) as archive:
        assert json.loads(archive.read("comparison.json")) == comparison.document
        assert json.loads(archive.read("document-view.json"))["comparison"] == comparison.document
        assert b'id="comparison-matrix"' in archive.read("report.html")
    output = tmp_path / "report"
    result = cli(
        "report",
        "--input",
        str(root / "result.json"),
        "--out",
        str(output),
        "--comparison",
        str(comparison_path),
    )
    assert result.returncode == 0, result.stderr
    assert (
        json.loads((output / "document-view.json").read_text())["comparison"] == comparison.document
    )


def test_markdown_matrices_are_contiguous_commonmark_tables() -> None:
    from anthropic_readiness.document_rendering import render_document_markdown
    from anthropic_readiness.documents import build_document_view

    rendered = render_document_markdown(build_document_view(source()))
    assert "|\n| --- |" in rendered
    assert "| --- |\n| " in rendered
    assert "|\n\n| --- |" not in rendered


def test_legacy_in_memory_rendering_does_not_invent_a_source_file_identity() -> None:
    from anthropic_readiness.reporting import render_html, render_markdown
    from tests.acceptance.test_reports import mixed

    result = mixed()
    assert render_html(result)
    assert render_markdown(result)
    for renderer in (render_html, render_markdown):
        with pytest.raises(ValueError, match="document_source_identity_required"):
            renderer(result, presentation=PresentationOptions("en", "light"))


def test_report_presentation_does_not_change_requests(
    server: SyntheticServer, tmp_path: Path
) -> None:
    target = target_file(tmp_path, server.url + "/cases")
    results = []
    for locale, theme in [("en", "dark"), ("zh-CN", "light")]:
        output = tmp_path / locale
        response = cli(
            "run",
            "--target",
            str(target),
            "--out",
            str(output),
            "--allow-live",
            "--language",
            locale,
            "--theme",
            theme,
        )
        assert response.returncode == 0, response.stderr
        assert set(json.loads(response.stdout)) == {"run_id", "profiles", "actual_requests"}
        result_bytes = (output / "result.json").read_bytes()
        result = json.loads(result_bytes)
        view = json.loads((output / "document-view.json").read_text())
        assert view["facts"]["source_result_sha256"] == hashlib.sha256(result_bytes).hexdigest()
        assert view["presentation"] == {"schema_version": "1.0", "locale": locale, "theme": theme}
        assert result["plan"]["actual_requests"] == 3
        results.append(result)
    assert len(server.requests) == 6
    normalized = [
        (path, headers["anthropic-version"], json.loads(body))
        for path, headers, body in server.requests
    ]
    assert normalized[:3] == normalized[3:]
    assert [case["dimensions"] for case in results[0]["cases"]] == [
        case["dimensions"] for case in results[1]["cases"]
    ]
