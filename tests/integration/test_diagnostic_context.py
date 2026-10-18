"""Provenance is committed before requests and cannot be invented on recovery."""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from anthropic_readiness import application
from anthropic_readiness.config import Limits, load_target
from anthropic_readiness.credentials import MemoryCredentials
from anthropic_readiness.diagnostics import context as context_module
from anthropic_readiness.diagnostics import identity
from anthropic_readiness.diagnostics.context import context_for_plan
from anthropic_readiness.evidence import json_bytes
from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.models import Capture, JsonObject, RequestSpec, object_value, strict_json
from anthropic_readiness.operations.models import Admission
from anthropic_readiness.runner import RunPlan
from tests.acceptance.test_runner import FixtureTransport
from tests.diagnostic_fixtures import recipe_fixture
from tests.http_server import SyntheticServer
from tests.integration.test_history_migration import legacy_store
from tests.integration.test_job_manager import wait_terminal

ROOT = Path(__file__).resolve().parents[2]
SESSION = "a" * 64


def plan_fixture(url: str | None = None) -> RunPlan:
    target = load_target(ROOT / "examples/target.yaml")
    if url is not None:
        target = replace(target, messages_url=url)
    return application.build_plan(target.to_json(), ["anthropic-basic"])


def document(path: Path) -> JsonObject:
    return object_value(strict_json(path.read_text()))


def copy_implementation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "installed"
    shutil.copytree(identity._package_root(), root, ignore=shutil.ignore_patterns("__pycache__"))
    monkeypatch.setattr(identity, "_package_root", lambda: root)
    return root


def test_context_exists_before_first_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = plan_fixture()
    context = context_for_plan(plan, recipe_fixture(plan)).document
    original = deepcopy(context)
    output = tmp_path / "assessment"

    class CheckingTransport(FixtureTransport):
        def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
            saved = document(output / "assessment-context.json")
            assert saved["run_id"] == "11111111-1111-4111-8111-111111111111"
            assert saved["recipe_sha256"] == context["recipe_sha256"]
            return super().send(request, limits, deadline)

    transport = CheckingTransport()
    monkeypatch.setattr(application, "HttpTransport", lambda: transport)
    result = application.run_assessment(
        plan,
        output,
        credentials=MemoryCredentials(None),
        assessment_context=context,
        run_id="11111111-1111-4111-8111-111111111111",
    )
    assert transport.calls == 3
    assert context == original
    assert result.run_id == document(output / "assessment-context.json")["run_id"]
    final = document(output / "assessment-context-verification.json")
    assert final["identity_status"] == "unchanged"
    assert (
        final["context_sha256"]
        == hashlib.sha256((output / "assessment-context.json").read_bytes()).hexdigest()
    )
    assert final["reasons"] == []
    assert (
        final["result_sha256"] == hashlib.sha256((output / "result.json").read_bytes()).hexdigest()
    )


def test_context_does_not_touch_an_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = plan_fixture()
    context = context_for_plan(plan, recipe_fixture(plan)).document
    output = tmp_path / "assessment"
    output.mkdir()
    (output / "assessment-context.json").write_bytes(b"historical bytes")
    transport = FixtureTransport()
    monkeypatch.setattr(application, "HttpTransport", lambda: transport)
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    with pytest.raises(FileExistsError):
        application.run_assessment(
            plan, output, credentials=MemoryCredentials(None), assessment_context=context
        )
    assert transport.calls == 0
    assert {path.name: path.read_bytes() for path in output.iterdir()} == before


def test_context_write_failure_sends_zero_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = plan_fixture()
    context = context_for_plan(plan, recipe_fixture(plan)).document
    transport = FixtureTransport()
    monkeypatch.setattr(application, "HttpTransport", lambda: transport)

    def fail(path: Path, data: bytes) -> None:
        raise OSError("synthetic_context_write_failure")

    monkeypatch.setattr(context_module, "atomic_write", fail)
    with pytest.raises(OSError, match="synthetic_context_write_failure"):
        application.run_assessment(
            plan,
            tmp_path / "assessment",
            credentials=MemoryCredentials(None),
            assessment_context=context,
        )
    assert transport.calls == 0


def test_admission_context_is_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    installed = copy_implementation(tmp_path, monkeypatch)
    plan = plan_fixture()
    context = context_for_plan(plan, recipe_fixture(plan)).document
    store = JobStore(tmp_path / "jobs")
    now = datetime.now(UTC)
    frozen = store.create_plan(
        plan.target.to_json(), plan.profiles, SESSION, now=now, context=context
    )
    frozen_bytes = (store.root / "plans" / f"{frozen.id}.json").read_bytes()
    admitted = store.admit(frozen.id, SESSION, "one", now=now)
    path = store.root / "runs" / admitted.job.id / "assessment-context.json"
    before = path.read_bytes()
    assert document(path)["run_id"] == admitted.job.id
    assert store.get_plan_context(frozen.id) == context
    changed = installed / "validation/messages.py"
    changed.write_text(changed.read_text() + "\n# Synthetic post-admission change.\n")
    for key in ("one", "second-key"):
        duplicate = store.admit(frozen.id, SESSION, key, now=now + timedelta(days=1))
        assert duplicate.job.id == admitted.job.id
        assert duplicate.created is False
    assert path.read_bytes() == before
    assert (store.root / "plans" / f"{frozen.id}.json").read_bytes() == frozen_bytes


