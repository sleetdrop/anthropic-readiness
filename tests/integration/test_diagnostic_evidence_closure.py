"""Missing or misbound capture proof cannot establish a successful repair."""

import hashlib
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from anthropic_readiness.application import prepare_assessment
from anthropic_readiness.config import load_target
from anthropic_readiness.diagnostics.context import ContextObserver
from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.evidence import json_bytes
from anthropic_readiness.models import JsonObject, JsonValue, object_value, strict_json
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.runner import execute_run
from tests.acceptance.test_runner import FixtureTransport
from tests.diagnostic_fixtures import portable_archive


def execute(root: Path, *, failed: bool) -> Path:
    plan, context = prepare_assessment(
        load_target(Path("examples/target.yaml")).to_json(), ("anthropic-basic",)
    )
    observer = ContextObserver(
        root, context.document, DiskExecutionObserver(root / "operations", root)
    )
    execute_run(plan, FixtureTransport(fail_second=failed), root, observer=observer)
    observer.finalize()
    return root


def read_json(path: Path) -> JsonObject:
    return object_value(strict_json(path.read_text()))


def objects(value: JsonValue) -> list[JsonObject]:
    """Keep references while mutating an independently owned synthetic document."""
    assert isinstance(value, list)
    assert all(isinstance(item, dict) for item in value)
    return [item for item in value if isinstance(item, dict)]


def delivery_copy(original: Path, destination: Path, damage: str) -> Path:
    """Change owned synthetic copies; keep all enclosing result hashes coherent."""
    shutil.copytree(original, destination)
    shutil.rmtree(destination / "operations")
    document = read_json(destination / "result.json")
    case = objects(document["cases"])[1]
    attempt = objects(case["attempts"])[0]
    prefix = f"evidence/{case['id']}/{attempt['id']}/"
    inventory = objects(document["evidence"])
    assertions = [
        item
        for record in objects(document["cases"])
        for observed in objects(record["attempts"])
        for item in objects(observed["assertions"])
    ]
    if damage in {"body.bin", "events.jsonl", "response.json"}:
        missing = prefix + damage
        (destination / missing).unlink()
        document["evidence"] = [item for item in inventory if item["path"] != missing]
        for assertion in assertions:
            assertion["evidence_refs"] = [
                ref for ref in objects(assertion["evidence_refs"]) if ref["path"] != missing
            ]
    elif damage == "capture_manifest":
        relative = prefix + "response.json"
        metadata = read_json(destination / relative)
        next(item for item in objects(metadata["files"]) if item["path"] == "body.bin")[
            "sha256"
        ] = "0" * 64
        data = json_bytes(metadata)
        (destination / relative).write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        for ref in [
            *inventory,
            *(ref for item in assertions for ref in objects(item["evidence_refs"])),
        ]:
            if ref["path"] == relative:
                ref["sha256"] = digest
    else:
        assertion = next(
            item for item in objects(attempt["assertions"]) if item["id"] == "MSG-CORE"
        )
        assert assertion["status"] == "PASS"
        assertion["evidence_refs"] = (
            []
            if damage == "pass_reference"
            else [next(ref for ref in inventory if str(ref["path"]).endswith("body.bin"))]
        )
    result_bytes = json_bytes(document)
    (destination / "result.json").write_bytes(result_bytes)
    final_path = destination / "assessment-context-verification.json"
    final = read_json(final_path)
    final["result_sha256"] = hashlib.sha256(result_bytes).hexdigest()
    final_path.write_bytes(json_bytes(final))
    return destination


@pytest.mark.parametrize(
    "damage",
    [
        "body.bin",
        "events.jsonl",
        "response.json",
        "capture_manifest",
        "pass_reference",
        "foreign_reference",
    ],
)
def test_incomplete_or_misbound_proof_cannot_claim_recovery(tmp_path: Path, damage: str) -> None:
    before = execute(tmp_path / "before", failed=True)
    after = execute(tmp_path / "after", failed=False)
    damaged = delivery_copy(after, tmp_path / "damaged", damage)
    original = {
        path.relative_to(damaged): path.read_bytes()
        for path in damaged.rglob("*")
        if path.is_file()
    }
    service = DiagnosticService(tmp_path / "data")
    facts = service.source_facts(damaged)
    assert object_value(facts["evidence_verification"])["status"] == "missing_or_invalid"
    eligibility = object_value(facts["eligibility"])
    assert eligibility["read"] is True
    assert eligibility["retest"] is eligibility["compare"] is False
    reasons = eligibility["reasons"]
    assert isinstance(reasons, list)
    assert "diagnostic_evidence_unavailable" in reasons
    comparison = service.compare_sources(before, damaged).document
    assert comparison["comparable"] is False
    assert comparison["all_previous_failures_passed"] is False
    with pytest.raises(ValueError, match="export_evidence_invalid"):
        service.export(damaged, tmp_path / "invalid.zip", include_evidence=True)

    # Assemble an untrusted envelope independently of the guarded product exporter.
    archive, _ = portable_archive(tmp_path / "delivery", source_dir=damaged)
    now = datetime.now(UTC)
    preview = service.preview(archive, "owner", now=now)
    baseline = service.commit(str(preview["preview_id"]), "owner", now=now)
    imported = service.store.root / str(baseline.document["artifact_root"])
    for record in (
        preview,
        baseline.document,
        service.get(str(baseline.document["id"])).document,
        service.source_facts(imported),
    ):
        permissions = object_value(record["eligibility"])
        assert permissions["read"] is True
        assert permissions["retest"] is permissions["compare"] is False
    assert (
        service.compare(str(baseline.document["id"]), after).document[
            "all_previous_failures_passed"
        ]
        is False
    )
    assert original == {
        path.relative_to(damaged): path.read_bytes()
        for path in damaged.rglob("*")
        if path.is_file()
    }


def test_complete_response_proof_can_establish_recovery(tmp_path: Path) -> None:
    before = execute(tmp_path / "before", failed=True)
    after = execute(tmp_path / "after", failed=False)
    service = DiagnosticService(tmp_path / "data")
    comparison = service.compare_sources(before, after).document
    assert comparison["comparable"] is True
    assert comparison["all_previous_failures_passed"] is True
