"""Pure reader-facing explanations; recorded verdicts remain authoritative."""

import json
from collections.abc import Sequence

from anthropic_readiness.models import JsonObject, JsonValue, RunResult

CASE_NAMES = {
    "ANT-MESSAGE-001": "非流式问候",
    "ANT-TEXT-SSE-001": "流式问候",
    "ANT-TEXT-SSE-002": "流式计数 1 至 5",
    "ANT-TOOL-FORCED-001": "强制工具调用（Hanoi 天气）",
}
STATE_NAMES = {
    "PASS": "通过",
    "FAIL": "未通过",
    "BLOCKED": "环境阻塞",
    "INDETERMINATE": "证据不足",
    "SKIP": "跳过",
    "not_evaluated": "未评估",
}


def objects(value: JsonValue) -> list[JsonObject]:
    return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def case_name(case_id: JsonValue) -> str:
    return CASE_NAMES.get(str(case_id), str(case_id))


def state_name(state: JsonValue) -> str:
    return STATE_NAMES.get(str(state), str(state))


def overview(result: RunResult) -> tuple[str, str]:
    states = [p.get("readiness") for p in result.profiles]
    title = (
        "本次检查未通过"
        if "not_ready" in states
        else "本次已测项目通过"
        if states and all(s == "passed" for s in states)
        else "本次检查尚未完成"
    )
    executed = sum(bool(c.get("attempts")) for c in result.cases)
    dimensions = [c.get("dimensions") for c in result.cases]
    behavior = sum(isinstance(d, dict) and d.get("behavior") == "PASS" for d in dimensions)
    protocol = sum(isinstance(d, dict) and d.get("protocol") == "PASS" for d in dimensions)
    if (
        executed == len(result.cases)
        and executed > 0
        and behavior == executed
        and protocol < executed
        and "not_ready" in states
    ):
        title = "任务已完成，兼容检查未通过"
    return title, (
        f"已执行 {executed}/{len(result.cases)} 个用例；"
        f"任务行为通过 {behavior} 个，协议格式通过 {protocol} 个。"
        "两项分别统计，任务完成不等于协议全部符合。"
    )


def findings(result: RunResult, diagnostics: Sequence[JsonObject]) -> list[JsonObject]:
    groups: dict[tuple[str, str, str], JsonObject] = {}
    for case in result.cases:
        assertions = objects(case.get("preconditions")) + [
            a
            for attempt in objects(case.get("attempts"))
            for a in objects(attempt.get("assertions"))
        ]
        for assertion in assertions:
            if assertion.get("status") == "PASS" or not assertion.get("required"):
                continue
            key = str(assertion.get("id"))
            reason = str(assertion.get("reason_code"))
            identity = (key, reason, str(assertion.get("status")))
            if identity not in groups:
                title, impact, action = _explanation(key, reason)
                groups[identity] = {
                    "id": key,
                    "status": assertion.get("status"),
                    "category": assertion.get("category"),
                    "title": title,
                    "impact": impact,
                    "action": action,
                    "cases": [],
                    "observations": [],
                }
            group = groups[identity]
            members = group["cases"]
            assert isinstance(members, list)
            if case.get("id") not in members:
                members.append(case.get("id"))
            observations = group["observations"]
            assert isinstance(observations, list)
            for diagnostic in diagnostics:
                if (
                    diagnostic.get("case_id") == case.get("id")
                    and diagnostic.get("assertion_id") == key
                ):
                    observations.append(diagnostic)
    for index, group in enumerate(groups.values(), 1):
        group["number"] = f"F{index:02}"
        group["anchor"] = f"finding-{index}"
        group["kind"] = (
            "身份配置待确认"
            if group["id"] == "MSG-MODEL"
            else "执行条件"
            if group["category"] == "environment"
            else "任务行为"
            if group["category"] == "behavior"
            else "客户端约束"
            if group["category"] == "client"
            else "格式差异"
        )
        if group["id"] == "MSG-CORE" and objects(group.get("observations")):
            group["title"] = "停止字段不完整"
        if group["status"] != "FAIL":
            group["impact"] = "本项记录为" + state_name(group["status"]) + "，不能当作已完整通过。"
    return list(groups.values())


