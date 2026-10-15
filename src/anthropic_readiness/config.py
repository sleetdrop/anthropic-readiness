"""Strict local target loading; credentials are injected only at execution."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit

import yaml
from yaml.nodes import MappingNode

from anthropic_readiness.models import JsonObject, JsonValue, object_value
from anthropic_readiness.schema import load_schema, validate_document


class UniqueLoader(yaml.SafeLoader):
    """Safe YAML with duplicate (including merged) keys rejected."""


def _mapping(loader: UniqueLoader, node: MappingNode) -> dict[str, object]:
    loader.flatten_mapping(node)
    values: dict[str, object] = {}
    for key_node, value_node in node.value:
        key: object = loader.construct_object(key_node)
        if not isinstance(key, str):
            raise ValueError("yaml_key_must_be_string")
        if key in values:
            raise ValueError(f"duplicate_yaml_key:{key}")
        values[key] = loader.construct_object(value_node)
    return values


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def canonical_bytes(value: JsonValue) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()


def fingerprint(value: JsonValue) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def string(value: JsonValue) -> str:
    if not isinstance(value, str):
        raise ValueError("expected_string")
    return value


def strings(value: JsonValue) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError("expected_array")
    return tuple(string(item) for item in value)


def _number(value: JsonValue) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError("invalid_limit")
    return float(value)


def _positive_int(value: JsonValue) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError("invalid_integer_limit")
    return value


@dataclass(frozen=True)
class Limits:
    connect_timeout_s: float = 5
    read_timeout_s: float = 30
    attempt_timeout_s: float = 90
    run_timeout_s: float = 300
    max_response_bytes: int = 4194304
    max_event_bytes: int = 262144
    max_events: int = 10000
    max_requests: int = 4
    max_tokens: int = 512

    def to_json(self) -> JsonObject:
        return object_value(asdict(self))


@dataclass(frozen=True)
class TargetConfig:
    name: str
    delivery_id: str
    messages_url: str
    model: str
    api_version: str
    beta_headers: tuple[str, ...]
    contract_id: str
    contract_revision: str
    auth_mode: str
    credential_env: str | None
    capabilities: tuple[tuple[str, bool], ...]
    response_model_policy: str
    response_model_aliases: tuple[str, ...]
    limits: Limits

    def credential(self, environment: Mapping[str, str]) -> str | None:
        if self.auth_mode == "none":
            return None
        value = environment.get(self.credential_env or "")
        if not value or not value.strip():
            raise ValueError("missing_credential")
        if "\r" in value or "\n" in value:
            raise ValueError("invalid_credential")
        return value

    def supports(self, capability: str) -> bool:
        return dict(self.capabilities).get(capability, False)

    def to_json(self) -> JsonObject:
        return {
            "schema_version": "1.0",
            "name": self.name,
            "delivery_id": self.delivery_id,
            "protocol": "anthropic.messages",
            "messages_url": self.messages_url,
            "model": self.model,
            "api_version": self.api_version,
            "beta_headers": list(self.beta_headers),
            "protocol_contract": {"id": self.contract_id, "revision": self.contract_revision},
            "auth": {
                "mode": self.auth_mode,
                **({"credential_env": self.credential_env} if self.credential_env else {}),
            },
            "capabilities": dict(self.capabilities),
            "response_model_policy": self.response_model_policy,
            "response_model_aliases": list(self.response_model_aliases),
            "limits": self.limits.to_json(),
        }

    def fingerprint(self, contract_hash: str) -> str:
        value = self.to_json()
        value.pop("delivery_id")
        value["contract_sha256"] = contract_hash
        return fingerprint(value)


def load_target(path: Path) -> TargetConfig:
    try:
        raw: object = yaml.load(path.read_text(), Loader=UniqueLoader)
        value = object_value(raw)
    except (yaml.YAMLError, RecursionError) as exc:
        raise ValueError("invalid_yaml") from exc
    validate_document(value, load_schema("target"))
    url = string(value["messages_url"])
    try:
        parsed = urlsplit(url)
        _ = parsed.port
        valid = (
            parsed.scheme in {"http", "https"}
            and parsed.hostname
            and not parsed.username
            and not parsed.password
            and not any(c in url for c in "?#")
            and not any(c.isspace() or ord(c) < 32 for c in url)
        )
    except ValueError as exc:
        raise ValueError("invalid_url") from exc
    if not valid:
        raise ValueError("invalid_url")
    if not string(value["model"]).strip():
        raise ValueError("empty_model")
    lim = object_value(value["limits"])
    limits = Limits(
        connect_timeout_s=_number(lim.get("connect_timeout_s", 5)),
        read_timeout_s=_number(lim.get("read_timeout_s", 30)),
        attempt_timeout_s=_number(lim.get("attempt_timeout_s", 90)),
        run_timeout_s=_number(lim.get("run_timeout_s", 300)),
        max_response_bytes=_positive_int(lim.get("max_response_bytes", 4194304)),
        max_event_bytes=_positive_int(lim.get("max_event_bytes", 262144)),
        max_events=_positive_int(lim.get("max_events", 10000)),
        max_requests=_positive_int(lim.get("max_requests", 4)),
        max_tokens=_positive_int(lim.get("max_tokens", 512)),
    )
    auth = object_value(value["auth"])
    contract = object_value(value["protocol_contract"])
    caps = object_value(value["capabilities"])
    return TargetConfig(
        string(value["name"]),
        string(value["delivery_id"]),
        url,
        string(value["model"]),
        string(value["api_version"]),
        tuple(sorted(set(strings(value["beta_headers"])))),
        string(contract["id"]),
        string(contract["revision"]),
        string(auth["mode"]),
        string(auth["credential_env"]) if "credential_env" in auth else None,
        tuple((key, val) for key, val in sorted(caps.items()) if isinstance(val, bool)),
        string(value["response_model_policy"]),
        tuple(sorted(set(strings(value["response_model_aliases"])))),
        limits,
    )
