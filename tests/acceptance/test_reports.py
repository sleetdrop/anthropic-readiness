"""Reports preserve machine facts and treat captured strings as data."""

from dataclasses import replace
from pathlib import Path

import pytest

from anthropic_readiness.models import RunResult, object_value, strict_json
from anthropic_readiness.reporting import render_html, render_markdown
from anthropic_readiness.schema import result_from_document

ROOT = Path(__file__).resolve().parents[2]


def mixed() -> RunResult:
    return result_from_document(
        object_value(strict_json((ROOT / "tests/fixtures/results/mixed.json").read_text()))
    )


def test_matching_identity_statuses_counts_and_references() -> None:
    result = mixed()
    html = render_html(result)
    markdown = render_markdown(result)
    for value in (
        result.run_id,
        result.assessment_id,
        "ANT-MESSAGE-001",
        "ANT-TEXT-SSE-001",
        "ANT-TEXT-SSE-002",
        "STR-START",
        "FAIL",
        "PASS",
        result.contract["content_sha256"],
    ):
        assert str(value) in html
        assert str(value) in markdown
    for reference in ("messages", "streaming", "sse", "versioning", "stop-reasons"):
        assert f"[{reference}]" in markdown
        assert f"ref-{reference}" in html
    assert "请求／传输调用 3" in html
    assert "请求／传输调用：3" in markdown
    assert "离线合成数据" in html
    assert "离线合成数据" in markdown
    assert "Claude Code ready" not in html + markdown
    assert "无法独立复核" in markdown


def test_markdown_is_self_contained_and_has_no_raw_html_injection() -> None:
    result = mixed()
    malicious = "<script>alert(1)</script>\n```\n| forged | PASS |\n[run](javascript:alert(1))"
    result = replace(
        result,
        target={**result.target, "name": "中文目标" + "long-" * 80},
        limitations=(*result.limitations, malicious),
    )
    html = render_html(result)
    markdown = render_markdown(result)
    assert "<script>" not in html + markdown
    assert "<script src=" not in html
    assert 'href="javascript:' not in html
    assert "中文目标" in html
    assert "中文目标" in markdown
    for concept in ("方法", "范围", "限制", "证据", "术语", "参考资料", "INDETERMINATE"):
        assert concept in markdown
    assert "| forged | PASS |" not in markdown


def test_report_rerender_preserves_source_and_marks_missing_evidence(tmp_path: Path) -> None:
    from tests.acceptance.test_cli import cli

    source = ROOT / "tests/fixtures/results/mixed.json"
    before = source.read_bytes()
    out = tmp_path / "report"
    command = cli("report", "--input", str(source), "--out", str(out))
    assert command.returncode == 0, command.stderr
    assert source.read_bytes() == before
    assert (out / "report.html").exists()
    assert (out / "report.md").exists()
    assert "无法独立复核" in (out / "report.md").read_text()


@pytest.mark.parametrize("state", ["BLOCKED", "INDETERMINATE", "SKIP"])
def test_unexecuted_cases_are_not_reported_as_observed_samples(state: str) -> None:
    from anthropic_readiness.models import AssertionResult, JsonObject, Status

    result = mixed()
    blocked: list[JsonObject] = []
    for case in result.cases:
        item = AssertionResult("CASE-PRECONDITION", "environment", Status(state), "not_executed")
        blocked.append(
            {
                **case,
                "status": state,
                "attempts": [],
                "preconditions": [item.to_json()],
                "dimensions": {
                    "environment": state,
                    "protocol": "not_evaluated",
                    "behavior": "not_evaluated",
                    "client": "not_evaluated",
                },
            }
        )
    result = replace(
        result,
        cases=tuple(blocked),
        evidence=(),
        plan={**result.plan, "actual_requests": 0},
        profiles=tuple({**profile, "readiness": "incomplete"} for profile in result.profiles),
    )
    markdown = render_markdown(result)
    assert "已执行用例：0" in markdown
    assert "断言：3" in markdown
    assert "CASE-PRECONDITION" in markdown
