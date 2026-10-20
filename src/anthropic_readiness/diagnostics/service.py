"""Shared diagnostic operations for CLI and local Web adapters."""

import hashlib
import time
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from anthropic_readiness.config import fingerprint
from anthropic_readiness.diagnostics.comparison import compare_assessments
from anthropic_readiness.diagnostics.context import context_for_plan, validate_plan_context
from anthropic_readiness.diagnostics.contracts import validate_diagnostic, validate_projection
from anthropic_readiness.diagnostics.identity import check_identity, installed_identity
from anthropic_readiness.diagnostics.importing import (
    context_binding,
    read_manifest,
    source_identity,
    validate_import,
)
from anthropic_readiness.diagnostics.models import (
    AssessmentContext,
    BaselineRecord,
    Comparison,
    ImplementationIdentity,
    RetestRecipe,
)
from anthropic_readiness.diagnostics.packages import (
    ARCHIVE_LIMITS,
    build_export_manifest,
    build_package_files,
    portable_context,
    write_package,
)
from anthropic_readiness.diagnostics.recipes import (
    build_recipe,
    validate_recipe_binding,
    validate_recipe_evidence,
)
from anthropic_readiness.diagnostics.recipes import (
    prepare_retest as regenerate_retest,
)
from anthropic_readiness.diagnostics.reduction import (
    baseline_eligibility,
    comparison_inventory,
    controlled_result_complete,
)
from anthropic_readiness.diagnostics.store import DiagnosticStore
from anthropic_readiness.document_rendering import (
    render_agent_index,
    render_document_html,
    render_document_markdown,
    render_package_readme,
)
from anthropic_readiness.documents import build_document_view
from anthropic_readiness.evidence import json_bytes, safe_path
from anthropic_readiness.models import JsonObject, JsonValue, object_value, strict_json
from anthropic_readiness.presentation import DEFAULT_PRESENTATION, PresentationOptions
from anthropic_readiness.report_models import ReportSource
from anthropic_readiness.report_sources import load_report_source
from anthropic_readiness.runner import RunPlan


