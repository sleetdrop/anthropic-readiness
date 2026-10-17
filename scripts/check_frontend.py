"""Offline frontend checks with explicit prerequisites and real JUnit accounting."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from anthropic_readiness.json_validation import checked_validator
from anthropic_readiness.schema import load_schema
from scripts.check import ROOT, CheckSpec, run_checks


def checks(suite: str, out: Path) -> list[CheckSpec]:
    def command(name: str, argv: list[str], *, junit: Path | None = None) -> CheckSpec:
        return CheckSpec(
            name,
            argv,
            300,
            "junit" if junit else "command",
            junit_path=junit,
            cwd=ROOT,
            blocked_exit_codes=(2,) if name == "prerequisites" else (),
        )

    prerequisite = command("prerequisites", ["node", "tests/browser/prerequisites.js", suite])
    if suite == "browser":
        os.environ["READINESS_BROWSER_ROOT"] = str(out / "fixture")
        os.environ["PLAYWRIGHT_JUNIT_OUTPUT_FILE"] = str(out / "browser.xml")
        os.environ["READINESS_BROWSER_ARTIFACTS"] = str(out / "browser-artifacts")
        return [
            prerequisite,
            command(
                "browser",
                ["node", "node_modules/@playwright/test/cli.js", "test"],
                junit=out / "browser.xml",
            ),
            command(
                "cleanup",
                [
                    sys.executable,
                    "-m",
                    "scripts.browser_fixture",
                    "--verify-cleanup",
                    "--root",
                    str(out / "fixture"),
                ],
            ),
        ]
    return [
        prerequisite,
        command("types", ["npm", "run", "check:types"]),
        command("lint", ["npm", "run", "check:lint"]),
        command("format", ["npm", "run", "check:format"]),
        command("templates", [sys.executable, "-m", "scripts.check_templates"]),
        command(
            "unit",
            [
                "node",
                "--test",
                "--test-reporter=junit",
                f"--test-reporter-destination={out / 'unit.xml'}",
                *[str(path) for path in sorted((ROOT / "tests/frontend").glob("*.test.js"))],
            ],
            junit=out / "unit.xml",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("static", "browser"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    run_checks(
        checks(args.suite, output), output, scope="frontend-" + args.suite, stop_on_blocked=True
    )
    document = json.loads((output / "check-result.json").read_text())
    # Reuse the packaged developer-check contract rather than inventing a second status format.
    checked_validator(load_schema("check-result")).validate(document)
    return {"passed": 0, "failed": 1, "blocked": 2}[document["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
