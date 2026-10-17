"""Deterministic visual projection of recorded assessment facts."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime

from anthropic_readiness.models import JsonObject, JsonValue, object_value
from anthropic_readiness.report_models import ReportSource, ReportView
from anthropic_readiness.report_reading import case_findings, case_name, overview

STATES = ("PASS", "FAIL", "INDETERMINATE", "BLOCKED", "SKIP", "pending", "running", "not_evaluated")
DIMENSIONS = ("behavior", "protocol", "environment", "client")
GROUPS = (
    ("message", "基础消息", ("ANT-MESSAGE-001",)),
    ("streaming", "流式消息", ("ANT-TEXT-SSE-001", "ANT-TEXT-SSE-002")),
    ("forced_tool", "强制工具选择（非完整工具闭环）", ("ANT-TOOL-FORCED-001",)),
)


def counts(values: list[str]) -> JsonObject:
    return {state: values.count(state) for state in STATES}


def figure(
    identifier: str,
    kind: str,
    title: str,
    caption: str,
    unit: str,
    columns: list[JsonValue],
    rows: list[JsonValue],
) -> JsonObject:
    return {
        "id": identifier,
        "kind": kind,
        "title": title,
        "caption": caption,
        "unit": unit,
        "columns": columns,
        "rows": rows,
    }


def duration(start: str, end: str) -> float | None:
    try:
        elapsed = (
            datetime.fromisoformat(end) - datetime.fromisoformat(start)
        ).total_seconds() * 1000
        return elapsed if elapsed >= 0 else None
    except (ValueError, TypeError):
        return None


def build_report_view(source: ReportSource) -> ReportView:
    result, execution = source.result, source.execution
    if result is None and execution is None:
        raise ValueError("report_source_unavailable")
    target = (
        result.target
        if result is not None
        else object_value(execution["target"])
        if execution
        else {}
    )
    contract = (
        result.contract
        if result is not None
        else object_value(execution["contract"])
        if execution
        else {}
    )
    records = {str(case["id"]): case for case in source.case_records}
    groups = case_findings(source.case_records, source.diagnostics)
    for group in groups:
        group["affected_cases"] = (
            len({str(value) for value in group["cases"]}) if isinstance(group["cases"], list) else 0
        )
        group["id"] = group["anchor"]
    states = (
        {str(item["case_id"]): str(item["state"]) for item in objects(execution["case_states"])}
        if execution
        else {}
    )
    cases: list[JsonObject] = []
    for definition in objects(source.plan["cases"]):
        case_id = str(definition["id"])
        record = records.get(case_id)
        state = str(record["status"]) if record else states.get(case_id, "pending")
        # A missing verified checkpoint cannot certify an operational completion.
        if record is None and state not in {"pending", "running"}:
            state = "pending"
        attempts = deepcopy(objects(record["attempts"])) if record else []
        cases.append(
            {
                "case_id": case_id,
                "name": case_name(case_id),
                "required": definition["required"],
                "status": state,
                "dimensions": deepcopy(record["dimensions"])
                if record
                else dict.fromkeys(DIMENSIONS, state),
                "finding_ids": [
                    group["id"]
                    for group in groups
                    if isinstance(group["cases"], list) and case_id in group["cases"]
                ],
                "attempts": list(attempts),
                "preconditions": deepcopy(record["preconditions"]) if record else [],
                "duration_ms": sum(float(str(attempt["duration_ms"])) for attempt in attempts)
                if attempts
                else None,
            }
        )
    capabilities: list[JsonObject] = []
    known = {case_id for _, _, ids in GROUPS for case_id in ids}
    definitions = (
        *GROUPS,
        (
            "other",
            "其他已记录用例",
            tuple(str(case["case_id"]) for case in cases if case["case_id"] not in known),
        ),
    )
    for key, name, ids in definitions:
        members = [case for case in cases if case["case_id"] in ids]
        if members:
            capabilities.append(
                {
                    "key": key,
                    "name": name,
                    "case_ids": [case["case_id"] for case in members],
                    "dimensions": {
                        dimension: counts(
                            [str(object_value(case["dimensions"])[dimension]) for case in members]
                        )
                        for dimension in DIMENSIONS
                    },
                }
            )
    matrix_rows: list[JsonValue] = []
    for group in capabilities:
        for dimension in DIMENSIONS:
            cell = object_value(object_value(group["dimensions"])[dimension])
            for state in STATES:
                matrix_rows.append([group["key"], dimension, state, cell[state]])
    summary_counts = counts([str(case["status"]) for case in cases])
    title, description = (
        overview(result)
        if result is not None
        else (
            "本次检查尚未完成（部分记录）",
            "仅展示已核验的用例检查点；待执行与执行中均不代表兼容性通过。",
        )
    )
    started = result.started_at if result else execution["started_at"] if execution else None
    finished = result.finished_at if result else execution["finished_at"] if execution else None
    elapsed = (
        duration(result.started_at, result.finished_at)
        if result
        else execution["elapsed_ms"]
        if execution
        else None
    )
    timing_rows: list[JsonValue]
    if execution is not None and objects(execution["spans"]):
        timing = figure(
            "fig-timing",
            "timeline",
            "已记录的执行时间线",
            "毫秒，自执行开始计时；保留真实间隔，空结束值表示未闭合。等待响应头不等同于 TCP 已连接；接收活动不等同于首 token。",
            "ms",
            ["case_id", "attempt_id", "phase", "start_ms", "end_ms"],
            [
                [
                    span["case_id"],
                    span["attempt_id"],
                    span["phase"],
                    span["start_ms"],
                    span["end_ms"],
                ]
                for span in objects(execution["spans"])
            ],
        )
    else:
        timing_rows = [[case["case_id"], case["duration_ms"]] for case in cases]
        timing = figure(
            "fig-timing",
            "duration",
            "用例耗时对照",
            "仅比较各用例已记录的尝试耗时之和；未记录执行时序，不能据此重建开始时间、间隔或并行关系。空值表示无可用耗时。",
            "ms",
            ["case_id", "duration_ms"],
            timing_rows,
        )
    limitations = (
        list(result.limitations)
        if result
        else ["部分执行记录，不是 schema-valid 最终结果，也不是完整兼容性结论。"]
    )
    limitations.extend(
        [
            "仅覆盖所选有限用例，未重新判定原断言；任务完成不等于协议全部符合。",
            "客户端工作流未测试；强制工具选择不等于完整工具闭环。",
            "API 版本标头和规则快照固定，不证明端点严格区分不同协议版本；没有实测依据时不提供客户端锁版本保证。",
        ]
    )
    if source.evidence_verification["status"] != "verified":
        limitations.append("证据未完整核验，未提取字段级说明；未附可核验的字段摘录，无法独立复核。")
    for warning in source.diagnostics:
        if warning.get("kind") == "source_warning":
            limitations.append(
                "来源诊断："
                + str(warning["code"])
                + "；相关记录不可用，未用于重建时间线或最终结论。"
            )
    if execution:
        warnings = execution["warnings"]
        assert isinstance(warnings, list)
        limitations.extend(
            "执行记录警告：" + str(value) for value in warnings if isinstance(value, str)
        )
    references: list[JsonValue] = []
    for reference in objects(contract.get("sources")):
        if str(reference.get("url", "")).startswith("https://"):
            references.append(
                {
                    "id": reference["id"],
                    "title": "WHATWG Server-sent events"
                    if reference["id"] == "sse"
                    else "Anthropic " + str(reference["id"]),
                    "url": reference["url"],
                    "checked_at": reference.get("retrieved_at"),
                    "scope": reference.get("summary"),
                }
            )
    profiles: list[JsonValue] = [deepcopy(profile) for profile in result.profiles] if result else []
    document: JsonObject = {
        "schema_version": "1.0",
        "presentation_version": "2.0",
        "run_id": result.run_id if result else execution["run_id"] if execution else "",
        "mode": result.mode if result else "live",
        "status": "complete" if result else "partial",
        "source_result_sha256": source.result_sha256,
        "provenance": {
            "assessment_id": result.assessment_id if result else None,
            "source_run_id": result.source_run_id if result else None,
            "tool": deepcopy(result.tool) if result else {},
            "execution_environment": deepcopy(result.execution_environment) if result else {},
            "contract": deepcopy(contract),
            "target": deepcopy(target),
            "profiles": profiles,
            "report_context": deepcopy(result.report_context) if result else {},
        },
        "identity": {
            "target_name": target["name"],
            "model": target["model"],
            "api_version": contract["api_version"],
            "betas": contract.get("beta_headers", []),
            "contract_id": contract["id"],
            "contract_revision": contract["revision"],
        },
        "summary": {
            "title": title,
            "description": description,
            "planned_cases": len(cases),
            "executed_cases": sum(bool(case["attempts"]) for case in cases),
            "completed_cases": len(source.case_records),
            "actual_requests": source.plan["actual_requests"]
            if result
            else execution["actual_requests"]
            if execution
            else 0,
            "request_cap": object_value(source.plan["limits"])["max_requests"],
            "duration_ms": elapsed,
            "started_at": started,
            "finished_at": finished,
            "counts": summary_counts,
        },
        "cases": list(cases),
        "groups": list(capabilities),
        "findings": list(groups),
        "figures": [
            figure(
                "fig-capabilities",
                "matrix",
                "能力与检查维度",
                f"按用例统计；总范围 {len(cases)} 个用例。每格保留全部状态计数，客户端维度尚未评估。",
                "cases",
                ["group", "dimension", "state", "count"],
                matrix_rows,
            ),
            figure(
                "fig-status",
                "distribution",
                "用例状态分布",
                f"分母为计划中的 {len(cases)} 个用例；执行状态与兼容判定分别保留。",
                "cases",
                ["state", "count"],
                [[state, summary_counts[state]] for state in STATES],
            ),
            figure(
                "fig-impact",
                "impact",
                "问题影响范围",
                "每项为不同受影响用例数；问题之间可以重叠，不能相加推断失败用例总数。排序表示覆盖范围，不推断严重程度。",
                "distinct_cases",
                ["finding_id", "title", "affected_cases"],
                [
                    [group["id"], group["title"], group["affected_cases"]]
                    for group in sorted(groups, key=lambda item: -int(str(item["affected_cases"])))
                ],
            ),
            timing,
        ],
        "evidence_verification": deepcopy(source.evidence_verification),
        "limitations": list(dict.fromkeys(limitations)),
        "references": references,
        "execution": deepcopy(execution),
    }
    return ReportView(document)


def objects(value: JsonValue) -> list[JsonObject]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []
