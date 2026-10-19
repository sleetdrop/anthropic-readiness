"""Explicit local Web settings."""

import math
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class WebSettings:
    host: str = "127.0.0.1"
    port: int = 8765
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1", "[::1]")
    allowed_origins: tuple[str, ...] = (
        "http://localhost:8765",
        "http://127.0.0.1:8765",
        "http://[::1]:8765",
    )
    credential_env_allowlist: tuple[str, ...] = ()
    max_body_bytes: int = 65536
    max_import_bytes: int = 256 * 1024 * 1024
    import_timeout_s: float = 60

    def __post_init__(self) -> None:
        if self.host not in {"127.0.0.1", "::1", "localhost", "0.0.0.0"}:
            raise ValueError("invalid_local_bind")
        if type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ValueError("invalid_web_port")
        if type(self.max_body_bytes) is not int or not 1 <= self.max_body_bytes <= 65536:
            raise ValueError("invalid_body_limit")
        if (
            type(self.max_import_bytes) is not int
            or not 1 <= self.max_import_bytes <= 256 * 1024 * 1024
        ):
            raise ValueError("invalid_import_limit")
        if (
            isinstance(self.import_timeout_s, bool)
            or not math.isfinite(self.import_timeout_s)
            or not 0 < self.import_timeout_s <= 60
        ):
            raise ValueError("invalid_import_timeout")
        if not self.allowed_hosts or set(self.allowed_hosts) - {"localhost", "127.0.0.1", "[::1]"}:
            raise ValueError("invalid_local_hosts")
        defaults = ("http://localhost:8765", "http://127.0.0.1:8765", "http://[::1]:8765")
        if self.port != 8765 and self.allowed_origins == defaults:
            object.__setattr__(
                self,
                "allowed_origins",
                tuple(f"http://{host}:{self.port}" for host in self.allowed_hosts),
            )
        if any(
            not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)
            for name in self.credential_env_allowlist
        ):
            raise ValueError("invalid_credential_reference")
