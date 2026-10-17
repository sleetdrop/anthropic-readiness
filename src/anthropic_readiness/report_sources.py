"""Verify source artifacts before exposing their facts to presentation."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from anthropic_readiness.config import target_from_document
from anthropic_readiness.evidence import safe_path, verify_evidence
from anthropic_readiness.models import EvidenceRef, JsonObject, RunResult, object_value, strict_json
from anthropic_readiness.operations.checkpoints import checkpoint_refs, validate_checkpoint
from anthropic_readiness.operations.journal import RunJournal
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.operations.storage import MAX_DOCUMENT_BYTES
from anthropic_readiness.report_models import ReportSource
from anthropic_readiness.report_reading import message_diagnostic
from anthropic_readiness.schema import result_from_document


def source_bytes(root: Path, relative: str) -> bytes:
    path = safe_path(root, relative)
    with path.open("rb") as stream:
        data = stream.read(MAX_DOCUMENT_BYTES + 1)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("report_source_size_limit")
    return data


def safe_reference_path(path: str) -> bool:
    return re.fullmatch(
        r"evidence/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(?:request\.json|response\.json|body\.bin|reads\.json|events\.jsonl)",
        path,
    ) is not None and ".." not in path.split("/")


def assertions_for(case: JsonObject) -> list[JsonObject]:
    return objects(case.get("preconditions")) + [
        item
        for attempt in objects(case.get("attempts"))
        for item in objects(attempt.get("assertions"))
    ]


def evidence_quality(
    root: Path, cases: tuple[JsonObject, ...], refs: tuple[EvidenceRef, ...]
) -> JsonObject:
    errors = verify_evidence(root, refs)
    inventory = {(ref.path, ref.sha256) for ref in refs}
    for ref in refs:
        if not safe_reference_path(ref.path):
            errors.append("invalid_report_evidence_path")
    for case in cases:
        for assertion in assertions_for(case):
            references = checkpoint_refs({"evidence_refs": assertion.get("evidence_refs", [])})
            if assertion["status"] == "FAIL" and not references:
                errors.append("missing_assertion_evidence:" + str(assertion["id"]))
            for ref in references:
                if (ref.path, ref.sha256) not in inventory:
                    errors.append("assertion_reference_not_in_inventory:" + ref.path)
                errors.extend(verify_evidence(root, (ref,)))
    return {
        "status": "missing_or_invalid" if errors else "verified" if refs else "no_evidence",
        "errors": list(dict.fromkeys(errors)),
    }


def verified_diagnostics(
    cases: tuple[JsonObject, ...], target: JsonObject, root: Path
) -> tuple[JsonObject, ...]:
    diagnostics: list[JsonObject] = []
    for case in cases:
        for assertion in assertions_for(case):
            if assertion.get("status") != "FAIL" or assertion.get("id") not in {
                "MSG-CORE",
                "MSG-MODEL",
            }:
                continue
            for reference in objects(assertion.get("evidence_refs")):
                try:
                    path = str(reference["path"])
                    if not safe_reference_path(path):
                        continue
                    data = source_bytes(root, path)
                    if (
                        len(data) > 8 * 1024 * 1024
                        or hashlib.sha256(data).hexdigest() != reference["sha256"]
                    ):
                        continue
                    event = reference.get("event")
                    start = False
                    if type(event) is int and path.endswith("events.jsonl"):
                        frame = object_value(strict_json(data.decode().splitlines()[event]))
                        payload = object_value(strict_json(str(frame["data"])))
                        if payload.get("type") != "message_start":
                            continue
                        message = object_value(payload["message"])
                        start = True
                    elif path.endswith("body.bin"):
                        message = object_value(strict_json(data.decode()))
                    else:
                        continue
                    diagnostic = message_diagnostic(
                        case["id"], assertion["id"], message, start, target, reference
                    )
                    if diagnostic is not None:
                        diagnostics.append(diagnostic)
                except (OSError, ValueError, KeyError, IndexError):
                    continue
    return tuple(diagnostics)


def bind_execution(context: JsonObject, result: RunResult | None, digest: str | None) -> None:
    plan = object_value(context["plan"])
    planned = objects(plan["cases"])
    states = objects(context["case_states"])
    ids = [case["id"] for case in planned]
    if (
        len(ids) != len(set(map(str, ids)))
        or [case["case_id"] for case in states] != ids
        or context["config_sha256"] != plan["config_fingerprint"]
        or target_from_document(object_value(context["target"])).fingerprint(
            str(object_value(context["contract"])["content_sha256"])
        )
        != context["config_sha256"]
    ):
        raise ValueError("sidecar_plan_identity")
    if result is not None and (
        context["run_id"] != result.run_id
        or context["result_sha256"] != digest
        or context["target"] != result.target
        or context["contract"] != result.contract
        or {**plan, "actual_requests": result.plan["actual_requests"]} != result.plan
        or context["actual_requests"] != result.plan["actual_requests"]
        or any(
            state["state"] != case["status"]
            for state, case in zip(states, result.cases, strict=True)
        )
    ):
        raise ValueError("sidecar_result_identity")
    attempt_cases = (
        {
            str(attempt["id"]): case["id"]
            for case in result.cases
            for attempt in objects(case["attempts"])
        }
        if result is not None
        else {}
    )
    for span in objects(context["spans"]):
        start = float(str(span["start_ms"]))
        end = float(str(span["end_ms"])) if span["end_ms"] is not None else None
        if (
            span["case_id"] not in ids
            or start > float(str(context["elapsed_ms"]))
            or (end is not None and (end < start or end > float(str(context["elapsed_ms"]))))
            or (
                result is not None
                and span["attempt_id"] is not None
                and attempt_cases.get(str(span["attempt_id"])) != span["case_id"]
            )
        ):
            raise ValueError("sidecar_span_identity")


def load_report_source(root: Path, *, operations_root: Path | None = None) -> ReportSource:
    operations = operations_root if operations_root is not None else root / "operations"
    result: RunResult | None = None
    digest: str | None = None
    warnings: list[JsonObject] = []
    if safe_path(root, "result.json").exists():
        data = source_bytes(root, "result.json")
        result = result_from_document(object_value(strict_json(data.decode())))
        digest = hashlib.sha256(data).hexdigest()
    execution: JsonObject | None = None
    if operations.exists():
        try:
            if safe_path(operations, "execution.json").exists():
                initial = object_value(
                    strict_json(source_bytes(operations, "execution.json").decode())
                )
                execution = RunJournal(
                    operations, str(initial["run_id"]), evidence_root=root
                ).snapshot()
                bind_execution(execution, result, digest)
        except (OSError, ValueError, KeyError):
            execution = None
            warnings.append({"kind": "source_warning", "code": "sidecar_invalid"})
    if result is None and execution is None:
        raise ValueError("report_source_unavailable")
    cases = result.cases if result is not None else ()
    refs = result.evidence if result is not None else ()
    if result is None and execution is not None:
        committed: list[JsonObject] = []
        retained: list[EvidenceRef] = []
        for state in objects(execution["case_states"]):
            relative = state["checkpoint_path"]
            if relative is None:
                continue
            try:
                if relative != "checkpoints/" + str(state["case_id"]) + ".json":
                    raise ValueError("checkpoint_reference_path")
                data = source_bytes(operations, str(relative))
                if hashlib.sha256(data).hexdigest() != state["checkpoint_sha256"]:
                    raise ValueError("checkpoint_hash_mismatch")
                document = object_value(strict_json(data.decode()))
                validate_checkpoint(document, execution, root)
                if object_value(document["case_record"])["status"] != state["state"]:
                    raise ValueError("checkpoint_state_mismatch")
                committed.append(object_value(document["case_record"]))
                retained.extend(checkpoint_refs(document))
            except (OSError, ValueError, KeyError):
                warnings.append(
                    {
                        "kind": "source_warning",
                        "code": "checkpoint_invalid",
                        "case_id": state["case_id"],
                    }
                )
        cases, refs = tuple(committed), tuple(retained)
    quality = evidence_quality(root, cases, refs)
    if warnings and result is None:
        quality = {
            "status": "missing_or_invalid",
            "errors": [str(item["code"]) for item in warnings],
        }
    target = (
        result.target
        if result is not None
        else object_value(execution["target"])
        if execution is not None
        else {}
    )
    diagnostics = (
        verified_diagnostics(cases, target, root) if quality["status"] == "verified" else ()
    )
    return ReportSource(
        result,
        digest,
        cases,
        execution,
        quality,
        (*diagnostics, *warnings),
        result.plan
        if result is not None
        else object_value(execution["plan"])
        if execution is not None
        else {},
        refs,
    )
