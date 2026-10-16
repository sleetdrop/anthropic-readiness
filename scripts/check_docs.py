"""Check local links, collaboration YAML and required CI child accounting."""

from __future__ import annotations

import argparse
import re
from collections.abc import Sequence
from pathlib import Path

import yaml


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root
    documents = [
        p for name in ("README.md", "CONTRIBUTING.md", "AGENTS.md") if (p := root / name).is_file()
    ]
    documents.extend((root / "docs").rglob("*.md"))
    errors = [*broken_links(root, documents), *validate_collaboration(root)]
    print("\n".join(errors) if errors else "documentation_collaboration: passed")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
