"""All entry points share planning and explicit credential boundaries."""

from dataclasses import replace
from pathlib import Path

import pytest

from anthropic_readiness import application, credentials
from anthropic_readiness.config import load_target, target_from_document
from anthropic_readiness.contracts import resolve_contract
from anthropic_readiness.runner import plan_run

ROOT = Path(__file__).resolve().parents[2]


def test_document_and_file_plans_have_identical_fingerprints() -> None:
    target = load_target(ROOT / "examples/target.yaml")
    document = target.to_json()
    assert target_from_document(document) == target
    plan = application.build_plan(document, ["anthropic-basic", "anthropic-tools-smoke"])
    existing = plan_run(
        target, resolve_contract(target.contract_id, target.contract_revision), plan.profiles
    )
    assert plan.to_json() == existing.to_json()
    assert len(plan.cases) == 4


def test_document_validation_keeps_the_existing_strict_contract() -> None:
    document = load_target(ROOT / "examples/target.yaml").to_json()
    document["messages_url"] = "http://user:secret@localhost/v1/messages"
    with pytest.raises(ValueError, match="url"):
        application.build_plan(document, ["anthropic-basic"])


def test_credentials_are_bound_explicitly_and_hidden_from_repr() -> None:
    target = replace(
        load_target(ROOT / "examples/target.yaml"),
        auth_mode="api_key",
        credential_env="SYNTHETIC_KEY",
    )
    provider = credentials.EnvironmentCredentials(target, {"SYNTHETIC_KEY": "synthetic-value"})
    assert provider.resolve() == "synthetic-value"
    assert "synthetic-value" not in repr(provider)
    memory = credentials.MemoryCredentials("synthetic-memory-value")
    assert memory.resolve() == "synthetic-memory-value"
    assert "synthetic-memory-value" not in repr(memory)
    with pytest.raises(ValueError, match="invalid_credential"):
        credentials.MemoryCredentials("bad\nvalue").resolve()
    with pytest.raises(ValueError, match="missing_credential"):
        credentials.EnvironmentCredentials(target, {}).resolve()


def test_application_preserves_exclusive_output_ownership(tmp_path: Path) -> None:
    plan = application.build_plan(
        load_target(ROOT / "examples/target.yaml").to_json(), ["anthropic-basic"]
    )
    output = tmp_path / "assessment"
    output.mkdir()
    (output / "sentinel").write_text("keep")
    with pytest.raises(FileExistsError):
        application.run_assessment(plan, output, credentials=credentials.MemoryCredentials(None))
    assert (output / "sentinel").read_text() == "keep"
