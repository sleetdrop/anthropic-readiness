"""Application execution ports and sticky thread-safe cancellation."""

from collections.abc import Callable
from threading import Lock
from typing import Protocol

from anthropic_readiness.models import EvidenceRef, JsonObject
from anthropic_readiness.operations.models import WorkerEvent


class CancelToken:
    def __init__(self) -> None:
        self._lock = Lock()
        self._reason: str | None = None
        self._callbacks: list[Callable[[], None]] = []

    def cancel(self, reason_code: str) -> None:
        with self._lock:
            if self._reason is None:
                self._reason = reason_code
                callbacks = tuple(self._callbacks)
            else:
                callbacks = ()
        for callback in callbacks:
            callback()

    def register(self, callback: Callable[[], None]) -> Callable[[], None]:
        with self._lock:
            cancelled = self._reason is not None
            if not cancelled:
                self._callbacks.append(callback)
        if cancelled:
            callback()

        def unsubscribe() -> None:
            with self._lock:
                if callback in self._callbacks:
                    self._callbacks.remove(callback)

        return unsubscribe

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

    def commit_case(self, case: JsonObject, refs: tuple[EvidenceRef, ...]) -> JsonObject: ...


class ObservationError(RuntimeError):
    """A mandatory observation failed; never reinterpret it as target behavior."""


def emit_observation(observer: ExecutionObserver | None, event: WorkerEvent) -> None:
    if observer is not None:
        try:
            observer.emit(event)
        except Exception as exc:
            raise ObservationError("observation_failed") from exc
