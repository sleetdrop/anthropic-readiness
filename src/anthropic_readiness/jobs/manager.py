"""One local owner supervises explicit jobs and sequences durable observations."""

from __future__ import annotations

import hashlib
import multiprocessing
import sqlite3
import time
from collections import deque
from collections.abc import Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from multiprocessing.connection import Connection, wait
from multiprocessing.process import BaseProcess
from pathlib import Path
from threading import Condition, Thread
from typing import cast

from anthropic_readiness.application import build_plan
from anthropic_readiness.credentials import AllowlistedCredentials, MemoryCredentials
from anthropic_readiness.diagnostics.context import bind_run_context
from anthropic_readiness.evidence import json_bytes, safe_path, verify_evidence
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.jobs.worker import (
    MAX_CREDENTIAL_BYTES,
    receive_message,
    send_message,
    worker_main,
)
from anthropic_readiness.models import JsonObject, RunResult, object_value
from anthropic_readiness.operations.checkpoints import checkpoint_refs
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.operations.journal import RunJournal
from anthropic_readiness.operations.models import (
    EventKind,
    JobRecord,
    JobState,
    ProgressEvent,
    WorkerEvent,
)
from anthropic_readiness.operations.ports import CredentialProvider
from anthropic_readiness.operations.reduction import TERMINAL, objects
from anthropic_readiness.operations.storage import locked, read_document
from anthropic_readiness.schema import result_from_document


@dataclass
class OwnedWorker:
    run_id: str
    process: BaseProcess
    control: Connection
    observations: Connection
    receipt: int = 0
    cancel_at: float | None = None
    retired_at: float | None = None
    failure: str | None = None


