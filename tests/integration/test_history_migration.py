"""Rule filtering upgrades old local indexes without changing frozen source plans."""

import hashlib
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from anthropic_readiness.application import build_plan
from anthropic_readiness.config import load_target
from anthropic_readiness.evidence import json_bytes
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.operations.models import FrozenPlan

ROOT = Path(__file__).resolve().parents[2]


def legacy_store(root: Path) -> FrozenPlan:
    root.mkdir()
    plan = build_plan(load_target(ROOT / "examples/target.yaml").to_json(), ["anthropic-basic"])
    now = datetime.now(UTC)
    frozen = FrozenPlan(
        str(uuid4()),
        "a" * 64,
        now.isoformat(),
        (now + timedelta(seconds=900)).isoformat(),
        str(plan.to_json()["config_fingerprint"]),
        plan.target.to_json(),
        plan.profiles,
        plan.to_json(),
    )
    (root / "plans").mkdir()
    data = json_bytes(frozen.to_json())
    (root / "plans" / (frozen.id + ".json")).write_bytes(data)
    with closing(sqlite3.connect(root / "jobs.sqlite3")) as connection:
        connection.executescript("""
            CREATE TABLE plans (id TEXT PRIMARY KEY, session_id TEXT NOT NULL, sha256 TEXT NOT NULL, expires_at TEXT NOT NULL, target_name TEXT NOT NULL, model TEXT NOT NULL, profiles TEXT NOT NULL);
            CREATE TABLE jobs (id TEXT PRIMARY KEY, plan_id TEXT NOT NULL UNIQUE REFERENCES plans(id), state TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, last_sequence INTEGER NOT NULL DEFAULT 0, result_path TEXT);
            CREATE UNIQUE INDEX one_active_job ON jobs((1)) WHERE state IN ('running', 'cancelling');
            CREATE TABLE admissions (session_id TEXT NOT NULL, operation TEXT NOT NULL, plan_id TEXT NOT NULL REFERENCES plans(id), job_id TEXT NOT NULL REFERENCES jobs(id), PRIMARY KEY(session_id, operation));
            CREATE TABLE presets (id TEXT PRIMARY KEY, target TEXT NOT NULL, updated_at TEXT NOT NULL);
            PRAGMA user_version=1;
        """)
        connection.execute(
            "INSERT INTO plans VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                frozen.id,
                frozen.session_id,
                hashlib.sha256(data).hexdigest(),
                frozen.expires_at,
                plan.target.name,
                plan.target.model,
                '["anthropic-basic"]',
            ),
        )
        connection.commit()
    return frozen


def test_legacy_store_migrates_without_mutating_plan_bytes(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    frozen = legacy_store(root)
    path = root / "plans" / (frozen.id + ".json")
    before = path.read_bytes()
    store = JobStore(root)
    with closing(sqlite3.connect(root / "jobs.sqlite3")) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
    assert path.read_bytes() == before
    job = store.admit(frozen.id, frozen.session_id, "migrated", now=datetime.now(UTC)).job
    filtered = store.history(
        {
            "contract_id": "anthropic-messages-2023-06-01-core",
            "contract_revision": "1.0.0",
            "api_version": "2023-06-01",
        },
        None,
    )
    assert str(job.id) in str(filtered)
    assert store.history({"contract_revision": "absent"}, None)["items"] == []


def test_corrupt_legacy_plan_aborts_migration_without_partial_schema(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    frozen = legacy_store(root)
    (root / "plans" / (frozen.id + ".json")).write_bytes(b"modified plan")
    with pytest.raises(ValueError, match="plan_integrity"):
        JobStore(root)
    with closing(sqlite3.connect(root / "jobs.sqlite3")) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        columns = {row[1] for row in connection.execute("PRAGMA table_info(plans)")}
        assert "contract_revision" not in columns
