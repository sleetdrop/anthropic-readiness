"""SQLite indexes and immutable files for local previews and atomic admission."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from anthropic_readiness.application import build_plan
from anthropic_readiness.config import fingerprint, strings, target_from_document
from anthropic_readiness.evidence import atomic_write, json_bytes, safe_path
from anthropic_readiness.models import JsonObject, object_value, strict_json
from anthropic_readiness.operations.contracts import validate_operational
from anthropic_readiness.operations.models import (
    Admission,
    FrozenPlan,
    JobRecord,
    JobState,
    transition_allowed,
)
from anthropic_readiness.operations.storage import MAX_DOCUMENT_BYTES, locked


def utc(now: datetime) -> str:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("invalid_clock_timezone")
    return now.astimezone(UTC).isoformat()


def identifier(value: str) -> str:
    try:
        if str(uuid.UUID(value)) != value:
            raise ValueError
    except ValueError as exc:
        raise ValueError("invalid_identifier") from exc
    return value


def owner(value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("invalid_session_binding")
    return value


def job_record(row: sqlite3.Row) -> JobRecord:
    record = JobRecord(
        str(row["id"]),
        str(row["plan_id"]),
        cast(JobState, str(row["state"])),
        str(row["created_at"]),
        str(row["updated_at"]),
        int(row["last_sequence"]),
        str(row["result_path"]) if row["result_path"] is not None else None,
    )
    validate_operational(record.to_json(), "job")
    return record


class JobStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        with locked(root, "migration.lock"):
            self.path = safe_path(root, "jobs.sqlite3")
            if not self.path.exists():
                atomic_write(self.path, b"")
            with self._connection() as connection:
                version = connection.execute("PRAGMA user_version").fetchone()[0]
                if version not in {0, 1}:
                    raise ValueError("unsupported_job_store_version")
                if version == 0:
                    connection.executescript("""
                        BEGIN IMMEDIATE;
                        CREATE TABLE plans (
                            id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
                            sha256 TEXT NOT NULL, expires_at TEXT NOT NULL,
                            target_name TEXT NOT NULL, model TEXT NOT NULL,
                            profiles TEXT NOT NULL
                        );
                        CREATE TABLE jobs (
                            id TEXT PRIMARY KEY, plan_id TEXT NOT NULL UNIQUE REFERENCES plans(id),
                            state TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                            last_sequence INTEGER NOT NULL DEFAULT 0, result_path TEXT
                        );
                        CREATE UNIQUE INDEX one_active_job ON jobs((1))
                            WHERE state IN ('running', 'cancelling');
                        CREATE TABLE admissions (
                            session_id TEXT NOT NULL, operation TEXT NOT NULL,
                            plan_id TEXT NOT NULL REFERENCES plans(id),
                            job_id TEXT NOT NULL REFERENCES jobs(id),
                            PRIMARY KEY(session_id, operation)
                        );
                        CREATE TABLE presets (
                            id TEXT PRIMARY KEY, target TEXT NOT NULL, updated_at TEXT NOT NULL
                        );
                        PRAGMA user_version=1;
                        COMMIT;
                    """)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        safe_path(self.root, "jobs.sqlite3")
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
                connection.commit()
            except BaseException:
                connection.rollback()
                raise

    def create_plan(
        self, target: JsonObject, profiles: tuple[str, ...], session_id: str, *, now: datetime
    ) -> FrozenPlan:
        owner(session_id)
        plan = build_plan(target, profiles)
        frozen = FrozenPlan(
            str(uuid.uuid4()),
            session_id,
            utc(now),
            utc(now + timedelta(seconds=900)),
            str(plan.to_json()["config_fingerprint"]),
            plan.target.to_json(),
            plan.profiles,
            plan.to_json(),
        )
        document = frozen.to_json()
        validate_operational(document, "plan")
        data = json_bytes(document)
        directory = safe_path(self.root, "plans")
        directory.mkdir(mode=0o700, exist_ok=True)
        atomic_write(safe_path(self.root, "plans/" + frozen.id + ".json"), data)
        with self._transaction() as connection:
            connection.execute(
                "INSERT INTO plans VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    frozen.id,
                    session_id,
                    hashlib.sha256(data).hexdigest(),
                    frozen.expires_at,
                    plan.target.name,
                    plan.target.model,
                    json.dumps(plan.profiles),
                ),
            )
        return frozen

    def _plan(
        self,
        connection: sqlite3.Connection,
        plan_id: str,
        session_id: str | None = None,
        *,
        now: datetime | None = None,
    ) -> FrozenPlan:
        identifier(plan_id)
        row = connection.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
        if row is None or (session_id is not None and row["session_id"] != owner(session_id)):
            raise ValueError("plan_not_found")
        if now is not None and utc(now) >= row["expires_at"]:
            raise ValueError("plan_expired")
        path = safe_path(self.root, "plans/" + plan_id + ".json")
        with path.open("rb") as stream:
            data = stream.read(MAX_DOCUMENT_BYTES + 1)
        if len(data) > MAX_DOCUMENT_BYTES or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("plan_integrity")
        document = object_value(strict_json(data.decode()))
        validate_operational(document, "plan")
        if document["id"] != plan_id or document["session_id"] != row["session_id"]:
            raise ValueError("plan_integrity")
        return FrozenPlan(
            plan_id,
            str(document["session_id"]),
            str(document["created_at"]),
            str(document["expires_at"]),
            str(document["config_sha256"]),
            object_value(document["target"]),
            strings(document["profiles"]),
            object_value(document["plan"]),
        )

    def get_plan(self, plan_id: str, session_id: str, *, now: datetime) -> FrozenPlan:
        with self._connection() as connection:
            return self._plan(connection, plan_id, session_id, now=now)

    def admit(
        self, plan_id: str, session_id: str, idempotency_key: str, *, now: datetime
    ) -> Admission:
        identifier(plan_id)
        owner(session_id)
        if (
            not idempotency_key
            or len(idempotency_key) > 128
            or any(ord(char) < 32 for char in idempotency_key)
        ):
            raise ValueError("invalid_idempotency_key")
        with self._transaction() as connection:
            prior = connection.execute(
                "SELECT * FROM admissions WHERE session_id=? AND operation=?",
                (session_id, idempotency_key),
            ).fetchone()
            if prior is not None:
                if prior["plan_id"] != plan_id:
                    raise ValueError("idempotency_mismatch")
                row = connection.execute(
                    "SELECT * FROM jobs WHERE id=?", (prior["job_id"],)
                ).fetchone()
                return Admission(job_record(row), False)
            plan_row = connection.execute(
                "SELECT session_id FROM plans WHERE id=?", (plan_id,)
            ).fetchone()
            if plan_row is None or plan_row["session_id"] != session_id:
                raise ValueError("plan_not_found")
            existing = connection.execute(
                "SELECT * FROM jobs WHERE plan_id=?", (plan_id,)
            ).fetchone()
            if existing is not None:
                connection.execute(
                    "INSERT INTO admissions VALUES (?, ?, ?, ?)",
                    (session_id, idempotency_key, plan_id, existing["id"]),
                )
                return Admission(job_record(existing), False)
            frozen = self._plan(connection, plan_id, session_id, now=now)
            waiting = connection.execute(
                "SELECT COUNT(*) FROM jobs WHERE state='queued'"
            ).fetchone()[0]
            if waiting >= 8:
                raise ValueError("queue_full")
            run_id = str(uuid.uuid4())
            stamp = utc(now)
            job = JobRecord(run_id, plan_id, "queued", stamp, stamp, 0, None)
            validate_operational(job.to_json(), "job")
            root = safe_path(self.root, "runs/" + run_id)
            root.mkdir(mode=0o700, parents=True)
            atomic_write(root / "plan.json", json_bytes(frozen.to_json()))
            connection.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    job.id,
                    job.plan_id,
                    job.state,
                    job.created_at,
                    job.updated_at,
                    job.last_sequence,
                    job.result_path,
                ),
            )
            connection.execute(
                "INSERT INTO admissions VALUES (?, ?, ?, ?)",
                (session_id, idempotency_key, plan_id, job.id),
            )
            return Admission(job, True)

    def get_job(self, run_id: str) -> JobRecord:
        identifier(run_id)
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise ValueError("job_not_found")
            return job_record(row)

    def get_admitted_plan(self, run_id: str) -> FrozenPlan:
        job = self.get_job(run_id)
        with self._connection() as connection:
            frozen = self._plan(connection, job.plan_id)
            path = safe_path(self.root, "runs/" + job.id + "/plan.json")
            if path.read_bytes() != json_bytes(frozen.to_json()):
                raise ValueError("plan_integrity")
            return frozen

    def observe(self, run_id: str, sequence: int, result_path: str | None = None) -> JobRecord:
        identifier(run_id)
        if (
            type(sequence) is not int
            or sequence < 0
            or result_path not in {None, "assessment/result.json"}
        ):
            raise ValueError("invalid_job_observation")
        with self._transaction() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise ValueError("job_not_found")
            if row["state"] in {"completed", "cancelled", "interrupted", "error"}:
                if row["last_sequence"] == sequence and row["result_path"] == result_path:
                    return job_record(row)
                raise ValueError("terminal_job_immutable")
            if sequence < row["last_sequence"]:
                raise ValueError("job_sequence_backwards")
            connection.execute(
                "UPDATE jobs SET last_sequence=?, result_path=COALESCE(?, result_path) WHERE id=?",
                (sequence, result_path, run_id),
            )
            return job_record(
                connection.execute("SELECT * FROM jobs WHERE id=?", (run_id,)).fetchone()
            )

    def transition(self, run_id: str, expected: JobState, next_state: JobState) -> JobRecord:
        identifier(run_id)
        if not transition_allowed(expected, next_state):
            raise ValueError("illegal_job_transition")
        with self._transaction() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise ValueError("job_not_found")
            if row["state"] != expected:
                raise ValueError("job_state_conflict")
            try:
                connection.execute(
                    "UPDATE jobs SET state=?, updated_at=? WHERE id=?",
                    (next_state, utc(datetime.now(UTC)), run_id),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("active_job_exists") from exc
            updated = connection.execute("SELECT * FROM jobs WHERE id=?", (run_id,)).fetchone()
            return job_record(updated)

    def history(self, filters: JsonObject, cursor: str | None, limit: int = 50) -> JsonObject:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("invalid_history_limit")
        columns = {"state": "j.state", "target_name": "p.target_name", "model": "p.model"}
        if set(filters) - {*columns, "profile", "created_after", "created_before"}:
            raise ValueError("invalid_history_filter")
        clauses: list[str] = []
        values: list[str | int] = []
        for name, value in sorted(filters.items()):
            if not isinstance(value, str):
                raise ValueError("invalid_history_filter")
            if name in columns:
                clauses.append(columns[name] + "=?")
                values.append(value)
            elif name == "profile":
                clauses.append("EXISTS (SELECT 1 FROM json_each(p.profiles) WHERE value=?)")
                values.append(value)
            else:
                try:
                    value = utc(datetime.fromisoformat(value))
                except ValueError as exc:
                    raise ValueError("invalid_history_filter") from exc
                clauses.append("j.created_at" + (">=?" if name == "created_after" else "<=?"))
                values.append(value)
        if cursor is not None:
            try:
                if len(cursor) > 2048:
                    raise ValueError
                raw = object_value(
                    strict_json(base64.b64decode(cursor, altchars=b"-_", validate=True).decode())
                )
                if set(raw) != {"created_at", "id", "filters"} or raw["filters"] != fingerprint(
                    filters
                ):
                    raise ValueError
                stamp = utc(datetime.fromisoformat(str(raw["created_at"])))
                last_id = identifier(str(raw["id"]))
            except (ValueError, UnicodeError, binascii.Error) as exc:
                raise ValueError("invalid_history_cursor") from exc
            clauses.append("(j.created_at < ? OR (j.created_at = ? AND j.id < ?))")
            values.extend((stamp, stamp, last_id))
        query = "SELECT j.*, p.target_name, p.model, p.profiles FROM jobs j JOIN plans p ON j.plan_id=p.id"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY j.created_at DESC, j.id DESC LIMIT ?"
        values.append(limit + 1)
        with self._connection() as connection:
            rows = connection.execute(query, values).fetchall()
        items: list[JsonObject] = [
            {
                "job": job_record(row).to_json(),
                "target_name": str(row["target_name"]),
                "model": str(row["model"]),
                "profiles": strict_json(str(row["profiles"])),
            }
            for row in rows[:limit]
        ]
        next_cursor = None
        if len(rows) > limit:
            row = rows[limit - 1]
            next_cursor = base64.urlsafe_b64encode(
                json_bytes(
                    {
                        "created_at": str(row["created_at"]),
                        "id": str(row["id"]),
                        "filters": fingerprint(filters),
                    }
                )
            ).decode()
        return {"items": list(items), "next_cursor": next_cursor}

    def save_preset(self, preset_id: str | None, target: JsonObject) -> str:
        document = target_from_document(target).to_json()
        preset_id = str(uuid.uuid4()) if preset_id is None else identifier(preset_id)
        with self._transaction() as connection:
            connection.execute(
                "INSERT INTO presets VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET target=excluded.target, updated_at=excluded.updated_at",
                (
                    preset_id,
                    json.dumps(document, ensure_ascii=False, allow_nan=False),
                    utc(datetime.now(UTC)),
                ),
            )
        return preset_id

    def presets(self) -> tuple[JsonObject, ...]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM presets ORDER BY updated_at DESC, id DESC"
            ).fetchall()
        return tuple(
            {
                "id": identifier(str(row["id"])),
                "target": target_from_document(
                    object_value(strict_json(str(row["target"])))
                ).to_json(),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        )
