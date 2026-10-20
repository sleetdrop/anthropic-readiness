"""CLI/Web share verified source facts without trusting uploaded presentation."""

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest

from anthropic_readiness.application import prepare_assessment
from anthropic_readiness.config import load_target
from anthropic_readiness.diagnostics.context import ContextObserver
from anthropic_readiness.diagnostics.contracts import validate_diagnostic
from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.models import object_value
from anthropic_readiness.operations.models import WorkerEvent
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.operations.ports import CancelToken
from anthropic_readiness.runner import execute_run
from tests.acceptance.test_runner import FixtureTransport
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


@pytest.mark.parametrize("failure", ["cancelled", "internal_error"])
def test_terminal_partial_result_never_regains_controlled_eligibility(
    tmp_path: Path, failure: str
) -> None:
    plan, context = prepare_assessment(
        load_target(Path("examples/target.yaml")).to_json(),
        ("anthropic-basic", "anthropic-tools-smoke"),
    )
    token = CancelToken()
    source = tmp_path / "source"

    class CancelAfterFirst(DiskExecutionObserver):
        def emit(self, event: WorkerEvent) -> None:
            super().emit(event)
            if failure == "cancelled" and event.kind == "case_committed":
                token.cancel("synthetic_cancel_after_checkpoint")

    observer = ContextObserver(
        source, context.document, CancelAfterFirst(source / "operations", source)
    )
    transport = FixtureTransport(internal_second=failure == "internal_error")
    result = execute_run(plan, transport, source, observer=observer, control=token)
    observer.finalize()
    assert (source / "result.json").is_file()
    assert (
        result.execution_environment["interruption" if failure == "cancelled" else "internal_error"]
        is not None
    )
    original = {
        path.relative_to(source): path.read_bytes() for path in source.rglob("*") if path.is_file()
    }
    service = DiagnosticService(tmp_path / "data")
    archive = tmp_path / "source.zip"
    service.export(source, archive, include_evidence=True)
    now = datetime.now(UTC)
    preview = service.preview(archive, "owner", now=now)
    baseline = service.commit(str(preview["preview_id"]), "owner", now=now)
    imported = service.store.root / str(baseline.document["artifact_root"])
    assert (imported / "result.json").read_bytes() == original[Path("result.json")]
    for facts in (
        baseline.document,
        service.source_facts(source),
        service.source_facts(imported),
    ):
        eligibility = object_value(facts["eligibility"])
        assert eligibility["read"] is True
        assert eligibility["retest"] is False
        assert eligibility["compare"] is False
        reasons = eligibility["reasons"]
        assert isinstance(reasons, list)
        assert "diagnostic_partial_source" in reasons
    comparison = service.compare(str(baseline.document["id"]), source).document
    assert comparison["comparable"] is False
    assert comparison["all_previous_failures_passed"] is False
    assert original == {
        path.relative_to(source): path.read_bytes() for path in source.rglob("*") if path.is_file()
    }
    assert transport.calls == (1 if failure == "cancelled" else 2)
