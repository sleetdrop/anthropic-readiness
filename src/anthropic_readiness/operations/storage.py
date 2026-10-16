"""Private operational locking and replaceable snapshots; evidence stays exclusive."""

from __future__ import annotations

import os
import sys
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from anthropic_readiness.evidence import json_bytes, safe_path
from anthropic_readiness.models import JsonObject, object_value, strict_json

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

MAX_DOCUMENT_BYTES = 64 * 1024 * 1024
MAX_JOURNAL_BYTES = 16 * 1024 * 1024


@contextmanager
def locked(root: Path, name: str = "writer.lock", *, blocking: bool = True) -> Iterator[None]:
    if root.is_symlink():
        raise ValueError("symlink_operations_root")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = safe_path(root, name)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "r+b") as stream:
        if sys.platform == "win32":
            if os.fstat(fd).st_size == 0:
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(fd, msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        try:
            yield
        finally:
            if sys.platform == "win32":
                stream.seek(0)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(fd, fcntl.LOCK_UN)


def read_document(path: Path) -> JsonObject:
    if path.is_symlink():
        raise ValueError("symlink_operational_document")
    with path.open("rb") as stream:
        data = stream.read(MAX_DOCUMENT_BYTES + 1)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("operational_document_limit")
    return object_value(strict_json(data.decode()))


def replace_snapshot(root: Path, document: JsonObject) -> None:
    path = safe_path(root, "execution.json")
    temporary = safe_path(root, ".execution-" + uuid.uuid4().hex)
    data = json_bytes(document)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("operational_document_limit")
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(fd)
        os.replace(temporary, path)
        if sys.platform != "win32":
            directory_fd = os.open(root, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)
