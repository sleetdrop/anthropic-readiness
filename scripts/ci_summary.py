"""Present recorded CI evidence without replacing required check verdicts."""

from __future__ import annotations

import argparse
import html
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path


def _cell(value: object) -> str:
    if not isinstance(value, (str, Path, bool)):
        return "unavailable"
    text = str(value).replace("\n", " ").replace("\r", " ")
    return html.escape(text).translate({ord(char): f"&#{ord(char)};" for char in "|`[]()*_\\"})


def _duration(value: object) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return "not recorded"
    try:
        number = float(value)
    except OverflowError:
        return "not recorded"
    if math.isfinite(number) and number >= 0:
        return f"{number:.2f}"
    return "not recorded"


def _junit_summary(directory: Path) -> list[str]:
    rows: list[str] = []
    for path in sorted(directory.rglob("*.xml")):
        if path.name == "coverage.xml":
            continue
        label = _cell(path.relative_to(directory))
        try:
            tree = ET.parse(path)
        except (OSError, ET.ParseError):
            rows.append(f"| {label} | unreadable | unknown | unknown | unknown |")
            continue
        if tree.getroot().tag not in {"testsuites", "testsuite"}:
            continue
        cases = list(tree.iter("testcase"))
        failed = sum(case.find("failure") is not None for case in cases)
        errors = sum(case.find("error") is not None for case in cases)
        skipped = sum(case.find("skipped") is not None for case in cases)
        rows.append(f"| {label} | {len(cases)} | {failed} | {errors} | {skipped} |")
    return rows


def render_summary(root: Path) -> str:
    lines = [
        "## CI evidence",
        "",
        "Recorded observations only; required job exits remain the gate. "
        "A missing report, a smoke run or zero testcases does not establish full acceptance.",
        "",
        "Download this job's evidence from the workflow run's **Artifacts** section. "
        "Record paths below are relative to the artifacts directory.",
    ]
    paths = sorted(
        [
            *(root / "checks").rglob("check-result.json"),
            *(root / "images").rglob("image-result.json"),
        ]
    )
    if not paths:
        lines.extend(
            ["", "**No check or image result records were produced. Evidence unavailable.**"]
        )
    for path in paths:
        lines.extend(["", "### " + _cell(path.relative_to(root)), ""])
        try:
            value: object = json.loads(path.read_text())
            if not isinstance(value, dict) or not isinstance(value.get("checks"), list):
                raise ValueError("invalid_result")
            checks = value["checks"]
            if any(not isinstance(check, dict) for check in checks):
                raise ValueError("invalid_checks")
        except (OSError, ValueError):
            lines.append("**Unreadable result record. Evidence unavailable.**")
            continue
        lines.append(
            f"Reported status: **{_cell(value.get('status', 'unknown'))}**; "
            f"scope: {_cell(value.get('scope', 'unknown'))}; recorded checks: {len(checks)}."
        )
        for field in ("source_fingerprint", "image_context_fingerprint", "source_unchanged"):
            if field in value:
                lines.extend(["", f"{field}: {_cell(value[field])}"])
        missing = value.get("missing_checks")
        if missing:
            text = (
                ", ".join(_cell(item) for item in missing)
                if isinstance(missing, list)
                else "unavailable"
            )
            lines.extend(["", "Missing checks: " + text])
        if checks:
            lines.extend(["", "| Check | Recorded status | Duration (s) |", "| --- | --- | ---: |"])
            for check in checks:
                lines.append(
                    f"| {_cell(check.get('check_id', check.get('id', 'unknown')))} "
                    f"| {_cell(check.get('status', 'unknown'))} "
                    f"| {_duration(check.get('duration_s'))} |"
                )
        else:
            lines.extend(["", "No completed checks recorded."])
        junit = _junit_summary(path.parent)
        if junit:
            lines.extend(
                [
                    "",
                    "Actual testcase nodes (reports are separate; counts are not deduplicated):",
                    "",
                    "| JUnit report | Cases | Failures | Errors | Skipped |",
                    "| --- | ---: | ---: | ---: | ---: |",
                    *junit,
                ]
            )
        elif path.name == "check-result.json":
            lines.extend(["", "No JUnit reports available; testcase counts are unknown."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    print(render_summary(args.root), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
