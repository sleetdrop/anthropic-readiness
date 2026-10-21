"""Exclusive files, verified references and truthful transformed replay."""

import hashlib
import stat
from dataclasses import replace
from pathlib import Path

import pytest

from anthropic_readiness.evidence import (
    create_run_directory,
    json_bytes,
    load_capture,
    persist_capture,
    sanitize_capture,
    verify_evidence,
)
from anthropic_readiness.models import (
    CaptureEnd,
    EvidenceRef,
    ReadRecord,
    object_value,
    strict_json,
)
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


@pytest.mark.parametrize("schema_version", ["1.0", "1.1"])
@pytest.mark.parametrize("pending", [False, True])
def test_complete_replay_tail_verdict_comes_from_retained_bytes(
    tmp_path: Path, schema_version: str, pending: bool
) -> None:
    from anthropic_readiness.cases import build_request, list_cases
    from anthropic_readiness.config import load_target
    from anthropic_readiness.contracts import resolve_contract
    from anthropic_readiness.runner import replay_run, result_exit_code

    target = load_target(Path("examples/target.yaml"))
    case = list_cases()[1]
    body = Path("tests/fixtures/contracts/core-1.0.0/stream-valid.sse").read_bytes()
    if pending:
        body += b'event: content_block_delta\ndata: {"type":"content_block_delta"}'
    root = tmp_path / "capture"
    create_run_directory(root)
    original = replace(capture(body, True), request=build_request(case, target))
    refs = persist_capture(root, case.id, "synthetic", sanitize_capture(original, []))
    path = root / refs.capture_path
    bundle = resolve_contract(target.contract_id, target.contract_revision)
    control = replay_run(target, bundle, case.id, path, tmp_path / "control")
    expected_exit = 1 if pending else 0
    assert result_exit_code(control) == expected_exit

    metadata = object_value(strict_json(path.read_text()))
    metadata["schema_version"] = schema_version
    if schema_version == "1.0":
        metadata.pop("structural_sha256")
    metadata["tail"] = {**object_value(metadata["tail"]), "pending_data": not pending}
    changed = json_bytes(metadata)
    path.write_bytes(changed)
    loaded = load_capture(path)
    replayed = replay_run(target, bundle, case.id, path, tmp_path / "mutated")
    assert result_exit_code(replayed) == expected_exit
    assert loaded.capture.tail.pending_data is pending
    assert loaded.capture.body == body
    attempts = replayed.cases[0]["attempts"]
    assert isinstance(attempts, list)
    assertions = object_value(attempts[0])["assertions"]
    assert isinstance(assertions, list)
    framing = next(
        object_value(item) for item in assertions if object_value(item)["id"] == "SSE-FRAMING"
    )
    assert framing["status"] == ("FAIL" if pending else "PASS")
    assert path.read_bytes() == changed
    assert (path.parent / "body.bin").read_bytes() == body


@pytest.mark.parametrize(
    ("transformed", "end", "body_pending", "cached_pending"),
    [
        (True, "eof", False, True),
        (True, "eof", True, False),
        (False, "cancelled", False, True),
        (False, "cancelled", True, False),
    ],
)
def test_uncertain_replay_preserves_both_pending_tail_signals(
    tmp_path: Path, transformed: bool, end: CaptureEnd, body_pending: bool, cached_pending: bool
) -> None:
    from anthropic_readiness.cases import build_request, list_cases
    from anthropic_readiness.config import load_target
    from anthropic_readiness.contracts import resolve_contract
    from anthropic_readiness.runner import replay_run, result_exit_code

    target = load_target(Path("examples/target.yaml"))
    case = list_cases()[1]
    body = Path("tests/fixtures/contracts/core-1.0.0/stream-valid.sse").read_bytes()
    secret = "synthetic-redaction-token"
    if transformed:
        body = body.replace(b"Hello.", secret.encode())
    if body_pending:
        body += b"data: incomplete"
    root = tmp_path / "capture"
    create_run_directory(root)
    original = replace(capture(body, True), request=build_request(case, target), capture_end=end)
    refs = persist_capture(root, case.id, "synthetic", sanitize_capture(original, [secret]))
    path = root / refs.capture_path
    metadata = object_value(strict_json(path.read_text()))
    metadata["tail"] = {**object_value(metadata["tail"]), "pending_data": cached_pending}
    path.write_bytes(json_bytes(metadata))
    loaded = load_capture(path)
    assert loaded.transformed is transformed
    assert loaded.capture.capture_end == end
    assert loaded.capture.tail.pending_data is True
    replayed = replay_run(
        target,
        resolve_contract(target.contract_id, target.contract_revision),
        case.id,
        path,
        tmp_path / "replayed",
    )
    assert replayed.cases[0]["status"] == "INDETERMINATE"
    assert result_exit_code(replayed) == (130 if end == "cancelled" else 3)
