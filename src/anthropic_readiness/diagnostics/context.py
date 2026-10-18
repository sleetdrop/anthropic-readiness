"""Pre-request provenance and an immutable, separate final identity check."""

from __future__ import annotations

import hashlib
from pathlib import Path

from anthropic_readiness.config import fingerprint
from anthropic_readiness.diagnostics.core_contracts import validate_core
from anthropic_readiness.diagnostics.identity import check_identity, installed_identity
from anthropic_readiness.diagnostics.inventory import categorized_cases
from anthropic_readiness.diagnostics.models import (
    AssessmentContext,
    BaselineRecord,
    ImplementationIdentity,
    RetestRecipe,
)
from anthropic_readiness.diagnostics.recipes import build_recipe
from anthropic_readiness.evidence import atomic_write, json_bytes
from anthropic_readiness.models import EvidenceRef, JsonObject, object_value
from anthropic_readiness.operations.models import WorkerEvent
from anthropic_readiness.operations.ports import ExecutionObserver
from anthropic_readiness.operations.storage import MAX_DOCUMENT_BYTES
from anthropic_readiness.runner import RunPlan


def validate_plan_context(
    context: JsonObject, plan: JsonObject, *, run_id: str | None = None
) -> None:
    validate_core(context, "assessment-context")
    recipe = object_value(context["recipe"])
    recipe_body = {key: value for key, value in recipe.items() if key != "content_sha256"}
    if (
        fingerprint(recipe_body) != recipe["content_sha256"]
        or context["recipe_sha256"] != recipe["content_sha256"]
        or context["plan_sha256"] != fingerprint(plan)
        or context["config_sha256"] != plan["config_fingerprint"]
        or recipe["cases"] != categorized_cases(plan["cases"])
        or any(recipe[field] != plan[field] for field in ("profiles", "limits"))
    ):
        raise ValueError("diagnostic_context_binding")
    if run_id is not None and context["run_id"] not in (None, run_id):
        raise ValueError("diagnostic_run_identity")
    reasons = check_identity(
        ImplementationIdentity(object_value(recipe["implementation"])), installed_identity()
    )
    if reasons:
        raise ValueError("diagnostic_identity_changed:" + ",".join(reasons))


def context_for_plan(
    plan: RunPlan, recipe: RetestRecipe, *, baseline: BaselineRecord | None = None
) -> AssessmentContext:
    validate_core(recipe.document, "retest-recipe")
    if build_recipe(plan, installed_identity()).document != recipe.document:
        raise ValueError("diagnostic_recipe_plan")
    expected = {
        "requested": plan.target.model,
        "policy": plan.target.response_model_policy,
        "aliases": sorted(set(plan.target.response_model_aliases)),
    }
    if recipe.document["model"] != expected or recipe.document["capabilities"] != dict(
        plan.target.capabilities
    ):
        raise ValueError("diagnostic_recipe_plan")
    document: JsonObject = {
        "schema_version": "1.0",
        "run_id": None,
        "plan_sha256": fingerprint(plan.to_json()),
        "config_sha256": plan.to_json()["config_fingerprint"],
        "recipe": object_value(recipe.document),
        "recipe_sha256": recipe.document["content_sha256"],
        "baseline": (
            {"baseline_id": baseline.document["id"], "source": baseline.document["source"]}
            if baseline is not None
            else None
        ),
        "declared_changes": [],
    }
    validate_plan_context(document, plan.to_json())
    return AssessmentContext(document)


def bind_run_context(context: JsonObject, run_id: str) -> JsonObject:
    document = object_value(context)
    if document["run_id"] not in (None, run_id):
        raise ValueError("diagnostic_run_identity")
    document["run_id"] = run_id
    validate_core(document, "assessment-context")
    return document


class ContextObserver:
    def __init__(self, root: Path, context: JsonObject, delegate: ExecutionObserver) -> None:
        self.root = root
        self.context = object_value(context)
        self.delegate = delegate
        self._context_bytes: bytes | None = None
        self._finalized = False

    def begin(self, context: JsonObject) -> None:
        run_id = str(context["run_id"])
        validate_plan_context(self.context, object_value(context["plan"]), run_id=run_id)
        bound = bind_run_context(self.context, run_id)
        data = json_bytes(bound)
        atomic_write(self.root / "assessment-context.json", data)
        self.context = bound
        self._context_bytes = data
        self.delegate.begin(context)

    def emit(self, event: WorkerEvent) -> None:
        if event.kind == "result_committed":
            # The parent exposes completion as soon as this event is acknowledged.
            self.finalize()
        self.delegate.emit(event)

    def commit_case(self, case: JsonObject, refs: tuple[EvidenceRef, ...]) -> JsonObject:
        return self.delegate.commit_case(case, refs)

    def finalize(self) -> None:
        data = self._context_bytes
        if data is None or self._finalized:
            return
        expected = ImplementationIdentity(
            object_value(object_value(self.context["recipe"])["implementation"])
        )
        observed: str | None = None
        status = "unavailable"
        reasons: tuple[str, ...] = ("identity_unavailable",)
        try:
            actual = installed_identity()
            observed = str(actual.document["content_sha256"])
            reasons = check_identity(expected, actual)
            status = "changed" if reasons else "unchanged"
        except (ValueError, OSError):
            pass
        if (self.root / "assessment-context.json").read_bytes() != data:
            status = "unavailable"
            reasons = (*reasons, "diagnostic_context_changed")
        result_path = self.root / "result.json"
        result_digest: str | None = None
        if result_path.exists():
            with result_path.open("rb") as stream:
                result_data = stream.read(MAX_DOCUMENT_BYTES + 1)
            if len(result_data) > MAX_DOCUMENT_BYTES:
                status = "unavailable"
                reasons = (*reasons, "diagnostic_result_size_limit")
            else:
                result_digest = hashlib.sha256(result_data).hexdigest()
        verification: JsonObject = {
            "schema_version": "1.0",
            "run_id": self.context["run_id"],
            "context_sha256": hashlib.sha256(data).hexdigest(),
            "result_sha256": result_digest,
            "expected_implementation_sha256": expected.document["content_sha256"],
            "observed_implementation_sha256": observed,
            "identity_status": status,
            "reasons": list(reasons),
        }
        validate_core(verification, "assessment-context-verification")
        atomic_write(self.root / "assessment-context-verification.json", json_bytes(verification))
        self._finalized = True
