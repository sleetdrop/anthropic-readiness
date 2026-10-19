"""Disposable completed or interrupted jobs with synthetic failing evidence."""

import json
from datetime import UTC, datetime
from pathlib import Path

from anthropic_readiness.application import build_plan
from anthropic_readiness.config import TargetConfig, load_target
from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.models import object_value
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.operations.storage import replace_snapshot
from anthropic_readiness.runner import execute_run
from tests.acceptance.test_readable_reports import MissingFieldsTransport

ROOT = Path(__file__).resolve().parents[1]


def prepared_run(
    root: Path,
    *,
    partial: bool = False,
    keep_unpublished: bool = False,
    reconcile: bool = True,
    target: TargetConfig | None = None,
) -> str:
    store = JobStore(root)
    plan = store.create_plan(
        (target or load_target(ROOT / "examples/target.yaml")).to_json(),
        ("anthropic-basic",),
        "a" * 64,
        now=datetime.now(UTC),
    )
    job = store.admit(plan.id, "a" * 64, "fixture", now=datetime.now(UTC)).job
    store.transition(job.id, "queued", "running")
    assessment = root / "runs" / job.id / "assessment"
    operations = assessment.parent / "operations"
    execute_run(
        build_plan(plan.target, plan.profiles),
        MissingFieldsTransport(),
        assessment,
        run_id=job.id,
        observer=DiskExecutionObserver(operations, assessment),
    )
    if partial:
        context = object_value(json.loads((operations / "execution.json").read_text()))
        states = objects(context["case_states"])
        for index, state in enumerate(states[1:], 1):
            if not keep_unpublished or index != 1:
                (operations / str(state["checkpoint_path"])).unlink()
            state.update({"state": "pending", "checkpoint_path": None, "checkpoint_sha256": None})
            if keep_unpublished and index == 1:
                state["state"] = "running"
        context.update(
            {
                "case_states": list(states),
                "state": "running",
                "finished_at": None,
                "terminal_reason": None,
                "sequence": 0,
                "result_sha256": None,
                "actual_requests": 2 if keep_unpublished else 1,
                "spans": [
                    span
                    for span in objects(context["spans"])
                    if span["case_id"] == states[0]["case_id"]
                    or (keep_unpublished and span["case_id"] == states[1]["case_id"])
                ],
            }
        )
        replace_snapshot(operations, context)
        (operations / "events.jsonl").write_bytes(b"")
        (assessment / "result.json").unlink()
    if not reconcile:
        return job.id
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    manager.close()
    return job.id