def finding_count(groups: Sequence[JsonObject]) -> str:
    affected: set[str] = set()
    for group in groups:
        members = group.get("cases")
        if isinstance(members, list):
            affected.update(str(case) for case in members)
    return f"{len(groups)} 类问题，涉及 {len(affected)} 个用例"


def _explanation(key: str, reason: str) -> tuple[str, str, str]:
    if key == "MSG-CORE":
        return (
            "消息结构不符合要求",
            "核心消息结构检查未通过。具体缺失字段只在证据可核验时列出；也可能存在其他结构问题。",
            "按下方证据核对消息字段与类型。字段缺失与显式 null 不相同；流式起始消息的停止字段应显式为 null。",
        )
    if key == "MSG-MODEL":
        return (
            "模型名称与配置不一致",
            "响应中的模型名未满足本次身份策略；这不代表模型路由错误，也不能证明实际模型权重。",
            "确认别名映射后，在新配置中显式加入允许的响应模型名，再另行评估；本轮失败记录保持不变。",
        )
    if reason == "duplicate_message_start":
        return (
            "流式消息重复开始",
            "记录显示同一响应中出现多次 message_start，违反消息生命周期约束。",
            "修复重复的 message_start，确保每条响应只开始一次，再进行复测。",
        )
    return (
        "需要核查的检查项：" + key,
        "具体原因见技术附录中的规则与观测。",
        "先核查证据和执行前提，再决定修复或复测；证据不足、阻塞和跳过不能按通过处理。",
    )


def message_diagnostic(
    case_id: JsonValue,
    assertion_id: JsonValue,
    message: JsonObject,
    streaming_start: bool,
    target: JsonObject,
    reference: JsonObject,
) -> JsonObject | None:
    if message.get("type") != "message":
        return None
    expected: str
    actual: str
    if assertion_id == "MSG-CORE":
        missing = [key for key in ("stop_reason", "stop_sequence") if key not in message]
        if not missing:
            return None
        expected = (
            "流式起始消息：stop_reason: null；stop_sequence: null"
            if streaming_start
            else "最终消息：stop_reason 为停止原因；stop_sequence 存在，无匹配序列时为 null"
        )
        actual = "字段缺失：" + "、".join(missing)
        expected_fields: JsonObject = (
            {"stop_reason": None, "stop_sequence": None}
            if streaming_start
            else {"stop_sequence": None}
            if "stop_sequence" in missing
            else {}
        )
        actual_fields: JsonObject = {
            key: message[key] for key in ("stop_reason", "stop_sequence") if key in message
        }
        expected_label = "应有字段（局部示意）"
    elif assertion_id == "MSG-MODEL":
        aliases = target.get("response_model_aliases")
        allowed = (
            "、".join(str(v) for v in aliases)
            if isinstance(aliases, list) and aliases
            else "未配置"
        )
        expected = f"请求模型：{target.get('model')}；允许别名：{allowed}"
        actual = f"响应模型：{message.get('model')}"
        expected_fields = {"requested_model": target.get("model"), "allowed_aliases": aliases}
        actual_fields = {"model": message.get("model")}
        expected_label = "本次身份配置（非请求正文）"
    else:
        return None
    return {
        "case_id": case_id,
        "assertion_id": assertion_id,
        "expected": expected,
        "actual": actual,
        "reference": reference,
        "source_label": "message_start.message" if streaming_start else "JSON 响应根对象",
        "expected_label": expected_label,
        "expected_excerpt": json.dumps(expected_fields, ensure_ascii=False, indent=2)
        if expected_fields
        else "",
        "actual_excerpt": json.dumps(actual_fields, ensure_ascii=False, indent=2),
    }
