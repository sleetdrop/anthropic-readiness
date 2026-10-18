"""Active publication and post-interruption recovery are distinct read boundaries."""

import json
from pathlib import Path

import pytest

from anthropic_readiness.exports import ExportPolicy, ExportService
from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.models import object_value
from anthropic_readiness.report_sources import load_report_source
from anthropic_readiness.report_view import build_report_view
from tests.export_fixtures import prepared_run


def test_unpublished_checkpoint_is_hidden_while_active_then_recovered(tmp_path: Path) -> None:
    run_id = prepared_run(tmp_path, partial=True, keep_unpublished=True, reconcile=False)
    root = tmp_path / "runs" / run_id
    execution_before = (root / "operations/execution.json").read_bytes()
    active = load_report_source(root / "assessment", operations_root=root / "operations")
    assert len(active.case_records) == 1
    assert not any("ANT-TEXT-SSE-001" in ref.path for ref in active.evidence_refs)
    assert (root / "operations/execution.json").read_bytes() == execution_before
    manager = JobManager(JobStore(tmp_path), credential_allowlist={})
    manager.start()
    manager.close()
    interrupted = (root / "operations/execution.json").read_bytes()
    source = load_report_source(root / "assessment", operations_root=root / "operations")
    assert len(source.case_records) == 2
    view = build_report_view(source).document
    assert view["status"] == "partial"
    assert object_value(view["summary"])["completed_cases"] == 2
    limitations = view["limitations"]
    assert isinstance(limitations, list)
    assert any("恢复" in str(note) for note in limitations)
    preview = ExportService(tmp_path).preview(run_id, ExportPolicy(("zip",), True))
    files = preview["files"]
    assert isinstance(files, list)
    assert "operations/checkpoints/ANT-TEXT-SSE-001.json" in files
    assert any(
        "ANT-TEXT-SSE-001" in str(name) for name in files if str(name).startswith("evidence/")
    )
    assert (root / "operations/execution.json").read_bytes() == interrupted


@pytest.mark.parametrize("mutation", ["evidence", "identity", "unstarted", "request_count"])
def test_invalid_unpublished_checkpoint_cannot_make_a_clean_export(
    tmp_path: Path, mutation: str
) -> None:
    run_id = prepared_run(tmp_path, partial=True, keep_unpublished=True)
    root = tmp_path / "runs" / run_id
    path = root / "operations/checkpoints/ANT-TEXT-SSE-001.json"
    checkpoint = json.loads(path.read_text())
    if mutation == "identity":
        checkpoint["run_id"] = "foreign-run"
        path.write_text(json.dumps(checkpoint))
    elif mutation == "evidence":
        ref = checkpoint["evidence_refs"][0]
        (root / "assessment" / ref["path"]).write_bytes(b"replaced")
    else:
        context_path = root / "operations/execution.json"
        context = json.loads(context_path.read_text())
        if mutation == "unstarted":
            context["case_states"][1]["state"] = "pending"
        else:
            context["actual_requests"] = 1
        context_path.write_text(json.dumps(context))
    source = load_report_source(root / "assessment", operations_root=root / "operations")
    assert source.evidence_verification["status"] == "missing_or_invalid"
    assert len(source.case_records) == 1
    with pytest.raises(ValueError, match="export_evidence_invalid"):
        ExportService(tmp_path).create(run_id, ExportPolicy(("zip",), True))
