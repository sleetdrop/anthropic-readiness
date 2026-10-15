"""Versioned case selection fixes request count, prompts and capabilities."""

from dataclasses import replace
from pathlib import Path

import pytest

from anthropic_readiness.cases import build_request, list_cases, select_cases
from anthropic_readiness.config import load_target


def test_exact_case_set_and_profile_deduplication() -> None:
    assert [case.id for case in list_cases()] == [
        "ANT-MESSAGE-001",
        "ANT-TEXT-SSE-001",
        "ANT-TEXT-SSE-002",
        "ANT-TOOL-FORCED-001",
    ]
    assert len(select_cases(["anthropic-basic"])) == 3
    assert len(select_cases(["anthropic-basic", "anthropic-tools-smoke", "anthropic-basic"])) == 4
    assert all(case.version == 1 for case in list_cases())


@pytest.mark.parametrize(
    "profile",
    ["claude-code-basic", "tool-loop", "optional-thinking", "optional-parallel", "unknown"],
)
def test_unimplemented_profile_rejected(profile: str) -> None:
    with pytest.raises(ValueError, match="unsupported_profile"):
        select_cases([profile])


def test_prompts_budget_and_exact_headers() -> None:
    target = load_target(Path("examples/target.yaml"))
    target = replace(
        target,
        limits=replace(target.limits, max_tokens=21),
        beta_headers=("synthetic-a", "synthetic-b"),
    )
    requests = [build_request(case, target) for case in list_cases()]
    assert [r.body["messages"] for r in requests] == [
        [{"role": "user", "content": text}]
        for text in [
            "Say hello in one short sentence.",
            "Say hello in one short sentence.",
            "Count from 1 to 5, using digits.",
            "Use get_weather to check the weather in Hanoi.",
        ]
    ]
    assert all(r.body["max_tokens"] == 21 for r in requests)
    assert all(dict(r.headers)["anthropic-version"] == "2023-06-01" for r in requests)
    assert all(dict(r.headers)["anthropic-beta"] == "synthetic-a,synthetic-b" for r in requests)
    assert all("x-api-key" not in dict(r.headers) for r in requests)
    assert requests[-1].body["tool_choice"] == {"type": "tool", "name": "get_weather"}
    assert [r.streaming for r in requests] == [False, True, True, False]


def test_selected_unsupported_capability_stays_in_plan() -> None:
    target = load_target(Path("examples/target.yaml"))
    target = replace(target, capabilities=(("streaming", False), ("tools", False)))
    selected = select_cases(["anthropic-basic", "anthropic-tools-smoke"])
    assert len(selected) == 4
    assert [c.id for c in selected if not c.available(target)] == [
        "ANT-TEXT-SSE-001",
        "ANT-TEXT-SSE-002",
        "ANT-TOOL-FORCED-001",
    ]
