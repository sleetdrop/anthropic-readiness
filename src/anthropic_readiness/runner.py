"""Explicit bounded plans, truthful case accounting and offline replay."""

from __future__ import annotations

import os
import platform
import signal
import subprocess
import threading
import time
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from types import FrameType
from typing import Literal

from anthropic_readiness import __version__
from anthropic_readiness.cases import CaseDefinition, build_request, list_cases, select_cases
from anthropic_readiness.config import TargetConfig, fingerprint
from anthropic_readiness.contracts import ContractBundle, validate_target_contract
from anthropic_readiness.evidence import (
    CaptureRefs,
    SanitizedCapture,
    atomic_write,
    create_run_directory,
    json_bytes,
    load_capture,
    persist_capture,
    sanitize_capture,
    sanitize_json,
    verify_evidence,
)
from anthropic_readiness.models import (
    AssertionResult,
    Capture,
    EvidenceRef,
    JsonObject,
    JsonValue,
    RunResult,
    Status,
    ValidationResult,
    aggregate_required,
    object_value,
    readiness,
    strict_json,
)
from anthropic_readiness.schema import (
    load_schema,
    result_from_document,
    validate_document,
    validate_result_semantics,
)
from anthropic_readiness.validation.messages import validate_message
from anthropic_readiness.validation.stream import StreamValidator


def _assertion_plan(case: CaseDefinition, target: TargetConfig) -> list[JsonValue]:
    ids = [
        "HTTP-STATUS",
        "HTTP-CONTENT-TYPE",
        "CAPTURE-COMPLETE",
        "MSG-CORE",
        "MSG-MODEL",
        "MSG-STOP",
        "MSG-STOP-SEQUENCE",
        "TASK-COMPLETE",
    ]
    ids.extend(
        [
            "SSE-FRAMING",
            "STR-JSON",
            "STR-TYPE",
            "STR-LIFECYCLE",
            "STR-START",
            "STR-DELTA",
            "STR-STOP",
        ]
        if case.streaming
        else ["MSG-JSON"]
    )
    if case.behavior == "tool":
        ids.extend(["MSG-TOOL-CALLS", "MSG-TOOL-ID", "MSG-TOOL-NAME", "MSG-TOOL-INPUT"])
    return [
        {
            "id": key,
            "version": 1,
            "required": key != "MSG-MODEL" or target.response_model_policy != "structure_only",
        }
        for key in ids
    ]


@dataclass(frozen=True)
class RunPlan:
    target: TargetConfig
    bundle: ContractBundle
    profiles: tuple[str, ...]
    cases: tuple[CaseDefinition, ...]
    mode: Literal["live", "replay"] = "live"

    def to_json(self, actual_requests: int = 0) -> JsonObject:
        return {
            "cases": [
                {
                    "id": c.id,
                    "version": c.version,
                    "required": True,
                    "assertions": _assertion_plan(c, self.target),
                }
                for c in self.cases
            ],
            "profiles": [
                {
                    "id": p,
                    "version": 1,
                    "cases": [c.id for c in self.cases if self.mode == "replay" or p in c.profiles],
                }
                for p in self.profiles
            ],
            "actual_requests": actual_requests,
            "planned_requests": len(self.cases) if self.mode == "live" else 0,
            "limits": self.target.limits.to_json(),
            "repeat": 1,
            "retry": 0,
            "config_fingerprint": self.target.fingerprint(self.bundle.content_sha256),
            "test_fingerprint": fingerprint(
                [
                    {"id": c.id, "version": c.version, "body": build_request(c, self.target).body}
                    for c in self.cases
                ]
            ),
        }


def plan_run(target: TargetConfig, bundle: ContractBundle, profiles: Sequence[str]) -> RunPlan:
    validate_target_contract(target, bundle)
    cases = select_cases(profiles)
    if len(cases) > target.limits.max_requests:
        raise ValueError("request_budget_insufficient")
    return RunPlan(target, bundle, tuple(dict.fromkeys(profiles)), cases)


def _utc() -> str:
    return datetime.now(UTC).isoformat()


