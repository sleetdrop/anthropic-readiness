"""Versioned, offline reader context and source citations."""

from importlib.resources import files

from anthropic_readiness.models import JsonObject, JsonValue, object_value, strict_json

TITLES = {
    "versioning": "Anthropic API versioning",
    "messages": "Anthropic Messages API",
    "streaming": "Anthropic streaming messages",
    "sse": "WHATWG Server-sent events",
    "stop-reasons": "Anthropic stop reasons",
}


def build_report_context(contract: JsonObject, mode: str) -> JsonObject:
    template = object_value(
        strict_json(
            files("anthropic_readiness").joinpath("resources/report-context.json").read_text()
        )
    )
    references: list[JsonValue] = []
    sources = contract.get("sources")
    rules = contract.get("rules")
    for source in sources if isinstance(sources, list) else []:
        if not isinstance(source, dict):
            continue
        source_id = str(source["id"])
        related: list[JsonValue] = []
        for rule in rules if isinstance(rules, list) else []:
            if isinstance(rule, dict):
                source_ids = rule.get("source_ids")
                if isinstance(source_ids, list) and source_id in source_ids:
                    related.append(rule.get("id"))
        references.append(
            {
                "reference_id": source_id,
                "title": TITLES.get(source_id, source_id),
                "url": source["url"],
                "retrieved_at": source.get("retrieved_at"),
                "source_kind": "standard" if source_id == "sse" else "official_documentation",
                "rule_ids": related,
                "introduction": source.get("summary", ""),
            }
        )
    references.append(
        {
            "reference_id": "contract",
            "title": f"{contract.get('id')} / {contract.get('revision')}",
            "url": "#contract",
            "spec_as_of": contract.get("spec_as_of"),
            "source_kind": "test_contract",
            "rule_ids": [rule.get("id") for rule in rules if isinstance(rule, dict)]
            if isinstance(rules, list)
            else [],
            "introduction": "本工具维护的有限测试子集；不是官方兼容性认证。",
        }
    )
    return {
        **template,
        "references": references,
        "data_kind": "synthetic_or_user_capture" if mode == "replay" else "live_endpoint",
        "request_count_semantics": "Initiated transport calls; no retries.",
        "client": "not_evaluated",
    }
