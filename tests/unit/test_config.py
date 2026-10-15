"""Reject ambiguous configuration before any transport activity."""

from pathlib import Path

import pytest

from anthropic_readiness.config import load_target

EXAMPLE = Path(__file__).resolve().parents[2] / "examples/target.yaml"


def write_target(tmp_path: Path, old: str = "", new: str = "") -> Path:
    path = tmp_path / "target.yaml"
    text = EXAMPLE.read_text()
    path.write_text(text.replace(old, new) if old else text)
    return path


def test_duplicate_yaml_key_rejected(tmp_path: Path) -> None:
    path = write_target(tmp_path)
    path.write_text(path.read_text() + "\nmodel: duplicate\n")
    with pytest.raises(ValueError, match="duplicate"):
        load_target(path)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("streaming: true", 'streaming: "false"'),
        ("limits: {}", "limits: {connect_timeout_s: true}"),
        ("limits: {}", "limits: {read_timeout_s: .nan}"),
    ],
)
def test_string_false_and_boolean_timeout_rejected(tmp_path: Path, old: str, new: str) -> None:
    with pytest.raises(ValueError, match=r"schema|invalid_limit"):
        load_target(write_target(tmp_path, old, new))


@pytest.mark.parametrize(
    "url",
    [
        "http://user:pass@localhost/v1/messages",
        "http://localhost/v1/messages?key=foo",
        "http://localhost/v1/messages#foo",
        "http://localhost:wrong/v1/messages",
        "http://localhost/v1/messages?",
    ],
)
def test_url_credentials_query_fragment_rejected(tmp_path: Path, url: str) -> None:
    with pytest.raises(ValueError, match="url"):
        load_target(write_target(tmp_path, "http://127.0.0.1:8000/v1/messages", url))


def test_local_url_accepted(tmp_path: Path) -> None:
    target = load_target(write_target(tmp_path))
    assert target.messages_url == "http://127.0.0.1:8000/v1/messages"
    assert target.limits.attempt_timeout_s == 90
    assert target.credential({}) is None


@pytest.mark.parametrize("secret", [None, ""])
def test_missing_credentials(tmp_path: Path, secret: str | None) -> None:
    target = load_target(
        write_target(tmp_path, "mode: none", "mode: api_key\n  credential_env: SYNTHETIC_KEY")
    )
    with pytest.raises(ValueError, match="missing_credential"):
        target.credential({} if secret is None else {"SYNTHETIC_KEY": secret})


@pytest.mark.parametrize("policy", ["structure_only", "request_or_alias"])
def test_model_policy_and_fingerprint(tmp_path: Path, policy: str) -> None:
    first = load_target(
        write_target(
            tmp_path, "response_model_policy: request_or_alias", f"response_model_policy: {policy}"
        )
    )
    second = load_target(write_target(tmp_path, "example-build-001", "example-build-002"))
    if policy == "request_or_alias":
        assert first.fingerprint("hash") == second.fingerprint("hash")
    else:
        assert first.fingerprint("hash") != second.fingerprint("hash")
