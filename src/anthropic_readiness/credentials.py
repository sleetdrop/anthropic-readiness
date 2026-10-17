"""Explicit credential providers; never include secrets in representations."""

import os
from collections.abc import Mapping

from anthropic_readiness.config import TargetConfig


class EnvironmentCredentials:
    def __init__(self, target: TargetConfig, environment: Mapping[str, str] | None = None) -> None:
        self._target = target
        self._environment = environment

    def resolve(self) -> str | None:
        return self._target.credential(
            os.environ if self._environment is None else self._environment
        )


class MemoryCredentials:
    def __init__(self, value: str | None) -> None:
        self._value = value

    def resolve(self) -> str | None:
        if self._value is not None and (
            not self._value.strip() or "\r" in self._value or "\n" in self._value
        ):
            raise ValueError("invalid_credential")
        return self._value


class AllowlistedCredentials:
    def __init__(self, name: str, allowed: Mapping[str, str]) -> None:
        self._name = name
        self._allowed = allowed

    def resolve(self) -> str | None:
        if self._name not in self._allowed:
            raise ValueError("unknown_credential_reference")
        return MemoryCredentials(self._allowed[self._name]).resolve()
