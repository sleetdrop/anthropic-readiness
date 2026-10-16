"""Disposable spawned processes for supervision and parent-loss fault boundaries."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from multiprocessing.connection import Connection
from pathlib import Path
from threading import Event

from anthropic_readiness.credentials import MemoryCredentials
from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.models import JsonObject
from tests.operation_fixtures import context


def unresponsive_worker(
    plan: JsonObject, root: Path, control: Connection, observations: Connection
) -> None:
    control.recv_bytes()
    Event().wait(60)


def hostile_worker(
    plan: JsonObject, root: Path, control: Connection, observations: Connection
) -> None:
    message = json.loads(control.recv_bytes())
    observations.send_bytes(
        json.dumps(
            {
                "type": "event",
                "receipt_id": 1,
                "event": {
                    "kind": "request_started",
                    "occurred_at": datetime.now(UTC).isoformat(),
                    "elapsed_ms": 0,
                    "payload": {"credential": message["credential"]},
                },
            }
        ).encode()
    )
    Event().wait(60)


def leaky_begin_worker(
    plan: JsonObject, root: Path, control: Connection, observations: Connection
) -> None:
    initialization = json.loads(control.recv_bytes())
    value = context()
    value.update(
        {
            "run_id": root.name,
            "target": plan["target"],
            "plan": plan["plan"],
            "config_sha256": plan["config_sha256"],
            "warnings": [initialization["credential"]],
        }
    )
    observations.send_bytes(
        json.dumps({"type": "begin", "receipt_id": 1, "context": value}).encode()
    )
    Event().wait(60)


class CheckpointBarrierManager(JobManager):
    def __init__(self, store: JobStore, notification: Connection) -> None:
        super().__init__(store, credential_allowlist={})
        self.notification = notification

    def _accept_message(self, message: JsonObject) -> None:
        event = message.get("event")
        if isinstance(event, dict) and event.get("kind") == "case_committed":
            assert self._active is not None
            self.notification.send_bytes(
                json.dumps(
                    {"checkpoint": "pending_ack", "worker_pid": self._active.process.pid}
                ).encode()
            )
            Event().wait(60)
        super()._accept_message(message)


def parent_with_checkpoint_barrier(
    root: Path, target: JsonObject, notification: Connection
) -> None:
    store = JobStore(root)
    plan = store.create_plan(target, ("anthropic-basic",), "a" * 64, now=datetime.now(UTC))
    manager = CheckpointBarrierManager(store, notification)
    manager.start()
    job = manager.submit(plan.id, "a" * 64, "parent-loss-test", MemoryCredentials(None))
    notification.send_bytes(job.id.encode())
    Event().wait(60)
