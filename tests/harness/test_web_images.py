"""Container delivery must independently prove Web behavior and safe local defaults."""

import json
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from anthropic_readiness.models import object_value
from anthropic_readiness.schema import load_schema
from scripts.check_images import Acceptance, EnvironmentUnavailable, assess_image_checks, main

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


def test_image_contract_is_available_through_packaged_schema_loader() -> None:
    schema = load_schema("image-result")
    version = object_value(object_value(schema["properties"])["schema_version"])
    assert version["enum"] == ["2.0", "2.1"]


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
            if label == "host-gateway-resolve":
                return "172.17.0.1"
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


@pytest.mark.parametrize(
    ("system", "binding"), [("Darwin", "127.0.0.1::8080"), ("Linux", "172.17.0.1::8080")]
)
def test_host_peer_binding_matches_the_platform_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, system: str, binding: str
) -> None:
    commands: dict[str, list[str]] = {}

    class Recorded(Acceptance):
        def docker(
            self, label: str, args: list[str], expected: int = 0, timeout: float = 120
        ) -> str:
            commands[label] = args
            if label == "peer-start":
                (self.peer_state / "ready").write_text("8080")
            if label == "host-gateway-resolve":
                return "172.17.0.1"
            return "127.0.0.1:34567" if label == "peer-published-port" else "synthetic"

    monkeypatch.setattr("scripts.check_images.platform.system", lambda: system)
    fixture = Recorded(tmp_path, "linux/arm64", "full")
    fixture.start_peer()
    args = commands["peer-start"]
    assert args[args.index("-p") + 1] == binding


def test_public_host_gateway_cannot_broaden_synthetic_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Recorded(Acceptance):
        def docker(
            self, label: str, args: list[str], expected: int = 0, timeout: float = 120
        ) -> str:
            if label == "peer-start":
                (self.peer_state / "ready").write_text("8080")
            return "8.8.8.8" if label == "host-gateway-resolve" else "synthetic"

    monkeypatch.setattr("scripts.check_images.platform.system", lambda: "Linux")
    fixture = Recorded(tmp_path, "linux/arm64", "full")
    with pytest.raises(EnvironmentUnavailable, match="private_host_gateway"):
        fixture.start_peer()


@pytest.mark.parametrize("architecture", ["arm64", "amd64"])
def test_development_browser_cache_is_bound_to_platform_and_revision(
    tmp_path: Path, architecture: str
) -> None:
    commands: dict[str, list[str]] = {}

    class Recorded(Acceptance):
        def docker(
            self, label: str, args: list[str], expected: int = 0, timeout: float = 120
        ) -> str:
            commands[label] = args
            if label == "dev-browser-cache-inspect":
                return json.dumps(
                    {
                        "Labels": {
                            "io.anthropic-readiness.kind": "browser-cache",
                            "io.anthropic-readiness.platform": "linux/" + architecture,
                            "io.anthropic-readiness.revision": "1248",
                        }
                    }
                )
            if label == "dev-image-inspect":
                return json.dumps({"Architecture": architecture})
            return "{}"

    fixture = Recorded(tmp_path, "linux/" + architecture, "full")
    fixture.development_platform = "linux/" + architecture
    fixture.dev = "anthropic-readiness-dev:" + architecture
    fixture.run_development()
    assert (
        f"anthropic-readiness-playwright-{architecture}-1248:/home/developer/.cache/ms-playwright"
        in commands["dev-start"]
    )
    assert "dev-frontend-prepare" in commands
    assert not fixture.volumes, (
        "development tool cache is retained separately from disposable job data"
    )


@pytest.mark.parametrize(
    ("engine", "development", "target"),
    [("aarch64", "linux/arm64", "linux/amd64"), ("x86_64", "linux/amd64", "linux/arm64")],
)
def test_cross_target_images_keep_native_development_gates(
    tmp_path: Path, engine: str, development: str, target: str
) -> None:
    commands: dict[str, list[str]] = {}

    class Recorded(Acceptance):
        def command(
            self, label: str, argv: list[str], expected: int = 0, timeout: float = 120
        ) -> str:
            return "a" * 40

        def docker(
            self, label: str, args: list[str], expected: int = 0, timeout: float = 120
        ) -> str:
            commands[label] = args
            return engine if label == "engine-architecture" else "{}"

        def run_runtime(self) -> None:
            pass

        def run_development(self) -> None:
            pass

        def start_peer(self) -> None:
            pass

        def run_cli_live(self, host_url: str) -> None:
            pass

    fixture = Recorded(tmp_path, target, "full", ("runtime",))
    fixture.run(False, None)
    runtime = commands["build-runtime"]
    dev = commands["build-dev"]
    assert runtime[runtime.index("--platform") + 1] == target
    assert dev[dev.index("--platform") + 1] == development


def image_record(version: str) -> dict[str, object]:
    return {
        "schema_version": version,
        "scope": "full",
        "targets": ["runtime", "web"],
        "platform": "linux/amd64",
        "host_machine": "arm64",
        "execution": "emulated",
        "started_at": "2026-10-17T00:00:00Z",
        "finished_at": "2026-10-17T00:01:00Z",
        "image_context_fingerprint": "a" * 64,
        "source_unchanged": True,
        "skip_build": False,
        "status": "blocked",
        "error": "synthetic_unavailable",
        "checks": [],
        "missing_checks": ["dev-offline-full"],
    }


def test_image_v21_records_development_separately_and_keeps_v20_readable() -> None:
    validator = Draft202012Validator(load_schema("image-result"))
    assert not list(validator.iter_errors(image_record("2.0")))
    current = {
        **image_record("2.1"),
        "engine_architecture": "aarch64",
        "development_platform": "linux/arm64",
        "development_execution": "native",
    }
    assert not list(validator.iter_errors(current))


def test_full_pass_cannot_claim_unrun_development_and_v20_cannot_gain_v21_fields() -> None:
    validator = Draft202012Validator(load_schema("image-result"))
    current = {
        **image_record("2.1"),
        "engine_architecture": "aarch64",
        "development_platform": None,
        "development_execution": "not_run",
        "status": "passed",
        "error": None,
        "missing_checks": [],
    }
    assert list(validator.iter_errors(current))
    legacy = {**image_record("2.0"), "engine_architecture": "aarch64"}
    assert list(validator.iter_errors(legacy))


@pytest.mark.parametrize("phase", ["run", "cleanup"])
def test_unexpected_controller_failure_still_has_a_failed_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    output = tmp_path / "unexpected"

    def fail(self: Acceptance, skip_build: bool, host_url: str | None) -> None:
        if phase == "run":
            raise TypeError("synthetic_controller_failure")

    cleaned: list[bool] = []

    def cleanup(self: Acceptance) -> None:
        cleaned.append(True)
        if phase == "cleanup":
            raise TypeError("synthetic_controller_failure")

    monkeypatch.setattr(Acceptance, "run", fail)
    monkeypatch.setattr(Acceptance, "cleanup", cleanup)
    monkeypatch.setattr(
        sys, "argv", ["check_images", "--platform", "linux/arm64", "--out", str(output)]
    )
    try:
        code = main()
    except TypeError:
        code = None
    assert code == 1
    assert cleaned == [True]
    record = json.loads((output / "image-result.json").read_text())
    assert record["status"] == "failed"
    assert record["missing_checks"]
    assert "synthetic_controller_failure" in record["error"]