def test_identity_changes_between_preview_and_start(
    server: SyntheticServer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    installed = copy_implementation(tmp_path, monkeypatch)
    plan = plan_fixture(server.url + "/cases")
    context = context_for_plan(plan, recipe_fixture(plan)).document
    store = JobStore(tmp_path / "jobs")
    frozen = store.create_plan(
        plan.target.to_json(), plan.profiles, SESSION, now=datetime.now(UTC), context=context
    )
    source = installed / "validation/messages.py"
    source.write_text(source.read_text() + "\n# Synthetic change after preview.\n")
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        with pytest.raises(ValueError, match="diagnostic_identity_changed"):
            manager.submit(frozen.id, SESSION, "changed", MemoryCredentials(None))
        assert store.history({}, None)["items"] == []
        assert server.requests == []
    finally:
        manager.close()


def test_changed_identity_after_run_does_not_rewrite_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    installed = copy_implementation(tmp_path, monkeypatch)
    plan = plan_fixture()
    context = context_for_plan(plan, recipe_fixture(plan)).document

    class ChangedTransport(FixtureTransport):
        def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
            if self.calls == 0:
                path = installed / "validation/messages.py"
                path.write_text(path.read_text() + "\n# Synthetic change during execution.\n")
            return super().send(request, limits, deadline)

    transport = ChangedTransport()
    monkeypatch.setattr(application, "HttpTransport", lambda: transport)
    output = tmp_path / "assessment"
    result = application.run_assessment(
        plan, output, credentials=MemoryCredentials(None), assessment_context=context
    )
    assert transport.calls == 3
    assert document(output / "result.json") == result.to_json()
    assert document(output / "assessment-context-verification.json")["identity_status"] == "changed"
    assert document(output / "assessment-context.json")["recipe_sha256"] == context["recipe_sha256"]


def test_old_store_is_not_backfilled_as_verified(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    frozen = legacy_store(root)
    before = (root / "plans" / f"{frozen.id}.json").read_bytes()
    store = JobStore(root)
    assert store.get_plan_context(frozen.id) is None
    admitted = store.admit(frozen.id, frozen.session_id, "legacy", now=datetime.now(UTC))
    assert not (root / "runs" / admitted.job.id / "assessment-context.json").exists()
    assert (root / "plans" / f"{frozen.id}.json").read_bytes() == before


def test_worker_uses_identical_bound_context(server: SyntheticServer, tmp_path: Path) -> None:
    plan = plan_fixture(server.url + "/cases")
    context = context_for_plan(plan, recipe_fixture(plan)).document
    store = JobStore(tmp_path)
    frozen = store.create_plan(
        plan.target.to_json(), plan.profiles, SESSION, now=datetime.now(UTC), context=context
    )
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        job = manager.submit(frozen.id, SESSION, "run", MemoryCredentials(None))
        assert wait_terminal(store, job.id).state == "completed"
        root = store.root / "runs" / job.id
        assert (root / "assessment-context.json").read_bytes() == (
            root / "assessment/assessment-context.json"
        ).read_bytes()
        assert (
            document(root / "assessment/assessment-context-verification.json")["identity_status"]
            == "unchanged"
        )
        assert len(server.requests) == 3
    finally:
        manager.close()


def test_worker_rejects_wrong_context_before_requests(
    server: SyntheticServer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = plan_fixture(server.url + "/cases")
    context = context_for_plan(plan, recipe_fixture(plan)).document
    store = JobStore(tmp_path)
    frozen = store.create_plan(
        plan.target.to_json(), plan.profiles, SESSION, now=datetime.now(UTC), context=context
    )
    real = store.admit

    def tampered(
        plan_id: str, session_id: str, idempotency_key: str, *, now: datetime
    ) -> Admission:
        admitted = real(plan_id, session_id, idempotency_key, now=now)
        path = store.root / "runs" / admitted.job.id / "assessment-context.json"
        value = document(path)
        value["run_id"] = "22222222-2222-4222-8222-222222222222"
        path.write_bytes(json_bytes(value))
        return admitted

    monkeypatch.setattr(store, "admit", tampered)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        job = manager.submit(frozen.id, SESSION, "tampered", MemoryCredentials(None))
        assert wait_terminal(store, job.id).state == "error"
        assert server.requests == []
    finally:
        manager.close()


def test_crash_before_database_commit_never_runs_or_overwrites_orphan(
    server: SyntheticServer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = plan_fixture(server.url + "/cases")
    context = context_for_plan(plan, recipe_fixture(plan)).document
    store = JobStore(tmp_path)
    now = datetime.now(UTC)
    frozen = store.create_plan(
        plan.target.to_json(), plan.profiles, SESSION, now=now, context=context
    )
    real = store._transaction

    @contextmanager
    def interrupted() -> Iterator[sqlite3.Connection]:
        with real() as connection:
            yield connection
            raise OSError("synthetic_crash_before_commit")

    monkeypatch.setattr(store, "_transaction", interrupted)
    with pytest.raises(OSError, match="synthetic_crash_before_commit"):
        store.admit(frozen.id, SESSION, "crash", now=now)
    orphan = next((tmp_path / "runs").iterdir())
    saved = (orphan / "assessment-context.json").read_bytes()
    restarted = JobStore(tmp_path)
    assert restarted.history({}, None)["items"] == []
    manager = JobManager(restarted, credential_allowlist={})
    manager.start()
    manager.close()
    assert server.requests == []
    monkeypatch.setattr(uuid, "uuid4", lambda: UUID(orphan.name))
    with pytest.raises(FileExistsError):
        restarted.admit(frozen.id, SESSION, "collision", now=now)
    assert (orphan / "assessment-context.json").read_bytes() == saved
    assert not (orphan / "assessment").exists()
