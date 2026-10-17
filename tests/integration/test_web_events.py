"""SSE observes persisted progress and never controls upstream execution."""

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from anthropic_readiness.application import build_plan
from anthropic_readiness.config import load_target
from anthropic_readiness.credentials import MemoryCredentials
from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.models import JsonObject, object_value
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.runner import execute_run
from anthropic_readiness.web import events
from tests.acceptance.test_runner import FixtureTransport
from tests.http_server import SyntheticServer
from tests.web_fixtures import anyio_backend as anyio_backend

pytestmark = pytest.mark.anyio
ROOT = Path(__file__).resolve().parents[2]
SESSION = "a" * 64


def completed_manager(root: Path) -> tuple[JobManager, str]:
    store = JobStore(root)
    plan = store.create_plan(
        load_target(ROOT / "examples/target.yaml").to_json(),
        ("anthropic-basic",),
        SESSION,
        now=datetime.now(UTC),
    )
    job = store.admit(plan.id, SESSION, "event-fixture", now=datetime.now(UTC)).job
    store.transition(job.id, "queued", "running")
    output = root / "runs" / job.id / "assessment"
    execute_run(
        build_plan(plan.target, plan.profiles),
        FixtureTransport(),
        output,
        run_id=job.id,
        observer=DiskExecutionObserver(output.parent / "operations", output),
    )
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    return manager, job.id


def data(frame: str) -> JsonObject:
    return object_value(
        json.loads(next(line[6:] for line in frame.splitlines() if line.startswith("data: ")))
    )


async def test_snapshot_cursor_gap_and_ahead_reset(tmp_path: Path) -> None:
    manager, run_id = completed_manager(tmp_path)
    try:
        initial = [chunk async for chunk in events.event_stream(run_id, 0, manager)]
        assert initial[0].startswith("event: snapshot\n")
        snapshot = data(initial[0])
        execution = snapshot["execution"]
        assert isinstance(execution, dict)
        sequence = int(str(execution["sequence"]))
        for _ in range(2):
            replay = [chunk async for chunk in events.event_stream(run_id, sequence - 2, manager)]
            assert [data(chunk)["sequence"] for chunk in replay] == [sequence - 1, sequence]
        ahead = [chunk async for chunk in events.event_stream(run_id, sequence + 100, manager)]
        assert ahead[0].startswith("event: reset\n")
        assert manager.store.get_job(run_id).state == "completed"
    finally:
        manager.close()


async def test_sse_heartbeat_never_dispatches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    now = [0.0]

    async def advance(seconds: float) -> None:
        now[0] += seconds

    monkeypatch.setattr(events, "monotonic", lambda: now[0])
    monkeypatch.setattr(events, "sleep", advance)
    plan = store.create_plan(
        load_target(ROOT / "examples/target.yaml").to_json(),
        ("anthropic-basic",),
        SESSION,
        now=datetime.now(UTC),
    )
    job = store.admit(plan.id, SESSION, "queued-observation-fixture", now=datetime.now(UTC)).job
    stream = events.event_stream(job.id, 0, manager)
    try:
        assert (await anext(stream)).startswith("event: snapshot\n")
        assert await anext(stream) == ": heartbeat\n\n"
        assert now[0] == 15
        assert store.get_job(job.id).state == "queued"
        assert not (tmp_path / "runs" / job.id / "assessment").exists()
        await stream.aclose()
        assert store.get_job(job.id).state == "queued"
    finally:
        store.transition(job.id, "queued", "cancelled")
        manager.close()


async def test_disconnect_observer_does_not_cancel_active_worker(
    server: SyntheticServer, tmp_path: Path
) -> None:
    store = JobStore(tmp_path)
    manager = JobManager(store, credential_allowlist={})
    manager.start()
    target = replace(load_target(ROOT / "examples/target.yaml"), messages_url=server.url + "/pings")
    plan = store.create_plan(target.to_json(), ("anthropic-basic",), SESSION, now=datetime.now(UTC))
    job = manager.submit(plan.id, SESSION, "disconnect", MemoryCredentials(None))
    stream = events.event_stream(job.id, 0, manager)
    try:
        for _ in range(500):
            if server.requests:
                break
            await asyncio.sleep(0.01)
        assert len(server.requests) == 1
        assert (await anext(stream)).startswith("event: snapshot\n")
        await stream.aclose()
        assert store.get_job(job.id).state == "running"
        manager.cancel(job.id)
    finally:
        await stream.aclose()
        manager.close()
