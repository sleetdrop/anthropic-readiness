"""Real synthetic plan/execution inputs; delivery metadata is independently assembled."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from anthropic_readiness.application import prepare_assessment
from anthropic_readiness.cases import build_request
from anthropic_readiness.config import fingerprint, load_target
from anthropic_readiness.diagnostics.context import ContextObserver
from anthropic_readiness.diagnostics.contracts import validate_diagnostic
from anthropic_readiness.diagnostics.core_contracts import validate_core
from anthropic_readiness.diagnostics.identity import installed_identity
from anthropic_readiness.diagnostics.inventory import categorized_cases
from anthropic_readiness.diagnostics.models import RetestRecipe
from anthropic_readiness.evidence import json_bytes
from anthropic_readiness.models import JsonObject, JsonValue, object_value, strict_json
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.operations.models import WorkerEvent
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.operations.ports import ObservationError
from anthropic_readiness.report_sources import load_report_source
from anthropic_readiness.runner import RunPlan, execute_run
from tests.acceptance.test_runner import FixtureTransport

REPOSITORY = Path(__file__).resolve().parents[1]


def portable_archive(
    root: Path,
    *,
    source_dir: Path | None = None,
    include_evidence: bool = True,
    legacy: bool = False,
    partial: bool = False,
    locale: str = "zh-CN",
    run_id: str | None = None,
) -> tuple[Path, Path]:
    """Synthetic real execution with independently assembled delivery metadata."""
    root.mkdir(parents=True, exist_ok=True)
    if source_dir is None:
        source_dir = root / "original"
        plan, context = prepare_assessment(
            load_target(REPOSITORY / "examples/target.yaml").to_json(),
            ("anthropic-basic", "anthropic-tools-smoke"),
        )

        class InterruptedObserver(DiskExecutionObserver):
            def emit(self, event: WorkerEvent) -> None:
                super().emit(event)
                if partial and event.kind == "case_committed":
                    raise ObservationError("synthetic_stop_after_checkpoint")

        observer = ContextObserver(
            source_dir, context.document, InterruptedObserver(source_dir / "operations", source_dir)
        )
        try:
            execute_run(
                plan,
                FixtureTransport(fail_second=True),
                source_dir,
                observer=observer,
                run_id=run_id,
            )
        except ObservationError:
            if not partial:
                raise
        finally:
            observer.finalize()
    source = load_report_source(source_dir)
    data: dict[str, bytes] = {
        "report.html": f'<html lang="{locale}"><script>throw Error("uploaded")</script></html>'.encode()
    }
    if source.result is not None:
        data["result.json"] = (source_dir / "result.json").read_bytes()
        source_run_id = source.result.run_id
    else:
        assert source.execution is not None
        source_run_id = str(source.execution["run_id"])
        data["operations/execution.json"] = json_bytes(source.execution)
        for item in source.checkpoint_inventory or ():
            relative = "operations/" + str(item["checkpoint_path"])
            data[relative] = (source_dir / relative).read_bytes()
    if include_evidence:
        for ref in source.evidence_refs:
            data[ref.path] = (source_dir / ref.path).read_bytes()
    quality = {
        **source.evidence_verification,
        "delivery": "external_files" if include_evidence else "omitted",
    }
    if not legacy:
        context_data = (source_dir / "assessment-context.json").read_bytes()
        context_value = object_value(strict_json(context_data.decode()))
        recipe = object_value(context_value["recipe"])
        data["assessment-context.json"] = context_data
        data["retest-recipe.json"] = json_bytes(recipe)
        data["assessment-context-verification.json"] = (
            source_dir / "assessment-context-verification.json"
        ).read_bytes()
        identity: JsonObject = {
            "run_id": source_run_id,
            "assessment_id": source.result.assessment_id if source.result is not None else None,
            "result_sha256": source.result_sha256,
            "checkpoint_sha256": fingerprint(list(source.checkpoint_inventory or ()))
            if source.result is None
            else None,
            "recipe_sha256": recipe["content_sha256"],
            "context_sha256": hashlib.sha256(context_data).hexdigest(),
        }
        marker: JsonObject = {
            "schema_version": "1.0",
            "source": identity,
            "partial": source.result is None,
            "recipe": {
                "path": "retest-recipe.json",
                "sha256": hashlib.sha256(data["retest-recipe.json"]).hexdigest(),
            },
            "context": {
                "path": "assessment-context.json",
                "sha256": hashlib.sha256(context_data).hexdigest(),
            },
            "files": file_inventory(data),
            "omissions": [] if include_evidence else ["evidence_files"],
            "evidence_verification": quality,
        }
        validate_diagnostic(marker, "diagnostic-package")
        data["diagnostic-package.json"] = json_bytes(marker)
    manifest: JsonObject = {
        "schema_version": "1.0",
        "export_id": str(uuid4()),
        "run_id": source_run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "presentation_version": "2.0",
        "source_result_sha256": source.result_sha256,
        "partial": source.result is None,
        "formats": ["zip"],
        "include_evidence": include_evidence,
        "files": file_inventory(data),
        "omissions": [] if include_evidence else ["evidence_files"],
        "evidence_verification": quality,
    }
    validate_operational(manifest, "export-manifest")
    data["manifest.json"] = json_bytes(manifest)
    archive = root / "input.zip"
    with ZipFile(archive, "x", compression=ZIP_DEFLATED) as output:
        for relative, content in sorted(data.items()):
            output.writestr(relative, content)
    return archive, source_dir


def file_inventory(data: dict[str, bytes]) -> list[JsonValue]:
    return [
        {"path": path, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
        for path, content in sorted(data.items())
    ]


def rewrite_archive(path: Path, mutate: Callable[[dict[str, bytes]], None]) -> None:
    """Rebind envelope hashes around an intentional synthetic semantic mutation."""
    with ZipFile(path) as package:
        data = {name: package.read(name) for name in package.namelist()}
    mutate(data)
    if "diagnostic-package.json" in data:
        marker = object_value(strict_json(data["diagnostic-package.json"].decode()))
        marker["files"] = file_inventory(
            {
                name: content
                for name, content in data.items()
                if name not in {"diagnostic-package.json", "manifest.json"}
            }
        )
        for key in ("recipe", "context"):
            reference = object_value(marker[key])
            reference["sha256"] = hashlib.sha256(data[str(reference["path"])]).hexdigest()
            marker[key] = reference
        identity = object_value(marker["source"])
        identity["context_sha256"] = object_value(marker["context"])["sha256"]
        identity["recipe_sha256"] = object_value(strict_json(data["retest-recipe.json"].decode()))[
            "content_sha256"
        ]
        marker["source"] = identity
        data["diagnostic-package.json"] = json_bytes(marker)
    manifest = object_value(strict_json(data["manifest.json"].decode()))
    manifest["files"] = file_inventory(
        {name: content for name, content in data.items() if name != "manifest.json"}
    )
    data["manifest.json"] = json_bytes(manifest)
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as package:
        for name, content in sorted(data.items()):
            package.writestr(name, content)


def recipe_fixture(plan: RunPlan) -> RetestRecipe:
    requests: list[JsonValue] = []
    beta_headers: list[JsonValue] = list(plan.target.beta_headers)
    aliases: list[JsonValue] = []
    aliases.extend(sorted(set(plan.target.response_model_aliases)))
    for case in plan.cases:
        request = build_request(case, plan.target)
        normalized: JsonObject = {
            "method": "POST",
            "headers": dict(request.headers),
            "body": request.body,
            "streaming": request.streaming,
        }
        requests.append({"case_id": case.id, **normalized, "sha256": fingerprint(normalized)})
    value: JsonObject = {
        "schema_version": "1.0",
        "implementation": installed_identity().document,
        "contract": {
            "id": plan.target.contract_id,
            "revision": plan.target.contract_revision,
            "content_sha256": plan.bundle.content_sha256,
        },
        "protocol": {
            "name": "anthropic.messages",
            "api_version": plan.target.api_version,
            "beta_headers": beta_headers,
        },
        "model": {
            "requested": plan.target.model,
            "policy": plan.target.response_model_policy,
            "aliases": aliases,
        },
        "capabilities": dict(plan.target.capabilities),
        "limits": plan.target.limits.to_json(),
        "profiles": plan.to_json()["profiles"],
        "cases": categorized_cases(plan.to_json()["cases"]),
        "requests": requests,
        "repeat": 1,
        "retry": 0,
    }
    value["content_sha256"] = fingerprint(value)
    validate_core(value, "retest-recipe")
    return RetestRecipe(value)