def _tool_metadata() -> JsonObject:
    commit: str | None = None
    dirty: bool | None = None
    try:
        root = Path(__file__).resolve().parents[2]
        revision = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
        if revision.returncode == 0:
            commit = revision.stdout.strip()
            changed = subprocess.run(
                ["git", "-C", str(root), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=False,
                timeout=2,
            )
            dirty = bool(changed.stdout) if changed.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return {
        "version": __version__,
        "commit": commit,
        "dirty": dirty,
        "python": platform.python_version(),
        "validator_version": "1.0.0",
        "dependencies": {name: version(name) for name in ("httpx", "jsonschema", "PyYAML")},
    }


def _dimensions(assertions: Sequence[AssertionResult]) -> JsonObject:
    result: JsonObject = {}
    for dimension in ("protocol", "behavior", "client", "environment"):
        statuses = [a.status for a in assertions if a.required and a.category == dimension]
        result[dimension] = aggregate_required(statuses).value if statuses else "not_evaluated"
    return result


def _validate(capture: Capture, case: CaseDefinition, plan: RunPlan) -> ValidationResult:
    checks: list[AssertionResult] = []
    if capture.capture_end == "connection_error":
        return ValidationResult(
            (AssertionResult("HTTP-CONNECTION", "environment", Status.BLOCKED, "connection_error"),)
        )
    if capture.status_code is None:
        return ValidationResult(
            (
                AssertionResult(
                    "CAPTURE-COMPLETE", "environment", Status.INDETERMINATE, capture.capture_end
                ),
            )
        )
    http_ok = 200 <= capture.status_code < 300
    checks.append(
        AssertionResult(
            "HTTP-STATUS",
            "protocol",
            Status.PASS if http_ok else Status.FAIL,
            "http_success" if http_ok else "http_error",
            actual=str(capture.status_code),
        )
    )
    if not http_ok:
        checks.append(
            AssertionResult(
                "CAPTURE-COMPLETE",
                "environment",
                Status.PASS if capture.capture_end == "eof" else Status.INDETERMINATE,
                capture.capture_end,
            )
        )
        return ValidationResult(tuple(checks), {"failure_domain": "http_error"})
    expected_type = "text/event-stream" if case.streaming else "application/json"
    content_type = dict(capture.headers).get("content-type", "").split(";", 1)[0].strip().lower()
    checks.append(
        AssertionResult(
            "HTTP-CONTENT-TYPE",
            "protocol",
            Status.PASS if content_type == expected_type else Status.FAIL,
            "satisfied" if content_type == expected_type else "unexpected_content_type",
            expected=expected_type,
            actual=content_type,
        )
    )
    contract = case.contract_for(plan.target, plan.bundle.spec)
    if case.streaming:
        validator = StreamValidator(contract)
        for frame in capture.frames:
            validator.consume(frame)
        validated = validator.finish(capture.protocol_end, capture.capture_end, capture.tail)
    else:
        complete = capture.capture_end == "eof"
        checks.append(
            AssertionResult(
                "CAPTURE-COMPLETE",
                "environment",
                Status.PASS if complete else Status.INDETERMINATE,
                capture.capture_end,
            )
        )
        try:
            value = strict_json(capture.body.decode())
        except (ValueError, UnicodeError):
            checks.append(
                AssertionResult(
                    "MSG-JSON",
                    "protocol",
                    Status.FAIL if complete else Status.INDETERMINATE,
                    "invalid_json" if complete else "partial_response",
                )
            )
            return ValidationResult(tuple(checks))
        checks.append(AssertionResult("MSG-JSON", "protocol", Status.PASS, "satisfied"))
        validated = validate_message(value, contract)
    return ValidationResult((*checks, *validated.assertions), validated.observations)


def _bind(assertions: Sequence[AssertionResult], refs: CaptureRefs) -> tuple[AssertionResult, ...]:
    bound: list[AssertionResult] = []
    for item in assertions:
        suffix = (
            "events.jsonl"
            if item.event is not None
            else "response.json"
            if item.id.startswith(("HTTP-", "CAPTURE-"))
            else "body.bin"
        )
        reference = next(r for r in refs.refs if r.path.endswith("/" + suffix))
        bound.append(
            replace(
                item, evidence_refs=(replace(reference, event=item.event, pointer=item.pointer),)
            )
        )
    return tuple(bound)


@dataclass
class _Interruption:
    signum: int | None = None


@contextmanager
def _signals(transport: object, state: _Interruption) -> Iterator[None]:
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}

    def handler(signum: int, frame: FrameType | None) -> None:
        state.signum = signum
        cancel = getattr(transport, "cancel", None)
        if callable(cancel):
            cancel()

    try:
        for sig in previous:
            signal.signal(sig, handler)
        yield
    finally:
        for sig, old_handler in previous.items():
            signal.signal(sig, old_handler)


def _precondition(case: CaseDefinition, status: Status, reason: str) -> JsonObject:
    assertion = AssertionResult("CASE-PRECONDITION", "environment", status, reason)
    return {
        "id": case.id,
        "version": case.version,
        "required": True,
        "status": status.value,
        "preconditions": [assertion.to_json()],
        "attempts": [],
        "dimensions": _dimensions([assertion]),
    }