class JobManager:
    def __init__(self, store: JobStore, *, credential_allowlist: Mapping[str, str]) -> None:
        self.store = store
        self._allowlist = dict(credential_allowlist)
        self._condition = Condition()
        self._ownership: AbstractContextManager[None] | None = None
        self._thread: Thread | None = None
        self._stopping = False
        self._faulted = False
        self._queue: deque[str] = deque()
        self._credentials: dict[str, str | None] = {}
        self._active: OwnedWorker | None = None

    @property
    def credential_references(self) -> tuple[str, ...]:
        return tuple(sorted(self._allowlist))

    def credentials_for_reference(self, name: str) -> CredentialProvider:
        return AllowlistedCredentials(name, self._allowlist)

    def _root(self, run_id: str) -> Path:
        return safe_path(self.store.root, "runs/" + run_id)

    def _journal(self, run_id: str) -> RunJournal:
        root = self._root(run_id)
        return RunJournal(root / "operations", run_id, evidence_root=root / "assessment")

    def _ensure_journal(self, run_id: str) -> RunJournal:
        journal = self._journal(run_id)
        if safe_path(journal.root, "execution.json").exists():
            return journal
        job = self.store.get_job(run_id)
        frozen = self.store.get_admitted_plan(run_id)
        plan = build_plan(frozen.target, frozen.profiles)
        state = "queued" if job.state == "queued" else "running"
        journal.begin(
            {
                "schema_version": "1.0",
                "run_id": run_id,
                "config_sha256": frozen.config_sha256,
                "target": frozen.target,
                "contract": {**plan.bundle.manifest, "version_semantics": "unverified"},
                "plan": frozen.plan,
                "state": state,
                "sequence": 0,
                "case_states": [
                    {
                        "case_id": case.id,
                        "state": "pending",
                        "checkpoint_path": None,
                        "checkpoint_sha256": None,
                    }
                    for case in plan.cases
                ],
                "actual_requests": 0,
                "started_at": job.created_at,
                "updated_at": job.created_at,
                "finished_at": None,
                "elapsed_ms": 0,
                "spans": [],
                "warnings": [],
                "result_sha256": None,
                "terminal_reason": None,
            }
        )
        return journal

    def _append(self, run_id: str, event: WorkerEvent) -> None:
        entry = self._journal(run_id).append(event)
        self.store.observe(
            run_id,
            entry.sequence,
            "assessment/result.json" if event.kind == "result_committed" else None,
        )

    def _parent_event(self, journal: RunJournal, kind: EventKind, payload: JsonObject) -> None:
        snapshot = journal.snapshot()
        self._append(
            journal.run_id,
            WorkerEvent(
                kind, datetime.now(UTC).isoformat(), float(str(snapshot["elapsed_ms"])), payload
            ),
        )

    def _finish(self, run_id: str, terminal: JobState, reason: str | None = None) -> JobRecord:
        job = self.store.get_job(run_id)
        if job.state in TERMINAL:
            return job
        try:
            journal = self._ensure_journal(run_id)
            snapshot = journal.snapshot()
            before = str(snapshot["state"])
            if terminal == "cancelled" and before == "running":
                self._parent_event(
                    journal,
                    "job_transition",
                    {"from": before, "to": "cancelling", "reason_code": "cancel_requested"},
                )
                before = "cancelling"
            if before not in TERMINAL:
                self._parent_event(
                    journal,
                    "job_transition",
                    {
                        "from": before,
                        "to": terminal,
                        **({"reason_code": reason} if reason is not None else {}),
                    },
                )
            elif before != terminal:
                raise ValueError("terminal_execution_mismatch")
            current = journal.snapshot()
            self.store.observe(
                run_id,
                int(str(current["sequence"])),
                "assessment/result.json" if current["result_sha256"] is not None else None,
            )
        except (OSError, ValueError, RuntimeError, sqlite3.Error):
            # Do not dispatch more work if mandatory operational storage is unusable.
            self._faulted = True
            terminal = "error"
        self._credentials.pop(run_id, None)
        return self.store.transition(run_id, job.state, terminal)

    def _verified_result(self, run_id: str) -> RunResult:
        root = self._root(run_id)
        path = safe_path(root, "assessment/result.json")
        result = result_from_document(read_document(path))
        frozen = self.store.get_admitted_plan(run_id)
        expected_plan = {**frozen.plan, "actual_requests": result.plan["actual_requests"]}
        if (
            result.run_id != run_id
            or result.mode != "live"
            or result.target != frozen.target
            or result.plan != expected_plan
        ):
            raise ValueError("result_identity")
        refs = list(result.evidence)
        for case in result.cases:
            assertions = objects(case["preconditions"])
            for attempt in objects(case["attempts"]):
                assertions.extend(objects(attempt["assertions"]))
            for assertion in assertions:
                refs.extend(checkpoint_refs({"evidence_refs": assertion["evidence_refs"]}))
        if verify_evidence(root / "assessment", refs):
            raise ValueError("result_evidence_invalid")
        snapshot = self._journal(run_id).snapshot()
        expected = snapshot["result_sha256"]
        if expected is not None and hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("result_hash_mismatch")
        return result

    def _reconcile(self) -> None:
        for state in ("queued", "running", "cancelling"):
            cursor: str | None = None
            while True:
                page = self.store.history({"state": state}, cursor, 100)
                for item in objects(page["items"]):
                    job = object_value(item["job"])
                    run_id = str(job["id"])
                    path = safe_path(self._root(run_id), "assessment/result.json")
                    if not path.exists():
                        self._finish(run_id, "interrupted", "service_restarted")
                        continue
                    try:
                        result = self._verified_result(run_id)
                        journal = self._journal(run_id)
                        snapshot = journal.snapshot()
                        if snapshot["result_sha256"] is None:
                            self._parent_event(
                                journal,
                                "result_committed",
                                {
                                    "result_path": "result.json",
                                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                },
                            )
                        terminal = self._result_terminal(result, self.store.get_job(run_id))
                        self._finish(run_id, terminal, "recovered_final_result")
                    except (OSError, ValueError, RuntimeError):
                        self._finish(run_id, "error", "result_integrity_error")
                cursor = str(page["next_cursor"]) if page["next_cursor"] is not None else None
                if cursor is None:
                    break

    def start(self) -> None:
        with self._condition:
            if self._thread is not None:
                return
            ownership = locked(self.store.root, "service.lock", blocking=False)
            try:
                ownership.__enter__()
            except OSError as exc:
                raise ValueError("service_already_running") from exc
            self._ownership = ownership
            try:
                self._reconcile()
                self._stopping = False
                self._thread = Thread(
                    target=self._supervise, name="assessment-manager", daemon=True
                )
                self._thread.start()
            except BaseException:
                self._ownership.__exit__(None, None, None)
                self._ownership = None
                raise

    def submit(
        self, plan_id: str, session_id: str, idempotency_key: str, credentials: CredentialProvider
    ) -> JobRecord:
        with self._condition:
            if self._thread is None or self._stopping or self._faulted:
                raise ValueError("service_unavailable")
            admission = self.store.admit(
                plan_id, session_id, idempotency_key, now=datetime.now(UTC)
            )
            if not admission.created:
                return admission.job
            job = admission.job
            try:
                plan = self.store.get_admitted_plan(job.id)
                target = object_value(plan.target["auth"])
                secret = None
                if target["mode"] == "api_key":
                    secret = credentials.resolve()
                    if secret is None:
                        secret = self._allowlist.get(str(target["credential_env"]))
                    if secret is None:
                        return self._finish(job.id, "error", "missing_credential")
                    MemoryCredentials(secret).resolve()
                    if len(secret.encode()) > MAX_CREDENTIAL_BYTES:
                        raise ValueError("invalid_credential")
                self._credentials[job.id] = secret
                self._queue.append(job.id)
                self._condition.notify_all()
                return job
            except Exception:
                # Providers are an application boundary; exception text is private.
                return self._finish(job.id, "error", "invalid_credential")

    def _spawn(self, run_id: str) -> None:
        plan = self.store.get_admitted_plan(run_id)
        context = multiprocessing.get_context("spawn")
        parent_control, child_control = context.Pipe(duplex=True)
        parent_observations, child_observations = context.Pipe(duplex=False)
        process = context.Process(
            target=worker_main,
            args=(plan.to_json(), self._root(run_id), child_control, child_observations),
            name="readiness-" + run_id[:8],
        )
        self.store.transition(run_id, "queued", "running")
        try:
            initialization: JsonObject = {
                "type": "initialize",
                "credential": self._credentials.pop(run_id),
            }
            diagnostic_context = self.store.get_plan_context(plan.id)
            if diagnostic_context is not None:
                initialization["context_sha256"] = hashlib.sha256(
                    json_bytes(bind_run_context(diagnostic_context, run_id))
                ).hexdigest()
            process.start()
            self._active = OwnedWorker(run_id, process, parent_control, parent_observations)
            send_message(parent_control, initialization)
        except (OSError, ValueError, KeyError):
            parent_control.close()
            parent_observations.close()
            if process.pid is not None and process.is_alive():
                process.kill()
                process.join(timeout=1)
            process.close()
            self._active = None
            self._finish(run_id, "error", "worker_start_failed")
        finally:
            child_control.close()
            child_observations.close()

    @staticmethod
    def _result_terminal(result: RunResult, job: JobRecord) -> JobState:
        if job.state == "cancelling":
            return "cancelled"
        if result.execution_environment.get("internal_error") is not None:
            return "error"
        if result.execution_environment.get("interruption") is not None:
            return "interrupted"
        return "completed"

    def _accept_message(self, message: JsonObject) -> None:
        active = self._active
        if active is None:
            raise ValueError("worker_not_owned")
        if (
            set(message) == {"type", "code"}
            and message["type"] == "failed"
            and message["code"] == "worker_execution_error"
        ):
            self._finish(active.run_id, "error", "worker_execution_error")
            self._terminate()
            return
        if (
            message.get("type") not in {"begin", "event"}
            or type(message.get("receipt_id")) is not int
            or message["receipt_id"] != active.receipt + 1
        ):
            raise ValueError("ipc_message_invalid")
        job = self.store.get_job(active.run_id)
        if message["type"] == "begin":
            if set(message) != {"type", "receipt_id", "context"} or active.receipt != 0:
                raise ValueError("ipc_begin_invalid")
            value = object_value(message["context"])
            validate_operational(value, "execution")
            plan = self.store.get_admitted_plan(active.run_id)
            assessment = build_plan(plan.target, plan.profiles)
            expected: JsonObject = {
                "run_id": active.run_id,
                "config_sha256": plan.config_sha256,
                "target": plan.target,
                "plan": plan.plan,
                "contract": {**assessment.bundle.manifest, "version_semantics": "unverified"},
                "state": "running",
                "sequence": 0,
                "actual_requests": 0,
                "case_states": [
                    {
                        "case_id": case.id,
                        "state": "pending",
                        "checkpoint_path": None,
                        "checkpoint_sha256": None,
                    }
                    for case in assessment.cases
                ],
                "finished_at": None,
                "elapsed_ms": 0,
                "spans": [],
                "warnings": [],
                "result_sha256": None,
                "terminal_reason": None,
            }
            if (
                any(value[key] != item for key, item in expected.items())
                or value["updated_at"] != value["started_at"]
            ):
                raise ValueError("ipc_context_identity")
            self._journal(active.run_id).begin(value)
        else:
            if set(message) != {"type", "receipt_id", "event"}:
                raise ValueError("ipc_event_invalid")
            raw = object_value(message["event"])
            if set(raw) != {"kind", "occurred_at", "elapsed_ms", "payload"}:
                raise ValueError("ipc_event_invalid")
            event = WorkerEvent(
                cast(EventKind, raw["kind"]),
                str(raw["occurred_at"]),
                float(str(raw["elapsed_ms"])),
                object_value(raw["payload"]),
            )
            # Validate even advisory terminal transitions before discarding duplicates.
            validate_operational(
                {
                    "schema_version": "1.0",
                    "run_id": active.run_id,
                    "sequence": max(1, job.last_sequence + 1),
                    **event.to_json(),
                },
                "progress-event",
            )
            if event.kind == "job_transition":
                if event.payload.get("reason_code") not in {
                    None,
                    "cancel_requested",
                    "cancelled",
                    "internal_error",
                }:
                    raise ValueError("ipc_reason_code_invalid")
                if job.state not in TERMINAL and event.payload["to"] in TERMINAL:
                    raise ValueError("ipc_premature_terminal")
            if job.state in TERMINAL:
                if event.kind != "job_transition":
                    raise ValueError("event_after_terminal")
            else:
                self._append(active.run_id, event)
                if event.kind == "result_committed":
                    result = self._verified_result(active.run_id)
                    terminal = self._result_terminal(result, job)
                    if self._stopping:
                        terminal = "interrupted"
                    self._finish(
                        active.run_id,
                        terminal,
                        "service_shutdown"
                        if self._stopping
                        else "cancelled"
                        if terminal == "cancelled"
                        else None,
                    )
                    active.retired_at = time.monotonic()
        active.receipt = int(str(message["receipt_id"]))
        send_message(active.control, {"type": "ack", "receipt_id": active.receipt})

    def _terminate(self) -> None:
        active = self._active
        if active is None:
            return
        if active.process.is_alive():
            active.process.terminate()
            active.process.join(timeout=0.3)
        if active.process.is_alive():
            active.process.kill()
            active.process.join(timeout=1)
        self._release()

    def _release(self) -> None:
        active = self._active
        if active is None:
            return
        active.process.join(timeout=0.1)
        active.control.close()
        active.observations.close()
        if not active.process.is_alive():
            active.process.close()
        self._credentials.pop(active.run_id, None)
        self._active = None
        self._condition.notify_all()

    def _supervise(self) -> None:
        while True:
            with self._condition:
                if self._active is None:
                    if self._stopping:
                        return
                    if self._queue and not self._faulted:
                        run_id = self._queue.popleft()
                        try:
                            self._spawn(run_id)
                        except (OSError, ValueError, RuntimeError):
                            self._finish(run_id, "error", "worker_start_failed")
                    if self._active is None:
                        self._condition.wait(timeout=0.1)
                        continue
                active = self._active
            if active is None:
                continue
            ready = wait([active.observations, active.process.sentinel], timeout=0.05)
            with self._condition:
                if active is not self._active:
                    continue
                if active.failure is not None:
                    self._terminate()
                    self._finish(active.run_id, "interrupted", active.failure)
                    continue
                try:
                    if active.observations in ready:
                        self._accept_message(receive_message(active.observations))
                    elif active.process.sentinel in ready:
                        if self.store.get_job(active.run_id).state not in TERMINAL:
                            self._finish(active.run_id, "interrupted", "worker_exited")
                        self._release()
                except EOFError:
                    if self.store.get_job(active.run_id).state not in TERMINAL:
                        self._finish(active.run_id, "interrupted", "worker_control_closed")
                    self._terminate()
                except (OSError, sqlite3.Error):
                    self._faulted = True
                    try:
                        self._finish(active.run_id, "error", "worker_observation_failed")
                    finally:
                        self._terminate()
                except (ValueError, RuntimeError, UnicodeError):
                    try:
                        self._finish(active.run_id, "error", "worker_observation_failed")
                    finally:
                        self._terminate()
                if self._active is active:
                    if active.cancel_at is not None and time.monotonic() - active.cancel_at >= 5:
                        self._terminate()
                        self._finish(active.run_id, "interrupted", "cancel_grace_exceeded")
                    elif (
                        active.retired_at is not None and time.monotonic() - active.retired_at >= 5
                    ):
                        self._terminate()
                if self._faulted:
                    for run_id in tuple(self._queue):
                        self._finish(run_id, "error", "operational_storage_unavailable")
                    self._queue.clear()
                    self._credentials.clear()

    def cancel(self, run_id: str) -> JobRecord:
        with self._condition:
            job = self.store.get_job(run_id)
            if job.state in TERMINAL or job.state == "cancelling":
                return job
            if job.state == "queued":
                if run_id in self._queue:
                    self._queue.remove(run_id)
                return self._finish(run_id, "cancelled", "cancelled_before_start")
            job = self.store.transition(run_id, "running", "cancelling")
            if self._active is not None and self._active.run_id == run_id:
                self._active.cancel_at = time.monotonic()
                try:
                    send_message(
                        self._active.control, {"type": "cancel", "reason_code": "user_cancelled"}
                    )
                except (OSError, EOFError):
                    self._active.failure = "worker_control_closed"
                    self._condition.notify_all()
            return job

    def snapshot(self, run_id: str) -> JsonObject:
        with self._condition:
            job = self.store.get_job(run_id)
            execution = None
            journal = self._journal(run_id)
            if safe_path(journal.root, "execution.json").exists():
                execution = journal.snapshot()
            return {"job": job.to_json(), "execution": execution}

    def worker_observation(self, run_id: str) -> JsonObject:
        """Observe the owned child; timestamps do not imply upstream activity."""
        with self._condition:
            self.store.get_job(run_id)
            state = "not_running"
            if self._active is not None and self._active.run_id == run_id:
                try:
                    state = "running" if self._active.process.is_alive() else "not_running"
                except (OSError, ValueError):
                    state = "unknown"
            return {"state": state, "observed_at": datetime.now(UTC).isoformat()}

    def read_events(
        self, run_id: str, after: int
    ) -> tuple[JsonObject, tuple[ProgressEvent, ...], bool]:
        if type(after) is not int or after < 0:
            raise ValueError("invalid_event_cursor")
        with self._condition:
            snapshot = self.snapshot(run_id)
            execution = snapshot["execution"]
            sequence = int(str(execution["sequence"])) if isinstance(execution, dict) else 0
            reset = after > sequence
            events = (
                self._journal(run_id).after(sequence if reset else after)
                if execution is not None
                else ()
            )
            return snapshot, events, reset

    def close(self) -> None:
        with self._condition:
            if self._thread is None:
                return
            self._stopping = True
            for run_id in tuple(self._queue):
                self._finish(run_id, "interrupted", "service_shutdown")
            self._queue.clear()
            self._credentials.clear()
            if self._active is not None:
                job = self.store.get_job(self._active.run_id)
                if job.state not in TERMINAL:
                    if job.state == "running":
                        self.store.transition(job.id, "running", "cancelling")
                    self._active.cancel_at = time.monotonic()
                    try:
                        send_message(
                            self._active.control,
                            {"type": "cancel", "reason_code": "service_shutdown"},
                        )
                    except (OSError, EOFError):
                        self._active.failure = "service_shutdown"
            self._condition.notify_all()
            thread = self._thread
        thread.join(timeout=8)
        with self._condition:
            if thread.is_alive():
                raise RuntimeError("manager_shutdown_timeout")
            self._thread = None
            if self._ownership is not None:
                self._ownership.__exit__(None, None, None)
                self._ownership = None
