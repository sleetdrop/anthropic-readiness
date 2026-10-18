"""Shared application boundary for explicit planning and assessment execution."""

from collections.abc import Sequence
from pathlib import Path

from anthropic_readiness.config import target_from_document
from anthropic_readiness.contracts import resolve_contract
from anthropic_readiness.diagnostics.context import ContextObserver
from anthropic_readiness.models import JsonObject, RunResult
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.operations.ports import CancelToken, CredentialProvider, ExecutionObserver
from anthropic_readiness.runner import RunPlan, execute_run, plan_run
from anthropic_readiness.transport import HttpTransport


def build_plan(target: JsonObject, profiles: Sequence[str]) -> RunPlan:
    config = target_from_document(target)
    return plan_run(
        config, resolve_contract(config.contract_id, config.contract_revision), profiles
    )


def run_assessment(
    plan: RunPlan,
    output: Path,
    *,
    credentials: CredentialProvider,
    observer: ExecutionObserver | None = None,
    control: CancelToken | None = None,
    run_id: str | None = None,
    assessment_context: JsonObject | None = None,
) -> RunResult:
    delegate = (
        observer if observer is not None else DiskExecutionObserver(output / "operations", output)
    )
    context_observer = (
        ContextObserver(output, assessment_context, delegate)
        if assessment_context is not None
        else None
    )
    try:
        return execute_run(
            plan,
            HttpTransport(),
            output,
            credentials=credentials,
            observer=context_observer if context_observer is not None else delegate,
            control=control,
            run_id=run_id,
        )
    finally:
        if context_observer is not None:
            context_observer.finalize()
