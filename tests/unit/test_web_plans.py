"""Local URL planning never guesses arbitrary proxy paths or Docker aliases."""

from typing import Literal

import pytest

from anthropic_readiness.jobs.plans import resolve_messages_url


@pytest.mark.parametrize(
    ("value", "mode", "expected"),
    [
        ("http://localhost:3456", "base", "http://localhost:3456/v1/messages"),
        ("http://127.0.0.1:3456/", "base", "http://127.0.0.1:3456/v1/messages"),
        ("https://example.invalid/v1", "base", "https://example.invalid/v1/messages"),
        ("http://[::1]:3456/v1/", "base", "http://[::1]:3456/v1/messages"),
        (
            "https://example.invalid/proxy/messages",
            "messages",
            "https://example.invalid/proxy/messages",
        ),
    ],
)
def test_explicit_url_resolution(
    value: str, mode: Literal["base", "messages"], expected: str
) -> None:
    assert resolve_messages_url(value, mode) == expected


@pytest.mark.parametrize(
    ("value", "mode"),
    [
        ("https://example.invalid/proxy", "base"),
        ("https://example.invalid/v1/messages", "base"),
        ("https://user:secret@example.invalid", "base"),
        ("https://example.invalid?token=secret", "base"),
        ("https://example.invalid#fragment", "base"),
        ("file:///tmp/socket", "messages"),
        ("http://localhost:bad", "base"),
        ("https://example.invalid/\npath", "messages"),
        ("https://example.invalid/v1/messages", "automatic"),
    ],
)
def test_ambiguous_or_unsafe_urls_are_rejected(
    value: str, mode: Literal["base", "messages"]
) -> None:
    with pytest.raises(ValueError, match="url"):
        resolve_messages_url(value, mode)
