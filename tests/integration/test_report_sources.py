"""Only verified source bytes and bound operational sidecars enter report figures."""

import hashlib
import json
from pathlib import Path

import pytest

from anthropic_readiness.config import load_target
from anthropic_readiness.contracts import resolve_contract
from anthropic_readiness.models import JsonObject, object_value
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.operations.storage import replace_snapshot
from anthropic_readiness.report_sources import load_report_source
from anthropic_readiness.report_view import build_report_view
from anthropic_readiness.runner import execute_run, plan_run
from tests.acceptance.test_readable_reports import assessment
from tests.acceptance.test_runner import FixtureTransport

ROOT = Path(__file__).resolve().parents[2]


def observed(root: Path) -> Path:
    target = load_target(ROOT / "examples/target.yaml")
    plan = plan_run(
        target, resolve_contract(target.contract_id, target.contract_revision), ["anthropic-basic"]
    )
    execute_run(
        plan, FixtureTransport(), root, observer=DiskExecutionObserver(root / "operations", root)
    )
    return root


def test_verified_source_preserves_result_hash_and_diagnostics(tmp_path: Path) -> None:
    result_path = assessment(tmp_path / "source")
    before = result_path.read_bytes()
    source = load_report_source(result_path.parent)
    assert source.result is not None
    assert source.result_sha256 == hashlib.sha256(before).hexdigest()
    assert source.evidence_verification["status"] == "verified"
    assert source.diagnostics
    assert any("字段缺失" in str(item["actual"]) for item in source.diagnostics)
    view = build_report_view(source).document
    groups = view["groups"]
    assert isinstance(groups, list)
    assert len(groups) == 3
    assert any("强制工具" in str(object_value(group)["name"]) for group in groups)
    assert result_path.read_bytes() == before


def test_missing_evidence_removes_snippets_and_warns(tmp_path: Path) -> None:
    path = assessment(tmp_path / "source")
    source = load_report_source(path.parent)
    assert source.result is not None
    ref = next(ref for ref in source.result.evidence if ref.path.endswith("body.bin"))
    (path.parent / ref.path).write_text('{"model":"forged-not-a-snippet"}')
    damaged = load_report_source(path.parent)
    assert damaged.result is not None
    assert damaged.evidence_verification["status"] == "missing_or_invalid"
    assert damaged.diagnostics == ()
    view = build_report_view(damaged).document
    assert "forged-not-a-snippet" not in json.dumps(view)
    assert "证据" in str(view["limitations"])
    assert [case["status"] for case in damaged.case_records] == [
        case["status"] for case in source.case_records
    ]


def test_partial_checkpoint_is_not_final_result(tmp_path: Path) -> None:
    root = observed(tmp_path / "source")
    context = object_value(json.loads((root / "operations/execution.json").read_text()))
    cases = context["case_states"]
    assert isinstance(cases, list)
    for index, item in enumerate(cases[1:], 1):
        case = object_value(item)
        (root / "operations" / str(case["checkpoint_path"])).unlink()
        case.update({"state": "pending", "checkpoint_path": None, "checkpoint_sha256": None})
        cases[index] = case
    context.update(
        {
            "case_states": cases,
            "state": "interrupted",
            "result_sha256": None,
            "terminal_reason": "parent_restart",
            "sequence": 0,
            "actual_requests": 1,
            "spans": [
                span
                for span in objects(context["spans"])
                if span["case_id"] == object_value(cases[0])["case_id"]
            ],
        }
    )
    replace_snapshot(root / "operations", context)
    (root / "operations/events.jsonl").write_bytes(b"")
    (root / "result.json").unlink()
    source = load_report_source(root)
    assert source.result is None
    assert len(source.case_records) == 1
    view = build_report_view(source).document
    assert view.get("status") == "partial"
    summary = object_value(view["summary"])
    assert summary["planned_cases"] == 3
    assert summary["completed_cases"] == 1
    assert summary["actual_requests"] == 1
    assert object_value(summary["counts"])["pending"] == 2
    assert view["source_result_sha256"] is None


