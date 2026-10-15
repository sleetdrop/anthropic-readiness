# Synthetic HTTP behaviors

`tests/integration/conftest.py` serves only loopback data: complete messages,
service errors, truncated streams, duplicate starts, redirects, resets,
continuous pings, completed streams with open connections and compressed
body-limit probes. The source stream is pinned under `contracts/core-1.0.0`.
Tests block connections outside loopback; no live target is configured here.
