"""Contradictory derived facts cannot enter source views or imported baselines."""

import hashlib
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from anthropic_readiness.config import load_target
from anthropic_readiness.contracts import resolve_contract
from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.evidence import json_bytes
from anthropic_readiness.models import AssertionResult, Status, object_value, strict_json
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.report_sources import load_report_source
from anthropic_readiness.runner import execute_run, plan_run
from anthropic_readiness.schema import result_from_document
from tests.acceptance.test_runner import FixtureTransport
from tests.diagnostic_fixtures import portable_archive, rewrite_archive


@pytest.mark.parametrize(
    "damage",
    [
        "protocol",
        "behavior",
        "client",
        "environment",
        "missing_dimension",
        "empty_dimensions",
        "zero_requests",
        "extra_requests",
        "captured_zero",
    ],
)
def test_inconsistent_derived_facts_are_rejected_everywhere(tmp_path: Path, damage: str) -> None:
    archive, source = portable_archive(tmp_path / "delivery")
    original = (source / "result.json").read_bytes()
    document = object_value(strict_json(original.decode()))
    cases = objects(document["cases"])
    case = cases[1]
    assert case["dimensions"] == {
        "protocol": "FAIL",
        "behavior": "PASS",
        "client": "not_evaluated",
        "environment": "PASS",
    }
    if damage == "captured_zero":
        attempts = objects(case["attempts"])
        attempts[0]["actual_requests"] = 0
        attempts[0]["status"] = "INDETERMINATE"
        attempts[0]["assertions"] = [
            AssertionResult(
                "EXECUTION-COMPLETE", "environment", Status.INDETERMINATE, "internal_error"
            ).to_json()
        ]
        case["attempts"] = list(attempts)
        case["status"] = "INDETERMINATE"
        case["dimensions"] = {
            "protocol": "not_evaluated",
            "behavior": "not_evaluated",
            "client": "not_evaluated",
            "environment": "INDETERMINATE",
        }
        plan = object_value(document["plan"])
        plan["actual_requests"] = int(str(plan["actual_requests"])) - 1
        document["plan"] = plan
        profiles = objects(document["profiles"])
        next(row for row in profiles if row["id"] == "anthropic-basic")["readiness"] = "incomplete"
        document["profiles"] = list(profiles)
    elif damage.endswith("requests"):
        count = 0 if damage == "zero_requests" else 2
        total = 0
        for row in cases:
            attempts = objects(row["attempts"])
            for attempt in attempts:
                attempt["actual_requests"] = count
                total += count
            row["attempts"] = list(attempts)
        document["plan"] = {**object_value(document["plan"]), "actual_requests": total}
    else:
        dimensions = object_value(case["dimensions"])
        if damage == "missing_dimension":
            dimensions.pop("protocol")
        elif damage == "empty_dimensions":
            dimensions = {}
        else:
            dimensions[damage] = "FAIL" if damage in {"behavior", "environment"} else "PASS"
        case["dimensions"] = dimensions
    document["cases"] = list(cases)
    changed = json_bytes(document)
    result_digest = hashlib.sha256(changed).hexdigest()
    expected = (
        "live_attempt_request_count"
        if damage.endswith("requests") or damage == "captured_zero"
        else "case_dimensions"
    )

    def mutate(files: dict[str, bytes]) -> None:
        files["result.json"] = changed
        final = object_value(strict_json(files["assessment-context-verification.json"].decode()))
        final["result_sha256"] = result_digest
        files["assessment-context-verification.json"] = json_bytes(final)
        marker = object_value(strict_json(files["diagnostic-package.json"].decode()))
        marker["source"] = {**object_value(marker["source"]), "result_sha256": result_digest}
        files["diagnostic-package.json"] = json_bytes(marker)
        manifest = object_value(strict_json(files["manifest.json"].decode()))
        manifest["source_result_sha256"] = result_digest
        files["manifest.json"] = json_bytes(manifest)

    rewrite_archive(archive, mutate)
    damaged = tmp_path / "damaged"
    shutil.copytree(source, damaged, ignore=shutil.ignore_patterns("operations"))
    (damaged / "result.json").write_bytes(changed)
    final_path = damaged / "assessment-context-verification.json"
    final = object_value(strict_json(final_path.read_text()))
    final["result_sha256"] = result_digest
    final_path.write_bytes(json_bytes(final))
    archive_bytes = archive.read_bytes()
    with pytest.raises(ValueError, match=expected):
        result_from_document(document)
    with pytest.raises(ValueError, match=expected):
        load_report_source(damaged)
    service = DiagnosticService(tmp_path / "service")
    with pytest.raises(ValueError, match=expected):
        service.export(damaged, tmp_path / "invalid.zip", include_evidence=True)
    with pytest.raises(ValueError, match=expected):
        service.preview(archive, "owner", now=datetime.now(UTC))
    assert service.store.stored_baselines() == ()
    assert archive.read_bytes() == archive_bytes
    assert (source / "result.json").read_bytes() == original
    assert (damaged / "result.json").read_bytes() == changed


def test_internal_failure_before_send_retains_zero_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from anthropic_readiness.cases import CaseDefinition, build_request
    from anthropic_readiness.config import TargetConfig
    from anthropic_readiness.models import RequestSpec

    def cannot_build(case: CaseDefinition, target: TargetConfig) -> RequestSpec:
        monkeypatch.setattr("anthropic_readiness.runner.build_request", build_request)
        raise ValueError("synthetic_before_send")

    monkeypatch.setattr("anthropic_readiness.runner.build_request", cannot_build)
    target = load_target(Path("examples/target.yaml"))
    plan = plan_run(
        target, resolve_contract(target.contract_id, target.contract_revision), ["anthropic-basic"]
    )
    transport = FixtureTransport()
    result = execute_run(plan, transport, tmp_path / "source")
    assert result.plan["actual_requests"] == 0
    assert transport.calls == 0
    assert result_from_document(result.to_json()).plan["actual_requests"] == 0
    assert result.cases[0]["status"] == "INDETERMINATE"
