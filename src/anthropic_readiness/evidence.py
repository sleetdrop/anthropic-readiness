"""Sanitize in memory, then persist exclusive and verifiable evidence."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import uuid
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path, PurePosixPath

from anthropic_readiness.config import string
from anthropic_readiness.models import (
    Capture,
    CaptureEnd,
    DecodeTail,
    EvidenceRef,
    JsonObject,
    JsonValue,
    ProtocolEnd,
    ReadRecord,
    RequestSpec,
    object_value,
    strict_json,
)
from anthropic_readiness.schema import load_schema, validate_document
from anthropic_readiness.sse import SSEDecoder

REQUEST_HEADERS = {"content-type", "accept", "anthropic-version", "anthropic-beta"}
RESPONSE_HEADERS = {
    "content-type",
    "content-encoding",
    "request-id",
    "anthropic-request-id",
    "retry-after",
}
CAPTURE_ENDS: tuple[CaptureEnd, ...] = (
    "eof",
    "timeout",
    "read_error",
    "capture_limit",
    "cancelled",
    "connection_error",
)
PROTOCOL_ENDS: tuple[ProtocolEnd, ...] = ("message_stop", "error_event", "none")


class Redactor:
    def __init__(self, secrets: Sequence[str]):
        self.patterns: list[re.Pattern[bytes]] = []
        for secret in sorted({s for s in secrets if s}, key=len, reverse=True):
            parts: list[bytes] = []
            for char in secret:
                raw = re.escape(char.encode())
                escaped = re.escape(json.dumps(char, ensure_ascii=True)[1:-1].encode())
                code = ord(char)
                unicode_form = (
                    f"\\u{code:04x}" if code <= 65535 else json.dumps(char, ensure_ascii=True)[1:-1]
                ).encode()
                variants = [raw, escaped, b"(?i:" + re.escape(unicode_form) + b")"]
                if char == "/":
                    variants.append(re.escape(b"\\/"))
                parts.append(b"(?:" + b"|".join(variants) + b")")
            self.patterns.append(re.compile(b"".join(parts)))

    def bytes(self, value: bytes) -> bytes:
        for pattern in self.patterns:
            value = pattern.sub(b"[REDACTED]", value)
        return value

    def text(self, value: str) -> str:
        return self.bytes(value.encode()).decode()

    def json(self, value: JsonValue) -> JsonValue:
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, list):
            return [self.json(item) for item in value]
        if isinstance(value, dict):
            return {self.text(key): self.json(item) for key, item in value.items()}
        return value


def sanitize_json(value: JsonValue, secrets: Sequence[str]) -> JsonValue:
    return Redactor(secrets).json(value)


@dataclass(frozen=True)
class SanitizedCapture:
    capture: Capture
    original_sha256: str
    original_length: int
    transformed: bool = False
    transforms: tuple[str, ...] = ()
    replay_rechunked: bool = False


@dataclass(frozen=True)
class CaptureRefs:
    capture_path: str
    refs: tuple[EvidenceRef, ...]


def sanitize_capture(capture: Capture, secrets: Sequence[str]) -> SanitizedCapture:
    redactor = Redactor(secrets)
    body = redactor.bytes(capture.body)
    request = replace(
        capture.request,
        url=redactor.text(capture.request.url),
        body=object_value(redactor.json(capture.request.body)),
        headers=tuple(
            (k.lower(), redactor.text(v))
            for k, v in capture.request.headers
            if k.lower() in REQUEST_HEADERS
        ),
    )
    clean = replace(
        capture,
        request=request,
        body=body,
        headers=tuple(
            (k.lower(), redactor.text(v))
            for k, v in capture.headers
            if k.lower() in RESPONSE_HEADERS
        ),
        frames=tuple(
            replace(
                f, event=redactor.text(f.event), data=redactor.text(f.data), id=redactor.text(f.id)
            )
            for f in capture.frames
        ),
        error=redactor.text(capture.error) if capture.error is not None else None,
    )
    changed = body != capture.body
    return SanitizedCapture(
        clean,
        hashlib.sha256(capture.body).hexdigest(),
        len(capture.body),
        changed,
        ("credential_redaction",) if changed else (),
    )


def create_run_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=False)
    path.chmod(0o700)


def safe_path(root: Path, relative: str) -> Path:
    parts = PurePosixPath(relative).parts
    if (
        not parts
        or PurePosixPath(relative).is_absolute()
        or any(p in {".", ".."} for p in parts)
        or "\\" in relative
        or root.is_symlink()
    ):
        raise ValueError("invalid_evidence_path")
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("symlink_evidence_path")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("escaping_evidence_path")
    return path


def atomic_write(path: Path, data: bytes) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    temporary = path.with_name("." + path.name + "." + uuid.uuid4().hex)
    try:
        fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def json_bytes(value: JsonValue) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def persist_capture(
    root: Path, case_id: str, attempt_id: str, capture: SanitizedCapture
) -> CaptureRefs:
    for token in (case_id, attempt_id):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", token) or token in {".", ".."}:
            raise ValueError("invalid_capture_path_component")
    for part in ("evidence", f"evidence/{case_id}"):
        safe_path(root, part).mkdir(mode=0o700, exist_ok=True)
    relative = f"evidence/{case_id}/{attempt_id}"
    directory = safe_path(root, relative)
    directory.mkdir(mode=0o700, exist_ok=False)
    value = capture.capture
    request: JsonObject = {
        "url": value.request.url,
        "headers": dict(value.request.headers),
        "body": value.request.body,
        "streaming": value.request.streaming,
    }
    contents = {
        "request.json": json_bytes(request),
        "body.bin": value.body,
        "reads.json": json_bytes([object_value(asdict(r)) for r in value.reads]),
        "events.jsonl": b"".join(
            (json.dumps(asdict(f), ensure_ascii=False) + "\n").encode() for f in value.frames
        ),
    }
    local_refs: list[EvidenceRef] = []
    refs: list[EvidenceRef] = []
    for name, data in contents.items():
        atomic_write(directory / name, data)
        digest = hashlib.sha256(data).hexdigest()
        local_refs.append(EvidenceRef(name, digest))
        refs.append(EvidenceRef(f"{relative}/{name}", digest))
    metadata: JsonObject = {
        "schema_version": "1.0",
        "request": request,
        "status_code": value.status_code,
        "headers": dict(value.headers),
        "protocol_end": value.protocol_end,
        "capture_end": value.capture_end,
        "tail": object_value(asdict(value.tail)),
        "observed_bytes": value.observed_bytes,
        "retained_bytes": len(value.body),
        "duration_ms": value.duration_ms,
        "headers_ms": value.headers_ms,
        "error": value.error,
        "transformed": capture.transformed,
        "transforms": list(capture.transforms),
        "original_sha256": capture.original_sha256,
        "original_length": capture.original_length,
        "files": [r.to_json() for r in local_refs],
    }
    validate_document(metadata, load_schema("capture"))
    data = json_bytes(metadata)
    atomic_write(directory / "response.json", data)
    refs.append(EvidenceRef(f"{relative}/response.json", hashlib.sha256(data).hexdigest()))
    return CaptureRefs(f"{relative}/response.json", tuple(refs))


def _pointer(value: JsonValue, pointer: str) -> JsonValue:
    if pointer == "":
        return value
    if not pointer.startswith("/"):
        raise ValueError("invalid_json_pointer")
    for raw in pointer[1:].split("/"):
        if re.search(r"~(?![01])", raw):
            raise ValueError("invalid_json_pointer")
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict):
            value = value[key]
        elif isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", key):
            value = value[int(key)]
        else:
            raise ValueError("unresolved_json_pointer")
    return value


def verify_evidence(root: Path, refs: Sequence[EvidenceRef]) -> list[str]:
    errors: list[str] = []
    for ref in refs:
        try:
            path = safe_path(root, ref.path)
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != ref.sha256:
                raise ValueError("hash_mismatch")
            if ref.event is not None:
                if not ref.path.endswith("events.jsonl") or ref.event < 0:
                    raise ValueError("invalid_event_reference")
                lines = data.decode().splitlines()
                frame = object_value(strict_json(lines[ref.event]))
                if frame.get("sequence") != ref.event:
                    raise ValueError("event_sequence_mismatch")
                if ref.pointer is not None:
                    _pointer(strict_json(string(frame["data"])), ref.pointer)
            elif ref.pointer is not None:
                _pointer(strict_json(data.decode()), ref.pointer)
        except (OSError, ValueError, KeyError, IndexError) as exc:
            errors.append(f"{ref.path}:{type(exc).__name__}:{exc}")
    return errors


def _integer(value: JsonValue) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("invalid_capture_integer")
    return value


def _number(value: JsonValue) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError("invalid_capture_time")
    return float(value)


def load_capture(path: Path) -> SanitizedCapture:
    if path.is_symlink() or path.name != "response.json":
        raise ValueError("invalid_capture_path")
    metadata = object_value(strict_json(path.read_text()))
    validate_document(metadata, load_schema("capture"))
    directory = path.parent
    listed = metadata["files"]
    assert isinstance(listed, list)
    refs: list[EvidenceRef] = []
    for entry in listed:
        value = object_value(entry)
        refs.append(EvidenceRef(string(value["path"]), string(value["sha256"])))
    if {r.path for r in refs} != {"body.bin", "request.json", "reads.json", "events.jsonl"} or len(
        refs
    ) != 4:
        raise ValueError("capture_integrity:inventory")
    if errors := verify_evidence(directory, refs):
        raise ValueError("capture_integrity:" + ";".join(errors))
    request_data = object_value(strict_json((directory / "request.json").read_text()))
    if request_data != metadata["request"]:
        raise ValueError("capture_integrity:request")
    streaming = request_data.get("streaming")
    if not isinstance(streaming, bool):
        raise ValueError("invalid_capture_streaming")
    request = RequestSpec(
        string(request_data["url"]),
        tuple((k, string(v)) for k, v in object_value(request_data["headers"]).items()),
        object_value(request_data["body"]),
        streaming,
    )
    body = (directory / "body.bin").read_bytes()
    if len(body) != metadata["retained_bytes"]:
        raise ValueError("capture_integrity:retained_bytes")
    transformed = metadata["transformed"] is True
    original_hash = string(metadata["original_sha256"])
    original_length = _integer(metadata["original_length"])
    if not transformed and (
        hashlib.sha256(body).hexdigest() != original_hash or len(body) != original_length
    ):
        raise ValueError("capture_integrity:original_body")
    raw_reads = strict_json((directory / "reads.json").read_text())
    if not isinstance(raw_reads, list):
        raise ValueError("invalid_capture_reads")
    reads = tuple(
        ReadRecord(_integer(object_value(v)["length"]), _number(object_value(v)["received_ms"]))
        for v in raw_reads
    )
    rechunked = (
        transformed or metadata["capture_end"] != "eof" or sum(r.length for r in reads) != len(body)
    )
    if rechunked:
        reads = tuple(
            ReadRecord(min(4096, len(body) - offset), 0) for offset in range(0, len(body), 4096)
        )
    decoder = SSEDecoder(max(1, len(body) + 1), max(1, len(body) + 1))
    frames = []
    offset = 0
    for read in reads:
        if streaming:
            frames.extend(decoder.feed(body[offset : offset + read.length], read.received_ms))
        offset += read.length
    tail = decoder.finish() if streaming else DecodeTail()
    raw_tail = object_value(metadata["tail"])
    pending = raw_tail.get("pending_data")
    if not isinstance(pending, bool):
        raise ValueError("invalid_capture_tail")
    tail = replace(
        tail,
        pending_data=pending,
        encoding_errors=_integer(raw_tail["encoding_errors"]),
        limit_kind=string(raw_tail["limit_kind"])
        if raw_tail.get("limit_kind") is not None
        else None,
    )
    end = next(candidate for candidate in CAPTURE_ENDS if candidate == metadata["capture_end"])
    protocol = next(
        candidate for candidate in PROTOCOL_ENDS if candidate == metadata["protocol_end"]
    )
    status = _integer(metadata["status_code"]) if metadata["status_code"] is not None else None
    capture = Capture(
        request,
        status,
        tuple((k, string(v)) for k, v in object_value(metadata["headers"]).items()),
        body,
        reads,
        tuple(frames),
        protocol,
        end,
        tail,
        _integer(metadata["observed_bytes"]),
        _number(metadata["duration_ms"]),
        _number(metadata["headers_ms"]) if metadata["headers_ms"] is not None else None,
        string(metadata["error"]) if metadata["error"] is not None else None,
    )
    transforms = metadata["transforms"]
    if not isinstance(transforms, list):
        raise ValueError("invalid_capture_transforms")
    return SanitizedCapture(
        capture,
        original_hash,
        original_length,
        transformed,
        tuple(string(v) for v in transforms),
        rechunked,
    )
