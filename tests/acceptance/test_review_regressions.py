"""Whole-stage review counterexamples and legal controls."""

import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from anthropic_readiness.cases import build_request, list_cases
from anthropic_readiness.config import load_target
from anthropic_readiness.contracts import resolve_contract
from anthropic_readiness.evidence import create_run_directory, persist_capture, sanitize_capture
from anthropic_readiness.models import Capture, RequestSpec, object_value, strict_json
from anthropic_readiness.reporting import render_from_file
from anthropic_readiness.runner import execute_run, plan_run, replay_run, result_exit_code
from anthropic_readiness.schema import result_from_document
from anthropic_readiness.sse import SSEDecoder
from anthropic_readiness.validation.stream import StreamValidator
from tests.acceptance.test_runner import FixtureTransport
from tests.factories import capture

ROOT = Path(__file__).resolve().parents[2]


def test_reduced_profile_and_assertion_contract_cannot_certify_pass() -> None:
    original = object_value(strict_json((ROOT / "tests/fixtures/results/mixed.json").read_text()))
    result_from_document(original)
    value = json.loads(json.dumps(original))
    first = value["cases"][0]
    value["cases"] = [first]
    value["plan"]["cases"] = value["plan"]["cases"][:1]
    value["plan"]["profiles"][0]["cases"] = [first["id"]]
    value["profiles"][0]["cases"] = [first["id"]]
    value["profiles"][0]["readiness"] = "passed"
    value["plan"]["planned_requests"] = value["plan"]["actual_requests"] = 1
    with pytest.raises(ValueError, match=r"contract|profile"):
        result_from_document(value)

    value = json.loads(json.dumps(original))
    value["plan"]["cases"][0]["assertions"] = [
        a for a in value["plan"]["cases"][0]["assertions"] if a["id"] != "TASK-COMPLETE"
    ]
    value["cases"][0]["attempts"][0]["assertions"] = [
        a for a in value["cases"][0]["attempts"][0]["assertions"] if a["id"] != "TASK-COMPLETE"
    ]
    with pytest.raises(ValueError, match=r"contract|assertion"):
        result_from_document(value)


@pytest.mark.parametrize("secret", ["synthetic-text-secret", "message_start"])
def test_transformed_replay_preserves_only_proven_structure(tmp_path: Path, secret: str) -> None:
    target = load_target(ROOT / "examples/target.yaml")
    bundle = resolve_contract(target.contract_id, target.contract_revision)
    case = list_cases()[1]
    body = (ROOT / "tests/fixtures/contracts/core-1.0.0/stream-duplicate-start.sse").read_bytes()
    if secret != "message_start":
        body = body.replace(b"Hello.", secret.encode())
    source = tmp_path / "source"
    create_run_directory(source)
    clean = sanitize_capture(
        replace(capture(body, True), request=build_request(case, target)), [secret]
    )
    refs = persist_capture(source, case.id, "synthetic", clean)
    result = replay_run(target, bundle, case.id, source / refs.capture_path, tmp_path / "replay")
    assertions = json.loads(json.dumps(result.to_json()))["cases"][0]["attempts"][0]["assertions"]
    starts = next(a for a in assertions if a["id"] == "STR-START")
    if secret == "message_start":
        assert starts["status"] == "INDETERMINATE"
        assert result_exit_code(result) == 3
    else:
        assert starts["status"] == "FAIL"
        assert result_exit_code(result) == 1


def test_deep_json_keeps_known_failure_and_persisted_capture(tmp_path: Path) -> None:
    from anthropic_readiness.config import Limits

    class DeepTransport(FixtureTransport):
        def send(self, request: RequestSpec, limits: Limits, deadline: float) -> Capture:
            if self.calls == 1:
                self.calls += 1
                body = (
                    ROOT / "tests/fixtures/contracts/core-1.0.0/stream-duplicate-start.sse"
                ).read_bytes()
                body += (
                    b'event: extension\ndata: {"type":"extension","nested":'
                    + b"[" * 2000
                    + b"0"
                    + b"]" * 2000
                    + b"}\n\n"
                )
                return replace(capture(body, True), request=request)
            return super().send(request, limits, deadline)

    target = load_target(ROOT / "examples/target.yaml")
    out = tmp_path / "run"
    result = execute_run(
        plan_run(
            target,
            resolve_contract(target.contract_id, target.contract_revision),
            ["anthropic-basic"],
        ),
        DeepTransport(),
        out,
    )
    assert [c["status"] for c in result.cases] == ["PASS", "FAIL", "PASS"]
    assert result_exit_code(result) == 1
    text = (out / "result.json").read_text()
    assert "STR-START" in text
    assert "json_depth_limit" in text
    assert list((out / "evidence/ANT-TEXT-SSE-001").rglob("body.bin"))


