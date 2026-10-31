"""Owned subprocesses stop on cancellation and loss of the parent control pipe."""

import asyncio
import json
import multiprocessing
import os
import signal
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from anthropic_readiness.config import load_target
from anthropic_readiness.credentials import MemoryCredentials
from anthropic_readiness.jobs import manager as manager_module
from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.models import object_value, strict_json
from tests.fixtures.http.slow_peer import parent_with_checkpoint_barrier, unresponsive_worker
from tests.http_server import SyntheticServer
from tests.integration.test_job_manager import ROOT, SESSION, preview, wait_terminal
from tests.recovery_assertions import assert_recovered_interfaces


def _worker_has_exited(stat: Path) -> bool:
    try:
        return stat.read_text().split()[2] == "Z"
    except (FileNotFoundError, ProcessLookupError):
        # Linux may reap the process before or during the procfs read.
        return True


def test_force_stop_after_five_seconds_is_interrupted(
    server: SyntheticServer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(manager_module, "worker_main", unresponsive_worker)
    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        job = manager.submit(
            preview(store, server.url + "/cases"), SESSION, "stuck", MemoryCredentials(None)
        )
        deadline = time.monotonic() + 3
        while store.get_job(job.id).state == "queued" and time.monotonic() < deadline:
            time.sleep(0.02)
        started = time.monotonic()
        manager.cancel(job.id)
        assert wait_terminal(store, job.id, timeout=7).state == "interrupted"
        elapsed = time.monotonic() - started
        assert 5 <= elapsed < 7
        assert not server.requests
    finally:
        manager.close()
    assert not multiprocessing.active_children()


def test_worker_sigterm_preserves_partial_accounting(
    server: SyntheticServer, tmp_path: Path
) -> None:
    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    try:
        job = manager.submit(
            preview(store, server.url + "/pings"),
            SESSION,
            "worker-sigterm",
            MemoryCredentials(None),
        )
        deadline = time.monotonic() + 5
        while not server.requests and time.monotonic() < deadline:
            time.sleep(0.01)
        assert len(server.requests) == 1
        with manager._condition:
            assert manager._active is not None
            pid = manager._active.process.pid
            assert pid is not None
            os.kill(pid, signal.SIGTERM)
        assert wait_terminal(store, job.id).state == "interrupted"
        result = object_value(
            strict_json((tmp_path / "runs" / job.id / "assessment/result.json").read_text())
        )
        cases = result["cases"]
        assert isinstance(cases, list)
        assert len(cases) == 3
        assert len(server.requests) == 1
    finally:
        manager.close()
    assert not multiprocessing.active_children()


def test_parent_loss_after_checkpoint_never_sends_next_request(
    server: SyntheticServer, tmp_path: Path
) -> None:
    context = multiprocessing.get_context("spawn")
    parent_end, child_end = context.Pipe(duplex=False)
    target = replace(load_target(ROOT / "examples/target.yaml"), messages_url=server.url + "/cases")
    process = context.Process(
        target=parent_with_checkpoint_barrier, args=(tmp_path, target.to_json(), child_end)
    )
    process.start()
    child_end.close()
    run_id = None
    worker_pid = None
    worker_fd = None
    try:
        assert parent_end.poll(10)
        run_id = parent_end.recv_bytes().decode()
        assert parent_end.poll(10)
        notice = json.loads(parent_end.recv_bytes())
        assert notice["checkpoint"] == "pending_ack"
        worker_pid = int(notice["worker_pid"])
        # This integration test runs on Linux; mypy also checks it on macOS.
        pidfd_open = cast(Callable[[int], int], getattr(os, "pidfd_open"))  # noqa: B009
        worker_fd = pidfd_open(worker_pid)
        assert len(server.requests) == 1
        checkpoints = tmp_path / "runs" / run_id / "operations/checkpoints"
        assert len(list(checkpoints.glob("*.json"))) == 1
        # A pidfd binds cleanup to this owned Linux process even after parent loss.
        process.terminate()
        process.join(timeout=3)
        assert not process.is_alive()
        deadline = time.monotonic() + 7
        while time.monotonic() < deadline:
            stat = Path(f"/proc/{worker_pid}/stat")
            if _worker_has_exited(stat):
                break
            time.sleep(0.02)
        else:
            raise AssertionError("orphan_worker_did_not_stop")
        assert len(server.requests) == 1
        assert len(list(checkpoints.glob("*.json"))) == 1
        manager = JobManager(JobStore(tmp_path), credential_allowlist={})
        manager.start()
        try:
            assert manager.store.get_job(run_id).state == "interrupted"
            assert len(server.requests) == 1
            asyncio.run(assert_recovered_interfaces(tmp_path, run_id, manager))
            assert len(server.requests) == 1
        finally:
            manager.close()
    finally:
        parent_end.close()
        if process.is_alive():
            process.kill()
            process.join(timeout=3)
        if worker_fd is not None:
            with suppress(ProcessLookupError):
                send_pidfd_signal = cast(
                    Callable[[int, int], None],
                    getattr(signal, "pidfd_send_signal"),  # noqa: B009
                )
                send_pidfd_signal(worker_fd, signal.SIGKILL)
            os.close(worker_fd)
        process.close()
