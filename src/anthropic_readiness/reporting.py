"""Self-contained engineering reports from one validated set of facts."""

from __future__ import annotations

import hashlib
import html
import re
from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from urllib.parse import quote, urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from anthropic_readiness.context import build_report_context
from anthropic_readiness.evidence import (
    atomic_write,
    create_run_directory,
    json_bytes,
    safe_path,
    verify_evidence,
)
from anthropic_readiness.models import (
    EvidenceRef,
    JsonObject,
    JsonValue,
    RunResult,
    object_value,
    strict_json,
)
from anthropic_readiness.report_reading import (
    case_name,
    finding_count,
    findings,
    message_diagnostic,
    overview,
    state_name,
)
from anthropic_readiness.schema import result_from_document

EXPECTED = {
    "STR-START": "message_start 恰好一次，不用后来的消息覆盖之前的记录。",
    "STR-STOP": "message_stop 恰好一次，且位于消息增量和所有内容块关闭之后。",
    "STR-LIFECYCLE": "按连续 index 管理内容块；仅向已开启且未关闭的块发送增量。",
    "STR-JSON": "事件数据为严格 JSON 对象，字段类型有效。",
    "STR-TYPE": "SSE 事件名与 data.type 一致。",
    "STR-DELTA": "消息完成之前至少有一个有效 message_delta。",
    "SSE-FRAMING": "UTF-8、事件分隔及尾部采集符合 SSE 规则。",
    "MSG-CORE": "消息身份、角色、内容、停止字段与 usage 满足核心结构。",
    "MSG-MODEL": "响应模型满足显式的身份或别名策略。",
    "MSG-STOP": "停止原因在本规则快照可识别的范围内。",
    "MSG-STOP-SEQUENCE": "停止序列与本用例没有自定义停止序列的请求一致。",
    "MSG-TOOL-CALLS": "强制工具用例恰好返回一次工具调用。",
    "MSG-TOOL-ID": "工具 ID 非空且在响应内唯一。",
    "MSG-TOOL-NAME": "强制工具名精确为 get_weather。",
    "MSG-TOOL-INPUT": "参数为满足 schema 的对象，并精确指定 Hanoi。",
    "TASK-COMPLETE": "受控任务完成并以适合该任务的原因自然结束。",
    "CAPTURE-COMPLETE": "HTTP 采集完整；与消息协议终止独立记录。",
    "HTTP-STATUS": "收到成功 HTTP 状态。",
    "HTTP-CONTENT-TYPE": "响应类型与流式或非流式请求一致。",
}


def _objects(value: JsonValue) -> list[JsonObject]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _values(value: JsonValue) -> list[JsonValue]:
    return value if isinstance(value, list) else []


def _text(value: JsonValue) -> str:
    return "" if value is None else str(value)


def _short(value: JsonValue, limit: int = 1200) -> str:
    text = _text(value)
    return text if len(text) <= limit else text[:limit] + "…（显示已截短；完整数据见 result.json）"


