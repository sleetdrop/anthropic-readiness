"""Matrix state actions navigate to matching cases, including mixed groups."""

from html.parser import HTMLParser

from anthropic_readiness.report_rendering import render_report_html
from anthropic_readiness.report_view import build_report_view
from tests.unit.test_report_view import source


class MatrixLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.active = False
        self.body = False
        self.rows: list[list[list[tuple[str, str]]]] = []
        self.row: list[list[tuple[str, str]]] = []
        self.cell: list[tuple[str, str]] | None = None
        self.href: str | None = None
        self.label = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "table" and attributes.get("class") == "capability-matrix":
            self.active = True
        if not self.active:
            return
        if tag == "tbody":
            self.body = True
        if self.body and tag == "tr":
            self.row = []
        if self.body and tag == "td":
            self.cell = []
        if self.cell is not None and tag == "a":
            self.href = attributes.get("href")
            self.label = ""

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.label += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.href is not None and self.cell is not None:
            self.cell.append((self.href, self.label))
            self.href = None
        if tag == "td" and self.cell is not None:
            self.row.append(self.cell)
            self.cell = None
        if self.active and self.body and tag == "tr":
            self.rows.append(self.row)
        if self.active and tag == "table":
            self.active = self.body = False


def test_mixed_protocol_state_links_select_the_matching_case() -> None:
    parser = MatrixLinks()
    parser.feed(render_report_html(build_report_view(source())))
    protocol = parser.rows[1][1]
    passing = [href for href, label in protocol if "PASS" in label]
    failing = [href for href, label in protocol if "FAIL" in label]
    assert passing == ["#case-ANT-TEXT-SSE-002"]
    assert failing == ["#case-ANT-TEXT-SSE-001"]


def test_multi_member_state_has_native_disclosure_and_all_matching_links() -> None:
    html = render_report_html(build_report_view(source()))
    parser = MatrixLinks()
    parser.feed(html)
    client = parser.rows[1][3]
    assert {href for href, _ in client} == {"#case-ANT-TEXT-SSE-001", "#case-ANT-TEXT-SSE-002"}
    assert 'id="matrix-streaming-client-not_evaluated"' in html
    assert "<summary" in html
