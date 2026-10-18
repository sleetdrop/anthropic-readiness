"""Offline visual reports have equivalent accessible data and inert target content."""

import hashlib
import json
from dataclasses import replace
from html.parser import HTMLParser
from pathlib import Path

import pytest

from anthropic_readiness.models import JsonValue, object_value
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.report_rendering import render_report_html, render_report_markdown
from anthropic_readiness.report_sources import load_report_source
from anthropic_readiness.report_view import build_report_view
from anthropic_readiness.reporting import render_from_file
from tests.acceptance.test_readable_reports import assessment
from tests.export_fixtures import prepared_run
from tests.unit.test_report_view import source


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: dict[str, list[list[str]]] = {}
        self.figure: str | None = None
        self.row: list[str] | None = None
        self.cell: str | None = None
        self.scripts: list[str | None] = []
        self.unsafe: list[str] = []
        self.svg_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "table" and "data-figure" in attributes:
            self.figure = attributes["data-figure"]
            assert self.figure is not None
            self.rows[self.figure] = []
        if self.figure and tag == "tr":
            self.row = []
        if self.figure and tag == "td":
            self.cell = ""
        if tag == "script":
            self.scripts.append(attributes.get("type"))
        if tag in {"img", "iframe", "object", "embed"} or any(
            key.startswith("on") for key in attributes
        ):
            self.unsafe.append(tag)
        if tag == "svg":
            self.svg_count += 1

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.cell is not None and self.row is not None:
            self.row.append(self.cell)
            self.cell = None
        if tag == "tr" and self.figure and self.row:
            self.rows[self.figure].append(self.row)
        if tag == "table":
            self.figure = None


def test_report_has_matrix_charts_captions_and_equivalent_tables() -> None:
    view = build_report_view(source())
    html = render_report_html(view)
    markdown = render_report_markdown(view)
    parsed = ReportParser()
    parsed.feed(html)
    assert parsed.svg_count >= 3
    for figure in objects(view.document["figures"]):
        identifier = str(figure["id"])
        assert identifier in parsed.rows
        rows = figure["rows"]
        assert isinstance(rows, list)
        expected = [
            ["—" if value is None else str(value) for value in row]
            for row in rows
            if isinstance(row, list)
        ]
        assert parsed.rows[identifier] == expected
        assert str(figure["caption"]) in html
        assert str(figure["caption"]) in markdown
        assert identifier in markdown
    assert 'id="report-data"' in html
    assert "@media print" in html
    assert "<noscript>" in html
    assert "fetch(" not in html


def test_embedded_hostile_text_is_not_executable() -> None:
    original = source()
    assert original.result is not None
    payload = '</script><img src=x onerror="alert(1)"><script>bad()</script>'
    result = replace(
        original.result, target={**original.result.target, "name": payload}, limitations=(payload,)
    )
    view = build_report_view(replace(original, result=result))
    html = render_report_html(view)
    parser = ReportParser()
    parser.feed(html)
    assert parser.unsafe == []
    assert set(parser.scripts) == {"application/json", "module"}
    assert payload not in html
    assert "\\u003c/script\\u003e" in html
    assert "&lt;img" in html
    assert "|[link](javascript:" not in render_report_markdown(view)


def test_rerender_keeps_source_and_evidence_bytes(tmp_path: Path) -> None:
    source_path = assessment(tmp_path / "source")
    before = source_path.read_bytes()
    files = {
        path.relative_to(source_path.parent): path.read_bytes()
        for path in (source_path.parent / "evidence").rglob("*")
        if path.is_file()
    }
    output = tmp_path / "report"
    render_from_file(source_path, output)
    assert source_path.read_bytes() == (output / "result.json").read_bytes() == before
    assert all((output / relative).read_bytes() == data for relative, data in files.items())
    manifest = object_value(json.loads((output / "report-manifest.json").read_text()))
    assert manifest["presentation_version"] == "2.0"
    view = object_value(json.loads((output / "report-view.json").read_text()))
    assert view["source_result_sha256"] == hashlib.sha256(before).hexdigest()
    with pytest.raises(FileExistsError):
        render_from_file(source_path, output)


def test_csp_hash_covers_the_actual_formatted_inline_script() -> None:
    import base64
    import re

    html = render_report_html(build_report_view(source()))
    blocks = re.findall(r'<script type="module">(.*?)</script>', html, re.DOTALL)
    assert len(blocks) == 1
    expected = base64.b64encode(hashlib.sha256(blocks[0].encode()).digest()).decode()
    assert "sha256-" + expected in html


def test_unclosed_span_has_an_explicit_ongoing_marker() -> None:
    from copy import deepcopy

    from anthropic_readiness.report_models import ReportView

    document = deepcopy(build_report_view(source()).document)
    figures = objects(document["figures"])
    timing = next(figure for figure in figures if figure["id"] == "fig-timing")
    timing.update(
        {
            "kind": "timeline",
            "columns": ["case_id", "attempt_id", "phase", "start_ms", "end_ms"],
            "rows": [["ANT-TEXT-SSE-002", None, "case", 5.0, None]],
        }
    )
    document["figures"] = list(figures)
    html = render_report_html(ReportView(document))
    assert 'data-ongoing="true"' in html
    assert "进行中（未闭合）" in html


def test_partial_live_origin_is_unknown_without_a_persisted_marker(tmp_path: Path) -> None:
    run_id = prepared_run(tmp_path, partial=True)
    root = tmp_path / "runs" / run_id
    view = build_report_view(
        load_report_source(root / "assessment", operations_root=root / "operations")
    )
    assert view.document["mode"] == "live"
    context = object_value(object_value(view.document["provenance"])["report_context"])
    assert context.get("data_kind") == "unknown"
    for report in (render_report_html(view), render_report_markdown(view)):
        assert "来源信息未完整记录" in report
        assert "离线合成数据／捕获回放" not in report
        assert "显式真实端点测试" not in report


@pytest.mark.parametrize(
    ("data_kind", "label"),
    [
        ("live_endpoint", "显式真实端点测试"),
        ("synthetic", "离线合成数据／捕获回放"),
        ("unknown", "来源信息未完整记录"),
        ({"unexpected": True}, "来源信息未完整记录"),
        (["unexpected"], "来源信息未完整记录"),
    ],
)
def test_report_origin_follows_explicit_context(data_kind: JsonValue, label: str) -> None:
    original = source()
    assert original.result is not None
    result = replace(
        original.result,
        mode="live",
        report_context={**original.result.report_context, "data_kind": data_kind},
    )
    view = build_report_view(replace(original, result=result))
    for report in (render_report_html(view), render_report_markdown(view)):
        assert label in report
