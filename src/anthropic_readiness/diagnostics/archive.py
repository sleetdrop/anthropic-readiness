"""Bounded classic-ZIP data inspection and extraction into owned new staging."""

from __future__ import annotations

import hashlib
import math
import os
import re
import shutil
import stat
import struct
import tempfile
import time
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile, ZipInfo

from anthropic_readiness.models import JsonObject, JsonValue

_CHUNK = 64 * 1024
_END = struct.Struct("<4s4H2IH")
_CENTRAL = struct.Struct("<4s6H3I5H2I")
_LOCAL = struct.Struct("<4s5H3I2H")


@dataclass(frozen=True)
class ArchiveLimits:
    max_compressed_bytes: int = 256 * 1024 * 1024
    max_expanded_bytes: int = 512 * 1024 * 1024
    max_member_bytes: int = 256 * 1024 * 1024
    max_json_bytes: int = 64 * 1024 * 1024
    max_members: int = 4096
    max_directory_bytes: int = 64 * 1024 * 1024
    timeout_s: float = 60

    def __post_init__(self) -> None:
        for value in (
            self.max_compressed_bytes,
            self.max_expanded_bytes,
            self.max_member_bytes,
            self.max_json_bytes,
            self.max_members,
            self.max_directory_bytes,
        ):
            if type(value) is not int or value <= 0:
                raise ValueError("archive_invalid_limits")
        if (
            isinstance(self.timeout_s, bool)
            or not math.isfinite(self.timeout_s)
            or self.timeout_s <= 0
        ):
            raise ValueError("archive_invalid_limits")


@dataclass
class _Budget:
    limits: ArchiveLimits
    clock: Callable[[], float]
    deadline: float
    expanded: int = 0

    def check(self) -> None:
        if self.clock() >= self.deadline:
            raise ValueError("archive_timeout")

    def consume(self, amount: int) -> None:
        self.expanded += amount
        if self.expanded > self.limits.max_expanded_bytes:
            raise ValueError("archive_expansion_limit")
        self.check()


def _read(stream: BinaryIO, length: int) -> bytes:
    data = stream.read(length)
    if len(data) != length:
        raise ValueError("archive_integrity")
    return data


def _extra(data: bytes) -> None:
    offset = 0
    while offset < len(data):
        if offset + 4 > len(data):
            raise ValueError("archive_integrity")
        tag, length = struct.unpack_from("<HH", data, offset)
        if tag == 1:
            raise ValueError("archive_unsupported")
        offset += 4 + length
        if offset > len(data):
            raise ValueError("archive_integrity")


def _footer(stream: BinaryIO, size: int, budget: _Budget) -> tuple[int, int]:
    budget.check()
    if size > budget.limits.max_compressed_bytes:
        raise ValueError("archive_upload_limit")
    length = min(size, 65535 + _END.size)
    stream.seek(size - length)
    tail = _read(stream, length)
    position = tail.rfind(b"PK\x05\x06")
    if position < 0 or len(tail) - position < _END.size:
        raise ValueError("archive_integrity")
    values = _END.unpack_from(tail, position)
    _, disk, directory_disk, disk_count, count, directory_size, directory_offset, comment = values
    if (
        disk
        or directory_disk
        or count == 65535
        or disk_count == 65535
        or directory_size == 0xFFFFFFFF
        or directory_offset == 0xFFFFFFFF
    ):
        raise ValueError("archive_unsupported")
    if disk_count != count or position + _END.size + comment != len(tail):
        raise ValueError("archive_integrity")
    if count > budget.limits.max_members:
        raise ValueError("archive_member_count_limit")
    if directory_size > budget.limits.max_directory_bytes:
        raise ValueError("archive_directory_limit")
    if directory_offset + directory_size != size - length + position:
        raise ValueError("archive_integrity")
    # Count actual central records before ZipFile can allocate its in-memory index.
    stream.seek(directory_offset)
    end = directory_offset + directory_size
    seen = 0
    while stream.tell() < end:
        budget.check()
        if stream.tell() + _CENTRAL.size > end:
            raise ValueError("archive_integrity")
        record = _CENTRAL.unpack(_read(stream, _CENTRAL.size))
        if record[0] != b"PK\x01\x02":
            raise ValueError("archive_integrity")
        seen += 1
        if seen > count or seen > budget.limits.max_members:
            raise ValueError("archive_integrity")
        variable_size = record[10] + record[11] + record[12]
        if stream.tell() + variable_size > end:
            raise ValueError("archive_integrity")
        if (
            record[13]
            or record[8] == 0xFFFFFFFF
            or record[9] == 0xFFFFFFFF
            or record[16] == 0xFFFFFFFF
        ):
            raise ValueError("archive_unsupported")
        stream.seek(variable_size, os.SEEK_CUR)
    if seen != count:
        raise ValueError("archive_integrity")
    return directory_offset, count


