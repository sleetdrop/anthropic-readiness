"""Single-writer durable events and recoverable operational snapshots."""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import cast

from anthropic_readiness.evidence import atomic_write, safe_path, verify_evidence
from anthropic_readiness.models import JsonObject, object_value, strict_json
from anthropic_readiness.operations.checkpoints import validate_checkpoint
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.operations.models import EventKind, ProgressEvent, WorkerEvent
from anthropic_readiness.operations.reduction import objects, reduce_snapshot
from anthropic_readiness.operations.storage import (
    MAX_DOCUMENT_BYTES,
    MAX_JOURNAL_BYTES,
    locked,
    read_document,
    replace_snapshot,
)
from anthropic_readiness.schema import result_from_document


class RunJournal:
    def __init__(self, root: Path, run_id: str, *, evidence_root: Path | None = None) -> None:
        self.root = root
        self.run_id = run_id
        self.evidence_root = evidence_root if evidence_root is not None else root.parent
        self._mutex = Lock()

    def begin(self, context: JsonObject) -> None:
        validate_operational(context, "execution")
        if context["run_id"] != self.run_id:
            raise ValueError("execution_identity")
        planned = objects(object_value(context["plan"])["cases"])
        case_ids = [item["case_id"] for item in objects(context["case_states"])]
        if case_ids != [item["id"] for item in planned] or len(set(map(str, case_ids))) != len(
            case_ids
        ):
            raise ValueError("execution_case_inventory")
        if context["config_sha256"] != object_value(context["plan"])["config_fingerprint"]:
            raise ValueError("execution_config_identity")
        with self._mutex, locked(self.root):
            path = safe_path(self.root, "execution.json")
            if path.exists():
                previous = read_document(path)
                if any(
                    previous[key] != context[key]
                    for key in ("run_id", "config_sha256", "target", "contract", "plan")
                ):
                    raise ValueError("execution_identity")
                return
            if context["sequence"] != 0 or context["state"] not in {"queued", "running"}:
                raise ValueError("execution_initial_state")
            if safe_path(self.root, "events.jsonl").exists():
                raise ValueError("execution_orphan_journal")
            atomic_write(path, json.dumps(context, ensure_ascii=False, allow_nan=False).encode())
            atomic_write(safe_path(self.root, "events.jsonl"), b"")

    def _read(self) -> tuple[tuple[ProgressEvent, ...], bool]:
        path = safe_path(self.root, "events.jsonl")
        if not path.exists():
            return (), False
        with path.open("rb") as stream:
            data = stream.read(MAX_JOURNAL_BYTES + 1)
        if len(data) > MAX_JOURNAL_BYTES:
            raise ValueError("journal_size_limit")
        lines = data.splitlines(keepends=True)
        entries: list[ProgressEvent] = []
        torn = False
        for index, line in enumerate(lines):
            if index == len(lines) - 1 and not line.endswith(b"\n"):
                torn = True
                break
            try:
                raw = object_value(strict_json(line.decode()))
                validate_operational(raw, "progress-event")
                if raw["run_id"] != self.run_id or raw["sequence"] != len(entries) + 1:
                    raise ValueError("journal_sequence_identity")
                entries.append(
                    ProgressEvent(
                        "1.0",
                        self.run_id,
                        int(str(raw["sequence"])),
                        WorkerEvent(
                            cast(EventKind, raw["kind"]),
                            str(raw["occurred_at"]),
                            float(str(raw["elapsed_ms"])),
                            object_value(raw["payload"]),
                        ),
                    )
                )
            except (ValueError, UnicodeError) as exc:
                raise ValueError("journal_record_invalid") from exc
        return tuple(entries), torn

    def _verify_event(self, entry: ProgressEvent, snapshot: JsonObject) -> None:
        payload = entry.event.payload
        if entry.event.kind == "case_committed":
            relative = str(payload["checkpoint_path"])
            if relative != "checkpoints/" + str(payload["case_id"]) + ".json":
                raise ValueError("checkpoint_reference_path")
            path = safe_path(self.root, relative)
            data = path.read_bytes()
            if (
                len(data) > MAX_DOCUMENT_BYTES
                or hashlib.sha256(data).hexdigest() != payload["sha256"]
            ):
                raise ValueError("checkpoint_hash_mismatch")
            document = object_value(strict_json(data.decode()))
            validate_checkpoint(document, snapshot, self.evidence_root)
            case = object_value(document["case_record"])
            requests = sum(int(str(item["actual_requests"])) for item in objects(case["attempts"]))
            if (
                case["id"] != payload["case_id"]
                or case["status"] != payload["status"]
                or requests != payload["actual_requests"]
            ):
                raise ValueError("checkpoint_receipt_mismatch")
        elif entry.event.kind == "result_committed":
            if payload["result_path"] != "result.json":
                raise ValueError("result_reference_path")
            data = safe_path(self.evidence_root, "result.json").read_bytes()
            if (
                len(data) > MAX_DOCUMENT_BYTES
                or hashlib.sha256(data).hexdigest() != payload["sha256"]
            ):
                raise ValueError("result_hash_mismatch")
            result = result_from_document(object_value(strict_json(data.decode())))
            if (
                result.run_id != self.run_id
                or result.plan["config_fingerprint"] != snapshot["config_sha256"]
                or result.plan["actual_requests"] != snapshot["actual_requests"]
            ):
                raise ValueError("result_execution_identity")
            if verify_evidence(self.evidence_root, result.evidence):
                raise ValueError("result_evidence_invalid")
            observed = {
                str(item["case_id"]): item["state"] for item in objects(snapshot["case_states"])
            }
            if any(observed.get(str(case["id"])) != case["status"] for case in result.cases):
                raise ValueError("result_case_status_mismatch")

    def _snapshot(self) -> tuple[JsonObject, bool]:
        snapshot = read_document(safe_path(self.root, "execution.json"))
        validate_operational(snapshot, "execution")
        if snapshot["run_id"] != self.run_id:
            raise ValueError("execution_identity")
        entries, torn = self._read()
        sequence = int(str(snapshot["sequence"]))
        if sequence > len(entries):
            raise ValueError("journal_snapshot_ahead")
        for entry in entries[sequence:]:
            self._verify_event(entry, snapshot)
            snapshot = reduce_snapshot(snapshot, entry)
        if torn:
            warnings = list(snapshot["warnings"]) if isinstance(snapshot["warnings"], list) else []
            if "uncommitted_event_tail" not in warnings:
                warnings.append("uncommitted_event_tail")
            snapshot.update(
                {
                    "state": "interrupted",
                    "terminal_reason": "uncommitted_event_tail",
                    "warnings": warnings,
                }
            )
        return snapshot, torn

    def append(self, event: WorkerEvent) -> ProgressEvent:
        with self._mutex, locked(self.root):
            snapshot, torn = self._snapshot()
            if torn:
                raise ValueError("journal_torn_tail_read_only")
            entry = ProgressEvent("1.0", self.run_id, int(str(snapshot["sequence"])) + 1, event)
            validate_operational(entry.to_json(), "progress-event")
            self._verify_event(entry, snapshot)
            updated = reduce_snapshot(snapshot, entry)
            validate_operational(updated, "execution")
            data = (
                json.dumps(
                    entry.to_json(), ensure_ascii=False, separators=(",", ":"), allow_nan=False
                )
                + "\n"
            ).encode()
            path = safe_path(self.root, "events.jsonl")
            if path.stat().st_size + len(data) > MAX_JOURNAL_BYTES:
                raise ValueError("journal_size_limit")
            fd = os.open(path, os.O_WRONLY | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(fd, "ab") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(fd)
            replace_snapshot(self.root, updated)
            return entry

    def after(self, sequence: int) -> tuple[ProgressEvent, ...]:
        if type(sequence) is not int or sequence < 0:
            raise ValueError("invalid_journal_cursor")
        with self._mutex, locked(self.root):
            entries, _ = self._read()
            return tuple(entry for entry in entries if entry.sequence > sequence)

    def snapshot(self) -> JsonObject:
        with self._mutex, locked(self.root):
            snapshot, _ = self._snapshot()
            return deepcopy(snapshot)
