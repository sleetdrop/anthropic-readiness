"""W2 delivery claims require complete coverage and observed, source-bound checks."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from anthropic_readiness.models import JsonObject, object_value
from scripts import check_docs

ROOT = Path(__file__).resolve().parents[2]


def records() -> tuple[JsonObject, JsonObject]:
    acceptance: JsonObject = {
        "schema_version": "1.0",
        "stage": "W2",
        "requirements": [
            {"id": f"W2-{number:02}", "checks": ["full-source"]} for number in range(1, 18)
        ],
    }
    handoff: JsonObject = {
        "schema_version": "1.0",
        "stage": "W2",
        "status": "incomplete",
        "source": {
            "commit": "a" * 40,
            "fingerprint": "b" * 64,
            "image_context": "c" * 64,
            "reviewed_head": None,
        },
        "checks": [
            {
                "id": "full-source",
                "status": "passed",
                "identity_kind": "source",
                "source_identity": "b" * 64,
                "artifact": "artifacts/synthetic/check-result.json",
                "sha256": "d" * 64,
                "executed": True,
                "unit": "tests",
                "count": 1,
                "required_children": ["synthetic-test"],
                "children": [
                    {"id": "synthetic-test", "status": "passed", "executed": True, "count": 1}
                ],
                "reason": "Synthetic validator fixture, not observed project acceptance.",
            }
        ],
    }
    return acceptance, handoff


def validate(tmp_path: Path, acceptance: JsonObject, handoff: JsonObject) -> list[str]:
    schemas = tmp_path / "src/anthropic_readiness/resources/schemas"
    schemas.mkdir(parents=True)
    docs = tmp_path / "docs/harness"
    docs.mkdir(parents=True)
    for name, document in (("acceptance", acceptance), ("handoff", handoff)):
        filename = "diagnostic-workbench-" + name
        resource = ROOT / "src/anthropic_readiness/resources/schemas" / (filename + ".schema.json")
        assert resource.is_file(), "Packaged W2 acceptance contract is missing"
        (schemas / resource.name).write_bytes(resource.read_bytes())
        (docs / (filename + ".json")).write_text(json.dumps(document))
    return check_docs.validate_diagnostic_records(tmp_path)


def test_valid_observed_source_bound_delivery_record(tmp_path: Path) -> None:
    assert validate(tmp_path, *records()) == []


@pytest.mark.parametrize(
    "defect", ["missing_requirement", "unknown_source", "zero_tests", "unrun_child"]
)
def test_invalid_delivery_claim_is_rejected(tmp_path: Path, defect: str) -> None:
    acceptance, handoff = deepcopy(records())
    checks = handoff["checks"]
    assert isinstance(checks, list)
    check = object_value(checks[0])
    if defect == "missing_requirement":
        requirements = acceptance["requirements"]
        assert isinstance(requirements, list)
        requirements.pop()
    elif defect == "unknown_source":
        check["source_identity"] = "e" * 64
    elif defect == "zero_tests":
        check["count"] = 0
    else:
        children = check["children"]
        assert isinstance(children, list)
        child = object_value(children[0])
        child["executed"] = False
        children[0] = child
    checks[0] = check
    assert validate(tmp_path, acceptance, handoff)


def test_completion_requires_all_local_acceptance_children(tmp_path: Path) -> None:
    acceptance, handoff = records()
    handoff["status"] = "complete"
    assert validate(tmp_path, acceptance, handoff)
