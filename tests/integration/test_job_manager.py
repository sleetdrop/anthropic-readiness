"""One local owner supervises explicit jobs without retrying upstream requests."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from anthropic_readiness.application import build_plan
from anthropic_readiness.config import load_target
from anthropic_readiness.credentials import MemoryCredentials
from anthropic_readiness.evidence import json_bytes
from anthropic_readiness.jobs import manager as manager_module
from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.models import object_value, strict_json
from anthropic_readiness.operations.journal import RunJournal
from anthropic_readiness.operations.models import JobRecord, ProgressEvent, WorkerEvent
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.runner import execute_run
from tests.acceptance.test_runner import FixtureTransport
from tests.fixtures.http.slow_peer import hostile_worker, leaky_begin_worker
from tests.http_server import SyntheticServer

ROOT = Path(__file__).resolve().parents[2]
SESSION = "a" * 64
TERMINAL = {"completed", "cancelled", "interrupted", "error"}


def wait_terminal(store: JobStore, run_id: str, *, timeout: float = 10) -> JobRecord:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = store.get_job(run_id)
        if job.state in TERMINAL:
            return job
        time.sleep(0.02)
    raise AssertionError(f"job_did_not_terminate:{store.get_job(run_id).state}")


def preview(store: JobStore, url: str, *, authenticated: bool = False) -> str:
    target = replace(load_target(ROOT / "examples/target.yaml"), messages_url=url)
    if authenticated:
        target = replace(target, auth_mode="api_key", credential_env="SYNTHETIC_WEB_KEY")
    return store.create_plan(
        target.to_json(), ("anthropic-basic",), SESSION, now=datetime.now(UTC)
    ).id


def test_one_worker_and_duplicate_submission_do_not_repeat_credentials_or_requests(
    server: SyntheticServer, tmp_path: Path
) -> None:
    class UnusedCredentials:
        def resolve(self) -> str | None:
            raise AssertionError("duplicate_must_not_resolve")

    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        plan_id = preview(store, server.url + "/cases")
        job = manager.submit(plan_id, SESSION, "same-start", MemoryCredentials(None))
        duplicate = manager.submit(plan_id, SESSION, "same-start", UnusedCredentials())
        assert duplicate.id == job.id
        assert wait_terminal(store, job.id).state == "completed"
        assert len(server.requests) == 3
        snapshot = manager.snapshot(job.id)
        assert snapshot["job"] == store.get_job(job.id).to_json()
        execution = snapshot["execution"]
        assert isinstance(execution, dict)
        assert execution["actual_requests"] == 3
        assert store.get_job(job.id).last_sequence == execution["sequence"]
    finally:
        manager.close()
    assert not multiprocessing.active_children()


def test_queued_cancellation_is_idempotent_and_has_no_worker_request(
    server: SyntheticServer, tmp_path: Path
) -> None:
    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        active = manager.submit(
            preview(store, server.url + "/pings"), SESSION, "active", MemoryCredentials(None)
        )
        queued = manager.submit(
            preview(store, server.url + "/cases"), SESSION, "queued", MemoryCredentials(None)
        )
        cancelled = manager.cancel(queued.id)
        assert cancelled.state == "cancelled"
        assert manager.cancel(queued.id) == cancelled
        manager.cancel(active.id)
        assert wait_terminal(store, active.id).state == "cancelled"
        assert all(path == "/pings" for path, _, _ in server.requests)
        snapshot = manager.snapshot(queued.id)["execution"]
        assert isinstance(snapshot, dict)
        assert snapshot["actual_requests"] == 0
    finally:
        manager.close()


def test_failed_credentials_consume_plan_but_do_not_remain_queued(
    server: SyntheticServer, tmp_path: Path
) -> None:
    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        plan_id = preview(store, server.url + "/cases", authenticated=True)
        job = manager.submit(plan_id, SESSION, "missing-key", MemoryCredentials(None))
        assert job.state == "error"
        assert (
            manager.submit(plan_id, SESSION, "missing-key", MemoryCredentials("new-value")).id
            == job.id
        )
        assert not server.requests
        execution = manager.snapshot(job.id)["execution"]
        assert isinstance(execution, dict)
        assert execution["terminal_reason"] == "missing_credential"
    finally:
        manager.close()


def test_restart_never_redispatches(server: SyntheticServer, tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    unfinished = store.admit(
        preview(store, server.url + "/cases"), SESSION, "orphan", now=datetime.now(UTC)
    ).job
    manager = JobManager(JobStore(tmp_path), credential_allowlist={})
    manager.start()
    try:
        assert store.get_job(unfinished.id).state == "interrupted"
        assert not server.requests
        assert (
            manager.submit(unfinished.plan_id, SESSION, "orphan", MemoryCredentials(None)).state
            == "interrupted"
        )
    finally:
        manager.close()


def test_restart_reconciles_a_proven_final_result_without_a_worker(
    server: SyntheticServer, tmp_path: Path
) -> None:
    store = JobStore(tmp_path)
    plan_id = preview(store, server.url + "/cases")
    job = store.admit(plan_id, SESSION, "finished-before-index", now=datetime.now(UTC)).job
    store.transition(job.id, "queued", "running")
    frozen = store.get_admitted_plan(job.id)
    output = tmp_path / "runs" / job.id / "assessment"
    operations = output.parent / "operations"
    execute_run(
        build_plan(frozen.target, frozen.profiles),
        FixtureTransport(),
        output,
        observer=DiskExecutionObserver(operations, output),
        run_id=job.id,
    )
    manager = JobManager(JobStore(tmp_path), credential_allowlist={})
    manager.start()
    try:
        reconciled = store.get_job(job.id)
        assert reconciled.state == "completed"
        assert reconciled.result_path == "assessment/result.json"
        assert not server.requests
    finally:
        manager.close()


def test_restart_rejects_a_result_that_claims_another_target(
    server: SyntheticServer, tmp_path: Path
) -> None:
    store = JobStore(tmp_path)
    job = store.admit(
        preview(store, server.url + "/cases"), SESSION, "wrong-target", now=datetime.now(UTC)
    ).job
    store.transition(job.id, "queued", "running")
    frozen = store.get_admitted_plan(job.id)
    output = tmp_path / "runs" / job.id / "assessment"
    operations = output.parent / "operations"
    result = execute_run(
        build_plan(frozen.target, frozen.profiles),
        FixtureTransport(),
        output,
        observer=DiskExecutionObserver(operations, output),
        run_id=job.id,
    )
    altered = result.to_json()
    altered_target = object_value(altered["target"])
    altered_target["model"] = "another-synthetic-model"
    altered["target"] = altered_target
    data = json_bytes(altered)
    (output / "result.json").write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    # Even internally consistent hashes cannot bind contradictory target identity.
    snapshot = object_value(strict_json((operations / "execution.json").read_text()))
    snapshot["result_sha256"] = digest
    (operations / "execution.json").write_bytes(json_bytes(snapshot))
    entries = [
        object_value(strict_json(line))
        for line in (operations / "events.jsonl").read_text().splitlines()
    ]
    for entry in entries:
        if entry["kind"] == "result_committed":
            payload = object_value(entry["payload"])
            payload["sha256"] = digest
            entry["payload"] = payload
    (operations / "events.jsonl").write_bytes(
        b"".join(json.dumps(entry).encode() + b"\n" for entry in entries)
    )
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        assert store.get_job(job.id).state == "error"
        assert not server.requests
    finally:
        manager.close()


def test_cancel_completion_race_has_one_terminal_state(
    server: SyntheticServer, tmp_path: Path
) -> None:
    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        job = manager.submit(
            preview(store, server.url + "/cases"), SESSION, "race", MemoryCredentials(None)
        )
        deadline = time.monotonic() + 8
        while (
            len(server.requests) < 3
            and store.get_job(job.id).state not in TERMINAL
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda index: manager.cancel(job.id), range(4)))
        terminal = wait_terminal(store, job.id)
        assert terminal.state in {"completed", "cancelled"}
        assert manager.cancel(job.id) == terminal
        transitions = [
            item.event.payload["to"]
            for item in RunJournal(
                tmp_path / "runs" / job.id / "operations",
                job.id,
                evidence_root=tmp_path / "runs" / job.id / "assessment",
            ).after(0)
            if item.event.kind == "job_transition"
        ]
        assert sum(state in TERMINAL for state in transitions if isinstance(state, str)) == 1
        assert len(server.requests) <= 3
    finally:
        manager.close()


def test_only_one_service_can_own_a_data_root(tmp_path: Path) -> None:
    first = JobManager(JobStore(tmp_path), credential_allowlist={})
    second = JobManager(JobStore(tmp_path), credential_allowlist={})
    first.start()
    try:
        with pytest.raises(ValueError, match="service_already_running"):
            second.start()
    finally:
        first.close()
        second.close()


def test_secret_never_enters_persisted_worker_messages(
    server: SyntheticServer, tmp_path: Path
) -> None:
    secret = "synthetic-private-browser-credential-85901"
    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        job = manager.submit(
            preview(store, server.url + "/cases", authenticated=True),
            SESSION,
            "secret",
            MemoryCredentials(secret),
        )
        assert wait_terminal(store, job.id).state == "completed"
        assert len(server.requests) == 3
        assert all(headers["x-api-key"] == secret for _, headers, _ in server.requests)
    finally:
        manager.close()
    assert all(
        secret.encode() not in path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    )


def test_server_credentials_use_only_the_explicit_allowlist(
    server: SyntheticServer, tmp_path: Path
) -> None:
    secret = "synthetic-server-allowlisted-value"
    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={"SYNTHETIC_WEB_KEY": secret})
    manager.start()
    try:
        job = manager.submit(
            preview(store, server.url + "/cases", authenticated=True),
            SESSION,
            "allowlisted",
            MemoryCredentials(None),
        )
        assert wait_terminal(store, job.id).state == "completed"
        assert len(server.requests) == 3
        assert all(headers["x-api-key"] == secret for _, headers, _ in server.requests)
    finally:
        manager.close()
    assert all(
        secret.encode() not in path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    )


def test_untrusted_ipc_is_rejected_without_persisting_its_secret(
    server: SyntheticServer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "synthetic-hostile-worker-secret-8510"
    monkeypatch.setattr(manager_module, "worker_main", hostile_worker)
    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        job = manager.submit(
            preview(store, server.url + "/cases", authenticated=True),
            SESSION,
            "hostile",
            MemoryCredentials(secret),
        )
        assert wait_terminal(store, job.id).state == "error"
        assert not server.requests
    finally:
        manager.close()
    assert all(
        secret.encode() not in path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    )


def test_provider_failure_never_leaves_an_unbound_queued_job(
    server: SyntheticServer, tmp_path: Path
) -> None:
    class BrokenCredentials:
        def resolve(self) -> str | None:
            raise RuntimeError("synthetic-private-provider-error")

    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        job = manager.submit(
            preview(store, server.url + "/cases", authenticated=True),
            SESSION,
            "broken-provider",
            BrokenCredentials(),
        )
        assert job.state == "error"
        assert not server.requests
    finally:
        manager.close()
    assert all(
        b"synthetic-private-provider-error" not in path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    )


def test_initial_worker_context_cannot_publish_arbitrary_private_diagnostics(
    server: SyntheticServer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "synthetic-leaky-worker-context-7125"
    monkeypatch.setattr(manager_module, "worker_main", leaky_begin_worker)
    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        job = manager.submit(
            preview(store, server.url + "/cases", authenticated=True),
            SESSION,
            "leaky-context",
            MemoryCredentials(secret),
        )
        path = tmp_path / "runs" / job.id / "operations/execution.json"
        deadline = time.monotonic() + 5
        while not path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert path.exists()
        assert secret.encode() not in path.read_bytes()
        assert wait_terminal(store, job.id).state == "error"
        assert not server.requests
    finally:
        manager.close()


def test_mandatory_storage_failure_stops_future_admission(
    server: SyntheticServer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = RunJournal.append

    def failed_append(self: RunJournal, event: WorkerEvent) -> ProgressEvent:
        if event.kind == "case_committed":
            raise OSError("synthetic_journal_disk_failure")
        return original(self, event)

    monkeypatch.setattr(RunJournal, "append", failed_append)
    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        first = preview(store, server.url + "/cases")
        later = preview(store, server.url + "/cases")
        job = manager.submit(first, SESSION, "failed-storage", MemoryCredentials(None))
        assert wait_terminal(store, job.id).state == "error"
        with pytest.raises(ValueError, match="service_unavailable"):
            manager.submit(later, SESSION, "after-storage-failure", MemoryCredentials(None))
        assert len(server.requests) == 1
    finally:
        manager.close()
