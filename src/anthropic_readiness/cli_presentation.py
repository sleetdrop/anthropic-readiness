"""Report-only command options, independent of execution configuration."""

import argparse
from pathlib import Path

from anthropic_readiness.diagnostics.contracts import validate_diagnostic
from anthropic_readiness.diagnostics.models import Comparison
from anthropic_readiness.models import object_value, strict_json
from anthropic_readiness.presentation import LOCALES, THEMES, PresentationOptions


def add_presentation_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--language", choices=LOCALES, default="zh-CN", help="Report language")
    parser.add_argument(
        "--theme", choices=THEMES, default="system", help="Initial report appearance"
    )


def presentation_options(args: argparse.Namespace) -> PresentationOptions:
    return PresentationOptions(args.language, args.theme)


def load_comparison(path: Path | None) -> Comparison | None:
    if path is None:
        return None
    with path.open("rb") as stream:
        raw = stream.read(64 * 1024 * 1024 + 1)
    if len(raw) > 64 * 1024 * 1024:
        raise ValueError("diagnostic_document_limit")
    document = object_value(strict_json(raw.decode()))
    validate_diagnostic(document, "comparison")
    return Comparison(document)
