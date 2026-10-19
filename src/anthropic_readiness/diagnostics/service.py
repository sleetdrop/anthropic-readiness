"""Shared diagnostic operations for CLI and local Web adapters."""

import hashlib
import time
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from anthropic_readiness.config import fingerprint
from anthropic_readiness.diagnostics.comparison import compare_assessments
from anthropic_readiness.diagnostics.contracts import validate_diagnostic, validate_projection
from anthropic_readiness.diagnostics.identity import check_identity, installed_identity
from anthropic_readiness.diagnostics.importing import (
    context_binding,
    read_manifest,
    source_identity,
    validate_import,
)
from anthropic_readiness.diagnostics.models import (
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
    validate_recipe_binding,
    validate_recipe_evidence,
)
from anthropic_readiness.diagnostics.reduction import baseline_eligibility, comparison_inventory
from anthropic_readiness.diagnostics.store import DiagnosticStore
from anthropic_readiness.evidence import json_bytes, safe_path
from anthropic_readiness.models import JsonObject, JsonValue, object_value, strict_json
from anthropic_readiness.report_models import ReportSource
from anthropic_readiness.report_rendering import render_report_html, render_report_markdown
from anthropic_readiness.report_sources import load_report_source
from anthropic_readiness.report_view import build_report_view


class DiagnosticService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.store = DiagnosticStore(root / "diagnostics")

    def preview(self, archive: Path, owner: str, *, now: datetime) -> JsonObject:
        return self.store.preview(archive, owner, now=now)

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
        self, source_dir: Path, *, include_evidence: bool
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
        view = build_report_view(projected)
        data.update(
            {
                "report.html": render_report_html(view).encode(),
                "report.md": render_report_markdown(view).encode(),
                "report-view.json": json_bytes(view.document),
            }
        )
        return projected, build_package_files(
            projected, context, raw_files=data, include_evidence=include_evidence
        )

    def preview_export(self, source_dir: Path, *, include_evidence: bool) -> JsonObject:
        source, files = self._export_files(source_dir, include_evidence=include_evidence)
        names: list[JsonValue] = []
        names.extend(sorted((*files, "manifest.json")))
        return {
            "schema_version": "1.0",
            "include_evidence": include_evidence,
            "source_result_sha256": source.result_sha256,
            "partial": source.result is None,
            "files": names,
            "disclosures": ["source_contains_target_context"],
            "evidence_verification": source.evidence_verification,
        }

    def export(self, source_dir: Path, destination: Path, *, include_evidence: bool) -> JsonObject:
        source, files = self._export_files(source_dir, include_evidence=include_evidence)
        formats: list[JsonValue] = ["zip"]
        files["manifest.json"] = json_bytes(
            build_export_manifest(files, source, include_evidence=include_evidence, formats=formats)
        )
        return write_package(files, destination)

    def source_facts(self, source_dir: Path) -> JsonObject:
        source, evidence_root, _ = self._read_source(source_dir)
        context, files = portable_context(evidence_root, fallback_root=source_dir)
        recipe = object_value(context.document["recipe"]) if context is not None else None
        identity = source_identity(source)
        metadata: JsonObject = {
            "source_valid": True,
            "complete": source.result is not None,
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