def _paths(infos: list[ZipInfo], budget: _Budget) -> None:
    names: set[str] = set()
    spellings: dict[str, str] = {}
    expanded = 0
    for info in infos:
        budget.check()
        name = info.orig_filename
        parts = name.split("/")
        if (
            not re.fullmatch(r"[A-Za-z0-9_./-]{1,240}", name)
            or any(part in {"", ".", ".."} for part in parts)
            or name != info.filename
            or name.casefold() in names
        ):
            raise ValueError("archive_path")
        names.add(name.casefold())
        for length in range(1, len(parts) + 1):
            prefix = "/".join(parts[:length])
            key = prefix.casefold()
            if key in spellings and spellings[key] != prefix:
                raise ValueError("archive_path")
            spellings[key] = prefix
        mode = stat.S_IFMT(info.external_attr >> 16)
        if mode not in (0, stat.S_IFREG) or info.external_attr & 0x10:
            raise ValueError("archive_member_type")
        if (
            info.extract_version > 20
            or info.flag_bits & ~0x80E
            or info.compress_type not in {ZIP_STORED, ZIP_DEFLATED}
        ):
            raise ValueError("archive_unsupported")
        _extra(info.extra)
        if info.file_size > budget.limits.max_member_bytes:
            raise ValueError("archive_member_limit")
        if name.endswith((".json", ".jsonl")) and info.file_size > budget.limits.max_json_bytes:
            raise ValueError("archive_json_limit")
        expanded += info.file_size
        if expanded > budget.limits.max_expanded_bytes:
            raise ValueError("archive_expansion_limit")
    for name in names:
        if any(
            "/".join(name.split("/")[:index]) in names for index in range(1, len(name.split("/")))
        ):
            raise ValueError("archive_path")


def _data_offset(stream: BinaryIO, info: ZipInfo, next_offset: int) -> int:
    stream.seek(info.header_offset)
    record = _LOCAL.unpack(_read(stream, _LOCAL.size))
    if (
        record[0] != b"PK\x03\x04"
        or record[1] > 20
        or record[2] != info.flag_bits
        or record[3] != info.compress_type
    ):
        raise ValueError("archive_integrity")
    if record[9] > 240 or stream.tell() + record[9] + record[10] > next_offset:
        raise ValueError("archive_integrity")
    if _read(stream, record[9]) != info.filename.encode("ascii"):
        raise ValueError("archive_integrity")
    _extra(_read(stream, record[10]))
    data_offset = stream.tell()
    end = data_offset + info.compress_size
    if end > next_offset:
        raise ValueError("archive_integrity")
    expected = (info.CRC, info.compress_size, info.file_size)
    if info.flag_bits & 8:
        if any(
            actual not in (0, wanted) for actual, wanted in zip(record[6:9], expected, strict=True)
        ):
            raise ValueError("archive_integrity")
        stream.seek(end)
        length = next_offset - end
        if length not in (12, 16):
            raise ValueError("archive_integrity")
        descriptor = _read(stream, length)
        if length == 16:
            if descriptor[:4] != b"PK\x07\x08":
                raise ValueError("archive_integrity")
            descriptor = descriptor[4:]
        if struct.unpack("<III", descriptor) != expected:
            raise ValueError("archive_integrity")
    elif tuple(record[6:9]) != expected or end != next_offset:
        raise ValueError("archive_integrity")
    return data_offset


