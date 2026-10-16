"""Spawned assessment worker with bounded JSON pipes and parent acknowledgements."""

from __future__ import annotations

import os
from contextlib import suppress
from multiprocessing.connection import Connection
from pathlib import Path
from threading import Condition, Event, Thread, Timer

from anthropic_readiness.application import build_plan, run_assessment
from anthropic_readiness.config import strings
from anthropic_readiness.credentials import MemoryCredentials
from anthropic_readiness.evidence import json_bytes
from anthropic_readiness.models import EvidenceRef, JsonObject, object_value, strict_json
from anthropic_readiness.operations.checkpoints import CheckpointStore
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.operations.models import WorkerEvent
from anthropic_readiness.operations.ports import CancelToken, ObservationError

MAX_IPC_BYTES = 262144
MAX_CREDENTIAL_BYTES = 16384


def send_message(channel: Connection, message: JsonObject) -> None:
    data = json_bytes(message)
    if len(data) > MAX_IPC_BYTES:
        raise ValueError("ipc_size_limit")
    channel.send_bytes(data)


def receive_message(channel: Connection) -> JsonObject:
    return object_value(strict_json(channel.recv_bytes(MAX_IPC_BYTES).decode()))


class PipeObserver:
    def __init__(
        self, root: Path, control: Connection, observations: Connection, token: CancelToken
    ) -> None:
        self.root = root
        self.control = control
        self.observations = observations
        self.token = token
        self._condition = Condition()
        self._receipt = 0
        self._acknowledged = 0
        self._lost = False
        self._stopped = Event()
        self._hard_stop: Timer | None = None
        self._watchdog = Thread(target=self._watch, name="parent-control", daemon=True)
        self._watchdog.start()

    def _watch(self) -> None:
        try:
            while not self._stopped.is_set():
                message = receive_message(self.control)
                if (
                    set(message) == {"type", "receipt_id"}
                    and message["type"] == "ack"
                    and type(message["receipt_id"]) is int
                ):
                    with self._condition:
                        if message["receipt_id"] != self._acknowledged + 1:
                            raise ValueError("ipc_ack_sequence")
                        self._acknowledged = message["receipt_id"]
                        self._condition.notify_all()
                elif (
                    set(message) == {"type", "reason_code"}
                    and message["type"] == "cancel"
                    and message["reason_code"] in {"user_cancelled", "service_shutdown"}
                ):
                    self.token.cancel(str(message["reason_code"]))
                else:
                    raise ValueError("ipc_control_invalid")
        except (EOFError, OSError, ValueError, UnicodeError):
            if not self._stopped.is_set():
                with self._condition:
                    self._lost = True
                    self._condition.notify_all()
                self._hard_stop = Timer(5, lambda: os._exit(71))
                self._hard_stop.daemon = True
                self._hard_stop.start()
                self.token.cancel("parent_lost")

    def _publish(self, message: JsonObject) -> None:
        with self._condition:
            if self._lost:
                raise ObservationError("parent_control_lost")
            self._receipt += 1
            message["receipt_id"] = self._receipt
            try:
                send_message(self.observations, message)
            except (OSError, EOFError) as exc:
                self.token.cancel("parent_lost")
                raise ObservationError("parent_control_lost") from exc
            self._condition.wait_for(lambda: self._acknowledged == self._receipt or self._lost)
            if self._lost:
                raise ObservationError("parent_control_lost")

    def begin(self, context: JsonObject) -> None:
        self._publish({"type": "begin", "context": context})

    def emit(self, event: WorkerEvent) -> None:
        self._publish({"type": "event", "event": event.to_json()})

    def commit_case(self, case: JsonObject, refs: tuple[EvidenceRef, ...]) -> JsonObject:
        return CheckpointStore(
            self.root / "operations", self.root.name, evidence_root=self.root / "assessment"
        ).commit(case, refs)

    def close(self) -> None:
        self._stopped.set()
        if self._hard_stop is not None:
            self._hard_stop.cancel()
        self.control.close()
        self.observations.close()
        self._watchdog.join(timeout=0.1)


def worker_main(
    plan: JsonObject, root: Path, control: Connection, observations: Connection
) -> None:
    observer: PipeObserver | None = None
    try:
        validate_operational(plan, "plan")
        initialization = receive_message(control)
        if set(initialization) != {"type", "credential"} or initialization["type"] != "initialize":
            raise ValueError("ipc_initialization_invalid")
        secret = initialization["credential"]
        if secret is not None and (
            not isinstance(secret, str) or len(secret.encode()) > MAX_CREDENTIAL_BYTES
        ):
            raise ValueError("invalid_credential")
        provider = MemoryCredentials(secret)
        provider.resolve()
        token = CancelToken()
        observer = PipeObserver(root, control, observations, token)
        assessment = build_plan(object_value(plan["target"]), strings(plan["profiles"]))
        if assessment.to_json() != plan["plan"]:
            raise ValueError("plan_integrity")
        run_assessment(
            assessment,
            root / "assessment",
            credentials=provider,
            observer=observer,
            control=token,
            run_id=root.name,
        )
    except (Exception, KeyboardInterrupt):
        # Only a fixed code crosses the boundary. Exceptions can contain model text.
        with suppress(OSError, EOFError, ValueError):
            send_message(observations, {"type": "failed", "code": "worker_execution_error"})
    finally:
        if observer is not None:
            observer.close()
        else:
            control.close()
            observations.close()