def execute_run(
    plan: RunPlan,
    transport: object,
    output_dir: Path,
    *,
    environment: Mapping[str, str] | None = None,
    clock: Callable[[], float] = time.monotonic,
    replay: SanitizedCapture | None = None,
) -> RunResult:
    from anthropic_readiness.transport import HttpTransport

    if not isinstance(transport, HttpTransport):
        raise TypeError("invalid_transport")
    if (plan.mode == "replay") != (replay is not None):
        raise ValueError("run_mode_capture_mismatch")
    create_run_directory(output_dir)
    started = _utc()
    deadline = clock() + plan.target.limits.run_timeout_s
    state = _Interruption()
    secret: str | None = None
    credential_error: str | None = None
    if plan.mode == "live":
        try:
            secret = plan.target.credential(os.environ if environment is None else environment)
        except ValueError as exc:
            credential_error = str(exc)
    secrets = [secret] if secret else []
    cases: list[JsonObject] = []
    refs: list[EvidenceRef] = []
    assertion_refs: list[EvidenceRef] = []
    requests = 0
    internal_error: str | None = None
    with _signals(transport, state):
        for case in plan.cases:
            if state.signum is not None or internal_error is not None:
                cases.append(
                    _precondition(
                        case,
                        Status.INDETERMINATE,
                        "cancelled" if state.signum else "internal_error",
                    )
                )
                continue
            if clock() >= deadline:
                cases.append(_precondition(case, Status.INDETERMINATE, "run_deadline_exceeded"))
                continue
            if not case.available(plan.target):
                cases.append(_precondition(case, Status.SKIP, "capability_not_declared"))
                continue
            if credential_error:
                cases.append(_precondition(case, Status.BLOCKED, credential_error))
                continue
            attempt_id = str(uuid.uuid4())
            actual_requests = 0
            try:
                if replay is not None:
                    capture = replay.capture
                    sanitized = replay
                else:
                    request = build_request(case, plan.target)
                    if secret:
                        request = replace(
                            request, headers=(*request.headers, ("x-api-key", secret))
                        )
                    requests += 1
                    actual_requests = 1
                    capture = transport.send(request, plan.target.limits, deadline)
                    sanitized = sanitize_capture(capture, secrets)
                validated = _validate(capture, case, plan)
                if replay is not None and replay.transformed:
                    validated = replace(
                        validated,
                        assertions=tuple(
                            replace(
                                a, status=Status.INDETERMINATE, reason_code="transformed_capture"
                            )
                            if a.id not in {"HTTP-STATUS", "CAPTURE-COMPLETE"}
                            else a
                            for a in validated.assertions
                        ),
                    )
                persisted = persist_capture(output_dir, case.id, attempt_id, sanitized)
                refs.extend(persisted.refs)
                assertions = _bind(validated.assertions, persisted)
                assertion_refs.extend(
                    ref for assertion in assertions for ref in assertion.evidence_refs
                )
                attempt_status = aggregate_required([a.status for a in assertions if a.required])
                observations = object_value(sanitize_json(validated.observations, secrets))
                attempt: JsonObject = {
                    "id": attempt_id,
                    "index": 1,
                    "status": attempt_status.value,
                    "actual_requests": actual_requests,
                    "termination": {
                        "protocol_end": capture.protocol_end,
                        "capture_end": capture.capture_end,
                        "error": sanitized.capture.error,
                    },
                    "duration_ms": capture.duration_ms,
                    "observations": observations,
                    "assertions": [a.to_json() for a in assertions],
                }
                cases.append(
                    {
                        "id": case.id,
                        "version": case.version,
                        "required": True,
                        "status": attempt_status.value,
                        "preconditions": [],
                        "attempts": [attempt],
                        "dimensions": _dimensions(assertions),
                    }
                )
                if capture.capture_end == "cancelled" and state.signum is None:
                    state.signum = signal.SIGINT
            except (KeyboardInterrupt, Exception) as exc:
                if isinstance(exc, OSError):
                    raise
                if isinstance(exc, KeyboardInterrupt):
                    state.signum = signal.SIGINT
                else:
                    internal_error = str(sanitize_json(f"{type(exc).__name__}:{exc}", secrets))
                assertion = AssertionResult(
                    "EXECUTION-COMPLETE",
                    "environment",
                    Status.INDETERMINATE,
                    "cancelled" if state.signum else "internal_error",
                )
                attempt = {
                    "id": attempt_id,
                    "index": 1,
                    "status": Status.INDETERMINATE.value,
                    "actual_requests": actual_requests,
                    "termination": {
                        "capture_end": "cancelled" if state.signum else "internal_error"
                    },
                    "duration_ms": 0,
                    "observations": {},
                    "assertions": [assertion.to_json()],
                }
                cases.append(
                    {
                        "id": case.id,
                        "version": case.version,
                        "required": True,
                        "status": Status.INDETERMINATE.value,
                        "preconditions": [],
                        "attempts": [attempt],
                        "dimensions": _dimensions([assertion]),
                    }
                )
    profiles: list[JsonObject] = []
    for profile in plan.profiles:
        members = [
            c
            for c, definition in zip(cases, plan.cases, strict=True)
            if plan.mode == "replay" or profile in definition.profiles
        ]
        statuses = [Status(str(c["status"])) for c in members]
        profiles.append(
            {
                "id": profile,
                "version": 1,
                "cases": [c["id"] for c in members],
                "readiness": readiness(aggregate_required(statuses)),
            }
        )
    result = RunResult(
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        plan.mode,
        started,
        _utc(),
        _tool_metadata(),
        {
            "os": platform.system(),
            "architecture": platform.machine(),
            "interruption": state.signum,
            "internal_error": internal_error,
        },
        {**plan.bundle.manifest, "version_semantics": "unverified"},
        object_value(sanitize_json(plan.target.to_json(), secrets)),
        plan.to_json(requests),
        tuple(profiles),
        tuple(cases),
        tuple(refs),
        {
            "version": "1.0",
            "data_kind": "synthetic_or_user_capture" if plan.mode == "replay" else "live_endpoint",
            "method": "Deterministic black-box assertions; no model judge.",
            "request_count_semantics": "Initiated transport calls; no retries.",
            "client": "not_evaluated",
        },
        (
            "Only the declared core subset is assessed.",
            "Claude Code workflows are not evaluated.",
            "API date does not freeze model behavior.",
            *(
                ("Single capture only; original profiles are not evaluated.",)
                if plan.mode == "replay"
                else ()
            ),
        ),
    )
    document = object_value(sanitize_json(result.to_json(), secrets))
    validate_document(document, load_schema("result"))
    if errors := validate_result_semantics(document):
        raise RuntimeError("result_semantics:" + ";".join(errors))
    all_refs = [*refs, *assertion_refs]
    for case_record in cases:
        attempts = case_record.get("attempts")
        if isinstance(attempts, list):
            for attempt_record in attempts:
                if isinstance(attempt_record, dict):
                    assertions_json = attempt_record.get("assertions")
                    if isinstance(assertions_json, list):
                        for assertion_json in assertions_json:
                            if (
                                isinstance(assertion_json, dict)
                                and assertion_json.get("status") == "FAIL"
                                and not assertion_json.get("evidence_refs")
                            ):
                                raise RuntimeError("failure_without_evidence")
    if errors := verify_evidence(output_dir, all_refs):
        raise RuntimeError("evidence_integrity:" + ";".join(errors))
    atomic_write(output_dir / "result.json", json_bytes(document))
    return result_from_document(document)


