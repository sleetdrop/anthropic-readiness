"""Read-only SSE replay; UI backpressure never gates worker acknowledgement."""

import json
from asyncio import sleep
from collections.abc import AsyncGenerator
from time import monotonic

from anthropic_readiness.jobs.manager import JobManager
from anthropic_readiness.models import JsonObject
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.operations.reduction import TERMINAL


def snapshot_frame(name: str, document: JsonObject, sequence: int) -> str:
    validate_operational({"kind": "progress_snapshot", "data": document}, "web-api")
    return (
        f"event: {name}\nid: {sequence}\ndata: "
        + json.dumps(document, ensure_ascii=False, allow_nan=False)
        + "\n\n"
    )


async def event_stream(run_id: str, after: int, manager: JobManager) -> AsyncGenerator[str, None]:
    first = True
    had_execution = False
    cursor = after
    last_output = monotonic()
    while True:
        snapshot, pending, reset = manager.read_events(run_id, cursor)
        execution = snapshot["execution"]
        sequence = int(str(execution["sequence"])) if isinstance(execution, dict) else 0
        if (
            reset
            or (first and after == 0)
            or (not first and not had_execution and execution is not None)
        ):
            yield snapshot_frame("reset" if reset else "snapshot", snapshot, sequence)
            cursor = sequence
            last_output = monotonic()
        else:
            for entry in pending:
                yield (
                    f"event: progress\nid: {entry.sequence}\ndata: "
                    + json.dumps(entry.to_json(), ensure_ascii=False, allow_nan=False)
                    + "\n\n"
                )
                cursor = entry.sequence
                last_output = monotonic()
        first = False
        had_execution = execution is not None
        job = snapshot["job"]
        if isinstance(job, dict) and job["state"] in TERMINAL:
            return
        now = monotonic()
        if now - last_output >= 15:
            yield ": heartbeat\n\n"
            last_output = now
        await sleep(min(1.0, max(0.0, 15 - (monotonic() - last_output))))
