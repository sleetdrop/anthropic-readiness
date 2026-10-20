"""Check local links, collaboration YAML and required CI child accounting."""

from __future__ import annotations

import argparse
import re
from collections.abc import Sequence
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from anthropic_readiness.models import JsonObject, object_value, strict_json


def broken_links(root: Path, documents: Sequence[Path]) -> list[str]:
    errors: list[str] = []
    for document in documents:
        for raw in re.findall(r"\[[^\]]*\]\(([^)]+)\)", document.read_text()):
            target = raw.strip("<>").split("#", 1)[0]
            if (
                not target
                or re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target)
                or target.startswith("/")
            ):
                continue
            path = document.parent / target
            if not path.exists():
                errors.append(f"{document.relative_to(root)}:{target}")
    return errors


def validate_collaboration(root: Path) -> list[str]:
    errors: list[str] = []
    expected = [
        "README.md",
        "CONTRIBUTING.md",
        "AGENTS.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".pre-commit-config.yaml",
        ".devcontainer/devcontainer.json",
        "Dockerfile",
        "docs/architecture.md",
        "docs/development.md",
        "docs/container-usage.md",
    ]
    expected.extend(
        ".github/ISSUE_TEMPLATE/" + name + ".yml"
        for name in ("bug_report", "compatibility_report", "feature_request", "protocol_update")
    )
    expected.extend(".github/workflows/" + name + ".yml" for name in ("ci", "container-matrix"))
    for name in expected:
        if not (root / name).is_file():
            errors.append("missing_collaboration_file:" + name)
    for path in (root / ".github").rglob("*.yml"):
        try:
            value: object = yaml.safe_load(path.read_text())
            if not isinstance(value, dict):
                raise ValueError("expected_mapping")
            if path.parent.name == "ISSUE_TEMPLATE":
                if not all(key in value for key in ("name", "description", "body")):
                    raise ValueError("invalid_issue_form")
                continue
            if path.parent.name != "workflows":
                continue
            triggers = value.get("on", value.get(True))
            if not triggers or "pull_request_target" in triggers:
                raise ValueError("unsafe_or_missing_trigger")
            if value.get("permissions") != {"contents": "read"}:
                raise ValueError("workflow_permissions")
            text = path.read_text()
            if "${{ secrets." in text or re.search(r"\bdocker\s+push\b", text):
                raise ValueError("publishing_not_in_stage_a")
            jobs = value.get("jobs")
            if not isinstance(jobs, dict):
                raise ValueError("missing_jobs")
            for job in jobs.values():
                if not isinstance(job, dict):
                    raise ValueError("invalid_job")
                steps = job.get("steps", [])
                if not isinstance(steps, list):
                    raise ValueError("invalid_steps")
                for step in steps:
                    if isinstance(step, dict) and "uses" in step:
                        action = str(step["uses"])
                        if not re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", action):
                            raise ValueError("unpinned_action")
            if path.name == "ci.yml":
                required = jobs.get("ci-required")
                if not isinstance(required, dict) or "always()" not in str(required.get("if")):
                    raise ValueError("missing_required_aggregator")
                needs = required.get("needs")
                if (
                    not isinstance(needs, list)
                    or not needs
                    or set(needs) != set(jobs) - {"ci-required"}
                ):
                    raise ValueError("incomplete_required_jobs")
                if "scripts/ci_required.py" not in str(required.get("steps")):
                    raise ValueError("missing_required_status_validation")
        except (yaml.YAMLError, ValueError, TypeError) as exc:
            errors.append(f"collaboration_invalid:{path.relative_to(root)}:{exc}")
    return errors


DIAGNOSTIC_CHECK_IDS = frozenset(
    {
        "full-source",
        "unit",
        "integration",
        "acceptance",
        "installed-packages",
        "frontend-static",
        "browser",
        "arm64-images",
        "amd64-images",
        "protected-contracts",
        "owned-cleanup",
        "preview",
        "independent-review",
        "remote-ci",
        "python-3.11",
        "native-amd64-development",
        "real-endpoint",
    }
)
DIAGNOSTIC_EXTERNAL_IDS = frozenset(
    {"remote-ci", "python-3.11", "native-amd64-development", "real-endpoint"}
)


def validate_diagnostic_records(root: Path) -> list[str]:
    """Validate recorded evidence claims; absent local artifacts are not rerun in CI."""
    try:
        documents: dict[str, JsonObject] = {}
        for name in ("acceptance", "handoff"):
            filename = "diagnostic-workbench-" + name
            schema = object_value(
                strict_json(
                    (
                        root
                        / "src/anthropic_readiness/resources/schemas"
                        / (filename + ".schema.json")
                    ).read_text()
                )
            )
            document = object_value(
                strict_json((root / "docs/harness" / (filename + ".json")).read_text())
            )
            Draft202012Validator(schema).validate(document)
            documents[name] = document
        acceptance, handoff = documents["acceptance"], documents["handoff"]
        source = object_value(handoff["source"])
        identities = {
            "source": source["fingerprint"],
            "image_context": source["image_context"],
            "review": source["reviewed_head"],
        }
        values = handoff["checks"]
        assert isinstance(values, list)
        checks: dict[str, JsonObject] = {}
        for value in values:
            check = object_value(value)
            identifier = str(check["id"])
            if identifier in checks:
                raise ValueError("duplicate_check:" + identifier)
            checks[identifier] = check
            children = check["children"]
            required = check["required_children"]
            assert isinstance(children, list)
            assert isinstance(required, list)
            child_ids = [str(object_value(child)["id"]) for child in children]
            if len(child_ids) != len(set(child_ids)):
                raise ValueError("duplicate_child:" + identifier)
            if check["status"] == "passed":
                expected = identities.get(str(check["identity_kind"]))
                if expected is None or check["source_identity"] != expected:
                    raise ValueError("unknown_source_identity:" + identifier)
                if {str(item) for item in required} - set(child_ids):
                    raise ValueError("missing_required_child:" + identifier)
                expected_kind = (
                    "review"
                    if identifier == "independent-review"
                    else "image_context"
                    if identifier in {"arm64-images", "amd64-images"}
                    else "source"
                )
                if check["identity_kind"] != expected_kind:
                    raise ValueError("wrong_source_scope:" + identifier)
        requirements = acceptance["requirements"]
        assert isinstance(requirements, list)
        covered: set[str] = set()
        for value in requirements:
            requirement = object_value(value)
            references = requirement["checks"]
            assert isinstance(references, list)
            covered.update(str(item) for item in references)
        if covered - checks.keys():
            raise ValueError("unknown_coverage_check")
        if handoff["status"] == "complete":
            needed = (DIAGNOSTIC_CHECK_IDS - DIAGNOSTIC_EXTERNAL_IDS) | covered
            if any(
                identifier not in checks or checks[identifier]["status"] != "passed"
                for identifier in needed
            ):
                raise ValueError("incomplete_delivery_claim")
        return []
    except (OSError, ValueError, ValidationError) as exc:
        return ["diagnostic_acceptance_invalid:" + str(exc).splitlines()[0]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root
    documents = [
        p for name in ("README.md", "CONTRIBUTING.md", "AGENTS.md") if (p := root / name).is_file()
    ]
    documents.extend((root / "docs").rglob("*.md"))
    errors = [
        *broken_links(root, documents),
        *validate_collaboration(root),
        *validate_diagnostic_records(root),
    ]
    print("\n".join(errors) if errors else "documentation_collaboration: passed")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
