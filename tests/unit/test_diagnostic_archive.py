"""Archive limits are enforced before allocation/publication, using tiny fixtures."""

from __future__ import annotations

import io
import socket
import stat
import struct
import sys
import warnings
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from anthropic_readiness.diagnostics import archive
from anthropic_readiness.diagnostics.archive import (
    ArchiveLimits,
    extract_checked_archive,
    inspect_archive,
)
from anthropic_readiness.models import object_value


def package(
    tmp_path: Path, entries: list[tuple[str, bytes]], *, compression: int = zipfile.ZIP_DEFLATED
) -> Path:
    path = tmp_path / "input.zip"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(path, "w", compression=compression) as output:
            for name, data in entries:
                output.writestr(name, data)
    return path


def mutate(
    path: Path,
    *,
    local: tuple[int, bytes] | None = None,
    central: tuple[int, bytes] | None = None,
    footer: tuple[int, bytes] | None = None,
) -> None:
    data = bytearray(path.read_bytes())
    for signature, change in (
        (b"PK\x03\x04", local),
        (b"PK\x01\x02", central),
        (b"PK\x05\x06", footer),
    ):
        if change is not None:
            offset, replacement = change
            start = data.index(signature) + offset
            data[start : start + len(replacement)] = replacement
    path.write_bytes(data)


@pytest.mark.parametrize("compression", [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED])
def test_valid_archive_round_trip_and_permissions(tmp_path: Path, compression: int) -> None:
    path = package(
        tmp_path, [("result.json", b"{}"), ("evidence/body.bin", b"hello")], compression=compression
    )
    inventory = inspect_archive(path, ArchiveLimits())
    destination = tmp_path / "checked"
    extract_checked_archive(path, destination, inventory, ArchiveLimits())
    assert (destination / "result.json").read_bytes() == b"{}"
    assert (destination / "evidence/body.bin").read_bytes() == b"hello"
    assert stat.S_IMODE(destination.stat().st_mode) == 0o700
    assert stat.S_IMODE((destination / "result.json").stat().st_mode) == 0o600
    assert inventory["expanded_bytes"] == 7


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "/absolute",
        "a/../escape",
        "a//b",
        "a/./b",
        "a\\b",
        "C:/file",
        "a/",
        "é.json",
        "a b",
        "a" * 241,
    ],
)
def test_unsafe_names_are_rejected_without_touching_neighbors(tmp_path: Path, name: str) -> None:
    sentinel = tmp_path / "sentinel"
    sentinel.write_bytes(b"keep")
    path = package(tmp_path, [(name, b"data")])
    with pytest.raises(ValueError, match="archive_path"):
        inspect_archive(path, ArchiveLimits())
    assert sentinel.read_bytes() == b"keep"
    assert sorted(item.name for item in tmp_path.iterdir()) == ["input.zip", "sentinel"]


@pytest.mark.parametrize("names", [["a", "a"], ["a", "A"], ["a", "a/b"], ["A/x", "a/y"]])
def test_duplicate_or_ambiguous_names_are_rejected(tmp_path: Path, names: list[str]) -> None:
    path = package(tmp_path, [(name, b"x") for name in names])
    with pytest.raises(ValueError, match="archive_path"):
        inspect_archive(path, ArchiveLimits())


@pytest.mark.parametrize(
    "mode", [stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO, stat.S_IFDIR]
)
def test_nonregular_members_are_rejected(tmp_path: Path, mode: int) -> None:
    path = tmp_path / "input.zip"
    info = zipfile.ZipInfo("link")
    info.create_system = 3
    info.external_attr = (mode | 0o600) << 16
    with zipfile.ZipFile(path, "w") as output:
        output.writestr(info, b"target")
    with pytest.raises(ValueError, match="archive_member_type"):
        inspect_archive(path, ArchiveLimits())