def test_capture_is_retained_even_if_validator_crashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import anthropic_readiness.runner as runner

    def broken(*args: object) -> None:
        raise RuntimeError("synthetic validator fault")

    monkeypatch.setattr(runner, "_validate", broken)
    target = load_target(ROOT / "examples/target.yaml")
    out = tmp_path / "run"
    result = execute_run(
        plan_run(
            target,
            resolve_contract(target.contract_id, target.contract_revision),
            ["anthropic-basic"],
        ),
        FixtureTransport(),
        out,
    )
    assert result_exit_code(result) == 4
    assert list((out / "evidence/ANT-MESSAGE-001").rglob("body.bin"))
    assert result.evidence


@pytest.mark.parametrize("field", ["sha256", "event", "pointer"])
def test_report_checks_assertion_refs_not_only_inventory(tmp_path: Path, field: str) -> None:
    target = load_target(ROOT / "examples/target.yaml")
    source = tmp_path / "source"
    execute_run(
        plan_run(
            target,
            resolve_contract(target.contract_id, target.contract_revision),
            ["anthropic-basic"],
        ),
        FixtureTransport(fail_second=True),
        source,
    )
    path = source / "result.json"
    value = json.loads(path.read_text())
    assertion = next(
        a for a in value["cases"][1]["attempts"][0]["assertions"] if a["id"] == "STR-START"
    )
    assertion["evidence_refs"][0][field] = {
        "sha256": "0" * 64,
        "event": 999,
        "pointer": "/nonexistent",
    }[field]
    path.write_text(json.dumps(value))
    output = tmp_path / "report"
    render_from_file(path, output)
    manifest = json.loads((output / "report-manifest.json").read_text())
    assert manifest["evidence_verification"]["status"] == "missing_or_invalid"
    assert manifest["evidence_verification"]["errors"]


def test_timeout_utf8_prefix_is_not_a_proven_encoding_defect() -> None:
    body = (ROOT / "tests/fixtures/contracts/core-1.0.0/stream-valid.sse").read_bytes()
    decoder = SSEDecoder(262144, 10000)
    frames = decoder.feed(body + b": \xe4", 0)
    tail = decoder.finish(complete=False)
    validator = StreamValidator(list_cases()[1].contract)
    for frame in frames:
        validator.consume(frame)
    result = validator.finish("message_stop", "timeout", tail)
    assert not any(a.status.value == "FAIL" for a in result.assertions)
    for suffix, complete, errors in [
        (b": \xe4\xb8\xad\n\n", True, 0),
        (b": \xe4", True, 1),
        (b": \xff", False, 1),
    ]:
        control = SSEDecoder(262144, 10000)
        control.feed(body + suffix, 0)
        assert control.finish(complete=complete).encoding_errors == errors


def test_installed_layout_never_borrows_parent_repository_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import anthropic_readiness.runner as runner

    binary = tmp_path / "bin"
    binary.mkdir()
    fake_git = binary / "git"
    fake_git.write_text(
        '#!/bin/sh\ncase "$*" in\n *rev-parse*) echo aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa;;\n *status*) echo "?? unrelated";;\nesac\n'
    )
    fake_git.chmod(0o700)
    monkeypatch.setenv("PATH", str(binary) + os.pathsep + os.environ["PATH"])
    monkeypatch.setattr(
        runner,
        "__file__",
        str(
            tmp_path / "unrelated/.venv/lib/python3.12/site-packages/anthropic_readiness/runner.py"
        ),
    )
    metadata = runner._tool_metadata()
    assert metadata["commit"] is None
    assert metadata["dirty"] is None


@pytest.mark.parametrize("mutation", ["version", "empty"])
def test_report_profile_identity_cannot_disagree_with_plan(mutation: str) -> None:
    value = json.loads((ROOT / "tests/fixtures/results/mixed.json").read_text())
    if mutation == "version":
        value["profiles"][0]["version"] = 99
    else:
        value["plan"]["profiles"] = []
        value["profiles"] = []
    with pytest.raises(ValueError, match="profile"):
        result_from_document(value)


def test_legacy_partial_capture_rechecks_utf8_suffix(tmp_path: Path) -> None:
    target = load_target(ROOT / "examples/target.yaml")
    case = list_cases()[1]
    body = (ROOT / "tests/fixtures/contracts/core-1.0.0/stream-valid.sse").read_bytes() + b": \xe4"
    old = replace(capture(body, True), request=build_request(case, target), capture_end="timeout")
    assert old.tail.encoding_errors == 1
    source = tmp_path / "source"
    create_run_directory(source)
    refs = persist_capture(source, case.id, "legacy", sanitize_capture(old, []))
    path = source / refs.capture_path
    metadata = json.loads(path.read_text())
    metadata["schema_version"] = "1.0"
    metadata.pop("structural_sha256")
    path.write_text(json.dumps(metadata))
    result = replay_run(
        target,
        resolve_contract(target.contract_id, target.contract_revision),
        case.id,
        path,
        tmp_path / "replay",
    )
    assert result_exit_code(result) == 3
    assert result.cases[0]["status"] == "INDETERMINATE"
