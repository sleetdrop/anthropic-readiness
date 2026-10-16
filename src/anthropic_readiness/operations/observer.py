"""Lazy local progress adapter; assessment output is owned by the runner."""

from pathlib import Path

from anthropic_readiness.models import EvidenceRef, JsonObject
from anthropic_readiness.operations.checkpoints import CheckpointStore
from anthropic_readiness.operations.journal import RunJournal
from anthropic_readiness.operations.models import WorkerEvent


class DiskExecutionObserver:
    def __init__(self, operations_root: Path, evidence_root: Path) -> None:
        self.operations_root = operations_root
        self.evidence_root = evidence_root
        self._journal: RunJournal | None = None
        self._store: CheckpointStore | None = None

    def begin(self, context: JsonObject) -> None:
        run_id = str(context["run_id"])
        self._journal = RunJournal(self.operations_root, run_id, evidence_root=self.evidence_root)
        self._store = CheckpointStore(
            self.operations_root, run_id, evidence_root=self.evidence_root
        )
        self._journal.begin(context)

    def emit(self, event: WorkerEvent) -> None:
        if self._journal is None:
            raise RuntimeError("observer_not_started")
        self._journal.append(event)

    def commit_case(self, case: JsonObject, refs: tuple[EvidenceRef, ...]) -> JsonObject:
        if self._store is None:
            raise RuntimeError("observer_not_started")
        return self._store.commit(case, refs)
