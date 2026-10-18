"""Render validated report projections using immutable packaged presentation assets."""

from __future__ import annotations

import base64
import hashlib
import html
import json
import re
from importlib.resources import files
from string import Template
from urllib.parse import quote, urlsplit

from anthropic_readiness.models import JsonObject, JsonValue, object_value
from anthropic_readiness.report_models import ReportView
from anthropic_readiness.report_reading import finding_count, state_name
from anthropic_readiness.report_view import DIMENSIONS, STATES, objects

_RESOURCES = files("anthropic_readiness").joinpath("resources")
_TEMPLATE = Template(_RESOURCES.joinpath("report-v2.html").read_text())
_STYLES = _RESOURCES.joinpath("report-v2.css").read_text()
_SCRIPT = _RESOURCES.joinpath("report-v2.js").read_text()
COLORS = {
    "PASS": "#567c68",
    "FAIL": "#ad5549",
    "INDETERMINATE": "#b2853c",
    "BLOCKED": "#7a718d",
    "SKIP": "#87928c",
    "pending": "#bac2bb",
    "running": "#58788f",
    "not_evaluated": "#cdd2cd",
}
LABELS = {
    "behavior": "任务行为",
    "protocol": "协议格式",
    "environment": "执行条件",
    "client": "客户端",
    "pending": "待评估",
    "running": "执行中",
}


def text(value: JsonValue) -> str:
    return "—" if value is None else str(value)


def h(value: JsonValue) -> str:
    return html.escape(text(value), quote=True)


def md(value: JsonValue) -> str:
    escaped = html.escape(text(value), quote=False).replace("\\", "\\\\")
    return re.sub(r"([`*\[\]()#_!|])", r"\\\1", escaped).replace("\r", "").replace("\n", " / ")


def values(value: JsonValue) -> list[JsonValue]:
    return value if isinstance(value, list) else []


def status(value: JsonValue) -> str:
    state = str(value)
    label = LABELS.get(state, state_name(state))
    return f'<span class="status {h(state)}">{h(label)} · {h(state)}</span>'


def pretty(value: JsonValue) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)


def code_excerpt(value: JsonValue) -> str:
    encoded = str(value)
    for character in ("&", "<", ">", "~", "|"):
        encoded = encoded.replace(character, f"\\u{ord(character):04x}")
    return encoded


def safe_url(value: JsonValue) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme == "https" and parsed.netloc else None
    except ValueError:
        return None


def evidence_notice(document: JsonObject) -> str:
    quality = object_value(document["evidence_verification"])
    if quality.get("delivery") == "omitted":
        return (
            "生成时已在本机核对来源证据；本导出未附证据文件，接收者无法独立复核。"
            if quality["status"] == "verified"
            else "本导出未附证据文件，且来源证据未完整核验；无法独立复核。"
        )
    if quality.get("delivery") == "external_files":
        return "生成时已核对来源证据；HTML 不内嵌捕获，请与完整 ZIP 内的清单及证据一起复核。单独转发本文件无法独立复核。"
    return (
        "随附证据的路径、哈希与引用已核验；这不是独立的服务复测。"
        if quality["status"] == "verified"
        else "证据未完整核验，未提取字段级说明；无法独立复核。未附可核验的字段摘录。"
    )


