"""Compatible report entry points backed by the shared verified visual projection."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from anthropic_readiness.evidence import atomic_write, create_run_directory, json_bytes, safe_path
from anthropic_readiness.models import JsonObject, RunResult, object_value, strict_json
from anthropic_readiness.report_models import ReportSource
from anthropic_readiness.report_rendering import render_report_html, render_report_markdown
from anthropic_readiness.report_sources import (
    evidence_quality,
    load_report_source,
    safe_reference_path,
    source_bytes,
)
from anthropic_readiness.report_view import build_report_view
from anthropic_readiness.schema import result_from_document


def memory_source(result: RunResult, diagnostics: Sequence[JsonObject] = ()) -> ReportSource:
    result_from_document(result.to_json())
    quality = result.report_context.get("evidence_verification")
    verification: JsonObject = (
        object_value(quality)
        if isinstance(quality, dict)
        else {
            "status": "missing_or_invalid" if result.evidence else "no_evidence",
            "errors": ["evidence_not_verified_in_memory"],
        }
    )
    return ReportSource(
        result,
        None,
        result.cases,
        None,
        verification,
        tuple(diagnostics) if verification["status"] == "verified" else (),
        result.plan,
    )


def render_html(result: RunResult, diagnostics: Sequence[JsonObject] = ()) -> str:
    return render_report_html(build_report_view(memory_source(result, diagnostics)))


def render_markdown(result: RunResult, diagnostics: Sequence[JsonObject] = ()) -> str:
    return render_report_markdown(build_report_view(memory_source(result, diagnostics)))


def write_projection(source: ReportSource, output_dir: Path) -> None:
    view = build_report_view(source)
    atomic_write(output_dir / "report.html", render_report_html(view).encode())
    atomic_write(output_dir / "report.md", render_report_markdown(view).encode())
    atomic_write(output_dir / "report-view.json", json_bytes(view.document))
    atomic_write(
        output_dir / "report-manifest.json",
        json_bytes(
            {
                "schema_version": "1.0",
                "presentation_version": "2.0",
                "run_id": view.document["run_id"],
                "assessment_id": source.result.assessment_id if source.result else None,
                "source_result_sha256": source.result_sha256,
                "evidence_verification": source.evidence_verification,
            }
        ),
    )


def write_reports(result: RunResult, output_dir: Path) -> None:
    source = load_report_source(output_dir)
    if source.result is None or source.result.to_json() != result.to_json():
        raise ValueError("report_result_identity")
    write_projection(source, output_dir)


def render_from_file(source: Path, destination: Path) -> None:
    original = source_bytes(source.parent, source.name)
    result = result_from_document(object_value(strict_json(original.decode())))
    if any(not safe_reference_path(ref.path) for ref in result.evidence):
        raise ValueError("invalid_report_evidence_path")
    # Sidecars belong only to the assessment's canonical result, not an arbitrary
    # JSON input beside unrelated operational files.
    observed = load_report_source(source.parent) if source.name == "result.json" else None
    create_run_directory(destination)
    for ref in result.evidence:
        if evidence_quality(source.parent, (), (ref,))["status"] != "verified":
            continue
        data = source_bytes(source.parent, ref.path)
        if hashlib.sha256(data).hexdigest() != ref.sha256:
            continue
        target = safe_path(destination, ref.path)
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not target.exists():
            atomic_write(target, data)
    atomic_write(destination / "result.json", original)
    copied = load_report_source(destination)
    if observed is not None:
        copied = replace(
            copied,
            execution=observed.execution,
            diagnostics=(
                *copied.diagnostics,
                *(item for item in observed.diagnostics if item.get("kind") == "source_warning"),
            ),
        )
    write_projection(copied, destination)
    atomic_write(
        destination / "source-result.sha256", (hashlib.sha256(original).hexdigest() + "\n").encode()
    )
