"""Explicit local Messages URL resolution."""

from typing import Literal
from urllib.parse import urlsplit


def resolve_messages_url(value: str, mode: Literal["base", "messages"]) -> str:
    try:
        parsed = urlsplit(value)
        _ = parsed.port
        valid = (
            parsed.scheme in {"http", "https"}
            and parsed.hostname
            and not parsed.username
            and not parsed.password
            and not any(char in value for char in "?#")
            and not any(char.isspace() or ord(char) < 32 for char in value)
        )
    except ValueError as exc:
        raise ValueError("invalid_url") from exc
    if not valid or mode not in {"base", "messages"}:
        raise ValueError("invalid_url")
    if mode == "messages":
        return value
    if parsed.path in {"", "/"}:
        return value.rstrip("/") + "/v1/messages"
    if parsed.path in {"/v1", "/v1/"}:
        return value.rstrip("/") + "/messages"
    raise ValueError("ambiguous_base_url")
