"""Container bind ownership must not silently erase declared-root Git provenance."""

import shlex
import subprocess
from pathlib import Path

import pytest

from scripts.check import _git_state


def test_declared_git_root_records_identity_without_running_fsmonitor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return result.stdout.strip()

    git("init", "--quiet")
    git(
        "-c",
        "user.name=Synthetic fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "--quiet",
        "--allow-empty",
        "-m",
        "Synthetic fixture",
    )
    expected = git("rev-parse", "HEAD")
    marker = tmp_path / "hook-called"
    hook = tmp_path / "fsmonitor.sh"
    hook.write_text("#!/bin/sh\nprintf called > " + shlex.quote(str(marker)) + "\n")
    hook.chmod(0o700)
    git("config", "core.fsmonitor", str(hook))
    empty_config = tmp_path / "empty-config"
    empty_config.write_text("")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty_config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TEST_ASSUME_DIFFERENT_OWNER", "1")
    state = _git_state(tmp_path)
    assert state["commit"] == expected
    assert state["dirty"] is True
    assert not marker.exists(), "metadata inspection executed a repository hook"
