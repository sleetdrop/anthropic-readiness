"""Owned import previews and immutable, revalidated local baseline activation."""

from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import stat
import time
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from anthropic_readiness.diagnostics.archive import (
    ArchiveLimits,
    extract_checked_archive,
    inspect_archive,
)
from anthropic_readiness.diagnostics.contracts import validate_diagnostic, validate_storage
from anthropic_readiness.diagnostics.importing import read_json, validate_import
from anthropic_readiness.diagnostics.models import BaselineRecord
from anthropic_readiness.evidence import atomic_write, json_bytes, safe_path
from anthropic_readiness.models import JsonObject, JsonValue, object_value
from anthropic_readiness.report_models import ReportSource


def _id(value: str) -> str:
    try:
        if str(UUID(value)) == value:
            return value
    except ValueError:
        pass
    raise ValueError("diagnostic_invalid_identifier")


def _owner(value: str) -> None:
    if not value or len(value) > 128 or any(not (char.isalnum() or char in "-_") for char in value):
        raise ValueError("diagnostic_preview_owner")


def _now(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("diagnostic_invalid_time")
    return value.astimezone(UTC)


class DiagnosticStore:
    """root is the diagnostics directory, separate from the live jobs database."""

    def __init__(self, root: Path) -> None:
        self.root = root
        if root.is_symlink():
            raise ValueError("diagnostic_store_path")
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        for name in ("previews", "baselines"):
            safe_path(root, name).mkdir(mode=0o700, exist_ok=True)
        self.path = safe_path(root, "index.sqlite3")
        self.limits = ArchiveLimits()
        with self._connection() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS baselines (
                    id TEXT PRIMARY KEY, archive_sha256 TEXT NOT NULL UNIQUE,
                    record_sha256 TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS previews (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, expires_at TEXT NOT NULL,
                    state TEXT NOT NULL, document_sha256 TEXT, baseline_id TEXT
                );
            """)
        self.path.chmod(0o600)
        self._rebuild_index()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        safe_path(self.root, "index.sqlite3")
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
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

    def _directory(self, kind: str, identifier: str) -> Path:
        return safe_path(self.root, kind + "/" + _id(identifier))

    def _record(self, baseline_id: str) -> tuple[JsonObject, str]:
        directory = self._directory("baselines", baseline_id)
        if not safe_path(directory, "committed.json").exists():
            raise ValueError("diagnostic_baseline_not_found")
        marker, _ = read_json(directory, "committed.json")
        validate_storage(marker, "diagnostic-commit")
        record, digest = read_json(directory, "baseline.json")
        validate_diagnostic(record, "imported-baseline")
        if (
            set(marker) != {"schema_version", "baseline_sha256", "archive_sha256"}
            or marker["schema_version"] != "1.0"
            or marker["baseline_sha256"] != digest
            or marker["archive_sha256"] != record["archive_sha256"]
            or record["id"] != baseline_id
            or record["artifact_root"] != "baselines/" + baseline_id + "/source"
        ):
            raise ValueError("diagnostic_baseline_integrity")
        return record, digest

    def _rebuild_index(self) -> None:
        # Only the final publication marker establishes an activated baseline.
        # SQLite is a rebuildable lookup; failed staging directories remain inert.
        with self._transaction() as connection:
            for directory in safe_path(self.root, "baselines").iterdir():
                if directory.is_symlink() or not directory.is_dir():
                    continue
                try:
                    record, digest = self._record(directory.name)
                except (OSError, ValueError, KeyError):
                    continue
                connection.execute(
                    "INSERT OR IGNORE INTO baselines VALUES (?, ?, ?)",
                    (record["id"], record["archive_sha256"], digest),
                )

    def _cleanup(self, connection: sqlite3.Connection, now: datetime) -> None:
        rows = connection.execute(
            "SELECT id FROM previews WHERE expires_at<=? AND state!='committed'", (now.isoformat(),)
        ).fetchall()
        for row in rows:
            directory = self._directory("previews", str(row["id"]))
            if directory.exists():
                shutil.rmtree(directory)
            connection.execute("DELETE FROM previews WHERE id=?", (row["id"],))

    def _remaining(self, deadline: float) -> ArchiveLimits:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("archive_timeout")
        return replace(self.limits, timeout_s=remaining)

    def _copy_archive(self, source: Path, destination: Path, deadline: float) -> None:
        size = 0
        source_fd = os.open(
            source, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
        )
        with os.fdopen(source_fd, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise ValueError("archive_member_type")
            if metadata.st_size > self.limits.max_compressed_bytes:
                raise ValueError("archive_upload_limit")
            fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as output:
                while chunk := stream.read(65536):
                    self._remaining(deadline)
                    size += len(chunk)
                    if size > self.limits.max_compressed_bytes:
                        raise ValueError("archive_upload_limit")
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())

    def _relationship(
        self, identity: JsonObject, archive_digest: JsonValue, deadline: float
    ) -> JsonObject:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, archive_sha256 FROM baselines ORDER BY id"
            ).fetchall()
        variants: list[JsonValue] = []
        conflicts: list[JsonValue] = []
        for row in rows:
            self._remaining(deadline)
            try:
                record, _ = self._validated(str(row["id"]), deadline)
            except (OSError, ValueError):
                continue
            if row["archive_sha256"] == archive_digest:
                return {"kind": "identical", "baseline_ids": [record["id"]]}
            previous = object_value(record["source"])
            if previous == identity:
                variants.append(record["id"])
            elif previous["run_id"] == identity["run_id"] or (
                identity["assessment_id"] is not None
                and previous["assessment_id"] == identity["assessment_id"]
            ):
                conflicts.append(record["id"])
        return {
            "kind": "variant" if variants else "conflict" if conflicts else "new",
            "baseline_ids": variants or conflicts,
        }

    def preview(
        self, archive: Path, owner: str, *, now: datetime, deadline: float | None = None
    ) -> JsonObject:
        _owner(owner)
        now = _now(now)
        maximum_deadline = time.monotonic() + self.limits.timeout_s
        deadline = min(maximum_deadline, deadline) if deadline is not None else maximum_deadline
        self._remaining(deadline)
        preview_id = str(uuid4())
        expires = now + timedelta(minutes=15)
        directory = self._directory("previews", preview_id)
        with self._transaction() as connection:
            self._cleanup(connection, now)
            count = connection.execute(
                "SELECT COUNT(*) FROM previews WHERE state IN ('building','ready') AND expires_at>?",
                (now.isoformat(),),
            ).fetchone()[0]
            if count >= 2:
                raise ValueError("diagnostic_preview_limit")
            directory.mkdir(mode=0o700)
            connection.execute(
                "INSERT INTO previews VALUES (?, ?, ?, 'building', NULL, NULL)",
                (preview_id, owner, expires.isoformat()),
            )
        try:
            copied = directory / "archive.zip"
            self._copy_archive(archive, copied, deadline)
            inventory = inspect_archive(copied, self._remaining(deadline))
            extract_checked_archive(
                copied, directory / "source", inventory, self._remaining(deadline)
            )
            _, metadata = validate_import(directory / "source", inventory, deadline=deadline)
            self._remaining(deadline)
            response: JsonObject = {
                "schema_version": "1.0",
                "preview_id": preview_id,
                "expires_at": expires.isoformat(),
                **metadata,
                "relationship": self._relationship(
                    object_value(metadata["source"]), inventory["archive_sha256"], deadline
                ),
            }
            private: JsonObject = {
                "schema_version": "1.0",
                "owner": owner,
                "expires_at": expires.isoformat(),
                "inventory": inventory,
                "response": response,
            }
            data = json_bytes(private)
            validate_storage(private, "diagnostic-import-preview")
            atomic_write(directory / "preview.json", data)
            with self._transaction() as connection:
                self._remaining(deadline)
                connection.execute(
                    "UPDATE previews SET state='ready', document_sha256=? WHERE id=? AND state='building'",
                    (hashlib.sha256(data).hexdigest(), preview_id),
                )
            return response
        except BaseException:
            if directory.exists():
                shutil.rmtree(directory)
            with self._transaction() as connection:
                connection.execute("DELETE FROM previews WHERE id=?", (preview_id,))
            raise

    def _publish_commit(self, directory: Path, record: JsonObject, digest: str) -> None:
        atomic_write(
            directory / "committed.json",
            json_bytes(
                {
                    "schema_version": "1.0",
                    "baseline_sha256": digest,
                    "archive_sha256": record["archive_sha256"],
                }
            ),
        )
        if os.name != "nt":
            for path in (directory, directory.parent):
                fd = os.open(path, os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)

    def commit(self, preview_id: str, owner: str, *, now: datetime) -> BaselineRecord:
        _owner(owner)
        now = _now(now)
        original = self._directory("previews", preview_id)
        moved: Path | None = None
        try:
            with self._transaction() as connection:
                row = connection.execute(
                    "SELECT * FROM previews WHERE id=?", (_id(preview_id),)
                ).fetchone()
                if row is None:
                    raise ValueError("diagnostic_preview_not_found")
                if row["owner"] != owner:
                    raise ValueError("diagnostic_preview_owner")
                if row["state"] == "committed":
                    return self.get(str(row["baseline_id"]))
                if row["expires_at"] <= now.isoformat():
                    raise ValueError("diagnostic_preview_expired")
                if row["state"] != "ready":
                    raise ValueError("diagnostic_preview_not_ready")
                private, digest = read_json(original, "preview.json")
                validate_storage(private, "diagnostic-import-preview")
                if (
                    digest != row["document_sha256"]
                    or private["owner"] != owner
                    or private["expires_at"] != row["expires_at"]
                ):
                    raise ValueError("diagnostic_preview_integrity")
                deadline = time.monotonic() + self.limits.timeout_s
                inventory = inspect_archive(original / "archive.zip", self._remaining(deadline))
                if inventory != private["inventory"]:
                    raise ValueError("diagnostic_preview_integrity")
                _, metadata = validate_import(original / "source", inventory, deadline=deadline)
                self._remaining(deadline)
                if metadata["source"] != object_value(private["response"])["source"]:
                    raise ValueError("diagnostic_preview_integrity")
                duplicate = connection.execute(
                    "SELECT id FROM baselines WHERE archive_sha256=?",
                    (inventory["archive_sha256"],),
                ).fetchone()
                if duplicate is not None:
                    record = self.get(str(duplicate["id"])).document
                else:
                    baseline_id = str(uuid4())
                    record = {
                        "schema_version": "1.0",
                        "id": baseline_id,
                        "archive_sha256": inventory["archive_sha256"],
                        "source": metadata["source"],
                        "imported_at": now.isoformat(),
                        "artifact_root": "baselines/" + baseline_id + "/source",
                        "eligibility": metadata["eligibility"],
                        "evidence_verification": metadata["evidence_verification"],
                    }
                    validate_diagnostic(record, "imported-baseline")
                    data = json_bytes(record)
                    digest = hashlib.sha256(data).hexdigest()
                    atomic_write(original / "baseline.json", data)
                    moved = self._directory("baselines", baseline_id)
                    if moved.exists():
                        raise FileExistsError(moved)
                    os.replace(original, moved)
                    connection.execute(
                        "INSERT INTO baselines VALUES (?, ?, ?)",
                        (baseline_id, inventory["archive_sha256"], digest),
                    )
                    self._publish_commit(moved, record, digest)
                connection.execute(
                    "UPDATE previews SET state='committed', baseline_id=? WHERE id=?",
                    (record["id"], preview_id),
                )
            if original.exists():
                shutil.rmtree(original)
            return BaselineRecord(record)
        except BaseException:
            if moved is not None and moved.exists() and not (moved / "committed.json").exists():
                with suppress(OSError):
                    (moved / "baseline.json").unlink(missing_ok=True)
                    os.replace(moved, original)
            raise

    def _validated(self, baseline_id: str, deadline: float) -> tuple[JsonObject, ReportSource]:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM baselines WHERE id=?", (_id(baseline_id),)
            ).fetchone()
        if row is None:
            raise ValueError("diagnostic_baseline_not_found")
        try:
            record, digest = self._record(baseline_id)
            if digest != row["record_sha256"] or record["archive_sha256"] != row["archive_sha256"]:
                raise ValueError("diagnostic_baseline_integrity")
            directory = self._directory("baselines", baseline_id)
            inventory = inspect_archive(directory / "archive.zip", self._remaining(deadline))
            if inventory["archive_sha256"] != record["archive_sha256"]:
                raise ValueError("diagnostic_baseline_integrity")
            source, metadata = validate_import(directory / "source", inventory, deadline=deadline)
            self._remaining(deadline)
            if metadata["source"] != record["source"]:
                raise ValueError("diagnostic_baseline_integrity")
            # Eligibility is current observed proof, never an immutable green badge.
            return {
                **record,
                "eligibility": metadata["eligibility"],
                "evidence_verification": metadata["evidence_verification"],
            }, source
        except (OSError, ValueError, KeyError) as exc:
            raise ValueError("diagnostic_baseline_integrity") from exc

    def get(self, baseline_id: str) -> BaselineRecord:
        record, _ = self._validated(baseline_id, time.monotonic() + self.limits.timeout_s)
        validate_diagnostic(record, "imported-baseline")
        return BaselineRecord(record)

    def load_source(self, baseline_id: str) -> ReportSource:
        _, source = self._validated(baseline_id, time.monotonic() + self.limits.timeout_s)
        return source
