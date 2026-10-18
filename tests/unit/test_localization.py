"""Catalog parity and restricted formatting keep translations separate from source data."""

from importlib.resources import files
from typing import cast

import pytest

from anthropic_readiness.localization import load_catalog, translate, validate_catalogs
from anthropic_readiness.models import JsonObject, object_value, strict_json
from anthropic_readiness.presentation import Locale


def _documents() -> dict[str, JsonObject]:
    root = files("anthropic_readiness").joinpath("resources/locales")
    return {
        locale: object_value(strict_json(root.joinpath(f"{locale}.json").read_text()))
        for locale in ("zh-CN", "en")
    }


def _messages(document: JsonObject) -> JsonObject:
    messages = document["messages"]
    assert isinstance(messages, dict)
    return messages


def test_packaged_catalogs_have_matching_complete_messages() -> None:
    validate_catalogs(_documents())
    english = load_catalog("en")
    chinese = load_catalog("zh-CN")
    assert set(english) == set(chinese)
    assert translate(english, "case.count.one", {"count": 1}) == "1 case"
    assert translate(english, "case.count.other", {"count": 0}) == "0 cases"
    assert translate(english, "case.count.other", {"count": 4}) == "4 cases"
    assert translate(chinese, "case.count.other", {"count": 4}) == "4 个用例"


def test_removed_key_and_changed_parameter_fail_catalog_validation() -> None:
    documents = _documents()
    messages = _messages(documents["en"])
    del messages["nav.runs"]
    with pytest.raises(ValueError, match="catalog_keys"):
        validate_catalogs(documents)
    documents = _documents()
    _messages(documents["en"])["case.count.one"] = "{total} case"
    with pytest.raises(ValueError, match="catalog_parameters"):
        validate_catalogs(documents)


def test_missing_plural_form_is_rejected_even_when_both_catalogs_match() -> None:
    documents = _documents()
    for document in documents.values():
        del _messages(document)["case.count.other"]
    with pytest.raises(ValueError, match="catalog_count_forms"):
        validate_catalogs(documents)


@pytest.mark.parametrize(
    "template",
    ["{user.name}", "{user[0]}", "{value!r}", "{value:>20}", "{}", "{value", "{0}"],
)
def test_formatter_rejects_expressions_and_arbitrary_format_operations(template: str) -> None:
    with pytest.raises(ValueError, match="translation_template"):
        translate({"test": template}, "test", {"user": "raw", "value": "raw"})


def test_missing_key_or_parameters_is_an_error_not_silent_fallback() -> None:
    catalog = load_catalog("en")
    with pytest.raises(ValueError, match="translation_key"):
        translate(catalog, "not.authored")
    for params in (None, {"total": 4}, {"count": 4, "extra": 3}):
        with pytest.raises(ValueError, match="translation_parameters"):
            translate(catalog, "case.count.other", params)
    with pytest.raises(ValueError, match="presentation_locale"):
        load_catalog(cast(Locale, "../../outside"))


def test_source_parameters_are_preserved_as_plain_text_without_reformatting() -> None:
    raw = "<script>message_stop</script> {count} / example-model"
    params = {"code": "OLD-RULE", "detail": raw}
    result = translate(load_catalog("en"), "diagnostic.unknown", params)
    assert "OLD-RULE" in result
    assert raw in result
    assert params == {"code": "OLD-RULE", "detail": raw}
    assert translate({"literal": "{{raw}} {value}"}, "literal", {"value": "stop_sequence"}) == (
        "{raw} stop_sequence"
    )


@pytest.mark.parametrize("value", [float("inf"), float("nan"), True])
def test_non_json_numeric_parameters_are_rejected(value: float | bool) -> None:
    with pytest.raises(ValueError, match="translation_parameters"):
        translate({"count": "{count}"}, "count", {"count": value})


def test_catalogs_reject_invalid_schema_and_cannot_be_mutated_by_callers() -> None:
    documents = _documents()
    documents["en"]["extra"] = "not-permitted"
    with pytest.raises(ValueError, match="schema"):
        validate_catalogs(documents)
    catalog = load_catalog("en")
    assert not isinstance(catalog, dict)
