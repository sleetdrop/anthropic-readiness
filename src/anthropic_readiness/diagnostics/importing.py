"""Validate extracted bytes and relationships without trusting uploaded presentation."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

from anthropic_readiness.config import fingerprint
from anthropic_readiness.diagnostics.contracts import validate_diagnostic
from anthropic_readiness.diagnostics.core_contracts import validate_core
from anthropic_readiness.diagnostics.identity import check_identity, installed_identity
from anthropic_readiness.diagnostics.models import ImplementationIdentity, RetestRecipe
from anthropic_readiness.diagnostics.recipes import (
    validate_recipe_binding,
    validate_recipe_evidence,
)
from anthropic_readiness.diagnostics.reduction import baseline_eligibility
from anthropic_readiness.evidence import safe_path
from anthropic_readiness.models import JsonObject, JsonValue, object_value, strict_json
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.operations.storage import MAX_DOCUMENT_BYTES
from anthropic_readiness.report_models import ReportSource
from anthropic_readiness.report_sources import load_report_source


def read_json(root: Path, relative: str) -> tuple[JsonObject, str]:
    with safe_path(root, relative).open("rb") as stream:
        data = stream.read(MAX_DOCUMENT_BYTES + 1)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("diagnostic_document_limit")
    return object_value(strict_json(data.decode())), hashlib.sha256(data).hexdigest()


def source_identity(
    source: ReportSource, *, recipe_sha256: JsonValue = None, context_sha256: JsonValue = None
) -> JsonObject:
    return {
        "run_id": source.result.run_id
        if source.result
        else (source.execution["run_id"] if source.execution else None),
        "assessment_id": source.result.assessment_id if source.result else None,
        "result_sha256": source.result_sha256,
        "checkpoint_sha256": fingerprint(list(source.checkpoint_inventory or ()))
        if source.result is None
        else None,
        "recipe_sha256": recipe_sha256,
        "context_sha256": context_sha256,
    }


def _inventory(value: JsonValue) -> dict[str, JsonObject]:
    entries = objects(value)
    if not isinstance(value, list) or len(entries) != len(value):
        raise ValueError("diagnostic_inventory")
    result = {
        str(item["path"]): {key: item[key] for key in ("path", "bytes", "sha256")}
        for item in entries
    }
    if len(result) != len(entries):
        raise ValueError("diagnostic_inventory")
    return result


def verify_extracted(
    root: Path, inventory: JsonObject, *, deadline: float
) -> dict[str, JsonObject]:
    entries = _inventory(inventory["members"])
    paths: set[str] = set()
    pending = [root]
    maximum = 1 + len(entries) * 120
    visited = 0
    while pending:
        directory = pending.pop()
        for path in directory.iterdir():
            visited += 1
            if time.monotonic() >= deadline:
                raise ValueError("archive_timeout")
            if visited > maximum or path.is_symlink():
                raise ValueError("diagnostic_inventory")
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                relative = path.relative_to(root).as_posix()
                if relative not in entries:
                    raise ValueError("diagnostic_inventory")
                paths.add(relative)
            else:
                raise ValueError("diagnostic_inventory")
    if paths != set(entries):
        raise ValueError("diagnostic_inventory")
    for relative, entry in entries.items():
        digest = hashlib.sha256()
        count = 0
        with safe_path(root, relative).open("rb") as stream:
            while chunk := stream.read(65536):
                if time.monotonic() >= deadline:
                    raise ValueError("archive_timeout")
                count += len(chunk)
                if count > int(str(entry["bytes"])):
                    raise ValueError("diagnostic_inventory")
                digest.update(chunk)
        if count != entry["bytes"] or digest.hexdigest() != entry["sha256"]:
            raise ValueError("diagnostic_inventory")
    return entries


def _context_check(
    root: Path, recipe: JsonObject, context: JsonObject, context_digest: str, source: ReportSource
) -> tuple[bool, list[str]]:
    plan = {**source.plan, "actual_requests": 0}
    identity = source_identity(source)
    if (
        context["run_id"] != identity["run_id"]
        or context["plan_sha256"] != fingerprint(plan)
        or context["config_sha256"] != plan["config_fingerprint"]
        or context["recipe"] != recipe
        or context["recipe_sha256"] != recipe["content_sha256"]
    ):
        raise ValueError("diagnostic_context_mismatch")
    if not safe_path(root, "assessment-context-verification.json").exists():
        return False, ["diagnostic_final_identity_missing"]
    final, _ = read_json(root, "assessment-context-verification.json")
    validate_core(final, "assessment-context-verification")
    if (
        final["run_id"] != identity["run_id"]
        or final["context_sha256"] != context_digest
        or final["result_sha256"] != source.result_sha256
        or final["expected_implementation_sha256"]
        != object_value(recipe["implementation"])["content_sha256"]
    ):
        raise ValueError("diagnostic_context_mismatch")
    if final["identity_status"] == "unchanged":
        if (
            final["observed_implementation_sha256"] != final["expected_implementation_sha256"]
            or final["reasons"] != []
        ):
            raise ValueError("diagnostic_context_mismatch")
        return True, []
    return False, ["diagnostic_final_identity_" + str(final["identity_status"])]


def validate_import(
    root: Path, inventory: JsonObject, *, deadline: float
) -> tuple[ReportSource, JsonObject]:
    entries = verify_extracted(root, inventory, deadline=deadline)
    if "manifest.json" not in entries:
        raise ValueError("diagnostic_manifest_missing")
    manifest, _ = read_json(root, "manifest.json")
    if manifest.get("schema_version") == "1.0":
        validate_operational(manifest, "export-manifest")
    elif manifest.get("schema_version") == "2.0":
        validate_diagnostic(manifest, "export-manifest-v2")
    else:
        raise ValueError("diagnostic_manifest_version")
    if _inventory(manifest["files"]) != {
        key: value for key, value in entries.items() if key != "manifest.json"
    }:
        raise ValueError("diagnostic_inventory")
    if manifest["include_evidence"] is False and any(
        name.startswith("evidence/") for name in entries
    ):
        raise ValueError("diagnostic_evidence_delivery_mismatch")
    # Imported execution.json is a frozen snapshot, never a live writer journal.
    source = load_report_source(root, frozen_operations=True)
    if any(item.get("code") == "sidecar_invalid" for item in source.diagnostics):
        raise ValueError("diagnostic_source_mismatch")
    identity = source_identity(source)
    if (
        manifest["run_id"] != identity["run_id"]
        or manifest["source_result_sha256"] != source.result_sha256
        or manifest["partial"] != (source.result is None)
    ):
        raise ValueError("diagnostic_source_mismatch")
    complete = source.result is not None and source.result.mode == "live"
    if source.result is not None:
        complete = (
            complete
            and source.result.execution_environment.get("interruption") is None
            and source.result.execution_environment.get("internal_error") is None
        )
    metadata: JsonObject = {
        "source_valid": True,
        "complete": complete,
        "recipe_valid": False,
        "recipe_bound": False,
        "context_verified": False,
        "evidence_verified": source.evidence_verification["status"] == "verified",
        "identity_reasons": [],
    }
    reasons: list[JsonValue] = []
    if "diagnostic-package.json" in entries:
        marker, _ = read_json(root, "diagnostic-package.json")
        validate_diagnostic(marker, "diagnostic-package")
        if _inventory(marker["files"]) != {
            key: value
            for key, value in entries.items()
            if key not in {"manifest.json", "diagnostic-package.json"}
        }:
            raise ValueError("diagnostic_inventory")
        recipe_ref, context_ref = object_value(marker["recipe"]), object_value(marker["context"])
        recipe, recipe_digest = read_json(root, str(recipe_ref["path"]))
        context, context_digest = read_json(root, str(context_ref["path"]))
        validate_core(recipe, "retest-recipe")
        validate_core(context, "assessment-context")
        if (
            recipe_ref["sha256"] != recipe_digest
            or context_ref["sha256"] != context_digest
            or fingerprint({key: value for key, value in recipe.items() if key != "content_sha256"})
            != recipe["content_sha256"]
        ):
            raise ValueError("diagnostic_recipe_integrity")
        identity = source_identity(
            source, recipe_sha256=recipe["content_sha256"], context_sha256=context_digest
        )
        if marker["source"] != identity or marker["partial"] != (source.result is None):
            raise ValueError("diagnostic_source_mismatch")
        verified, final_reasons = _context_check(root, recipe, context, context_digest, source)
        try:
            identity_reasons = check_identity(
                ImplementationIdentity(object_value(recipe["implementation"])), installed_identity()
            )
        except ValueError:
            identity_reasons = ("diagnostic_identity_unavailable",)
        binding_reasons = validate_recipe_binding(RetestRecipe(recipe), source)
        capture_reasons = validate_recipe_evidence(RetestRecipe(recipe), source, root)
        reasons.extend(
            dict.fromkeys((*identity_reasons, *binding_reasons, *final_reasons, *capture_reasons))
        )
        metadata.update(
            {
                "recipe_valid": True,
                "recipe_bound": not binding_reasons and not capture_reasons,
                "context_verified": verified,
                "identity_reasons": reasons,
            }
        )
    else:
        reasons.append("diagnostic_legacy_source")
        metadata["identity_reasons"] = reasons
    eligibility = baseline_eligibility(metadata)
    quality = {
        **source.evidence_verification,
        "delivery": "external_files"
        if any(name.startswith("evidence/") for name in entries)
        else "omitted",
    }
    return source, {
        "source": identity,
        "eligibility": eligibility,
        "evidence_verification": quality,
        "disclosures": ["source_contains_target_context"],
    }
