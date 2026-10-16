"""Synthetic operational context, built from the installed core planning contract."""

from datetime import datetime, timedelta
from pathlib import Path

from anthropic_readiness.config import load_target
from anthropic_readiness.contracts import resolve_contract
from anthropic_readiness.models import AssertionResult, JsonObject, Status
from anthropic_readiness.operations.models import EventKind, WorkerEvent
from anthropic_readiness.runner import plan_run

RUN_ID = "11111111-1111-4111-8111-111111111111"
ATTEMPT_ID = "33333333-3333-4333-8333-333333333333"
NOW = "2026-10-17T00:00:00+00:00"
ROOT = Path(__file__).resolve().parents[1]


def context() -> JsonObject:
    target = load_target(ROOT / "examples/target.yaml")
    bundle = resolve_contract(target.contract_id, target.contract_revision)
    plan = plan_run(target, bundle, ["anthropic-basic"])
    return {
        "schema_version": "1.0",
        "run_id": RUN_ID,
        "config_sha256": target.fingerprint(bundle.content_sha256),
        "target": target.to_json(),
        "contract": {**bundle.manifest, "version_semantics": "unverified"},
        "plan": plan.to_json(),
        "state": "running",
        "sequence": 0,
        "case_states": [
            {
                "case_id": case.id,
                "state": "pending",
                "checkpoint_path": None,
                "checkpoint_sha256": None,
            }
            for case in plan.cases
        ],
        "actual_requests": 0,
        "started_at": NOW,
        "updated_at": NOW,
        "finished_at": None,
        "elapsed_ms": 0,
        "spans": [],
        "warnings": [],
        "result_sha256": None,
        "terminal_reason": None,
    }


def case_record(case_id: str = "ANT-MESSAGE-001") -> JsonObject:
    precondition = AssertionResult(
        "CASE-PRECONDITION", "environment", Status.INDETERMINATE, "synthetic_precondition"
    )
    return {
        "id": case_id,
        "version": 1,
        "required": True,
        "status": "INDETERMINATE",
        "preconditions": [precondition.to_json()],
        "attempts": [],
        "dimensions": {
            "behavior": "not_evaluated",
            "protocol": "not_evaluated",
            "environment": "INDETERMINATE",
            "client": "not_evaluated",
        },
    }


def event(kind: EventKind, elapsed_ms: float, payload: JsonObject) -> WorkerEvent:
    instant = datetime.fromisoformat(NOW) + timedelta(milliseconds=elapsed_ms)
    return WorkerEvent(kind, instant.isoformat(), elapsed_ms, payload)
