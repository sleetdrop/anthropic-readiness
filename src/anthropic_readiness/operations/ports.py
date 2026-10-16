"""Application execution ports and sticky thread-safe cancellation."""

from threading import Lock
from typing import Protocol

from anthropic_readiness.models import EvidenceRef, JsonObject
from anthropic_readiness.operations.models import WorkerEvent


class CancelToken:
    def __init__(self) -> None:
        self._lock = Lock()
        self._reason: str | None = None

    def cancel(self, reason_code: str) -> None:
        with self._lock:
            if self._reason is None:
                self._reason = reason_code

    @property
    def requested(self) -> bool:
        with self._lock:
            return self._reason is not None

    @property
    def reason_code(self) -> str | None:
        with self._lock:
            return self._reason


class CredentialProvider(Protocol):
    def resolve(self) -> str | None: ...


class ExecutionObserver(Protocol):
    def begin(self, context: JsonObject) -> None: ...

    def emit(self, event: WorkerEvent) -> None: ...

    def commit_case(self, case: JsonObject, refs: tuple[EvidenceRef, ...]) -> None: ...
