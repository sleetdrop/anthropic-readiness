# Synthetic HTTP behaviors

`tests/integration/conftest.py` serves only loopback data: complete messages,
service errors, truncated streams, duplicate starts, redirects, resets,
continuous pings, completed streams with open connections and compressed
body-limit probes. The source stream is pinned under `contracts/core-1.0.0`.
Tests block connections outside loopback; no live target is configured here.

The standalone `server.py` is the stdlib peer for CLI/Web image acceptance. Its
request journal contains only path, model, stream flag and credential-presence
boolean; it never records the credential value. The separate public CLI handoff
acceptance test owns two loopback peers: A has missing stop fields/model-policy
failures; B restores stop fields, retains model identity differences and duplicates
a counting-stream start while preserving task behavior. Neither uses a real model.
