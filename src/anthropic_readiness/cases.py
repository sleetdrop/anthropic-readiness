"""Four fixed requests; selection never removes unsupported required cases."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

from anthropic_readiness.config import TargetConfig
from anthropic_readiness.models import CaseContract, ContractSpec, JsonObject, RequestSpec

PROFILES = ("anthropic-basic", "anthropic-tools-smoke")


@dataclass(frozen=True)
class CaseDefinition:
    id: str
    streaming: bool
    behavior: str
    prompt: str
    profiles: tuple[str, ...]
    capabilities: tuple[str, ...] = ()
    version: int = 1

    @property
    def contract(self) -> CaseContract:
        return CaseContract(self.id, behavior=self.behavior)

    def contract_for(self, target: TargetConfig, spec: ContractSpec) -> CaseContract:
        return replace(
            self.contract,
            model=target.model,
            model_policy=target.response_model_policy,
            aliases=target.response_model_aliases,
            spec=spec,
        )

    def available(self, target: TargetConfig) -> bool:
        return all(target.supports(capability) for capability in self.capabilities)


_CASES = (
    CaseDefinition(
        "ANT-MESSAGE-001",
        False,
        "greeting",
        "Say hello in one short sentence.",
        ("anthropic-basic",),
    ),
    CaseDefinition(
        "ANT-TEXT-SSE-001",
        True,
        "greeting",
        "Say hello in one short sentence.",
        ("anthropic-basic",),
        ("streaming",),
    ),
    CaseDefinition(
        "ANT-TEXT-SSE-002",
        True,
        "count",
        "Count from 1 to 5, using digits.",
        ("anthropic-basic",),
        ("streaming",),
    ),
    CaseDefinition(
        "ANT-TOOL-FORCED-001",
        False,
        "tool",
        "Use get_weather to check the weather in Hanoi.",
        ("anthropic-tools-smoke",),
        ("tools",),
    ),
)


def list_cases() -> tuple[CaseDefinition, ...]:
    return _CASES


def select_cases(profile_ids: Sequence[str]) -> tuple[CaseDefinition, ...]:
    if not profile_ids or any(profile not in PROFILES for profile in profile_ids):
        raise ValueError("unsupported_profile")
    return tuple(
        case for case in _CASES if any(profile in case.profiles for profile in profile_ids)
    )


def build_request(case: CaseDefinition, target: TargetConfig) -> RequestSpec:
    headers = [
        ("content-type", "application/json"),
        ("accept", "text/event-stream" if case.streaming else "application/json"),
        ("anthropic-version", target.api_version),
    ]
    if target.beta_headers:
        headers.append(("anthropic-beta", ",".join(target.beta_headers)))
    body: JsonObject = {
        "model": target.model,
        "max_tokens": min(512, target.limits.max_tokens),
        "stream": case.streaming,
        "messages": [{"role": "user", "content": case.prompt}],
    }
    if case.behavior == "tool":
        body["tools"] = [
            {"name": case.contract.tool_name, "input_schema": case.contract.input_schema}
        ]
        body["tool_choice"] = {"type": "tool", "name": case.contract.tool_name}
    return RequestSpec(target.messages_url, tuple(headers), body, case.streaming)
