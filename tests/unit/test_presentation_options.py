"""Presentation preferences validate independently of execution and evidence."""

from dataclasses import FrozenInstanceError
from importlib.resources import files
from typing import cast

import pytest

from anthropic_readiness.models import object_value, strict_json
from anthropic_readiness.presentation import (
    Locale,
    PresentationOptions,
    Theme,
    parse_preferences,
    serialize_preferences,
)
from anthropic_readiness.schema import validate_document


def test_defaults_and_explicit_choices_have_checked_metadata() -> None:
    assert PresentationOptions().to_json() == {
        "schema_version": "1.0",
        "locale": "zh-CN",
        "theme": "system",
    }
    value = PresentationOptions(locale="en", theme="dark")
    assert serialize_preferences(value) == "v1.en.dark"
    assert parse_preferences("v1.en.dark") == value
    with pytest.raises(FrozenInstanceError):
        value.__setattr__("locale", "zh-CN")


@pytest.mark.parametrize("locale", ["zh", "EN", "fr", "", True, None])
def test_explicit_invalid_locale_is_rejected(locale: object) -> None:
    with pytest.raises(ValueError, match="presentation_locale"):
        PresentationOptions(locale=cast(Locale, locale))


@pytest.mark.parametrize("theme", ["auto", "DARK", "", True, None])
def test_explicit_invalid_theme_is_rejected(theme: object) -> None:
    with pytest.raises(ValueError, match="presentation_theme"):
        PresentationOptions(theme=cast(Theme, theme))


@pytest.mark.parametrize(
    "cookie",
    [
        None,
        "",
        "v2.en.dark",
        "v1.fr.dark",
        "v1.en.auto",
        "v1.en.dark.extra",
        " v1.en.dark",
        "x" * 1000,
    ],
)
def test_malformed_or_future_cookie_falls_back_without_inventing_choices(
    cookie: str | None,
) -> None:
    assert parse_preferences(cookie) == PresentationOptions()


def test_preference_contract_rejects_unknown_fields_and_values() -> None:
    root = files("anthropic_readiness").joinpath("resources/schemas")
    options_schema = object_value(
        strict_json(root.joinpath("presentation-options.schema.json").read_text())
    )
    preference_schema = object_value(
        strict_json(root.joinpath("preferences.schema.json").read_text())
    )
    validate_document(PresentationOptions().to_json(), options_schema)
    validate_document({"locale": "en", "theme": "light"}, preference_schema)
    for document in (
        {"locale": "en", "theme": "auto"},
        {"locale": "fr", "theme": "dark"},
        {"locale": "en", "theme": "dark", "token": "synthetic-secret"},
    ):
        with pytest.raises(ValueError, match="schema"):
            validate_document(document, preference_schema)