def matrix(document: JsonObject) -> str:
    rows: list[str] = []
    cases = {str(case["case_id"]): case for case in objects(document["cases"])}
    for group in objects(document["groups"]):
        dimensions = object_value(group["dimensions"])
        attention = any(
            int(str(count)) > 0
            for dimension in DIMENSIONS
            if dimension != "client"
            for key, count in object_value(dimensions[dimension]).items()
            if key not in {"PASS", "not_evaluated"}
        )
        members = values(group["case_ids"])
        links = " · ".join(
            f'<a data-open-detail href="#case-{h(case_id)}">{h(case_id)}</a>' for case_id in members
        )
        cells = []
        for dimension in DIMENSIONS:
            cell = object_value(dimensions[dimension])
            actions: list[str] = []
            for state in STATES:
                if cell[state] == 0:
                    continue
                matching = [
                    str(member)
                    for member in members
                    if object_value(cases[str(member)]["dimensions"])[dimension] == state
                ]
                label = f"{status(state)} <strong>{h(cell[state])}</strong>"
                identifier = f"matrix-{group['key']}-{dimension}-{state}"
                if len(matching) == 1:
                    actions.append(
                        f'<a class="matrix-link" id="{h(identifier)}" href="#case-{h(matching[0])}" data-open-detail>{label}</a>'
                    )
                elif matching:
                    member_links = "".join(
                        f'<li><a class="matrix-link" id="{h(identifier)}-{h(member)}" href="#case-{h(member)}" data-open-detail>{h(cases[member]["name"])}<small>{h(member)}</small></a></li>'
                        for member in matching
                    )
                    actions.append(
                        f'<details class="matrix-members" id="{h(identifier)}"><summary class="matrix-summary" id="{h(identifier)}-summary">{label}</summary><ul>{member_links}</ul></details>'
                    )
                else:
                    actions.append(f"<span>{label}</span>")
            cells.append('<td><div class="matrix-counts">' + "".join(actions) + "</div></td>")
        rows.append(
            f'<tr data-capability-row data-attention="{str(attention).lower()}"><th scope="row">{h(group["name"])}<br><small>{len(members)} 个用例</small><div class="source-ref">{links}</div></th>{"".join(cells)}</tr>'
        )
    headings = "".join(f'<th scope="col">{h(LABELS[key])}</th>' for key in DIMENSIONS)
    return (
        '<div class="table-scroll" role="region" aria-label="能力矩阵，可横向滚动" tabindex="0"><table class="capability-matrix"><caption>每格按原用例维度统计；混合状态逐项保留。多用例计数可展开对应成员；窄窗口可横向滚动。</caption><thead><tr><th scope="col">测试能力 / 样本范围</th>'
        + headings
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def chart(figure: JsonObject) -> str:
    kind = figure["kind"]
    rows = [row for row in values(figure["rows"]) if isinstance(row, list)]
    title_id = "svg-" + str(figure["id"])
    if kind == "timeline":
        spans = [row for row in rows if row[2] == "case"] or rows
        maximum = max(
            (float(str(row[4] if row[4] is not None else row[3])) for row in spans), default=0
        )
        shapes = []
        for index, row in enumerate(spans):
            start = float(str(row[3]))
            end = float(str(row[4])) if row[4] is not None else start
            x = 172 + (start / maximum * 330 if maximum else 0)
            width = (end - start) / maximum * 330 if maximum else 0
            y = 28 + index * 40
            ongoing = row[4] is None
            marker = (
                f'<circle data-ongoing="true" cx="{x:.3f}" cy="{y + 9.5}" r="4" fill="#58788f"/>'
                if ongoing
                else ""
            )
            label = "进行中（未闭合）" if ongoing else f"{end:.1f} ms"
            shapes.append(
                f'<text x="0" y="{y + 15}">{h(row[0])}</text><rect x="{x:.3f}" y="{y}" width="{width:.3f}" height="19" rx="2" fill="#58788f"/>{marker}<text class="axis-label" x="{x + width + 7:.3f}" y="{y + 14}">{h(label)}</text>'
            )
        shapes.append(
            f'<text class="axis-label" x="172" y="{len(spans) * 40 + 44}">0 → {maximum:.1f} ms · 用例区间；各阶段见数据表</text>'
        )
        height = max(95, len(spans) * 40 + 60)
    else:
        selected = [row for row in rows if kind != "distribution" or row[1] != 0]
        labels = [
            (
                text(row[1])
                if kind == "impact"
                else LABELS.get(text(row[0]), state_name(row[0]))
                if kind == "distribution"
                else text(row[0])
            )
            for row in selected
        ]
        numbers = [
            float(str(row[2] if kind == "impact" else row[1]))
            if (row[2] if kind == "impact" else row[1]) is not None
            else None
            for row in selected
        ]
        maximum = max((number for number in numbers if number is not None), default=0)
        shapes = []
        for index, (row, label, number) in enumerate(zip(selected, labels, numbers, strict=True)):
            y = 24 + index * 42
            width = number / maximum * 350 if number is not None and maximum else 0
            color = COLORS.get(str(row[0]), "#58788f")
            short_label = label if len(label) <= 22 else label[:21] + "…"
            value_label = (
                f"{number:.1f}"
                if kind == "duration" and number is not None
                else text(row[2] if kind == "impact" else row[1])
            )
            shapes.append(
                f'<text x="0" y="{y + 15}"><title>{h(label)}</title>{h(short_label)}</text><rect x="190" y="{y}" width="{width:.3f}" height="19" rx="2" fill="{color}"/><text x="{548}" y="{y + 15}">{h(value_label)}</text>'
            )
        if not selected:
            shapes.append('<text x="0" y="30">未记录需要关注的问题</text>')
        height = max(75, len(selected) * 42 + 22)
    return f'<svg role="img" aria-labelledby="{h(title_id)}" viewBox="0 0 650 {height}" xmlns="http://www.w3.org/2000/svg"><title id="{h(title_id)}">{h(figure["title"])}；单位 {h(figure["unit"])}</title>{"".join(shapes)}</svg>'


def figure_html(figure: JsonObject, document: JsonObject) -> str:
    rows = "".join(
        "<tr>" + "".join(f"<td>{h(value)}</td>" for value in row) + "</tr>"
        for row in values(figure["rows"])
        if isinstance(row, list)
    )
    columns = "".join(f'<th scope="col">{h(column)}</th>' for column in values(figure["columns"]))
    visual = matrix(document) if figure["kind"] == "matrix" else chart(figure)
    return f'<figure class="figure" id="{h(figure["id"])}"><h3>{h(figure["title"])}</h3>{visual}<figcaption>{h(figure["caption"])} <span>单位：{h(figure["unit"])} · {h(figure["id"])}</span></figcaption><details class="figure-data"><summary>查看等价数据表</summary><div class="table-scroll"><table data-figure="{h(figure["id"])}"><caption>{h(figure["title"])} / {h(figure["unit"])}</caption><thead><tr>{columns}</tr></thead><tbody>{rows}</tbody></table></div></details></figure>'


def observations_html(group: JsonObject) -> str:
    observations = objects(group["observations"])
    if not observations:
        return '<p class="muted">未附可核验的字段摘录；按原始断言记录展示，未重新判定。</p>'
    parts = []
    seen: set[str] = set()
    for observation in observations:
        identity = pretty(
            {
                key: observation.get(key)
                for key in ("expected_excerpt", "actual_excerpt", "source_label")
            }
        )
        if identity in seen:
            continue
        seen.add(identity)
        reference = object_value(observation["reference"])
        source = (
            "SSE 事件 " + str(reference["event"])
            if reference.get("event") is not None
            else "JSON 响应"
        )
        parts.append(
            f'<div class="comparison"><div><small>{h(observation.get("expected_label", "应有字段（局部示意）"))}</small><p>{h(observation["expected"])}</p><pre>{h(observation["expected_excerpt"])}</pre></div><div><small>实际字段摘录（局部字段）</small><p>{h(observation["actual"])}</p><pre>{h(observation["actual_excerpt"])}</pre></div></div><p class="source-ref">{h(source)} · {h(observation["source_label"])} · {h(reference["path"])} · SHA-256 {h(reference["sha256"])}</p>'
        )
    return "".join(parts)


def findings_html(document: JsonObject) -> str:
    groups = objects(document["findings"])
    parts = [
        f'<section class="section" id="findings"><h2>问题与证据</h2><p class="muted">{h(finding_count(groups))}。影响数按不同用例统计；同一用例可以涉及多项问题。</p>'
    ]
    for group in groups:
        links = " · ".join(
            f'<a data-open-detail href="#case-{h(case_id)}">{h(case_id)}</a>'
            for case_id in values(group["cases"])
        )
        parts.append(
            f'<article class="finding" id="{h(group["anchor"])}"><div class="finding-top"><a class="finding-number" href="#{h(group["anchor"])}">{h(group["number"])}</a><h3>{h(group["title"])}</h3><small>{h(group["kind"])} · {h(group["affected_cases"])} 个用例</small></div><p>原断言：{h(group["status"])} · <code>{h(group["assertion_id"])}</code> · {h(group["reason_code"])}</p><p>{h(group["impact"])}</p>{observations_html(group)}<p><strong>下一步</strong> {h(group["action"])}</p><p class="source-ref">涉及用例：{links}</p></article>'
        )
    if not groups:
        parts.append("<p>未记录需要关注的问题；结论仍受本次范围与证据质量约束。</p>")
    return "".join(parts) + "</section>"


def case_assertions(case: JsonObject) -> list[JsonObject]:
    return objects(case["preconditions"]) + [
        assertion
        for attempt in objects(case["attempts"])
        for assertion in objects(attempt["assertions"])
    ]


def appendix_html(document: JsonObject) -> str:
    provenance = object_value(document["provenance"])
    summary = object_value(document["summary"])
    context = object_value(provenance["report_context"])
    cases = objects(document["cases"])
    assertion_count = sum(len(case_assertions(case)) for case in cases)
    body = [
        f'<section class="section" id="appendix"><h2>技术附录</h2><p class="source-ref">Run: {h(document["run_id"])} · Assessment: {h(provenance["assessment_id"])}<br>Source SHA-256: {h(document["source_result_sha256"])}</p><p>请求／传输调用 {h(summary["actual_requests"])} · 已执行用例：{h(summary["executed_cases"])} · 断言：{assertion_count}</p><h3>阅读说明与方法</h3><p>{h(context.get("methodology", "固定请求、确定性黑盒断言；原始状态保持不变。"))}</p>'
    ]
    for note in values(context.get("reader_notes")):
        body.append(f'<p class="muted">{h(note)}</p>')
    body.append(
        '<details class="technical"><summary>契约、配置与采集环境</summary><pre>'
        + h(pretty(provenance))
        + "</pre></details>"
    )
    for case in cases:
        assertions = "".join(
            f'<tr><th scope="row">{h(assertion["id"])} / v{h(assertion["version"])}</th><td>{status(assertion["status"])}</td><td>{h(assertion["reason_code"])}<br>{h(assertion["expected"])}<br>{h(assertion["actual"])}</td><td class="source-ref">{h(pretty(assertion["evidence_refs"]))}</td></tr>'
            for assertion in case_assertions(case)
        )
        body.append(
            f'<details class="technical case-detail" id="case-{h(case["case_id"])}" tabindex="-1"><summary>{h(case["name"])} · {h(case["case_id"])} · {h(case["status"])}</summary><div class="table-scroll"><table><caption>原始断言与证据引用，未重新判定</caption><thead><tr><th>断言 / 版本</th><th>状态</th><th>条件与观测</th><th>证据</th></tr></thead><tbody>{assertions}</tbody></table></div><pre>{h(pretty({"attempts": case["attempts"], "preconditions": case["preconditions"]}))}</pre></details>'
        )
    body.append(
        "<h3>限制与未覆盖</h3><ul>"
        + "".join(f"<li>{h(value)}</li>" for value in values(document["limitations"]))
        + "</ul><h3>术语</h3><dl>"
    )
    for term in objects(context.get("glossary")):
        body.append(f"<dt>{h(term['term'])}</dt><dd>{h(term['definition'])}</dd>")
    return "".join(body) + "</dl></section>"


def report_origin(document: JsonObject) -> str:
    context = object_value(object_value(document["provenance"])["report_context"])
    kind = context.get("data_kind")
    if document["mode"] == "replay" or kind in ("synthetic", "synthetic_or_user_capture"):
        return "离线合成数据／捕获回放"
    if kind == "live_endpoint":
        return "显式真实端点测试"
    return "来源信息未完整记录"


def render_report_body(view: ReportView) -> str:
    document = view.document
    identity = object_value(document["identity"])
    summary = object_value(document["summary"])
    origin = report_origin(document)
    quality = object_value(document["evidence_verification"])
    groups = objects(document["findings"])
    metrics = [
        (f"{summary['completed_cases']} / {summary['planned_cases']}", "完成评估 / 计划用例"),
        (summary["actual_requests"], "实际请求 / 传输调用"),
        (len(groups), "归并后的问题类型"),
        (
            "—"
            if summary["duration_ms"] is None
            else f"{float(str(summary['duration_ms'])) / 1000:.2f} s",
            "执行耗时",
        ),
    ]
    metric_html = "".join(
        f'<div class="metric"><strong>{h(number)}</strong><span>{h(label)}</span></div>'
        for number, label in metrics
    )
    parts = [
        f'<section class="section" id="overview"><span class="eyebrow">先看结论 · {h(origin)} · {"部分记录" if document["status"] == "partial" else "最终结果"}</span><h1>{h(summary["title"])}</h1><p class="lead">{h(summary["description"])}</p><h2>运行摘要</h2><div class="meta-strip"><span>{h(identity["target_name"])}</span><span>请求模型 {h(identity["model"])}</span><span>API {h(identity["api_version"])}</span><span>规则 {h(identity["contract_revision"])}</span><span>beta：{h(", ".join(str(beta) for beta in values(identity["betas"])) or "无")}</span><span>{h(summary["started_at"])}</span></div><p class="notice {"verified" if quality["status"] == "verified" else ""}">{h(evidence_notice(document))}</p><div class="metrics">{metric_html}</div><p class="muted">{h(finding_count(groups))}。客户端工作流未测试；所有结论仅对应本次固定规则与样本。</p><noscript>交互脚本未启用；完整结论、图表、等价数据表与检查明细仍可阅读。</noscript></section>'
    ]
    figures = objects(document["figures"])
    parts.append(
        '<section class="section" id="capabilities"><div class="section-header"><h2>能力矩阵与分布</h2><label class="js-controls" hidden>能力筛选 <select data-capability-filter><option value="all">全部能力</option><option value="attention">仅需关注</option></select></label></div>'
    )
    parts.append(figure_html(figures[0], document))
    parts.append(
        '<div class="chart-grid">'
        + "".join(figure_html(figure, document) for figure in figures[1:3])
        + "</div>"
        + figure_html(figures[3], document)
        + "</section>"
    )
    parts.append(findings_html(document))
    case_rows = []
    for case in objects(document["cases"]):
        dimensions = object_value(case["dimensions"])
        links = " ".join(
            f'<a href="#{h(finding_id)}">{h(next((group["number"] for group in groups if group["id"] == finding_id), finding_id))}</a>'
            for finding_id in values(case["finding_ids"])
        )
        case_rows.append(
            f'<tr><th scope="row"><a href="#case-{h(case["case_id"])}" data-open-detail>{h(case["name"])}</a></th><td>{status(case["status"])}</td><td>{status(dimensions["behavior"])}</td><td>{status(dimensions["protocol"])}</td><td>{links or "—"}</td></tr>'
        )
    parts.append(
        '<section class="section" id="cases"><h2>用例结果</h2><div class="table-scroll"><table><thead><tr><th>任务</th><th>整体判定</th><th>任务行为</th><th>协议格式</th><th>相关问题</th></tr></thead><tbody>'
        + "".join(case_rows)
        + "</tbody></table></div></section>"
    )
    parts.append(appendix_html(document))
    parts.append(
        '<section class="section" id="references"><h2>参考资料</h2><p class="muted">规范引用说明检查依据，不能代替本次证据。检索日期属于规则快照；阅读报告不会联网更新。</p><ol class="reference-list">'
    )
    for reference in objects(document["references"]):
        url = safe_url(reference["url"])
        link = (
            f'<a href="{h(url)}" rel="noreferrer noopener">{h(reference["title"])}</a>'
            if url
            else h(reference["title"])
        )
        parts.append(
            f'<li id="ref-{h(reference["id"])}">[{h(reference["id"])}] {link} · {h(reference["checked_at"])}<br>{h(reference["scope"])}</li>'
        )
    return "".join(parts) + "</ol></section>"


def render_report_html(view: ReportView) -> str:
    script_block = _TEMPLATE.template.split('<script type="module">', 1)[1].split("</script>", 1)[0]
    script_block = script_block.replace("$script", _SCRIPT)
    digest = base64.b64encode(hashlib.sha256(script_block.encode()).digest()).decode()
    policy = (
        "default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-"
        + digest
        + "'; base-uri 'none'; form-action 'none'"
    )
    data = (
        json.dumps(view.document, ensure_ascii=False, allow_nan=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    return _TEMPLATE.substitute(
        title=h(object_value(view.document["summary"])["title"]),
        policy=h(policy),
        styles=_STYLES,
        body=render_report_body(view),
        data=data,
        script=_SCRIPT,
    )


def render_report_markdown(view: ReportView) -> str:
    document = view.document
    summary = object_value(document["summary"])
    identity = object_value(document["identity"])
    provenance = object_value(document["provenance"])
    context = object_value(provenance["report_context"])
    origin = report_origin(document)
    groups = objects(document["findings"])
    lines = [
        "# Anthropic 接口兼容性报告",
        "",
        f"**{origin}**",
        "",
        "## 先看结论",
        "",
        md(summary["title"]),
        "",
        md(summary["description"]),
        "",
        evidence_notice(document),
        "",
        "## 运行摘要",
        "",
        f"{md(identity['target_name'])} · 请求模型 {md(identity['model'])} · API {md(identity['api_version'])} · 规则 {md(identity['contract_revision'])}",
        "",
        finding_count(groups),
        "",
        "客户端工作流未测试；原始判定保持不变。",
        "",
        "## 图表与能力矩阵",
        "",
    ]
    for figure in objects(document["figures"]):
        columns = values(figure["columns"])
        lines.extend(
            [
                f"### {md(figure['title'])} / {figure['id']}",
                "",
                md(figure["caption"]),
                "",
                f"单位：{figure['unit']}",
                "",
                "| " + " | ".join(md(value) for value in columns) + " |",
                "| " + " | ".join("---" for _ in columns) + " |",
            ]
        )
        lines.extend(
            "| " + " | ".join(md(value) for value in row) + " |"
            for row in values(figure["rows"])
            if isinstance(row, list)
        )
        lines.append("")
    lines.extend(["## 问题与证据", ""])
    for group in groups:
        lines.extend(
            [
                f"### {group['number']} · {md(group['title'])}",
                "",
                f"{md(group['kind'])} · {group['affected_cases']} 个用例 · 原断言：{group['status']} · {md(group['assertion_id'])} / {md(group['reason_code'])}",
                "",
                md(group["impact"]),
                "",
                md(group["action"]),
                "",
            ]
        )
        observations = objects(group["observations"])
        if not observations:
            lines.append("未附可核验的字段摘录；未重新判定。")
        for observation in observations:
            reference = object_value(observation["reference"])
            lines.extend(
                [
                    md(observation["expected"]),
                    "",
                    md(observation["actual"]),
                    "",
                    md(observation["expected_label"]),
                    "",
                    "~~~json",
                    code_excerpt(observation["expected_excerpt"]),
                    "~~~",
                    "",
                    "实际字段摘录（局部字段）",
                    "",
                    "~~~json",
                    code_excerpt(observation["actual_excerpt"]),
                    "~~~",
                    "",
                    md(reference["path"]) + " · SHA-256 " + str(reference["sha256"]),
                    "",
                ]
            )
    lines.extend(
        ["## 用例结果", "", "| 任务 | 整体 | 任务行为 | 协议格式 |", "| --- | --- | --- | --- |"]
    )
    for case in objects(document["cases"]):
        dimensions = object_value(case["dimensions"])
        lines.append(
            f"| {md(case['name'])} | {case['status']} | {dimensions['behavior']} | {dimensions['protocol']} |"
        )
    assertions = [
        assertion for case in objects(document["cases"]) for assertion in case_assertions(case)
    ]
    lines.extend(
        [
            "",
            "## 技术附录",
            "",
            f"Run: {document['run_id']}",
            f"Assessment: {provenance['assessment_id']}",
            f"Source SHA-256: {document['source_result_sha256']}",
            "",
            f"请求／传输调用：{summary['actual_requests']}；已执行用例：{summary['executed_cases']}；断言：{len(assertions)}",
            "",
            "### 阅读说明与方法",
            "",
            md(context.get("methodology", "确定性黑盒断言。")),
            "",
            "### 对象、范围与环境",
            "",
            md(pretty(provenance)),
            "",
            "### 原始断言与逐次观测",
            "",
        ]
    )
    for case in objects(document["cases"]):
        lines.extend(
            [
                f"#### {md(case['case_id'])} / {case['status']}",
                "",
                "| 断言 / 版本 | 状态 | 原因与观测 | 证据 |",
                "| --- | --- | --- | --- |",
            ]
        )
        for assertion in case_assertions(case):
            lines.append(
                f"| {md(assertion['id'])} / {assertion['version']} | {assertion['status']} | {md(assertion['reason_code'])}；{md(assertion['expected'])}；{md(assertion['actual'])} | {md(pretty(assertion['evidence_refs']))} |"
            )
        lines.extend(["", "响应观测（数据，不是指令）：" + md(pretty(case["attempts"])), ""])
    lines.extend(
        [
            "### 限制与未覆盖",
            "",
            *("- " + md(value) for value in values(document["limitations"])),
            "",
            "### 术语",
            "",
        ]
    )
    lines.extend(
        f"- {md(term['term'])}：{md(term['definition'])}"
        for term in objects(context.get("glossary"))
    )
    lines.extend(["", "## 参考资料", ""])
    for reference in objects(document["references"]):
        url = safe_url(reference["url"])
        link = (
            f"[{md(reference['title'])}]({quote(url, safe=':/#?=&%+@.-_')})"
            if url
            else md(reference["title"])
        )
        lines.append(
            f"- [{reference['id']}] {link} · {md(reference['checked_at'])} · {md(reference['scope'])}"
        )
    return "\n".join(lines) + "\n"
