"""Exclusive case publication after structural, accounting and evidence checks."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

from anthropic_readiness.evidence import atomic_write, json_bytes, safe_path, verify_evidence
from anthropic_readiness.models import (
    EvidenceRef,
    JsonObject,
    Status,
    aggregate_required,
    object_value,
)
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.operations.reduction import objects
from anthropic_readiness.operations.storage import locked, read_document


def checkpoint_refs(document: JsonObject) -> tuple[EvidenceRef, ...]:
    return tuple(
        EvidenceRef(
            str(ref["path"]),
            str(ref["sha256"]),
            ref["event"] if type(ref["event"]) is int else None,
            str(ref["pointer"]) if ref["pointer"] is not None else None,
        )
        for ref in objects(document["evidence_refs"])
    )


def validate_checkpoint(document: JsonObject, context: JsonObject, evidence_root: Path) -> None:
    validate_operational(document, "checkpoint")
    if (
        document["run_id"] != context["run_id"]
        or document["config_sha256"] != context["config_sha256"]
    ):
        raise ValueError("checkpoint_identity")
    case = object_value(document["case_record"])
    planned = objects(object_value(context["plan"])["cases"])
    definition = next((item for item in planned if item["id"] == document["case_id"]), None)
    if (
        definition is None
        or case["id"] != document["case_id"]
        or case["version"] != definition["version"]
        or case["required"] != definition["required"]
    ):
        raise ValueError("checkpoint_case_identity")
    refs = checkpoint_refs(document)
    if verify_evidence(evidence_root, refs):
        raise ValueError("checkpoint_evidence_invalid")
    inventory = {(ref.path, ref.sha256) for ref in refs}
    assertions = objects(case["preconditions"])
    for attempt in objects(case["attempts"]):
        items = objects(attempt["assertions"])
        status = aggregate_required(
            [Status(str(item["status"])) for item in items if item["required"]]
        )
        if attempt["status"] != status.value:
            raise ValueError("checkpoint_attempt_status")
        assertions.extend(items)
    required = [Status(str(item["status"])) for item in assertions if item["required"]]
    if case["status"] != aggregate_required(required).value:
        raise ValueError("checkpoint_case_status")
    for assertion in assertions:
        asserted_refs = objects(assertion["evidence_refs"])
        if assertion["status"] == "FAIL" and not asserted_refs:
            raise ValueError("checkpoint_failure_without_evidence")
        for ref in asserted_refs:
            if (str(ref["path"]), str(ref["sha256"])) not in inventory:
                raise ValueError("checkpoint_evidence_inventory")
        wrapped: JsonObject = {"evidence_refs": list(asserted_refs)}
        if verify_evidence(evidence_root, checkpoint_refs(wrapped)):
            raise ValueError("checkpoint_assertion_evidence_invalid")


class CheckpointStore:
    def __init__(self, root: Path, run_id: str, *, evidence_root: Path) -> None:
        self.root = root
        self.run_id = run_id
        self.evidence_root = evidence_root

    def commit(self, case: JsonObject, refs: tuple[EvidenceRef, ...]) -> JsonObject:
        with locked(self.root, "checkpoints.lock"):
            context = read_document(safe_path(self.root, "execution.json"))
            validate_operational(context, "execution")
            if context["run_id"] != self.run_id:
                raise ValueError("checkpoint_identity")
            case_id = str(case["id"])
            if not re.fullmatch(r"[A-Za-z0-9_-]+", case_id):
                raise ValueError("checkpoint_case_id")
            document: JsonObject = {
                "schema_version": "1.0",
                "run_id": self.run_id,
                "config_sha256": context["config_sha256"],
                "case_id": case_id,
                "case_record": case,
                "evidence_refs": [ref.to_json() for ref in refs],
                "committed_at": datetime.now(UTC).isoformat(),
            }
            validate_checkpoint(document, context, self.evidence_root)
            directory = safe_path(self.root, "checkpoints")
            directory.mkdir(mode=0o700, exist_ok=True)
            relative = "checkpoints/" + case_id + ".json"
            data = json_bytes(document)
            atomic_write(safe_path(self.root, relative), data)
            return {
                "run_id": self.run_id,
                "case_id": case_id,
                "checkpoint_path": relative,
                "sha256": hashlib.sha256(data).hexdigest(),
                "status": case["status"],
                "actual_requests": sum(
                    int(str(item["actual_requests"])) for item in objects(case["attempts"])
                ),
            }

    def load_verified(self) -> tuple[JsonObject, ...]:
        with locked(self.root, "checkpoints.lock"):
            context = read_document(safe_path(self.root, "execution.json"))
            validate_operational(context, "execution")
            if context["run_id"] != self.run_id:
                raise ValueError("checkpoint_identity")
            directory = safe_path(self.root, "checkpoints")
            documents: list[JsonObject] = []
            for candidate in sorted(directory.glob("*.json")):
                path = safe_path(self.root, candidate.relative_to(self.root).as_posix())
                document = read_document(path)
                validate_checkpoint(document, context, self.evidence_root)
                if path.name != str(document["case_id"]) + ".json":
                    raise ValueError("checkpoint_filename")
                state = next(
                    item
                    for item in objects(context["case_states"])
                    if item["case_id"] == document["case_id"]
                )
                expected = state["checkpoint_sha256"]
                if (
                    expected is not None
                    and hashlib.sha256(path.read_bytes()).hexdigest() != expected
                ):
                    raise ValueError("checkpoint_hash_mismatch")
                documents.append(document)
            expected_ids = {
                str(item["case_id"])
                for item in objects(context["case_states"])
                if item["checkpoint_path"] is not None
            }
            if expected_ids - {str(document["case_id"]) for document in documents}:
                raise ValueError("missing_checkpoint")
            return tuple(documents)