class DiagnosticService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.store = DiagnosticStore(root / "diagnostics")

    def preview(
        self, archive: Path, owner: str, *, now: datetime, deadline: float | None = None
    ) -> JsonObject:
        return self.store.preview(archive, owner, now=now, deadline=deadline)

    def commit(self, preview_id: str, owner: str, *, now: datetime) -> BaselineRecord:
        return self.store.commit(preview_id, owner, now=now)

    def get(self, baseline_id: str) -> BaselineRecord:
        return self.store.get(baseline_id)

    def load_source(self, baseline_id: str) -> ReportSource:
        return self.store.load_source(baseline_id)

    @staticmethod
    def _read_artifact(root: Path, relative: str, expected: str) -> bytes:
        maximum = (
            ARCHIVE_LIMITS.max_json_bytes
            if relative.endswith((".json", ".jsonl"))
            else ARCHIVE_LIMITS.max_member_bytes
        )
        with safe_path(root, relative).open("rb") as stream:
            data = stream.read(maximum + 1)
        if len(data) > maximum or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("export_integrity")
        return data

    def _read_source(self, source_dir: Path) -> tuple[ReportSource, Path, Path]:
        evidence_root = source_dir
        if not (source_dir / "result.json").exists() and (
            (source_dir / "assessment").is_dir()
            or (
                (source_dir / "plan.json").is_file()
                and (source_dir / "operations/execution.json").is_file()
            )
        ):
            evidence_root = source_dir / "assessment"
        operations = source_dir / "operations"
        if (source_dir / "manifest.json").is_file():
            evidence_root = source_dir
            manifest, digest = read_manifest(source_dir)
            members = manifest["files"]
            if not isinstance(members, list) or len(members) >= ARCHIVE_LIMITS.max_members:
                raise ValueError("archive_member_count_limit")
            document = self._read_artifact(source_dir, "manifest.json", digest)
            inventory: JsonObject = {
                "members": [
                    *members,
                    {"path": "manifest.json", "sha256": digest, "bytes": len(document)},
                ]
            }
            source, _ = validate_import(
                source_dir, inventory, deadline=time.monotonic() + ARCHIVE_LIMITS.timeout_s
            )
        else:
            source = load_report_source(
                evidence_root, operations_root=operations, frozen_operations=True
            )
        return source, evidence_root, operations

    def _export_files(
        self,
        source_dir: Path,
        *,
        include_evidence: bool,
        presentation: PresentationOptions = DEFAULT_PRESENTATION,
        comparison: Comparison | None = None,
    ) -> tuple[ReportSource, dict[str, bytes]]:
        source, evidence_root, operations = self._read_source(source_dir)
        if include_evidence and (
            source.evidence_verification["status"] == "missing_or_invalid"
            or any(item.get("kind") == "source_warning" for item in source.diagnostics)
        ):
            raise ValueError("export_evidence_invalid")
        data: dict[str, bytes] = {}
        if source.result is not None and source.result_sha256 is not None:
            data["result.json"] = self._read_artifact(
                evidence_root, "result.json", source.result_sha256
            )
        elif source.execution is not None:
            data["operations/execution.json"] = json_bytes(source.execution)
            for item in source.checkpoint_inventory or ():
                relative = str(item["checkpoint_path"])
                data["operations/" + relative] = self._read_artifact(
                    operations, relative, str(item["checkpoint_sha256"])
                )
        if include_evidence:
            for ref in source.evidence_refs:
                data[ref.path] = self._read_artifact(evidence_root, ref.path, ref.sha256)
        context, metadata = portable_context(evidence_root, fallback_root=source_dir)
        data.update(metadata)
        projected = replace(
            source,
            evidence_verification={
                **source.evidence_verification,
                "delivery": "external_files"
                if include_evidence and source.evidence_refs
                else "omitted",
            },
        )
        view = build_document_view(projected, presentation=presentation, comparison=comparison)
        data.update(
            {
                "report.html": render_document_html(view).encode(),
                "report.md": render_document_markdown(view).encode(),
                "document-view.json": json_bytes(view.document),
                "README.md": render_package_readme(view).encode(),
            }
        )
        return projected, build_package_files(
            projected,
            context,
            raw_files=data,
            include_evidence=include_evidence,
            agent_index=render_agent_index(view),
            comparison=comparison,
        )

    def preview_export(
        self,
        source_dir: Path,
        *,
        include_evidence: bool,
        presentation: PresentationOptions = DEFAULT_PRESENTATION,
        comparison: Comparison | None = None,
    ) -> JsonObject:
        source, files = self._export_files(
            source_dir,
            include_evidence=include_evidence,
            presentation=presentation,
            comparison=comparison,
        )
        names: list[JsonValue] = []
        names.extend(sorted((*files, "manifest.json")))
        return {
            "schema_version": "1.0",
            "include_evidence": include_evidence,
            "source_result_sha256": source.result_sha256,
            "partial": source.result is None,
            "files": names,
            "disclosures": ["source_contains_target_context"],
            "presentation": presentation.to_json(),
            "evidence_verification": source.evidence_verification,
        }

    def export(
        self,
        source_dir: Path,
        destination: Path,
        *,
        include_evidence: bool,
        presentation: PresentationOptions = DEFAULT_PRESENTATION,
        comparison: Comparison | None = None,
    ) -> JsonObject:
        source, files = self._export_files(
            source_dir,
            include_evidence=include_evidence,
            presentation=presentation,
            comparison=comparison,
        )
        formats: list[JsonValue] = ["zip"]
        files["manifest.json"] = json_bytes(
            build_export_manifest(
                files,
                source,
                include_evidence=include_evidence,
                formats=formats,
                presentation=presentation,
            )
        )
        return write_package(files, destination)

    def source_facts(self, source_dir: Path) -> JsonObject:
        source, evidence_root, _ = self._read_source(source_dir)
        context, files = portable_context(evidence_root, fallback_root=source_dir)
        recipe = object_value(context.document["recipe"]) if context is not None else None
        identity = source_identity(source)
        metadata: JsonObject = {
            "source_valid": True,
            "complete": controlled_result_complete(source.result),
            "recipe_valid": False,
            "recipe_bound": False,
            "context_verified": False,
            "evidence_verified": source.evidence_verification["status"] == "verified",
            "identity_reasons": ["diagnostic_legacy_source"],
        }
        if context is not None and recipe is not None:
            digest = hashlib.sha256(files["assessment-context.json"]).hexdigest()
            if (
                fingerprint(
                    {key: value for key, value in recipe.items() if key != "content_sha256"}
                )
                != recipe["content_sha256"]
            ):
                raise ValueError("diagnostic_recipe_integrity")
            final = (
                object_value(strict_json(files["assessment-context-verification.json"].decode()))
                if "assessment-context-verification.json" in files
                else None
            )
            verified, final_reasons = context_binding(
                recipe, context.document, digest, source, final
            )
            try:
                reasons = list(
                    check_identity(
                        ImplementationIdentity(object_value(recipe["implementation"])),
                        installed_identity(),
                    )
                )
            except ValueError:
                reasons = ["diagnostic_identity_unavailable"]
            binding = (
                *validate_recipe_binding(RetestRecipe(recipe), source),
                *validate_recipe_evidence(RetestRecipe(recipe), source, evidence_root),
            )
            metadata.update(
                recipe_valid=True,
                recipe_bound=not binding,
                context_verified=verified,
                identity_reasons=list(dict.fromkeys((*reasons, *final_reasons, *binding))),
            )
            identity = source_identity(
                source, recipe_sha256=recipe["content_sha256"], context_sha256=digest
            )
        cases, checks = comparison_inventory(source.plan, source.case_records, recipe)
        target = (
            source.result.target
            if source.result is not None
            else object_value(source.execution["target"])
            if source.execution is not None
            else {}
        )
        facts: JsonObject = {
            "schema_version": "1.0",
            "source": identity,
            "plan": source.plan,
            "recipe": recipe,
            "context": context.document if context is not None else None,
            "target": target,
            "cases": cases,
            "checks": checks,
            "eligibility": baseline_eligibility(metadata),
            "evidence_verification": source.evidence_verification,
        }
        validate_projection(facts, "diagnostic-comparison-facts")
        return facts

    def compare_sources(self, before_dir: Path, after_dir: Path) -> Comparison:
        value = compare_assessments(self.source_facts(before_dir), self.source_facts(after_dir))
        validate_diagnostic(value.document, "comparison")
        return value

    def compare(self, baseline_id: str, source_dir: Path) -> Comparison:
        baseline = self.get(baseline_id).document
        return self.compare_sources(
            safe_path(self.store.root, str(baseline["artifact_root"])), source_dir
        )

    def prepare_retest(
        self, baseline_id: str, target: JsonObject
    ) -> tuple[RunPlan, AssessmentContext, JsonObject]:
        baseline = self.get(baseline_id)
        if object_value(baseline.document["eligibility"])["retest"] is not True:
            raise ValueError("diagnostic_retest_unavailable")
        before = self.source_facts(
            safe_path(self.store.root, str(baseline.document["artifact_root"]))
        )
        identity = installed_identity()
        recipe = RetestRecipe(object_value(before["recipe"]))
        plan, differences = regenerate_retest(recipe, target, identity)
        changes = differences["changes"]
        if not isinstance(changes, list):
            raise ValueError("diagnostic_retest_conditions")
        changes = [change for change in changes if object_value(change)["kind"] == "semantic"]
        original_target, local_target = object_value(before["target"]), plan.target.to_json()
        for field in ("name", "delivery_id", "messages_url", "auth"):
            if original_target.get(field) != local_target.get(field):
                changes.append(
                    {
                        "field": field,
                        "before": original_target.get(field),
                        "after": local_target.get(field),
                        "kind": "context",
                    }
                )
        differences["changes"] = changes
        context = context_for_plan(plan, build_recipe(plan, identity), baseline=baseline)
        context.document["declared_changes"] = changes
        validate_plan_context(context.document, plan.to_json())
        return plan, context, differences
