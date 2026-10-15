"""Only an exact, integrity-checked shipped contract can be selected."""

from dataclasses import replace
from pathlib import Path

import pytest

from anthropic_readiness.config import load_target
from anthropic_readiness.contracts import (
    resolve_contract,
    validate_bundle,
    validate_target_contract,
)

ID = "anthropic-messages-2023-06-01-core"


def test_unknown_bundle_rejected_before_transport() -> None:
    with pytest.raises(ValueError, match="unsupported_contract"):
        resolve_contract(ID, "latest")


def test_bundle_tamper_rejected() -> None:
    bundle = resolve_contract(ID, "1.0.0")
    changed = {**bundle.manifest, "revision": "tampered"}
    with pytest.raises(ValueError, match="integrity"):
        validate_bundle(changed, {})


def test_beta_mismatch_rejected() -> None:
    target = load_target(Path("examples/target.yaml"))
    bundle = resolve_contract(ID, "1.0.0")
    with pytest.raises(ValueError, match="contract_mismatch"):
        validate_target_contract(replace(target, beta_headers=("synthetic-beta",)), bundle)
    with pytest.raises(ValueError, match="contract_mismatch"):
        validate_target_contract(replace(target, api_version="2099-01-01"), bundle)


def test_resources_independent_of_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    bundle = resolve_contract(ID, "1.0.0")
    assert bundle.spec.api_version == "2023-06-01"
    assert len(bundle.content_sha256) == 64
