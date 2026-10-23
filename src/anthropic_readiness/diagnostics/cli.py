"""Standalone diagnostic commands; no optional Web dependencies or implicit live use."""

import argparse
import json
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from anthropic_readiness.application import run_assessment
from anthropic_readiness.cli_presentation import (
    add_presentation_options,
    load_comparison,
    presentation_options,
)
from anthropic_readiness.config import load_target
from anthropic_readiness.credentials import EnvironmentCredentials
from anthropic_readiness.diagnostics.contracts import validate_projection
from anthropic_readiness.diagnostics.service import DiagnosticService
from anthropic_readiness.evidence import atomic_write, create_run_directory, json_bytes
from anthropic_readiness.models import JsonObject
from anthropic_readiness.reporting import write_reports
from anthropic_readiness.runner import result_exit_code


def add_diagnostic_commands(parser: argparse.ArgumentParser) -> None:
    commands = parser.add_subparsers(dest="diagnostic_command", required=True)
    importing = commands.add_parser("import", help="Check and retain a portable ZIP offline")
    importing.add_argument("--package", type=Path, required=True)
    importing.add_argument("--data-dir", type=Path, required=True)
    inspect = commands.add_parser("inspect", help="Revalidate an imported baseline offline")
    inspect.add_argument("--baseline", required=True)
    inspect.add_argument("--data-dir", type=Path, required=True)
    export = commands.add_parser(
        "export", help="Export a source directory or canonical result.json"
    )
    export.add_argument("--input", type=Path, required=True)
    export.add_argument("--out", type=Path, required=True)
    export.add_argument("--include-evidence", action="store_true")
    export.add_argument(
        "--comparison", type=Path, help="Attach a checked comparison for this source"
    )
    retest = commands.add_parser(
        "retest", help="Preview or explicitly execute the original full scope"
    )
    retest.add_argument("--baseline", required=True)
    retest.add_argument("--data-dir", type=Path, required=True)
    retest.add_argument("--target", type=Path, required=True)
    retest.add_argument("--out", type=Path, required=True)
    opt_in = retest.add_mutually_exclusive_group()
    opt_in.add_argument("--allow-live", action="store_true")
    opt_in.add_argument("--dry-run", action="store_true")
    for command in (export, retest):
        add_presentation_options(command)
    compare = commands.add_parser(
        "compare", help="Compare checked observations offline; zero is not a pass"
    )
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--data-dir", type=Path, required=True)
    compare.add_argument("--input", type=Path, required=True)
    compare.add_argument("--out", type=Path, required=True)


def _source(path: Path) -> Path:
    if path.is_dir():
        return path
    if path.is_file() and path.name == "result.json":
        return path.parent
    raise ValueError("diagnostic_input_must_be_result_or_directory")


def _print(value: JsonObject) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))


def dispatch_diagnostics(args: argparse.Namespace) -> int:
    command = args.diagnostic_command
    if command == "retest" and not args.allow_live and not args.dry_run:
        raise ValueError("live_opt_in_required")
    if command == "export":
        print("Archive retains original target context; review before sharing.", file=sys.stderr)
        with TemporaryDirectory(prefix="anthropic-readiness-export-") as temporary:
            value = DiagnosticService(Path(temporary)).export(
                _source(args.input),
                args.out,
                include_evidence=args.include_evidence,
                presentation=presentation_options(args),
                comparison=load_comparison(args.comparison),
            )
        _print(value)
        return 0
    service = DiagnosticService(args.data_dir)
    if command == "import":
        owner, now = secrets.token_hex(32), datetime.now(UTC)
        preview = service.preview(args.package, owner, now=now)
        record = service.commit(str(preview["preview_id"]), owner, now=datetime.now(UTC))
        _print(record.document)
        return 0
    if command == "inspect":
        _print(service.get(args.baseline).document)
        return 0
    if command == "compare":
        value = service.compare(args.baseline, _source(args.input)).document
        atomic_write(args.out, json_bytes(value))
        _print(value)
        return 0
    if command != "retest":
        raise ValueError("unknown_diagnostic_command")
    target = load_target(args.target)
    try:
        plan, context, differences = service.prepare_retest(args.baseline, target.to_json())
    except ValueError as exc:
        if str(exc) == "diagnostic_retest_unavailable":
            print(
                "This baseline cannot establish a controlled retest. Configure a separate current test with the run command.",
                file=sys.stderr,
            )
        raise
    if args.dry_run:
        value = {
            "schema_version": "1.0",
            "kind": "retest_preview",
            "baseline": context.document["baseline"],
            "plan": plan.to_json(),
            "conditions": differences,
        }
        validate_projection(value, "diagnostic-retest-preview")
        create_run_directory(args.out)
        atomic_write(args.out / "retest-preview.json", json_bytes(value))
        _print(value)
        return 0
    print(
        f"Planned requests: {plan.planned_requests}; no retries. Conditions are recorded in assessment-context.json.",
        file=sys.stderr,
    )
    result = run_assessment(
        plan,
        args.out,
        credentials=EnvironmentCredentials(target),
        assessment_context=context.document,
    )
    write_reports(
        result,
        args.out,
        presentation=presentation_options(args),
        comparison=service.compare(args.baseline, args.out),
    )
    _print(
        {
            "run_id": result.run_id,
            "profiles": list(result.profiles),
            "actual_requests": result.plan["actual_requests"],
        }
    )
    return result_exit_code(result)
