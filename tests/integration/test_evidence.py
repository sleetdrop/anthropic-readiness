"""Exclusive files, verified references and truthful transformed replay."""

import hashlib
import stat
from dataclasses import replace
from pathlib import Path

import pytest

from anthropic_readiness.evidence import (
    create_run_directory,
    load_capture,
    persist_capture,
    sanitize_capture,
    verify_evidence,
)
from anthropic_readiness.models import EvidenceRef, ReadRecord
from tests.factories import capture


def test_existing_directory_and_path_escape_rejected(tmp_path: Path) -> None:
    root = tmp_path / "run"
    create_run_directory(root)
    with pytest.raises(FileExistsError):
        create_run_directory(root)
    with pytest.raises(ValueError, match="path"):
        persist_capture(root, "../escape", "attempt", sanitize_capture(capture(), []))
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "evidence").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="path"):
        persist_capture(root, "case", "attempt", sanitize_capture(capture(), []))


def test_persisted_capture_roundtrip_and_permissions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "run"
    create_run_directory(root)
    source = sanitize_capture(capture(), [])
    refs = persist_capture(root, "case", "attempt", source)
    assert verify_evidence(root, refs.refs) == []
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert all(stat.S_IMODE((root / ref.path).stat().st_mode) == 0o600 for ref in refs.refs)
    monkeypatch.chdir(tmp_path)
    loaded = load_capture(root / refs.capture_path)
    assert loaded.capture.body == source.capture.body
    assert not loaded.replay_rechunked
    with pytest.raises(FileExistsError):
        persist_capture(root, "case", "attempt", source)


def test_redacted_capture_does_not_reuse_old_boundaries(tmp_path: Path) -> None:
    root = tmp_path / "run"
    create_run_directory(root)
    secret = "synthetic-very-long-credential"
    body = ("data: " + secret + "\n\n").encode()
    source = replace(capture(body, True), reads=(ReadRecord(10, 1), ReadRecord(len(body) - 10, 2)))
    refs = persist_capture(root, "case", "attempt", sanitize_capture(source, [secret]))
    for path in root.rglob("*"):
        if path.is_file():
            assert secret.encode() not in path.read_bytes()
    loaded = load_capture(root / refs.capture_path)
    assert loaded.transformed
    assert loaded.replay_rechunked
    assert sum(read.length for read in loaded.capture.reads) == len(loaded.capture.body)
    assert loaded.capture.reads != source.reads


def test_bad_hash_path_event_and_pointer(tmp_path: Path) -> None:
    root = tmp_path / "run"
    create_run_directory(root)
    body = b'event: ping\ndata: {"type":"ping"}\n\n'
    refs = persist_capture(root, "case", "attempt", sanitize_capture(capture(body, True), []))
    event_ref = next(ref for ref in refs.refs if ref.path.endswith("events.jsonl"))
    assert verify_evidence(root, [replace(event_ref, event=0, pointer="/type")]) == []
    assert verify_evidence(root, [replace(event_ref, event=99)])
    assert verify_evidence(root, [replace(event_ref, event=0, pointer="/absent")])
    assert verify_evidence(root, [replace(event_ref, sha256="0" * 64)])
    assert verify_evidence(root, [EvidenceRef("../outside", hashlib.sha256(b"").hexdigest())])
    (root / event_ref.path).write_bytes(b"tampered")
    assert verify_evidence(root, refs.refs)
    with pytest.raises(ValueError, match="integrity"):
        load_capture(root / refs.capture_path)


def test_cancelled_partial_capture_remains_partial(tmp_path: Path) -> None:
    root = tmp_path / "run"
    create_run_directory(root)
    source = replace(
        capture(b"event: message_start\ndata: incomplete", True), capture_end="cancelled"
    )
    refs = persist_capture(root, "case", "attempt", sanitize_capture(source, []))
    loaded = load_capture(root / refs.capture_path)
    assert loaded.capture.capture_end == "cancelled"
    assert loaded.capture.tail.pending_data
    assert loaded.replay_rechunked
