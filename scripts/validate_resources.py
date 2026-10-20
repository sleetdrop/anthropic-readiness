"""Validate schemas, immutable bundles, fixture integrity and acceptance IDs."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from anthropic_readiness.config import load_target, string
from anthropic_readiness.contracts import validate_bundle
from anthropic_readiness.diagnostics.contracts import PROJECTION_SCHEMAS, STORAGE_SCHEMAS
from anthropic_readiness.diagnostics.contracts import SCHEMAS as DIAGNOSTIC_SCHEMAS
from anthropic_readiness.diagnostics.identity import _identity_from_root
from anthropic_readiness.localization import validate_catalogs
from anthropic_readiness.models import CaseContract, JsonObject, object_value, strict_json
from anthropic_readiness.schema import validate_document, validate_result_semantics
from anthropic_readiness.sse import SSEDecoder
from anthropic_readiness.validation.messages import validate_message
from anthropic_readiness.validation.stream import StreamValidator

CHECK_IDS = {
    "lock",
    "format",
    "lint",
    "type",
    "architecture",
    "schemas",
    "unit",
    "integration",
    "acceptance",
    "packaging",
    "documentation",
    "devcontainer",
    "runtime-amd64",
    "runtime-arm64",
    "python-3.11",
    "python-3.12",
    "visual-review",
    "independent-review",
    "remote-ci",
}


def _golden(path: Path, rule_id: str) -> str:
    if path.suffix == ".sse":
        decoder = SSEDecoder(262144, 10000)
        frames = decoder.feed(path.read_bytes(), 0)
        validator = StreamValidator(CaseContract("contract-golden"))
        end = "none"
        for frame in frames:
            validator.consume(frame)
            if frame.event == "message_stop":
                end = "message_stop"
        result = validator.finish(
            "message_stop" if end == "message_stop" else "none", "eof", decoder.finish()
        )
    else:
        contract = CaseContract(
            "contract-golden", behavior="tool" if rule_id == "MSG-TOOL-INPUT" else "greeting"
        )
        result = validate_message(strict_json(path.read_text()), contract)
    return next((a.status.value for a in result.assertions if a.id == rule_id), "missing_assertion")


def validate_resources(root: Path) -> list[str]:
    errors: list[str] = []
    resources = root / "src/anthropic_readiness/resources"
    schemas: dict[str, JsonObject] = {}
    for path in (resources / "schemas").glob("*.schema.json"):
        try:
            schema = object_value(strict_json(path.read_text()))
            Draft202012Validator.check_schema(schema)
            validate_document({}, {"$defs": {"checked": schema}})
            schemas[path.name.removesuffix(".schema.json")] = schema
        except (ValueError, SchemaError) as exc:
            errors.append(f"schema_invalid:{path.name}:{type(exc).__name__}")
    expected = {
        *DIAGNOSTIC_SCHEMAS,
        *STORAGE_SCHEMAS,
        *PROJECTION_SCHEMAS,
        "result",
        "target",
        "capture",
        "contract",
        "check-result",
        "image-result",
        "acceptance",
        "plan",
        "job",
        "execution",
        "checkpoint",
        "progress-event",
        "report-view",
        "export-manifest",
        "web-api",
        "web-console-acceptance",
        "web-console-handoff",
        "diagnostic-workbench-acceptance",
        "diagnostic-workbench-handoff",
        "presentation-options",
        "preferences",
        "localization-catalog",
        "diagnostic-identity-manifest",
        "assessment-context-verification",
    }
    if set(schemas) != expected:
        errors.append("schema_inventory")
    try:
        catalogs = {
            locale: object_value(
                strict_json((resources / "locales" / f"{locale}.json").read_text())
            )
            for locale in ("zh-CN", "en")
        }
        validate_catalogs(catalogs)
    except (OSError, ValueError) as exc:
        errors.append(f"catalog_invalid:{exc}")
    try:
        _identity_from_root(root / "src/anthropic_readiness")
    except (OSError, ValueError) as exc:
        errors.append(f"diagnostic_identity_invalid:{exc}")
    for path in (resources / "contracts").glob("*/*/manifest.json"):
        try:
            manifest = object_value(strict_json(path.read_text()))
            files = {
                p.name: p.read_bytes()
                for p in path.parent.iterdir()
                if p.is_file() and p.name != "manifest.json"
            }
            validate_bundle(manifest, files)
            fixture_paths: dict[str, Path] = {}
            integrity = manifest["fixture_integrity"]
            if not isinstance(integrity, list):
                raise ValueError("fixture_inventory")
            for entry in integrity:
                ref = object_value(entry)
                relative = Path(string(ref["path"]))
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("fixture_path")
                fixture = root / relative
                if hashlib.sha256(fixture.read_bytes()).hexdigest() != ref["sha256"]:
                    raise ValueError("fixture_hash")
                fixture_paths[fixture.name] = fixture
            rules = manifest["rules"]
            if not isinstance(rules, list):
                raise ValueError("rules_inventory")
            for rule_value in rules:
                rule = object_value(rule_value)
                rule_id = string(rule["id"])
                if (
                    _golden(fixture_paths[string(rule["positive_fixture"])], rule_id) != "PASS"
                    or _golden(fixture_paths[string(rule["negative_fixture"])], rule_id) != "FAIL"
                ):
                    raise ValueError("golden_verdict:" + rule_id)
        except (OSError, ValueError, KeyError) as exc:
            errors.append(f"contract_invalid:{path}:{exc}")
    if not list((resources / "contracts").glob("*/*/manifest.json")):
        errors.append("contract_inventory")
    if "result" in schemas:
        for fixture in (root / "tests/fixtures/results").glob("*.json"):
            try:
                value = object_value(strict_json(fixture.read_text()))
                validate_document(value, schemas["result"])
                if validate_result_semantics(value):
                    raise ValueError("result_relations")
            except ValueError as exc:
                errors.append(f"result_fixture_invalid:{fixture.name}:{exc}")
    acceptance = root / "docs/harness/acceptance.json"
    if acceptance.is_file() and "acceptance" in schemas:
        try:
            value = object_value(strict_json(acceptance.read_text()))
            validate_document(value, schemas["acceptance"])
            requirements = value["requirements"]
            assert isinstance(requirements, list)
            seen: set[str] = set()
            for item in requirements:
                requirement = object_value(item)
                identifier = string(requirement["id"])
                if identifier in seen:
                    raise ValueError("duplicate_requirement")
                seen.add(identifier)
                checks = requirement["checks"]
                if (
                    not isinstance(checks, list)
                    or not checks
                    or any(check not in CHECK_IDS for check in checks if isinstance(check, str))
                ):
                    raise ValueError("unknown_acceptance_check:" + identifier)
        except ValueError as exc:
            errors.append(f"acceptance_invalid:{exc}")
    else:
        errors.append("acceptance_missing")
    example = root / "examples/target.yaml"
    if example.is_file():
        try:
            load_target(example)
        except ValueError as exc:
            errors.append(f"example_invalid:{exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate_resources(args.root)
    print("\n".join(errors) if errors else "schemas_contracts_fixtures: passed")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
