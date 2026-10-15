"""Single-capture replay is case-scoped and makes zero requests."""

import json
from pathlib import Path

import pytest

from tests.acceptance.test_cli import ROOT, cli, target_file


@pytest.mark.parametrize(("name", "exit_code"), [("valid", 0), ("duplicate-start", 1)])
def test_replay_expected_exit_and_zero_requests(tmp_path: Path, name: str, exit_code: int) -> None:
    capture = (
        ROOT
        / f"tests/fixtures/captures/{name}/evidence/ANT-TEXT-SSE-001/fixture-attempt/response.json"
    )
    out = tmp_path / "run"
    completed = cli(
        "replay",
        "--capture",
        str(capture),
        "--target",
        str(target_file(tmp_path)),
        "--case",
        "ANT-TEXT-SSE-001",
        "--out",
        str(out),
    )
    assert completed.returncode == exit_code, completed.stderr
    result = json.loads((out / "result.json").read_text())
    assert result["mode"] == "replay"
    assert result["plan"]["actual_requests"] == 0
    assert len(result["cases"]) == 1
    assert result["profiles"][0]["id"] == "capture-replay"


def test_capture_contract_mismatch_rejected_before_output(tmp_path: Path) -> None:
    from dataclasses import replace

    from anthropic_readiness.cases import build_request, list_cases
    from anthropic_readiness.config import load_target
    from anthropic_readiness.evidence import create_run_directory, persist_capture, sanitize_capture
    from tests.factories import capture as make_capture

    target_path = target_file(tmp_path)
    target = load_target(target_path)
    selected = list_cases()[1]
    request = build_request(selected, target)
    request = replace(request, headers=(("anthropic-version", "2099-01-01"),))
    source = tmp_path / "source"
    create_run_directory(source)
    body = (ROOT / "tests/fixtures/contracts/core-1.0.0/stream-valid.sse").read_bytes()
    refs = persist_capture(
        source,
        selected.id,
        "attempt",
        sanitize_capture(replace(make_capture(body, True), request=request), []),
    )
    out = tmp_path / "run"
    completed = cli(
        "replay",
        "--capture",
        str(source / refs.capture_path),
        "--target",
        str(target_path),
        "--case",
        selected.id,
        "--out",
        str(out),
    )
    assert completed.returncode == 2
    assert not out.exists()
