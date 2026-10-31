"""The Linux worker exit probe must tolerate process disappearance races."""

from pathlib import Path

import pytest

from tests.integration.test_worker_lifecycle import _worker_has_exited


@pytest.mark.parametrize("error", [FileNotFoundError, ProcessLookupError])
def test_disappearing_process_counts_as_exited(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: type[OSError]
) -> None:
    def vanished(path: Path, *args: object, **kwargs: object) -> str:
        raise error("process exited while reading")

    monkeypatch.setattr(Path, "read_text", vanished)
    assert _worker_has_exited(tmp_path / "stat")


def test_live_and_zombie_process_states_are_distinguished(tmp_path: Path) -> None:
    stat = tmp_path / "stat"
    stat.write_text("42 (worker) S")
    assert not _worker_has_exited(stat)
    stat.write_text("42 (worker) Z")
    assert _worker_has_exited(stat)


def test_unexpected_read_error_is_not_treated_as_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def denied(path: Path, *args: object, **kwargs: object) -> str:
        raise PermissionError("access denied")

    monkeypatch.setattr(Path, "read_text", denied)
    with pytest.raises(PermissionError):
        _worker_has_exited(tmp_path / "stat")
