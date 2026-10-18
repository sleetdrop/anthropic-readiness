"""Checked packaged catalogs and restricted plain-text message substitution."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from functools import lru_cache
from importlib.resources import files
from string import Formatter
from types import MappingProxyType

from anthropic_readiness.json_validation import validate_document
from anthropic_readiness.models import JsonObject, object_value, strict_json
from anthropic_readiness.presentation import LOCALES, Locale, PresentationOptions


def _parameters(template: str) -> frozenset[str]:
    parameters: set[str] = set()
    try:
        for _, field, specification, conversion in Formatter().parse(template):
            if field is not None:
                if (
                    not re.fullmatch(r"[a-z][a-z0-9_]*", field)
                    or specification
                    or conversion is not None
                ):
                    raise ValueError("translation_template")
                parameters.add(field)
    except ValueError as exc:
        raise ValueError("translation_template") from exc
    return frozenset(parameters)


def validate_catalogs(documents: Mapping[str, JsonObject]) -> None:
    """Validate schema, locale ownership, authored-key parity and count forms."""
    if set(documents) != set(LOCALES):
        raise ValueError("catalog_locales")
    schema = object_value(
        strict_json(
            files("anthropic_readiness")
            .joinpath("resources/schemas/localization-catalog.schema.json")
            .read_text()
        )
    )
    signatures: dict[str, dict[str, frozenset[str]]] = {}
    for locale, document in documents.items():
        validate_document(document, schema)
        if document["locale"] != locale:
            raise ValueError("catalog_locale")
        messages = object_value(document["messages"])
        signature: dict[str, frozenset[str]] = {}
        for key, text in messages.items():
            if not isinstance(text, str):
                raise ValueError("catalog_message")
            signature[key] = _parameters(text)
        for key in signature:
            if key.endswith((".one", ".other")):
                stem = key.rsplit(".", 1)[0]
                if any(f"{stem}.{form}" not in signature for form in ("one", "other")):
                    raise ValueError("catalog_count_forms")
                if signature[f"{stem}.one"] != signature[f"{stem}.other"]:
                    raise ValueError("catalog_parameters")
        signatures[locale] = signature
    if signatures["zh-CN"].keys() != signatures["en"].keys():
        raise ValueError("catalog_keys")
    if signatures["zh-CN"] != signatures["en"]:
        raise ValueError("catalog_parameters")


@lru_cache(maxsize=1)
def _catalogs() -> Mapping[str, Mapping[str, str]]:
    root = files("anthropic_readiness").joinpath("resources/locales")
    documents: dict[str, JsonObject] = {
        locale: object_value(strict_json(root.joinpath(f"{locale}.json").read_text()))
        for locale in LOCALES
    }
    validate_catalogs(documents)
    catalogs: dict[str, Mapping[str, str]] = {}
    for locale, document in documents.items():
        messages = object_value(document["messages"])
        # Validation established string values; build a narrow immutable view.
        catalogs[locale] = MappingProxyType(
            {key: text for key, text in messages.items() if isinstance(text, str)}
        )
    return MappingProxyType(catalogs)


def load_catalog(locale: Locale) -> Mapping[str, str]:
    PresentationOptions(locale=locale)
    return _catalogs()[locale]


def translate(
    catalog: Mapping[str, str],
    key: str,
    params: Mapping[str, str | int | float] | None = None,
) -> str:
    """Return ordinary text. Each output renderer owns contextual escaping."""
    if key not in catalog:
        raise ValueError("translation_key")
    template = catalog[key]
    expected = _parameters(template)
    supplied = {} if params is None else dict(params)
    if set(supplied) != expected or any(
        isinstance(value, bool)
        or not isinstance(value, (str, int, float))
        or (isinstance(value, float) and not math.isfinite(value))
        for value in supplied.values()
    ):
        raise ValueError("translation_parameters")
    return template.format_map(supplied)