def _display_time(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return value + " (timezone unspecified)"
        return (
            parsed.astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S %z")
            + " Asia/Shanghai"
        )
    except (ValueError, ZoneInfoNotFoundError):
        return value + " (original timezone)"


def _coverage(result: RunResult) -> str:
    coverage = result.contract.get("coverage")
    return _text(coverage) if isinstance(coverage, dict) else "Coverage metadata unavailable."


def _md(value: JsonValue) -> str:
    text = html.escape(_text(value), quote=False).replace("\\", "\\\\")
    return re.sub(r"([`*\[\]()#_!|])", r"\\\1", text).replace("\r", "").replace("\n", " / ")


def _h(value: JsonValue) -> str:
    return html.escape(_text(value), quote=True)


def _context(result: RunResult) -> JsonObject:
    return {**build_report_context(result.contract, result.mode), **result.report_context}


def _synthetic(result: RunResult) -> bool:
    return result.mode == "replay" or _context(result).get("data_kind") != "live_endpoint"


def _counts(result: RunResult) -> tuple[int, int]:
    attempts = [attempt for case in result.cases for attempt in _objects(case.get("attempts"))]
    return len(attempts), sum(len(_objects(a.get("assertions"))) for a in attempts) + sum(
        len(_objects(c.get("preconditions"))) for c in result.cases
    )


def _availability(result: RunResult) -> str:
    value = _context(result).get("evidence_verification")
    if isinstance(value, dict) and value.get("status") == "verified":
        return "随附文件的路径与哈希已核对；这不是独立的服务复测。仅凭报告摘要仍无法独立复核完整事件顺序。"
    return "证据未完整核验，未提取字段级说明。证据文件未附、未核验或不完整：无法独立复核。摘要仅供初步解读；复核需要 result.json 与完整证据文件。"


def _reference_id(assertion_id: str) -> str:
    if assertion_id.startswith("STR-"):
        return "streaming"
    if assertion_id.startswith("SSE-"):
        return "sse"
    if assertion_id.startswith("TASK-"):
        return "stop-reasons"
    return "messages"


def _safe_reference_path(path: str) -> bool:
    return re.fullmatch(
        r"evidence/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(?:request\.json|response\.json|body\.bin|reads\.json|events\.jsonl)",
        path,
    ) is not None and ".." not in path.split("/")


def _url(value: JsonValue) -> str | None:
    if not isinstance(value, str):
        return None
    if value == "#contract":
        return value
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else None


def _evidence_label(ref: JsonObject) -> str:
    return (
        _text(ref.get("path"))
        + (f" · event {ref['event']}" if ref.get("event") is not None else "")
        + (f" · pointer {ref['pointer']}" if ref.get("pointer") is not None else "")
    )


def _masthead(result: RunResult) -> list[tuple[str, str]]:
    try:
        seconds = (
            datetime.fromisoformat(result.finished_at) - datetime.fromisoformat(result.started_at)
        ).total_seconds()
        elapsed = f"{seconds:.1f} 秒" if seconds >= 0 else "耗时不可用"
    except (ValueError, TypeError):
        elapsed = "耗时未记录"
    beta = ", ".join(str(v) for v in _values(result.contract.get("beta_headers"))) or "无"
    return [
        ("目标", _text(result.target.get("name"))),
        ("请求模型", _text(result.target.get("model"))),
        (
            "契约",
            f"API {result.contract.get('api_version')} · 规则 {result.contract.get('revision')} · beta {beta}",
        ),
        ("采集时间", _display_time(result.started_at)),
        (
            "执行",
            f"{result.plan.get('actual_requests')} 次请求 · 重试上限 {result.plan.get('retry')} · {elapsed}",
        ),
    ]


def _evidence_summary(result: RunResult) -> str:
    verification = _context(result).get("evidence_verification")
    if isinstance(verification, dict) and verification.get("status") == "verified":
        return "证据文件与引用已核验；这不是独立的服务复测。"
    return "证据未完整核验，字段级对照不可用；无法独立复核。"


def _observation_groups(group: JsonObject) -> list[JsonObject]:
    unique: dict[tuple[str, str, str, str], JsonObject] = {}
    for observation in _objects(group.get("observations")):
        pair = (
            _text(observation.get("expected")),
            _text(observation.get("actual")),
            _text(observation.get("expected_excerpt")),
            _text(observation.get("actual_excerpt")),
        )
        if pair not in unique:
            unique[pair] = {**observation, "sources": []}
        sources = unique[pair]["sources"]
        assert isinstance(sources, list)
        sources.append(observation)
    return list(unique.values())


def _source_label(observation: JsonObject) -> str:
    reference = observation.get("reference")
    event = reference.get("event") if isinstance(reference, dict) else None
    where = f"SSE 事件（索引 {event}）" if event is not None else "JSON 响应"
    return case_name(observation.get("case_id")) + " · " + where


def _source_html(observation: JsonObject) -> str:
    reference = observation.get("reference")
    path = _text(reference.get("path")) if isinstance(reference, dict) else ""
    label = _h(_source_label(observation))
    return f'<a href="{quote(path, safe="/")}">{label}</a>' if _safe_reference_path(path) else label


def _code_markdown(value: JsonValue) -> str:
    # Keep string values valid JSON while preventing embedded Markdown link syntax.
    text = re.sub(
        r'"(?:\\.|[^"\\])*"',
        lambda match: match.group().replace("[", r"\u005b").replace("]", r"\u005d"),
        _short(value, 1600),
    )
    text = html.escape(text, quote=False)
    fence = "`" * max(3, 1 + max((len(m.group()) for m in re.finditer(r"`+", text)), default=0))
    return f"{fence}json\n{text}\n{fence}"


def _reader_markdown(result: RunResult, diagnostics: Sequence[JsonObject]) -> list[str]:
    title, summary = overview(result)
    grouped = findings(result, diagnostics)
    lines = ["", "## 运行摘要", ""]
    lines.extend(f"- {label}：{_md(value)}" for label, value in _masthead(result))
    lines.extend(
        [
            "",
            "## 先看结论",
            "",
            "**" + title + "**",
            "",
            summary,
            "",
            finding_count(grouped) + "。分类只用于安排核查，不改变原始状态。",
            "",
            _evidence_summary(result),
            "",
            "任务行为：有没有完成指定任务。协议格式：响应结构、流式顺序及模型身份是否符合所选契约。",
            "",
            "客户端工作流未测试；单次样本不能证明长期稳定或完整 API 兼容。",
            "",
        ]
    )
    for group in grouped:
        lines.append(
            f"- {_md(group.get('number'))} · {_md(group.get('kind'))}：{_md(group.get('title'))}"
        )
    lines.extend(
        [
            "",
            "## 用例结果",
            "",
            "| 测试任务 | 任务行为 | 协议格式 | 执行条件 | 关联问题 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for case in result.cases:
        dimensions = object_value(case.get("dimensions", {}))
        related = (
            ", ".join(
                str(g["number"]) for g in grouped if case.get("id") in _values(g.get("cases"))
            )
            or "无"
        )
        values = (
            case_name(case.get("id")),
            state_name(dimensions.get("behavior")),
            state_name(dimensions.get("protocol")),
            state_name(dimensions.get("environment")),
            related,
        )
        lines.append("| " + " | ".join(_md(v) for v in values) + " |")
    lines.extend(["", "## 需要处理的问题", ""])
    if not grouped:
        lines.append("所选必需检查未发现待处理项；结论仍限于本次已测范围。")
    for group in grouped:
        lines.extend(
            [
                f"### {_md(group.get('number'))} · {_md(group.get('title'))}",
                "",
                f"处理方向：{_md(group.get('kind'))}；原断言：{_md(group.get('status'))}。",
                "",
                "涉及：" + "、".join(_md(case_name(c)) for c in _values(group.get("cases"))) + "。",
                "",
                "影响：" + _md(group.get("impact")),
                "",
            ]
        )
        observations = _observation_groups(group)
        if not observations:
            lines.append("未附可核验的字段摘录；此处仅解释原始检查记录，不推测具体字段值。")
        for observation in observations:
            lines.extend(
                [
                    "**局部字段对照**",
                    "",
                    "应满足：" + _md(observation.get("expected")),
                    "",
                    "实际情况：" + _md(observation.get("actual")),
                    "",
                ]
            )
            if observation.get("expected_excerpt"):
                lines.extend(
                    [
                        _md(observation.get("expected_label")),
                        "",
                        _code_markdown(observation.get("expected_excerpt")),
                        "",
                    ]
                )
            lines.extend(
                [
                    "实际字段摘录（未展示其他字段不表示其他字段缺失）：",
                    "",
                    _code_markdown(observation.get("actual_excerpt")),
                    "",
                ]
            )
            for source in _objects(observation.get("sources")):
                reference = object_value(source.get("reference", {}))
                path = _text(reference.get("path"))
                label = _md(_source_label(source))
                link = (
                    f"[{label}]({quote(path, safe='/')})" if _safe_reference_path(path) else label
                )
                lines.append("- 证据：" + link + "；位置：" + _md(source.get("source_label")))
            lines.append("")
        key = str(group.get("id"))
        lines.extend(
            [
                "建议：" + _md(group.get("action")),
                "",
                f"依据：{_md(key)}；定位见技术附录。[{_reference_id(key)}]",
                "",
            ]
        )
    lines.extend(["以上说明由原始判定与已校验证据生成，未重新判定、放宽条件或改写结果。", ""])
    return lines


def _reader_html(result: RunResult, diagnostics: Sequence[JsonObject]) -> str:
    title, summary = overview(result)
    grouped = findings(result, diagnostics)
    parts = [
        '<section class="reading"><p class="section-label">运行摘要</p><dl class="run-summary">'
    ]
    parts.extend(f"<dt>{_h(label)}</dt><dd>{_h(value)}</dd>" for label, value in _masthead(result))
    parts.append(
        '</dl><nav class="report-nav" aria-label="报告导航"><a href="#conclusion">结论</a><a href="#case-results">用例</a><a href="#findings">问题与证据</a><a href="#technical">原始记录</a></nav>'
    )
    parts.append(
        f'<div class="verdict"><h2 id="conclusion">先看结论</h2><p class="lead"><strong>{_h(title)}</strong></p><p>{_h(summary)}</p><p><strong>{_h(finding_count(grouped))}</strong>。分类只用于安排核查，不改变原始状态。</p></div>'
    )
    parts.append('<p class="evidence-note">' + _h(_evidence_summary(result)) + "</p>")
    if grouped:
        parts.append('<ul class="finding-index">')
        for group in grouped:
            parts.append(
                f'<li><a href="#{_h(group.get("anchor"))}">{_h(group.get("number"))} · {_h(group.get("title"))}</a><span>{_h(group.get("kind"))}</span></li>'
            )
        parts.append("</ul>")
    parts.extend(
        [
            '<p class="reader-key">任务行为：有没有完成指定任务。协议格式：响应结构、流式顺序及模型身份是否符合所选契约。</p>',
            '<p class="muted">客户端工作流未测试；单次样本不能证明长期稳定或完整 API 兼容。</p>',
            '<h2 id="case-results">用例结果</h2><div class="table-wrap"><table class="overview"><thead><tr><th>测试任务</th><th>任务行为</th><th>协议格式</th><th>执行条件</th><th>关联问题</th></tr></thead><tbody>',
        ]
    )
    for index, case in enumerate(result.cases, 1):
        dimensions = object_value(case.get("dimensions", {}))
        values = (
            case_name(case.get("id")),
            state_name(dimensions.get("behavior")),
            state_name(dimensions.get("protocol")),
            state_name(dimensions.get("environment")),
        )
        links = (
            " ".join(
                f'<a href="#{_h(g.get("anchor"))}">{_h(g.get("number"))}</a>'
                for g in grouped
                if case.get("id") in _values(g.get("cases"))
            )
            or "无"
        )
        parts.append(
            f'<tr id="case-row-{index}">'
            + "<td>"
            + _h(values[0])
            + "</td>"
            + "".join(
                f'<td class="{_h(dimensions.get(dimension))}">{_h(value)}</td>'
                for dimension, value in zip(
                    ("behavior", "protocol", "environment"), values[1:], strict=True
                )
            )
            + "<td>"
            + links
            + "</td></tr>"
        )
    parts.append('</tbody></table></div><h2 id="findings">需要处理的问题</h2>')
    if not grouped:
        parts.append("<p>所选必需检查未发现待处理项；结论仍限于本次已测范围。</p>")
    for group in grouped:
        parts.append(
            f'<article class="finding" id="{_h(group.get("anchor"))}"><p class="finding-label">{_h(group.get("number"))} · {_h(group.get("kind"))} · 原断言：{_h(group.get("status"))}</p><h3>'
            + _h(group.get("title"))
            + '</h3><p class="muted">涉及：'
            + "、".join(_h(case_name(c)) for c in _values(group.get("cases")))
            + "。</p><p>影响："
            + _h(group.get("impact"))
            + "</p>"
        )
        observations = _observation_groups(group)
        if not observations:
            parts.append(
                '<p class="muted">未附可核验的字段摘录；此处仅解释原始检查记录，不推测具体字段值。</p>'
            )
        for observation in observations:
            parts.append(
                '<section class="field-diff"><h4>局部字段对照</h4><p><strong>应满足：</strong>'
                + _h(observation.get("expected"))
                + "</p><p><strong>实际情况：</strong>"
                + _h(observation.get("actual"))
                + '</p><div class="comparison">'
            )
            if observation.get("expected_excerpt"):
                parts.append(
                    "<div><p>"
                    + _h(observation.get("expected_label"))
                    + "</p><pre><code>"
                    + _h(_short(observation.get("expected_excerpt"), 1600))
                    + "</code></pre></div>"
                )
            parts.append(
                "<div><p>实际字段摘录</p><pre><code>"
                + _h(_short(observation.get("actual_excerpt"), 1600))
                + '</code></pre></div></div><p class="excerpt-note">仅展示局部字段；未展示其他字段不表示其他字段缺失。</p><p class="source-links">证据：'
            )
            parts.append(
                "；".join(
                    _source_html(source) + " · " + _h(source.get("source_label"))
                    for source in _objects(observation.get("sources"))
                )
            )
            parts.append("</p></section>")
        key = str(group.get("id"))
        parts.append(
            '<p class="action"><strong>建议：</strong>'
            + _h(group.get("action"))
            + f'</p><p class="muted">依据：<code>{_h(key)}</code>；<a href="#technical">定位见技术附录</a>。<a href="#ref-{_reference_id(key)}">规范依据</a> · <a href="#case-results">返回用例结果</a></p></article>'
        )
    parts.append(
        '<p class="muted">以上说明由原始判定与已校验证据生成，未重新判定、放宽条件或改写结果。</p></section>'
    )
    return "".join(parts)


def render_markdown(result: RunResult, diagnostics: Sequence[JsonObject] = ()) -> str:
    result_from_document(result.to_json())
    context = _context(result)
    attempts, assertions = _counts(result)
    lines = [
        "# Anthropic 接口兼容性报告",
        "",
        "**离线合成数据／捕获回放**" if _synthetic(result) else "**显式真实端点测试**",
        "",
        *_reader_markdown(result, diagnostics),
        "## 技术附录",
        "",
        f"Run: {_md(result.run_id)}  ",
        f"Assessment: {_md(result.assessment_id)}  ",
        f"模式：{result.mode}；时间（UTC）：{_md(result.started_at)} → {_md(result.finished_at)}。",
        "",
        "## 阅读说明与方法",
        "",
        _md(context.get("methodology")),
        "",
        _availability(result),
        "",
    ]
    for note in _values(context.get("reader_notes")):
        lines.append("- " + _md(note))
    lines.extend(
        [
            "",
            "## 对象、范围与预算",
            "",
            f"- 目标：{_md(result.target.get('name'))}；交付：{_md(result.target.get('delivery_id'))}；模型：{_md(result.target.get('model'))}。",
            f"- API：{_md(result.contract.get('api_version'))}；beta：{_md(result.contract.get('beta_headers'))}。[versioning]",
            f"- 规则包：{_md(result.contract.get('id'))} / {_md(result.contract.get('revision'))}；截至 {_md(result.contract.get('spec_as_of'))}。[contract]",
            f"- 规则哈希：{_md(result.contract.get('content_sha256'))}。",
            "- 身份策略："
            + _md(result.target.get("response_model_policy"))
            + "；别名："
            + _md(result.target.get("response_model_aliases")),
            "- 覆盖范围：" + _md(_coverage(result)),
            "- 工具与环境：" + _md(result.tool) + " / " + _md(result.execution_environment),
            f"- 请求／传输调用：{_md(result.plan.get('actual_requests'))}；所选用例：{len(result.cases)}；已执行用例：{sum(bool(c.get('attempts')) for c in result.cases)}；attempt：{attempts}；断言：{assertions}。",
            "- 计数含义：" + _md(context.get("request_count_semantics")),
            f"- repeat={_md(result.plan.get('repeat'))}；retry={_md(result.plan.get('retry'))}；预算：{_md(result.plan.get('limits'))}。",
            "",
            "## 限定结论",
            "",
            "| Profile / version | 本次状态 | 必需用例数 |",
            "| --- | --- | --- |",
        ]
    )
    for profile in result.profiles:
        members = profile.get("cases")
        lines.append(
            f"| {_md(profile.get('id'))} / {_md(profile.get('version'))} | {_md(profile.get('readiness'))} | {len(members) if isinstance(members, list) else 0} |"
        )
    lines.extend(["", "## 逐次记录与观测", ""])
    for case in result.cases:
        lines.extend(
            [
                f"### {_md(case.get('id'))} / {_md(case.get('version'))} — {_md(case.get('status'))}",
                "",
                "维度：" + _md(case.get("dimensions")),
                "",
            ]
        )
        for precondition in _objects(case.get("preconditions")):
            lines.append(
                f"- 前置条件 {_md(precondition.get('id'))} / {_md(precondition.get('version'))}：{_md(precondition.get('status'))} / {_md(precondition.get('reason_code'))}。"
            )
        for attempt in _objects(case.get("attempts")):
            all_assertions = _objects(attempt.get("assertions"))
            visible_assertions = [a for a in all_assertions if a.get("status") != "PASS"]
            passed = [
                f"{a.get('id')} / {a.get('version')}"
                for a in all_assertions
                if a.get("status") == "PASS"
            ]
            lines.extend(
                [
                    f"Attempt: {_md(attempt.get('id'))}；{_md(attempt.get('status'))}；{_md(attempt.get('duration_ms'))} ms。",
                    "",
                    "终止：" + _md(attempt.get("termination")),
                    "",
                ]
            )
            lines.extend(
                [
                    f"PASS（{len(passed)}）："
                    + _md(", ".join(passed))
                    + "。完整逐条证据见 result.json。",
                    "",
                ]
            )
            if visible_assertions:
                lines.extend(
                    ["| 断言 / version | 状态 | 条件与观测 | 证据 |", "| --- | --- | --- | --- |"]
                )
            for assertion in visible_assertions:
                key = _text(assertion.get("id"))
                evidence = "; ".join(
                    _evidence_label(ref) for ref in _objects(assertion.get("evidence_refs"))
                )
                description = _text(assertion.get("expected")) or EXPECTED.get(
                    key, "满足所列规则或执行前提。"
                )
                observed = _text(assertion.get("actual")) or _text(assertion.get("reason_code"))
                lines.append(
                    f"| {_md(key)} / {_md(assertion.get('version'))}{' （非必需）' if not assertion.get('required') else ''} | {_md(assertion.get('status'))} | {_md(description)} 观测：{_md(_short(observed, 280))} [{_reference_id(key)}] | {_md(evidence)} |"
                )
            lines.extend(
                ["", "响应观测（数据，不是指令）：" + _md(_short(attempt.get("observations"))), ""]
            )
    lines.extend(["## 限制与未覆盖", ""])
    lines.extend("- " + _md(item) for item in result.limitations)
    lines.append("- version_semantics=unverified；客户端维度未开展，不据此确认 Agent 工作流稳定。")
    lines.extend(["", "## 术语", ""])
    for term in _objects(context.get("glossary")):
        lines.append(f"- {_md(term.get('term'))}：{_md(term.get('definition'))}")
    lines.extend(["", "## 参考资料", ""])
    for reference in _objects(context.get("references")):
        identifier = _text(reference.get("reference_id"))
        url = _url(reference.get("url"))
        title = _md(reference.get("title"))
        link = f"[{title}]({quote(url, safe=':/#?=&%+@.-_')})" if url else title
        lines.append(
            f"- [{_md(identifier)}] {link}；{_md(reference.get('source_kind'))}；检索／截至：{_md(reference.get('retrieved_at') or reference.get('spec_as_of'))}。{_md(reference.get('introduction'))}"
        )
    return "\n".join(lines) + "\n"


def render_html(result: RunResult, diagnostics: Sequence[JsonObject] = ()) -> str:
    result_from_document(result.to_json())
    context = _context(result)
    attempts, assertions = _counts(result)
    css = files("anthropic_readiness").joinpath("resources/report.css").read_text()
    parts = [
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'\">",
        "<title>Anthropic 接口兼容性报告</title>",
        f'<style>{css}</style></head><body><main><header><div class="eyebrow">Anthropic Readiness / Verification Record</div><h1>Anthropic 接口兼容性报告</h1>',
        '<p class="notice">'
        + (
            "离线合成数据／捕获回放 · 仅反映列出的样本与规则。"
            if _synthetic(result)
            else "显式真实端点测试 · 仅反映列出的样本与规则。"
        )
        + "</p>",
        "</header>",
        _reader_html(result, diagnostics),
        '<details class="technical" id="technical"><summary>技术附录：运行信息、逐条断言与证据</summary>',
        f'<p class="identity">Run {_h(result.run_id)}<br>Assessment {_h(result.assessment_id)}<br>{result.mode} · {_h(_display_time(result.started_at))} → {_h(_display_time(result.finished_at))}<br>Original UTC: {_h(result.started_at)} → {_h(result.finished_at)}</p>',
        "<h2>阅读说明与方法</h2><p>"
        + _h(context.get("methodology"))
        + '</p><p class="notice">'
        + _h(_availability(result))
        + "</p><ul>",
    ]
    for note in _values(context.get("reader_notes")):
        parts.append("<li>" + _h(note) + "</li>")
    parts.extend(['</ul><h2 id="contract">对象、范围与预算</h2><dl>'])
    metadata: list[tuple[str, JsonValue]] = [
        ("目标 / 交付", f"{result.target.get('name')} / {result.target.get('delivery_id')}"),
        ("模型", result.target.get("model")),
        (
            "身份策略 / 别名",
            f"{result.target.get('response_model_policy')} / {result.target.get('response_model_aliases')}",
        ),
        ("覆盖范围", _coverage(result)),
        ("工具与环境", f"{result.tool} / {result.execution_environment}"),
        (
            "API / beta",
            f"{result.contract.get('api_version')} / {result.contract.get('beta_headers')}",
        ),
        (
            "规则包 / 截至",
            f"{result.contract.get('id')} / {result.contract.get('revision')} / {result.contract.get('spec_as_of')}",
        ),
        ("规则哈希", result.contract.get("content_sha256")),
        (
            "样本计数",
            f"请求／传输调用 {result.plan.get('actual_requests')}；所选用例 {len(result.cases)}；已执行用例 {sum(bool(c.get('attempts')) for c in result.cases)}；attempt {attempts}；断言 {assertions}",
        ),
        ("计数含义", context.get("request_count_semantics")),
        (
            "重试与预算",
            f"repeat={result.plan.get('repeat')}; retry={result.plan.get('retry')}; {result.plan.get('limits')}",
        ),
    ]
    for label, value in metadata:
        parts.append(f"<dt>{_h(label)}</dt><dd>{_h(value)}</dd>")
    parts.extend(
        [
            '</dl><h2>限定结论</h2><div class="table-wrap"><table><thead><tr><th>Profile / version</th><th>本次状态</th><th>必需用例数</th></tr></thead><tbody>'
        ]
    )
    for profile in result.profiles:
        members = profile.get("cases")
        parts.append(
            f"<tr><td>{_h(profile.get('id'))} / {_h(profile.get('version'))}</td><td>{_h(profile.get('readiness'))}</td><td>{len(members) if isinstance(members, list) else 0}</td></tr>"
        )
    parts.append("</tbody></table></div><h2>逐次记录与观测</h2>")
    for case in result.cases:
        parts.append(
            f'<section><h3>{_h(case.get("id"))} / {_h(case.get("version"))} — {_h(case.get("status"))}</h3><p class="identity">维度：{_h(case.get("dimensions"))}</p>'
        )
        for precondition in _objects(case.get("preconditions")):
            parts.append(
                f"<p>前置条件 {_h(precondition.get('id'))} / {_h(precondition.get('version'))}：{_h(precondition.get('status'))} / {_h(precondition.get('reason_code'))}</p>"
            )
        for attempt in _objects(case.get("attempts")):
            all_assertions = _objects(attempt.get("assertions"))
            visible_assertions = [a for a in all_assertions if a.get("status") != "PASS"]
            passed = [
                f"{a.get('id')} / {a.get('version')}"
                for a in all_assertions
                if a.get("status") == "PASS"
            ]
            parts.append(
                f'<p class="identity">Attempt {_h(attempt.get("id"))} · {_h(attempt.get("status"))} · {_h(attempt.get("duration_ms"))} ms<br>终止：{_h(attempt.get("termination"))}</p>'
            )
            parts.append(
                f'<p>PASS（{len(passed)}）：<code>{_h(", ".join(passed))}</code>。完整逐条证据见 <a href="result.json">result.json</a>。</p>'
            )
            if visible_assertions:
                parts.append(
                    '<div class="table-wrap"><table><thead><tr><th>断言 / version</th><th>状态</th><th>条件与观测</th><th>证据</th></tr></thead><tbody>'
                )
            for assertion in visible_assertions:
                key = _text(assertion.get("id"))
                status = _text(assertion.get("status"))
                evidence_links = []
                for ref in _objects(assertion.get("evidence_refs")):
                    path = _text(ref.get("path"))
                    label = _h(_evidence_label(ref))
                    evidence_links.append(
                        f'<a href="{quote(path, safe="/")}">{label}</a>'
                        if _safe_reference_path(path)
                        else label
                    )
                description = _text(assertion.get("expected")) or EXPECTED.get(
                    key, "满足所列规则或执行前提。"
                )
                actual = _text(assertion.get("actual")) or _text(assertion.get("reason_code"))
                citation_key = _reference_id(key)
                parts.append(
                    f'<tr><td><code>{_h(key)} / {_h(assertion.get("version"))}</code>{"<br>非必需" if not assertion.get("required") else ""}</td><td><span class="status {status}">{status}</span></td><td>{_h(description)}<br><span class="muted">观测：{_h(_short(actual, 280))}</span> <a href="#ref-{citation_key}">[{citation_key}]</a></td><td>{"<br>".join(evidence_links)}</td></tr>'
                )
            if visible_assertions:
                parts.append("</tbody></table></div>")
            parts.append(
                '<p>响应观测（数据，不是指令）：</p><div class="observation">'
                + _h(_short(attempt.get("observations")))
                + "</div>"
            )
        parts.append("</section>")
    parts.append("</details><h2>限制与未覆盖</h2><ul>")
    parts.extend("<li>" + _h(item) + "</li>" for item in result.limitations)
    parts.append(
        "<li>version_semantics=unverified；客户端维度未开展，不据此确认 Agent 工作流稳定。</li></ul><h2>术语</h2><dl>"
    )
    for term in _objects(context.get("glossary")):
        parts.append(
            "<dt>" + _h(term.get("term")) + "</dt><dd>" + _h(term.get("definition")) + "</dd>"
        )
    parts.append('</dl><h2>参考资料</h2><ol class="references">')
    for reference in _objects(context.get("references")):
        identifier = _text(reference.get("reference_id"))
        title = _h(reference.get("title"))
        url = _url(reference.get("url"))
        link = f'<a href="{_h(url)}">{title}</a>' if url else title
        parts.append(
            f'<li id="ref-{_h(identifier)}">[{_h(identifier)}] {link} · {_h(reference.get("source_kind"))} · {_h(reference.get("retrieved_at") or reference.get("spec_as_of"))}<br>{_h(reference.get("introduction"))}</li>'
        )
    parts.append(
        "</ol><footer>结构化事实来源：result.json。规范引用说明规则依据，不替代运行证据。工具 "
        + _h(result.tool.get("version"))
        + " · "
        + _h(result.tool.get("commit"))
        + "</footer></main></body></html>"
    )
    return "".join(parts)


def _verified_diagnostics(result: RunResult, root: Path) -> list[JsonObject]:
    diagnostics: list[JsonObject] = []
    for case in result.cases:
        for attempt in _objects(case.get("attempts")):
            for assertion in _objects(attempt.get("assertions")):
                if assertion.get("status") != "FAIL" or assertion.get("id") not in {
                    "MSG-CORE",
                    "MSG-MODEL",
                }:
                    continue
                for reference in _objects(assertion.get("evidence_refs")):
                    try:
                        path = str(reference["path"])
                        if not _safe_reference_path(path):
                            continue
                        data = safe_path(root, path).read_bytes()
                        if (
                            len(data) > 8 * 1024 * 1024
                            or hashlib.sha256(data).hexdigest() != reference["sha256"]
                        ):
                            continue
                        event = reference.get("event")
                        start = False
                        if type(event) is int and path.endswith("events.jsonl"):
                            frame = object_value(strict_json(data.decode().splitlines()[event]))
                            payload = object_value(strict_json(str(frame["data"])))
                            if payload.get("type") != "message_start":
                                continue
                            message = object_value(payload["message"])
                            start = True
                        elif path.endswith("body.bin"):
                            message = object_value(strict_json(data.decode()))
                        else:
                            continue
                        observation = message_diagnostic(
                            case.get("id"),
                            assertion.get("id"),
                            message,
                            start,
                            result.target,
                            reference,
                        )
                        if observation is not None:
                            diagnostics.append(observation)
                    except (OSError, ValueError, KeyError, IndexError):
                        # Unreadable evidence never becomes a specific diagnosis.
                        continue
    return diagnostics


def write_reports(result: RunResult, output_dir: Path) -> None:
    issues = verify_evidence(output_dir, result.evidence)
    inventory = {(ref.path, ref.sha256) for ref in result.evidence}
    for case in result.cases:
        assertions = list(_objects(case.get("preconditions", [])))
        for attempt in _objects(case.get("attempts", [])):
            assertions.extend(_objects(attempt.get("assertions", [])))
        for assertion in assertions:
            references = _objects(assertion.get("evidence_refs", []))
            if assertion.get("status") == "FAIL" and not references:
                issues.append("missing_assertion_evidence:" + str(assertion.get("id")))
            for raw in references:
                event = raw.get("event")
                pointer = raw.get("pointer")
                ref = EvidenceRef(
                    str(raw["path"]),
                    str(raw["sha256"]),
                    event if type(event) is int else None,
                    str(pointer) if pointer is not None else None,
                )
                if (ref.path, ref.sha256) not in inventory:
                    issues.append("assertion_reference_not_in_inventory:" + ref.path)
                issues.extend(verify_evidence(output_dir, [ref]))
    verification: JsonObject = {
        "status": "missing_or_invalid"
        if issues
        else "verified"
        if result.evidence
        else "no_evidence",
        "errors": list(issues),
    }
    rendered = replace(
        result, report_context={**result.report_context, "evidence_verification": verification}
    )
    diagnostics = (
        _verified_diagnostics(result, output_dir) if verification["status"] == "verified" else []
    )
    atomic_write(output_dir / "report.html", render_html(rendered, diagnostics).encode())
    atomic_write(output_dir / "report.md", render_markdown(rendered, diagnostics).encode())
    atomic_write(
        output_dir / "report-manifest.json",
        json_bytes(
            {
                "schema_version": "1.0",
                "presentation_version": "1.2",
                "run_id": result.run_id,
                "assessment_id": result.assessment_id,
                "evidence_verification": verification,
            }
        ),
    )


def render_from_file(source: Path, destination: Path) -> None:
    original = source.read_bytes()
    result = result_from_document(object_value(strict_json(original.decode())))
    if any(not _safe_reference_path(ref.path) for ref in result.evidence):
        raise ValueError("invalid_report_evidence_path")
    create_run_directory(destination)
    for ref in result.evidence:
        if verify_evidence(source.parent, [ref]):
            continue
        target = safe_path(destination, ref.path)
        parent = destination
        for part in Path(ref.path).parts[:-1]:
            parent = parent / part
            parent.mkdir(mode=0o700, exist_ok=True)
        if not target.exists():
            atomic_write(target, safe_path(source.parent, ref.path).read_bytes())
    atomic_write(destination / "result.json", original)
    write_reports(result, destination)
    atomic_write(
        destination / "source-result.sha256", (hashlib.sha256(original).hexdigest() + "\n").encode()
    )