def _member(
    stream: BinaryIO, info: ZipInfo, offset: int, budget: _Budget, write: Callable[[bytes], object]
) -> JsonObject:
    stream.seek(offset)
    remaining = info.compress_size
    decoder = zlib.decompressobj(-zlib.MAX_WBITS) if info.compress_type == ZIP_DEFLATED else None
    digest = hashlib.sha256()
    actual = 0
    crc = 0
    while remaining:
        budget.check()
        chunk = _read(stream, min(remaining, _CHUNK))
        remaining -= len(chunk)
        pending = chunk
        while pending:
            if decoder is not None:
                output = decoder.decompress(pending, _CHUNK)
                pending = decoder.unconsumed_tail
                if decoder.unused_data:
                    raise ValueError("archive_integrity")
            else:
                output, pending = pending, b""
            actual += len(output)
            if actual > budget.limits.max_member_bytes:
                raise ValueError("archive_member_limit")
            if (
                info.filename.endswith((".json", ".jsonl"))
                and actual > budget.limits.max_json_bytes
            ):
                raise ValueError("archive_json_limit")
            budget.consume(len(output))
            digest.update(output)
            crc = zlib.crc32(output, crc)
            write(output)
    if (decoder is not None and not decoder.eof) or actual != info.file_size or crc != info.CRC:
        raise ValueError("archive_integrity")
    return {
        "path": info.filename,
        "sha256": digest.hexdigest(),
        "bytes": actual,
        "compressed_bytes": info.compress_size,
        "crc32": crc,
    }


def _scan(
    path: Path, limits: ArchiveLimits, clock: Callable[[], float], destination: Path | None = None
) -> JsonObject:
    budget = _Budget(limits, clock, clock() + limits.timeout_s)
    if path.is_symlink():
        raise ValueError("archive_member_type")
    with path.open("rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("archive_member_type")
        directory, count = _footer(stream, metadata.st_size, budget)
        with ZipFile(stream, "r", allowZip64=False) as package:
            infos = package.infolist()
            if len(infos) != count:
                raise ValueError("archive_integrity")
            _paths(infos, budget)
            ordered = sorted(infos, key=lambda item: item.header_offset)
            if ordered and ordered[0].header_offset != 0:
                raise ValueError("archive_integrity")
            members: list[JsonValue] = []
            for index, info in enumerate(ordered):
                budget.check()
                next_offset = (
                    ordered[index + 1].header_offset if index + 1 < len(ordered) else directory
                )
                offset = _data_offset(stream, info, next_offset)
                if destination is None:
                    member = _member(stream, info, offset, budget, lambda data: None)
                else:
                    output = destination / info.filename
                    parent = destination
                    for part in Path(info.filename).parts[:-1]:
                        parent = parent / part
                        parent.mkdir(mode=0o700, exist_ok=True)
                    with tempfile.NamedTemporaryFile(
                        dir=destination, prefix=".member-", delete=False
                    ) as staging:
                        temporary = Path(staging.name)
                        try:
                            member = _member(stream, info, offset, budget, staging.write)
                            staging.flush()
                            os.fsync(staging.fileno())
                            if output.exists():
                                raise ValueError("archive_path")
                            os.replace(temporary, output)
                        finally:
                            temporary.unlink(missing_ok=True)
                members.append(member)
            digest = hashlib.sha256()
            stream.seek(0)
            hashed = 0
            while chunk := stream.read(_CHUNK):
                budget.check()
                hashed += len(chunk)
                if hashed > limits.max_compressed_bytes:
                    raise ValueError("archive_upload_limit")
                digest.update(chunk)
            if hashed != metadata.st_size:
                raise ValueError("archive_integrity")
            return {
                "schema_version": "1.0",
                "archive_sha256": digest.hexdigest(),
                "bytes": hashed,
                "expanded_bytes": budget.expanded,
                "members": members,
            }


def inspect_archive(
    path: Path, limits: ArchiveLimits, *, clock: Callable[[], float] = time.monotonic
) -> JsonObject:
    try:
        return _scan(path, limits, clock)
    except (BadZipFile, zlib.error, struct.error, UnicodeError, NotImplementedError) as exc:
        raise ValueError("archive_integrity") from exc


def extract_checked_archive(
    path: Path,
    destination: Path,
    inventory: JsonObject,
    limits: ArchiveLimits,
    *,
    clock: Callable[[], float] = time.monotonic,
) -> None:
    destination.mkdir(mode=0o700, exist_ok=False)
    try:
        try:
            actual = _scan(path, limits, clock, destination)
        except (BadZipFile, zlib.error, struct.error, UnicodeError, NotImplementedError) as exc:
            raise ValueError("archive_integrity") from exc
        if actual != inventory:
            raise ValueError("archive_inventory_mismatch")
    except BaseException:
        # Only this new directory is owned here; existing neighbors are untouched.
        shutil.rmtree(destination)
        raise
