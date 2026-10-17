"""Container delivery must independently prove Web behavior and safe local defaults."""

from pathlib import Path

import pytest
import yaml

from scripts.check_images import Acceptance, assess_image_checks

ROOT = Path(__file__).resolve().parents[2]
WEB_CHECKS = (
    "web-image-inspect",
    "web-default-nonroot",
    "web-pages",
    "web-assessment",
    "web-exports",
    "web-volume-restart",
    "web-cancellation",
    "web-host-path",
)


@pytest.mark.parametrize("missing", WEB_CHECKS)
def test_web_image_is_not_cli_only_acceptance(missing: str) -> None:
    records: list[dict[str, object]] = [
        {"id": name, "status": "passed"} for name in WEB_CHECKS if name != missing
    ]
    records.append({"id": "runtime-help", "status": "passed"})
    status, absent = assess_image_checks(records, ("web",), "full")
    assert status != "passed"
    assert missing in absent


def test_compose_binds_only_host_loopback() -> None:
    document = yaml.safe_load((ROOT / "compose.yaml").read_text())
    service = document["services"]["readiness"]
    assert service["build"]["target"] == "web"
    assert service["ports"] == ["127.0.0.1:8765:8765"]
    assert service["read_only"] is True
    assert str(service["user"]) == "10001:10001"
    assert len(service["tmpfs"]) == 1
    assert "size=" in service["tmpfs"][0]
    assert service["volumes"] == ["readiness-data:/data"]
    assert "readiness-data" in document["volumes"]
    assert "docker.sock" not in (ROOT / "compose.yaml").read_text()


def test_docker_targets_separate_web_and_cli_dependencies() -> None:
    source = (ROOT / "Dockerfile").read_text()
    assert " AS web\n" in source
    assert "--extra web" in source
    assert '"serve"' in source
    assert '"/data"' in source
    assert "AS runtime\n" in source
    assert "node_modules" not in source[source.index("AS runtime\n") :]


def test_image_full_prepares_browser_before_disconnect() -> None:
    source = (ROOT / "scripts/check_images.py").read_text()
    assert '"dev-frontend-prepare"' in source
    assert source.index('"dev-frontend-prepare"') < source.index('"dev-isolate"')
    workflow = (ROOT / ".github/workflows/container-matrix.yml").read_text()
    assert "--targets runtime,web" in workflow


def test_peer_publishing_uses_normal_bridge_while_cli_peer_route_stays_internal(
    tmp_path: Path,
) -> None:
    commands: dict[str, list[str]] = {}

    class Recorded(Acceptance):
        def docker(
            self, label: str, args: list[str], expected: int = 0, timeout: float = 120
        ) -> str:
            commands[label] = args
            if label == "peer-start":
                (self.peer_state / "ready").write_text("8080")
            return "127.0.0.1:34567" if label == "peer-published-port" else "synthetic"

    fixture = Recorded(tmp_path, "linux/arm64", "smoke")
    fixture.start_peer()
    args = commands["peer-start"]
    published_network = args[args.index("--network") + 1]
    creation = next(
        value
        for value in commands.values()
        if value[:2] == ["network", "create"] and value[-1] == published_network
    )
    assert "--internal" not in creation, "Docker cannot publish a host UI from an isolated network"
    assert "--internal" in commands["network-create"]