@pytest.mark.parametrize("kind", ["encryption", "strong_encryption", "zip64", "split", "method"])
def test_unsupported_zip_features_are_rejected(tmp_path: Path, kind: str) -> None:
    path = package(tmp_path, [("a", b"data")])
    if kind in {"encryption", "strong_encryption"}:
        flags = struct.pack("<H", 1 if kind == "encryption" else 64)
        mutate(path, local=(6, flags), central=(8, flags))
    elif kind == "zip64":
        mutate(path, footer=(10, b"\xff\xff"))
    elif kind == "split":
        mutate(path, footer=(4, b"\x01\x00"))
    else:
        mutate(path, local=(8, struct.pack("<H", 12)), central=(10, struct.pack("<H", 12)))
    with pytest.raises(ValueError, match="archive_unsupported"):
        inspect_archive(path, ArchiveLimits())


@pytest.mark.parametrize(
    ("field", "limit"),
    [
        ("max_compressed_bytes", 1),
        ("max_expanded_bytes", 3),
        ("max_member_bytes", 3),
        ("max_json_bytes", 3),
        ("max_members", 1),
        ("max_directory_bytes", 1),
    ],
)
def test_declared_limits_are_enforced(tmp_path: Path, field: str, limit: int) -> None:
    path = package(tmp_path, [("a.json", b"1234"), ("b.json", b"{}")])
    with pytest.raises(ValueError, match=r"archive_.*limit"):
        inspect_archive(path, replace(ArchiveLimits(), **{field: limit}))


def test_footer_limits_precede_zipfile_allocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = package(tmp_path, [("a", b"x"), ("b", b"y")])
    mutate(path, footer=(8, struct.pack("<HH", 1, 1)))

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("ZipFile_must_not_allocate_before_footer_validation")

    monkeypatch.setattr(archive, "ZipFile", forbidden)
    with pytest.raises(ValueError, match="archive_integrity"):
        inspect_archive(path, ArchiveLimits())


def test_forged_expanded_size_cannot_hide_actual_expansion(tmp_path: Path) -> None:
    path = package(tmp_path, [("a", b"x" * 100_000)])
    mutate(path, local=(22, struct.pack("<I", 1)), central=(24, struct.pack("<I", 1)))
    with pytest.raises(ValueError, match="archive_member_limit"):
        inspect_archive(path, replace(ArchiveLimits(), max_member_bytes=100))


def test_crc_mismatch_and_truncated_compressed_stream_are_rejected(tmp_path: Path) -> None:
    path = package(tmp_path, [("a", b"payload")])
    mutate(path, local=(14, b"\x00" * 4), central=(16, b"\x00" * 4))
    with pytest.raises(ValueError, match="archive_integrity"):
        inspect_archive(path, ArchiveLimits())
    path = package(tmp_path, [("a", b"payload")])
    data = bytearray(path.read_bytes())
    data[31] ^= 0xFF
    path.write_bytes(data)
    with pytest.raises(ValueError, match="archive_integrity"):
        inspect_archive(path, ArchiveLimits())


def test_inventory_mismatch_cleans_only_owned_new_destination(tmp_path: Path) -> None:
    path = package(tmp_path, [("a", b"x")])
    inventory = inspect_archive(path, ArchiveLimits())
    members = inventory["members"]
    assert isinstance(members, list)
    members[0] = {**object_value(members[0]), "sha256": "0" * 64}
    destination = tmp_path / "staging"
    sentinel = tmp_path / "unrelated"
    sentinel.write_bytes(b"keep")
    with pytest.raises(ValueError, match="archive_inventory_mismatch"):
        extract_checked_archive(path, destination, inventory, ArchiveLimits())
    assert not destination.exists()
    assert sentinel.read_bytes() == b"keep"
    destination.mkdir()
    (destination / "existing").write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        extract_checked_archive(path, destination, inventory, ArchiveLimits())
    assert (destination / "existing").read_bytes() == b"keep"


