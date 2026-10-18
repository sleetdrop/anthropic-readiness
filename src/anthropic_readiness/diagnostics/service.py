"""Shared diagnostic operations for CLI and local Web adapters."""

from datetime import datetime
from pathlib import Path

from anthropic_readiness.diagnostics.models import BaselineRecord
from anthropic_readiness.diagnostics.store import DiagnosticStore
from anthropic_readiness.models import JsonObject
from anthropic_readiness.report_models import ReportSource


class DiagnosticService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.store = DiagnosticStore(root / "diagnostics")

    def preview(self, archive: Path, owner: str, *, now: datetime) -> JsonObject:
        return self.store.preview(archive, owner, now=now)

    def commit(self, preview_id: str, owner: str, *, now: datetime) -> BaselineRecord:
        return self.store.commit(preview_id, owner, now=now)

    def get(self, baseline_id: str) -> BaselineRecord:
        return self.store.get(baseline_id)

    def load_source(self, baseline_id: str) -> ReportSource:
        return self.store.load_source(baseline_id)
