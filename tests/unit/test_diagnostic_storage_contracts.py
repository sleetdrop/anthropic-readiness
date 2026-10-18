"""Private durable markers and previews also have packaged versioned boundaries."""

import pytest

from anthropic_readiness.diagnostics.contracts import validate_storage
from anthropic_readiness.models import JsonObject


def test_commit_marker_rejects_unknown_versions_fields_and_invalid_digests() -> None:
    valid: JsonObject = {
        "schema_version": "1.0",
        "baseline_sha256": "a" * 64,
        "archive_sha256": "b" * 64,
    }
    validate_storage(valid, "diagnostic-commit")
    for value in (
        {**valid, "schema_version": "2.0"},
        {**valid, "unexpected": True},
        {**valid, "baseline_sha256": "bad"},
    ):
        with pytest.raises(ValueError, match="schema"):
            validate_storage(value, "diagnostic-commit")


def test_preview_envelope_cannot_accept_an_arbitrary_response_or_inventory() -> None:
    with pytest.raises(ValueError, match="schema"):
        validate_storage(
            {
                "schema_version": "1.0",
                "owner": "local",
                "expires_at": "2026-11-01T00:15:00+00:00",
                "inventory": {},
                "response": {},
            },
            "diagnostic-import-preview",
        )