def replay_run(
    target: TargetConfig, bundle: ContractBundle, case_id: str, source: Path, output_dir: Path
) -> RunResult:
    from anthropic_readiness.transport import HttpTransport

    validate_target_contract(target, bundle)
    chosen = next((c for c in list_cases() if c.id == case_id), None)
    if chosen is None:
        raise ValueError("unknown_case")
    captured = load_capture(source)
    if captured.capture.request.streaming != chosen.streaming:
        raise ValueError("capture_case_mismatch")
    expected = build_request(chosen, target)
    captured_headers = dict(captured.capture.request.headers)
    expected_headers = dict(expected.headers)
    if any(
        captured_headers.get(key) != expected_headers.get(key)
        for key in ("anthropic-version", "anthropic-beta")
    ):
        raise ValueError("capture_contract_mismatch")
    if not captured.transformed and captured.capture.request.body != expected.body:
        raise ValueError("capture_request_mismatch")
    return execute_run(
        RunPlan(target, bundle, ("capture-replay",), (chosen,), "replay"),
        HttpTransport(),
        output_dir,
        replay=captured,
    )


def result_exit_code(result: RunResult) -> int:
    interruption = result.execution_environment.get("interruption")
    if isinstance(interruption, int) and not isinstance(interruption, bool):
        return 128 + interruption
    if result.execution_environment.get("internal_error") is not None:
        return 4
    statuses = [Status(str(c["status"])) for c in result.cases if c.get("required") is True]
    status = aggregate_required(statuses)
    return 0 if status == Status.PASS else 1 if status == Status.FAIL else 3
