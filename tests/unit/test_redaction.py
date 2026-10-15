"""Known credentials are removed before persistence, including escaped forms."""

import hashlib
import json
from dataclasses import replace

import pytest

from anthropic_readiness.evidence import sanitize_capture
from anthropic_readiness.models import ReadRecord
from tests.factories import capture

SECRET = 'synthetic/quote"slash\\密钥'


@pytest.mark.parametrize("encoding", ["raw", "json", "unicode"])
def test_raw_and_json_escaped_credentials(encoding: str) -> None:
    value = (
        SECRET
        if encoding == "raw"
        else json.dumps(SECRET, ensure_ascii=True)[1:-1]
        if encoding == "json"
        else "".join(f"\\u{ord(char):04X}" for char in SECRET)
    )
    raw = value.encode()
    source = replace(
        capture(raw), error=SECRET, headers=(("SET-cookie", SECRET), ("Request-ID", SECRET))
    )
    sanitized = sanitize_capture(source, [SECRET])
    assert sanitized.capture.body == b"[REDACTED]"
    assert sanitized.capture.error == "[REDACTED]"
    assert sanitized.capture.headers == (("request-id", "[REDACTED]"),)
    assert sanitized.original_sha256 == hashlib.sha256(raw).hexdigest()
    assert sanitized.original_length == len(raw)
    assert sanitized.transformed


def test_header_allowlists_and_cross_read_secret() -> None:
    body = b"before-" + SECRET.encode() + b"-after"
    source = capture(body)
    request = replace(
        source.request,
        headers=(
            ("X-API-KEY", SECRET),
            ("AUTHORIZATION", SECRET),
            ("Cookie", SECRET),
            ("Content-Type", "application/json"),
            ("Anthropic-Version", "2023-06-01"),
            ("Anthropic-Beta", "synthetic"),
        ),
    )
    source = replace(
        source, request=request, reads=(ReadRecord(10, 1), ReadRecord(len(body) - 10, 2))
    )
    sanitized = sanitize_capture(source, [SECRET])
    assert sanitized.capture.body == b"before-[REDACTED]-after"
    assert dict(sanitized.capture.request.headers) == {
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "synthetic",
    }
    assert sanitized.capture.reads == source.reads
    assert sanitized.transforms == ("credential_redaction",)
