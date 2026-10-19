"""CLI/Web share verified source facts without trusting uploaded presentation."""

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from anthropic_readiness.diagnostics.contracts import validate_diagnostic
from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.models import object_value
from tests.diagnostic_fixtures import portable_archive


def test_compare_owned_baseline_and_local_source_without_mutation(tmp_path: Path) -> None:
    archive, before_root = portable_archive(tmp_path / "before")
    _, after_root = portable_archive(tmp_path / "after")
    service = DiagnosticService(tmp_path / "data")
    now = datetime.now(UTC)
    preview = service.preview(archive, "a" * 64, now=now)
    baseline = service.commit(str(preview["preview_id"]), "a" * 64, now=now)
    facts = service.source_facts(before_root)
    original = deepcopy(facts)
    assert object_value(facts["eligibility"])["compare"] is True
    cases = facts["cases"]
    assert isinstance(cases, list)
    assert len(cases) == 4
    comparison = service.compare(str(baseline.document["id"]), after_root)
    validate_diagnostic(comparison.document, "comparison")
    assert comparison.document == service.compare_sources(before_root, after_root).document
    assert comparison.document["comparable"] is True
    summary = object_value(comparison.document["summary"])
    assert isinstance(summary["persistent"], int)
    assert summary["persistent"] > 0
    assert summary["new_failure"] == summary["recovered"] == 0
    assert facts == original


def test_partial_omitted_baseline_keeps_full_planned_denominators(tmp_path: Path) -> None:
    archive, _ = portable_archive(tmp_path / "source", partial=True, include_evidence=False)
    _, after = portable_archive(tmp_path / "after")
    service = DiagnosticService(tmp_path / "data")
    now = datetime.now(UTC)
    preview = service.preview(archive, "a" * 64, now=now)
    baseline = service.commit(str(preview["preview_id"]), "a" * 64, now=now)
    comparison = service.compare(str(baseline.document["id"]), after).document
    assert comparison["comparable"] is False
    assert comparison["all_previous_failures_passed"] is False
    coverage = object_value(comparison["coverage"])
    assert coverage["before_cases"] == coverage["after_cases"] == 4
    assert coverage["missing_required_cases"] == 3
    assert isinstance(coverage["missing_required_checks"], int)
    assert coverage["missing_required_checks"] > 0