def test_every_limit_inclusive_boundary(tmp_path: Path) -> None:
    path = package(tmp_path, [("a.json", b"{}"), ("b.json", b"{}")], compression=zipfile.ZIP_STORED)
    limits = ArchiveLimits(
        max_compressed_bytes=path.stat().st_size,
        max_expanded_bytes=4,
        max_member_bytes=2,
        max_json_bytes=2,
        max_members=2,
        max_directory_bytes=2 * (46 + len("a.json")),
    )
    inventory = inspect_archive(path, limits)
    extract_checked_archive(path, tmp_path / "exact", inventory, limits)
    assert (tmp_path / "exact/b.json").read_bytes() == b"{}"


def test_monotonic_deadline_is_injected_and_leaves_no_partial_output(tmp_path: Path) -> None:
    path = package(tmp_path, [("a", b"x")])
    inventory = inspect_archive(path, ArchiveLimits())
    ticks = iter([0.0, 61.0])
    with pytest.raises(ValueError, match="archive_timeout"):
        extract_checked_archive(
            path, tmp_path / "timeout", inventory, ArchiveLimits(), clock=lambda: next(ticks)
        )
    assert not (tmp_path / "timeout").exists()


def test_archive_never_executes_or_connects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = package(
        tmp_path,
        [
            ("malicious_archive_module.py", b"raise RuntimeError('executed')"),
            ("report.html", b"<script>fetch('https://invalid.example')</script>"),
        ],
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("archive_must_not_connect")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    inventory = inspect_archive(path, ArchiveLimits())
    extract_checked_archive(path, tmp_path / "data-only", inventory, ArchiveLimits())
    assert "malicious_archive_module" not in sys.modules


def test_every_nested_staging_directory_is_private(tmp_path: Path) -> None:
    path = package(tmp_path, [("evidence/case/attempt/body.bin", b"x")])
    inventory = inspect_archive(path, ArchiveLimits())
    destination = tmp_path / "private"
    extract_checked_archive(path, destination, inventory, ArchiveLimits())
    for directory in (
        destination,
        destination / "evidence",
        destination / "evidence/case",
        destination / "evidence/case/attempt",
    ):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700


@pytest.mark.parametrize(
    ("field", "code"),
    [("max_json_bytes", "archive_json_limit"), ("max_expanded_bytes", "archive_expansion_limit")],
)
def test_actual_byte_limits_do_not_trust_forged_sizes(
    tmp_path: Path, field: str, code: str
) -> None:
    path = package(tmp_path, [("a.json", b"x" * 100_000)])
    mutate(path, local=(22, struct.pack("<I", 1)), central=(24, struct.pack("<I", 1)))
    with pytest.raises(ValueError, match=code):
        inspect_archive(path, replace(ArchiveLimits(), **{field: 10}))


def test_forced_zip64_local_headers_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "zip64.zip"
    with zipfile.ZipFile(path, "w") as output, output.open("a", "w", force_zip64=True) as stream:
        stream.write(b"x")
    with pytest.raises(ValueError, match="archive_unsupported"):
        inspect_archive(path, ArchiveLimits())


def test_chunk_boundaries_and_empty_files_are_read_completely(tmp_path: Path) -> None:
    path = package(tmp_path, [("a", b"x" * (64 * 1024 * 3)), ("empty", b"")])
    inventory = inspect_archive(path, ArchiveLimits())
    destination = tmp_path / "chunks"
    extract_checked_archive(path, destination, inventory, ArchiveLimits())
    assert (destination / "a").read_bytes() == b"x" * (64 * 1024 * 3)
    assert (destination / "empty").read_bytes() == b""


def test_classic_data_descriptors_are_supported(tmp_path: Path) -> None:
    class ForwardOnly(io.BytesIO):
        def seek(self, offset: int, whence: int = 0) -> int:
            raise OSError("synthetic_forward_only")

    buffer = ForwardOnly()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as output:
        output.writestr("a.json", b"{}")
        output.writestr("b.bin", b"x" * 70_000)
    path = tmp_path / "descriptor.zip"
    path.write_bytes(buffer.getvalue())
    inventory = inspect_archive(path, ArchiveLimits())
    extract_checked_archive(path, tmp_path / "descriptor", inventory, ArchiveLimits())
    assert (tmp_path / "descriptor/b.bin").read_bytes() == b"x" * 70_000
