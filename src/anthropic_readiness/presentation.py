"""Pure presentation choices; never part of execution or judgment inputs."""

from dataclasses import dataclass
from typing import Literal

from anthropic_readiness.models import JsonObject

Locale = Literal["zh-CN", "en"]
Theme = Literal["light", "dark", "system"]
LOCALES: tuple[Locale, ...] = ("zh-CN", "en")
THEMES: tuple[Theme, ...] = ("light", "dark", "system")


@dataclass(frozen=True)
class PresentationOptions:
    locale: Locale = "zh-CN"
    theme: Theme = "system"

    def __post_init__(self) -> None:
        if self.locale not in LOCALES:
            raise ValueError("presentation_locale")
        if self.theme not in THEMES:
            raise ValueError("presentation_theme")

    def to_json(self) -> JsonObject:
        return {"schema_version": "1.0", "locale": self.locale, "theme": self.theme}


def parse_preferences(value: str | None) -> PresentationOptions:
    """Treat malformed/obsolete cookies as absent, not as explicit updates."""
    if value is not None and len(value) <= 64:
        parts = value.split(".")
        if len(parts) == 3 and parts[0] == "v1":
            locale, theme = parts[1:]
            if locale in LOCALES and theme in THEMES:
                return PresentationOptions(locale, theme)
    return PresentationOptions()


def serialize_preferences(options: PresentationOptions) -> str:
    return f"v1.{options.locale}.{options.theme}"
