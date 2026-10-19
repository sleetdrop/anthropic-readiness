"""Explicit command-line entry point; importing it performs no I/O."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from anthropic_readiness.application import prepare_assessment, run_assessment
from anthropic_readiness.config import load_target
from anthropic_readiness.contracts import SUPPORTED, resolve_contract, validate_target_contract
from anthropic_readiness.credentials import EnvironmentCredentials
from anthropic_readiness.diagnostics.cli import add_diagnostic_commands, dispatch_diagnostics
from anthropic_readiness.operations.observer import DiskExecutionObserver
from anthropic_readiness.reporting import render_from_file, write_reports
from anthropic_readiness.runner import replay_run, result_exit_code


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Anthropic Messages black-box readiness checks")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="Validate a target and pinned contract offline")
    validate.add_argument("--target", type=Path, required=True)
    contracts = commands.add_parser("contracts", help="Inspect shipped protocol contracts")
    contract_commands = contracts.add_subparsers(dest="contract_command", required=True)
    contract_commands.add_parser("list")
    show = contract_commands.add_parser("show")
    show.add_argument("id")
    show.add_argument("--revision", required=True)
    run = commands.add_parser("run", help="Plan or explicitly run live smoke requests")
    run.add_argument("--target", type=Path, required=True)
    run.add_argument("--profile", action="append")
    run.add_argument("--out", type=Path, required=True)
    opt_in = run.add_mutually_exclusive_group()
    opt_in.add_argument("--allow-live", action="store_true")
    opt_in.add_argument("--dry-run", action="store_true")
    replay = commands.add_parser("replay", help="Assess one captured response offline")
    replay.add_argument("--capture", type=Path, required=True)
    replay.add_argument("--target", type=Path, required=True)
    replay.add_argument("--case", required=True)
    replay.add_argument("--out", type=Path, required=True)
    report = commands.add_parser("report", help="Render an existing result offline")
    report.add_argument("--input", type=Path, required=True)
    report.add_argument("--out", type=Path, required=True)
    add_diagnostic_commands(
        commands.add_parser("diagnostics", help="Portable diagnosis and repair verification")
    )
    serve_parser = commands.add_parser("serve", help="Run the optional local Web console")
    serve_parser.add_argument("--data-dir", type=Path, required=True)
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.add_argument("--credential-env", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == "diagnostics":
            return dispatch_diagnostics(args)
        if args.command == "serve":
            try:
                from anthropic_readiness.web.serve import serve
                from anthropic_readiness.web.settings import WebSettings
            except ModuleNotFoundError:
                print(
                    'Web support requires: pip install "anthropic-readiness[web]"', file=sys.stderr
                )
                return 2
            return serve(
                args.data_dir,
                WebSettings(
                    host=args.host,
                    port=args.port,
                    credential_env_allowlist=tuple(dict.fromkeys(args.credential_env)),
                ),
            )
        if args.command == "report":
            render_from_file(args.input, args.out)
            return 0
        if args.command == "contracts":
            if args.contract_command == "list":
                print(
                    json.dumps([{"id": name, "revision": revision} for name, revision in SUPPORTED])
                )
            else:
                print(
                    json.dumps(
                        resolve_contract(args.id, args.revision).manifest,
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            return 0
        if args.command == "run" and not args.allow_live and not args.dry_run:
            raise ValueError("live_opt_in_required: use --allow-live or --dry-run")
        target = load_target(args.target)
        bundle = resolve_contract(target.contract_id, target.contract_revision)
        validate_target_contract(target, bundle)
        if args.command == "validate":
            print(
                json.dumps(
                    {
                        "status": "valid",
                        "config_fingerprint": target.fingerprint(bundle.content_sha256),
                    }
                )
            )
            return 0
        if args.command == "run":
            plan, context = prepare_assessment(
                target.to_json(), args.profile or ["anthropic-basic"]
            )
            if args.dry_run:
                print(json.dumps(plan.to_json(), ensure_ascii=False, indent=2))
                return 0
            print(f"Planned requests: {len(plan.cases)}; no retries.", file=sys.stderr)
            result = run_assessment(
                plan,
                args.out,
                credentials=EnvironmentCredentials(target),
                assessment_context=context.document,
            )
        else:
            result = replay_run(
                target,
                bundle,
                args.case,
                args.capture,
                args.out,
                observer=DiskExecutionObserver(args.out / "operations", args.out),
            )
        write_reports(result, args.out)
        print(
            json.dumps(
                {
                    "run_id": result.run_id,
                    "profiles": list(result.profiles),
                    "actual_requests": result.plan["actual_requests"],
                }
            )
        )
        return result_exit_code(result)
    except (ValueError, OSError) as exc:
        print(
            f"Usage/config/output error: {type(exc).__name__}: {str(exc).split(':', 1)[0]}",
            file=sys.stderr,
        )
        return 2
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        # Internal exception text may contain private adapter data; disclose only its type.
        print(f"Internal error: {type(exc).__name__}", file=sys.stderr)
        return 4
