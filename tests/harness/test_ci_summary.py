"""Exercise CI presentation with disposable, incomplete and contradictory evidence."""

import json
import subprocess
import sys
from pathlib import Path

from scripts.ci_summary import render_summary


def record(root: Path, relative: str, value: object) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


def test_missing_evidence_is_explicit() -> None:
    text = render_summary(Path("/nonexistent-ci-evidence"))
    assert "No check or image result records were produced" in text
    assert "passed" not in text


def test_failed_record_and_actual_testcase_counts_survive(tmp_path: Path) -> None:
    path = record(
        tmp_path,
        "checks/one/check-result.json",
        {
            "scope": "full",
            "status": "failed",
            "checks": [{"check_id": "unit", "status": "failed", "duration_s": 2.5}],
        },
    )
    path.with_name("unit.xml").write_text(
        '<testsuites><testsuite tests="999" failures="0">'
        "<testcase/><testcase><failure/></testcase><testcase><skipped/></testcase>"
        "</testsuite></testsuites>"
    )
    text = render_summary(tmp_path)
    assert "failed" in text
    assert "2.50" in text
    assert "| 3 | 1 | 0 | 1 |" in text
    assert "999" not in text


def test_multiple_records_and_partial_image_evidence_remain_separate(tmp_path: Path) -> None:
    record(tmp_path, "checks/a/check-result.json", {"status": "passed", "checks": []})
    record(
        tmp_path,
        "images/b/image-result.json",
        {
            "status": "blocked",
            "scope": "full",
            "missing_checks": ["dev-offline-full"],
            "checks": [],
        },
    )
    text = render_summary(tmp_path)
    assert "checks/a/check-result.json" in text
    assert "images/b/image-result.json" in text
    assert "blocked" in text
    assert "dev-offline-full" in text
    assert "No completed checks recorded" in text


def test_malformed_evidence_does_not_hide_other_records(tmp_path: Path) -> None:
    path = record(tmp_path, "checks/bad/check-result.json", [])
    path.write_text("{")
    record(tmp_path, "checks/good/check-result.json", {"status": "blocked", "checks": []})
    text = render_summary(tmp_path)
    assert "Unreadable result record" in text
    assert "checks/good/check-result.json" in text
    assert "blocked" in text


def test_cli_escapes_content_and_omits_unselected_configuration(tmp_path: Path) -> None:
    record(
        tmp_path,
        "checks/example/check-result.json",
        {"scope": "<img>|`\nheader", "status": "failed", "checks": [], "token": "synthetic-secret"},
    )
    result = subprocess.run(
        [sys.executable, "scripts/ci_summary.py", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "&lt;img&gt;&#124;&#96; header" in result.stdout
    assert "synthetic-secret" not in result.stdout
    assert "<img>" not in result.stdout


def test_markdown_links_cannot_be_injected_by_record_fields(tmp_path: Path) -> None:
    record(
        tmp_path,
        "checks/example/check-result.json",
        {"scope": "[click](https://example.invalid)*bold*", "status": "failed", "checks": []},
    )
    text = render_summary(tmp_path)
    assert "[click](https://example.invalid)" not in text
    assert "&#91;click&#93;&#40;https://example.invalid&#41;&#42;bold&#42;" in text


def test_out_of_range_duration_does_not_hide_later_failed_record(tmp_path: Path) -> None:
    record(
        tmp_path,
        "checks/a/check-result.json",
        {"status": "blocked", "checks": [{"check_id": "huge", "duration_s": 10**400}]},
    )
    record(tmp_path, "checks/b/check-result.json", {"status": "failed", "checks": []})
    text = render_summary(tmp_path)
    assert "| huge | unknown | not recorded |" in text
    assert "checks/b/check-result.json" in text
    assert "failed" in text


def test_nested_configuration_in_metadata_is_not_rendered(tmp_path: Path) -> None:
    nested = {"token": "synthetic-nested-secret"}
    record(
        tmp_path,
        "checks/a/check-result.json",
        {"status": nested, "scope": nested, "source_fingerprint": nested, "checks": []},
    )
    text = render_summary(tmp_path)
    assert "synthetic-nested-secret" not in text
    assert "unavailable" in text
