"""Resolve immutable, packaged data; never fetch rules at runtime."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib.resources import files
from pathlib import PurePosixPath

from anthropic_readiness.config import TargetConfig, fingerprint, string, strings
from anthropic_readiness.models import ContractSpec, JsonObject, object_value, strict_json
from anthropic_readiness.requirements import SUPPORTED as SUPPORTED
from anthropic_readiness.schema import load_schema, validate_document


@dataclass(frozen=True)
class ContractBundle:
    spec: ContractSpec
    manifest: JsonObject
    content_sha256: str


def validate_bundle(manifest: JsonObject, resources: dict[str, bytes]) -> None:
    expected = manifest.get("content_sha256")
    unsigned = {key: val for key, val in manifest.items() if key != "content_sha256"}
    if fingerprint(unsigned) != expected:
        raise ValueError("contract_integrity:manifest")
    validate_document(manifest, load_schema("contract"))
    entries = manifest["resources"]
    if not isinstance(entries, list):
        raise ValueError("contract_integrity:resources")
    seen: set[str] = set()
    for item in entries:
        ref = object_value(item)
        path = string(ref["path"])
        if (
            path in seen
            or PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
            or "\\" in path
        ):
            raise ValueError("contract_integrity:path")
        seen.add(path)
        if path not in resources or hashlib.sha256(resources[path]).hexdigest() != ref["sha256"]:
            raise ValueError("contract_integrity:resource")
    if set(resources) != seen:
        raise ValueError("contract_integrity:inventory")
    rules = manifest["rules"]
    if not isinstance(rules, list) or any(
        object_value(rule).get("implementation")
        not in {"message-core-v1", "stream-core-v1", "case-behavior-v1", "sse-framing-v1"}
        for rule in rules
    ):
        raise ValueError("unsupported_rule_implementation")


def resolve_contract(contract_id: str, revision: str) -> ContractBundle:
    if (contract_id, revision) not in SUPPORTED:
        raise ValueError(f"unsupported_contract:{contract_id}/{revision}")
    root = files("anthropic_readiness").joinpath(f"resources/contracts/{contract_id}/{revision}")
    manifest = object_value(strict_json(root.joinpath("manifest.json").read_text()))
    resources = {
        p.name: p.read_bytes() for p in root.iterdir() if p.is_file() and p.name != "manifest.json"
    }
    validate_bundle(manifest, resources)
    return ContractBundle(
        ContractSpec(
            string(manifest["id"]),
            string(manifest["revision"]),
            string(manifest["api_version"]),
            strings(manifest["beta_headers"]),
        ),
        manifest,
        string(manifest["content_sha256"]),
    )


def validate_target_contract(target: TargetConfig, bundle: ContractBundle) -> None:
    if (target.contract_id, target.contract_revision, target.api_version, target.beta_headers) != (
        bundle.spec.id,
        bundle.spec.revision,
        bundle.spec.api_version,
        bundle.spec.beta_headers,
    ):
        raise ValueError("contract_mismatch")
