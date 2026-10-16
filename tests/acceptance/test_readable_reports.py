"""Reader summaries explain unchanged verdicts using verified synthetic evidence."""

import json
from dataclasses import replace
from pathlib import Path

from anthropic_readiness.config import Limits, load_target
from anthropic_readiness.contracts import resolve_contract
from anthropic_readiness.models import Capture, RequestSpec
from anthropic_readiness.reporting import (
    render_from_file,
    render_html,
    render_markdown,
    write_reports,
)
from anthropic_readiness.runner import execute_run, plan_run
from tests.acceptance.test_reports import mixed
from tests.acceptance.test_runner import FixtureTransport
from tests.factories import capture

ROOT = Path(__file__).resolve().parents[2]


class MissingFieldsTransport(FixtureTransport):
    response_model = "synthetic-upstream-model"

    def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
        if request.streaming:
            raw = super().send(request, limits, deadline).body
            if "Count" in str(request.body.get("messages")):
                raw = raw.replace(b"Hello.", b"1 2 3 4 5")
            lines = []
            for line in raw.decode().splitlines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    message = data.get("message")
                    if isinstance(message, dict):
                        message["model"] = self.response_model
                        message.pop("stop_reason", None)
                        message.pop("stop_sequence", None)
                    if isinstance(data.get("delta"), dict):
                        data["delta"].pop("stop_sequence", None)
                    line = "data: " + json.dumps(data)
                lines.append(line)
            body = ("\n".join(lines) + "\n\n").encode()
        else:
            name = "message-valid-tool.json" if "tools" in request.body else "message-valid.json"
            message = json.loads((ROOT / "tests/fixtures/contracts/core-1.0.0" / name).read_text())
            message["model"] = self.response_model
            message.pop("stop_sequence")
            body = json.dumps(message).encode()
        return replace(capture(body, request.streaming), request=request)


def assessment(root: Path) -> Path:
    target = load_target(ROOT / "examples/target.yaml")
    plan = plan_run(
        target,
        resolve_contract(target.contract_id, target.contract_revision),
        ["anthropic-basic", "anthropic-tools-smoke"],
    )
    execute_run(plan, MissingFieldsTransport(), root)
    return root / "result.json"


def test_front_page_names_tasks_and_keeps_ids_in_appendix() -> None:
    result = mixed()
    html = render_html(result)
    md = render_markdown(result)
    for text in (html, md):
        text = text.replace("\\_", "_")
        assert "先看结论" in text
        assert "用例结果" in text
        assert "非流式问候" in text
        assert "流式计数" in text
        assert text.index("用例结果") < text.index("技术附录") < text.index(result.run_id)
        assert "任务行为" in text
        assert "协议格式" in text
        assert "客户端工作流未测试" in text
    assert '<details class="technical"' in html


def test_grouped_findings_explain_missing_fields_and_alias_without_rescoring(
    tmp_path: Path,
) -> None:
    source = assessment(tmp_path / "source")
    original = source.read_bytes()
    destination = tmp_path / "readable"
    render_from_file(source, destination)
    assert source.read_bytes() == original == (destination / "result.json").read_bytes()
    html = (destination / "report.html").read_text()
    md = (destination / "report.md").read_text()
    assert html.count("<h3>停止字段不完整</h3>") == 1
    assert html.count("<h3>模型名称与配置不一致</h3>") == 1
    for text in (html, md):
        text = text.replace("\\_", "_")
        assert "任务行为通过 4 个，协议格式通过 0 个" in text
        assert "stop_sequence" in text
        assert "字段缺失" in text
        assert "stop_reason" in text
        assert "null" in text
        assert "example-model" in text
        assert "synthetic-upstream-model" in text
        assert "允许别名：未配置" in text
        assert "确认别名映射后" in text
        assert "不代表模型路由错误" in text
        assert "未重新判定" in text
    manifest = json.loads((destination / "report-manifest.json").read_text())
    assert manifest["evidence_verification"]["status"] == "verified"
    assert manifest["presentation_version"] == "1.1"


def test_invalid_evidence_never_becomes_a_field_diagnosis(tmp_path: Path) -> None:
    from anthropic_readiness.models import object_value, strict_json
    from anthropic_readiness.schema import result_from_document

    source = assessment(tmp_path / "source")
    result = result_from_document(object_value(strict_json(source.read_text())))
    first_body = next(ref for ref in result.evidence if ref.path.endswith("body.bin"))
    (source.parent / first_body.path).write_text('{"model":"forged-diagnostic-value"}')
    write_reports(result, source.parent)
    text = (source.parent / "report.md").read_text()
    assert "证据未完整核验，未提取字段级说明" in text
    assert "forged-diagnostic-value" not in text
    assert "字段缺失：stop_sequence" not in text


def test_without_evidence_explains_recorded_failure_without_inventing_details() -> None:
    result = mixed()
    for text in (render_html(result), render_markdown(result)):
        assert "流式消息重复开始" in text
        assert "修复重复的 message_start" in text.replace("\\_", "_")
        assert "未附可核验的字段摘录" in text
        assert "任务行为通过 3 个，协议格式通过 2 个" in text


def test_verified_diagnostic_strings_cannot_inject_report_markup(tmp_path: Path) -> None:
    target = load_target(ROOT / "examples/target.yaml")
    transport = MissingFieldsTransport()
    transport.response_model = "<script>alert(1)</script>|[link](javascript:run)"
    out = tmp_path / "run"
    result = execute_run(
        plan_run(
            target,
            resolve_contract(target.contract_id, target.contract_revision),
            ["anthropic-basic"],
        ),
        transport,
        out,
    )
    write_reports(result, out)
    html = (out / "report.html").read_text()
    md = (out / "report.md").read_text()
    assert "<script>" not in html + md
    assert "&lt;script&gt;" in html + md
    assert 'href="javascript:' not in html
    assert "|[link](javascript:run)" not in md
