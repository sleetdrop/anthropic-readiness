"""New versioned boundaries reject missing identities without weakening old contracts."""

from copy import deepcopy
from importlib.resources import files

import pytest

from anthropic_readiness.diagnostics.contracts import validate_diagnostic
from anthropic_readiness.diagnostics.models import (
    AssessmentContext,
    BaselineRecord,
    Comparison,
    DiagnosticPackage,
    DocumentView,
    ImplementationIdentity,
    RetestRecipe,
    WorkbenchView,
)
from anthropic_readiness.models import JsonObject, object_value, strict_json
from anthropic_readiness.schema import load_schema, validate_document
from tests.diagnostic_contract_fixtures import contract_documents


@pytest.mark.parametrize("name", list(contract_documents()))
def test_contract_versions_and_required_identities(name: str) -> None:
    original = contract_documents()[name]
    before = deepcopy(original)
    validate_diagnostic(original, name)
    assert original == before
    for field, value in (("schema_version", "999"), ("undeclared", "synthetic")):
        invalid = {**original, field: value}
        with pytest.raises(ValueError, match="schema"):
            validate_diagnostic(invalid, name)
    missing = {key: value for key, value in original.items() if key != "schema_version"}
    with pytest.raises(ValueError, match="schema"):
        validate_diagnostic(missing, name)


def test_missing_recipe_check_and_file_identities_are_rejected() -> None:
    documents = contract_documents()
    context = documents["assessment-context"]
    del context["recipe_sha256"]
    with pytest.raises(ValueError, match="schema"):
        validate_diagnostic(context, "assessment-context")
    recipe = documents["retest-recipe"]
    cases = recipe["cases"]
    assert isinstance(cases, list)
    case = object_value(cases[0])
    case["assertions"] = [{"id": "MSG-CORE", "required": True, "category": "protocol"}]
    recipe["cases"] = [case]
    with pytest.raises(ValueError, match="schema"):
        validate_diagnostic(recipe, "retest-recipe")
    package = documents["diagnostic-package"]
    package["files"] = [{"path": "result.json", "bytes": 10}]
    with pytest.raises(ValueError, match="schema"):
        validate_diagnostic(package, "diagnostic-package")


@pytest.mark.parametrize("field", ["messages_url", "auth", "credential_env", "command"])
def test_recipe_is_not_an_endpoint_secret_or_execution_container(field: str) -> None:
    recipe = contract_documents()["retest-recipe"]
    recipe[field] = "synthetic-value"
    with pytest.raises(ValueError, match="schema"):
        validate_diagnostic(recipe, "retest-recipe")


def test_unknown_schema_and_nonfinite_json_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown_diagnostic_schema"):
        validate_diagnostic({}, "../../outside")
    invalid = contract_documents()["retest-recipe"]
    requests = invalid["requests"]
    assert isinstance(requests, list)
    request = object_value(requests[0])
    request["body"] = {"temperature": float("inf")}
    invalid["requests"] = [request]
    with pytest.raises(ValueError, match="Out of range float values"):
        validate_diagnostic(invalid, "retest-recipe")


@pytest.mark.parametrize("path", ["../outside", "/outside", "a/../b", "a\\b", "a//b", "é.json"])
def test_new_file_inventory_rejects_ambiguous_or_unsafe_paths(path: str) -> None:
    document = contract_documents()["diagnostic-package"]
    document["files"] = [{"path": path, "sha256": "a" * 64, "bytes": 1}]
    with pytest.raises(ValueError, match="schema"):
        validate_diagnostic(document, "diagnostic-package")


def test_original_result_and_view_contracts_still_validate() -> None:
    from tests.acceptance.test_reports import mixed

    result = mixed().to_json()
    validate_document(result, load_schema("result"))
    view = contract_documents()["document-view"]["facts"]
    validate_document(view, load_schema("report-view"))
    new_manifest = contract_documents()["export-manifest-v2"]
    old_manifest = {key: value for key, value in new_manifest.items() if key != "presentation"}
    old_manifest.update(schema_version="1.0", presentation_version="2.0")
    validate_document(old_manifest, load_schema("export-manifest"))
    with pytest.raises(ValueError, match="schema"):
        validate_document(new_manifest, load_schema("export-manifest"))


def test_all_values_are_data_only_and_contracts_are_packaged() -> None:
    wrappers = (
        ImplementationIdentity,
        RetestRecipe,
        AssessmentContext,
        DiagnosticPackage,
        BaselineRecord,
        Comparison,
        WorkbenchView,
        DocumentView,
    )
    values: JsonObject = {"synthetic": "data"}
    for wrapper in wrappers:
        assert wrapper(values).document == values
    for name in contract_documents():
        resource = files("anthropic_readiness").joinpath(f"resources/schemas/{name}.schema.json")
        schema = object_value(strict_json(resource.read_text()))
        assert schema["additionalProperties"] is False