@pytest.mark.parametrize(
    "field", ["run_id", "config_sha256", "target", "plan", "result_sha256", "case_states", "spans"]
)
def test_mismatched_sidecars_cannot_supply_timeline(tmp_path: Path, field: str) -> None:
    root = observed(tmp_path / "source")
    source = load_report_source(root)
    assert source.result is not None
    assert source.execution is not None
    document: JsonObject = object_value(
        json.loads((root / "operations/execution.json").read_text())
    )
    if field == "run_id":
        document[field] = "00000000-0000-0000-0000-000000000000"
    elif field in {"config_sha256", "result_sha256"}:
        document[field] = "0" * 64
    elif field == "target":
        document[field] = {**object_value(document[field]), "model": "unbound-model"}
    elif field == "plan":
        document[field] = {**object_value(document[field]), "planned_requests": 99}
    elif field == "case_states":
        document[field] = list(objects(document[field])[1:])
    else:
        spans = document[field]
        assert isinstance(spans, list)
        document[field] = [{**object_value(spans[0]), "case_id": "UNPLANNED"}]
    replace_snapshot(root / "operations", document)
    rejected = load_report_source(root)
    assert rejected.result is not None
    assert rejected.execution is None
    view = build_report_view(rejected).document
    assert all(figure["kind"] != "timeline" for figure in objects(view["figures"]))
    assert "sidecar" in str(view["limitations"])


def test_recorded_timeline_uses_exact_observed_coordinates(tmp_path: Path) -> None:
    root = observed(tmp_path / "source")
    source = load_report_source(root)
    assert source.execution is not None
    view = build_report_view(source).document
    timing = next(figure for figure in objects(view["figures"]) if figure["id"] == "fig-timing")
    assert timing["kind"] == "timeline"
    assert timing["rows"] == [
        [span["case_id"], span["attempt_id"], span["phase"], span["start_ms"], span["end_ms"]]
        for span in objects(source.execution["spans"])
    ]
    assert (
        view["source_result_sha256"]
        == hashlib.sha256((root / "result.json").read_bytes()).hexdigest()
    )


def test_unsafe_sidecar_does_not_hide_a_valid_original_result(tmp_path: Path) -> None:
    root = observed(tmp_path / "source")
    context = root / "operations/execution.json"
    moved = tmp_path / "unrelated-context.json"
    context.rename(moved)
    context.symlink_to(moved)
    source = load_report_source(root)
    assert source.result is not None
    assert source.execution is None
    assert any(warning.get("code") == "sidecar_invalid" for warning in source.diagnostics)


def test_partial_target_must_match_the_frozen_config_fingerprint(tmp_path: Path) -> None:
    root = observed(tmp_path / "source")
    (root / "result.json").unlink()
    document = object_value(json.loads((root / "operations/execution.json").read_text()))
    document["target"] = {**object_value(document["target"]), "model": "unbound-partial-model"}
    replace_snapshot(root / "operations", document)
    with pytest.raises(ValueError, match="report_source_unavailable"):
        load_report_source(root)


def test_partial_replay_retains_zero_request_mode(tmp_path: Path) -> None:
    from anthropic_readiness.runner import replay_run
    from tests.acceptance.test_cli import target_file

    target = load_target(target_file(tmp_path))
    root = tmp_path / "replay"
    replay_run(
        target,
        resolve_contract(target.contract_id, target.contract_revision),
        "ANT-TEXT-SSE-001",
        ROOT
        / "tests/fixtures/captures/valid/evidence/ANT-TEXT-SSE-001/fixture-attempt/response.json",
        root,
        observer=DiskExecutionObserver(root / "operations", root),
    )
    context = object_value(json.loads((root / "operations/execution.json").read_text()))
    context.update(
        {
            "state": "interrupted",
            "sequence": 0,
            "result_sha256": None,
            "terminal_reason": "fixture_interruption",
        }
    )
    replace_snapshot(root / "operations", context)
    (root / "operations/events.jsonl").write_bytes(b"")
    (root / "result.json").unlink()
    view = build_report_view(load_report_source(root)).document
    assert view["status"] == "partial"
    assert view["mode"] == "replay"
    assert object_value(view["summary"])["actual_requests"] == 0


def test_missing_bound_final_result_is_not_a_clean_partial(tmp_path: Path) -> None:
    root = observed(tmp_path / "source")
    (root / "result.json").unlink()
    with pytest.raises(ValueError, match="report_source_unavailable"):
        load_report_source(root)
