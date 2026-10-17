"""Verify target runtime images with native developer tooling and explicit evidence."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EnvironmentUnavailable(RuntimeError):
    """A required tool/platform could not execute; this is not an assertion PASS."""


def assess_image_checks(
    records: list[dict[str, object]], targets: tuple[str, ...], scope: str
) -> tuple[str, list[str]]:
    """Require each selected image's own observations rather than CLI-only success."""
    required: set[str] = {"engine-architecture"}
    if "runtime" in targets:
        required.update(
            {
                "image-inspect",
                "default-nonroot",
                "runtime-help",
                "replay-valid",
                "replay-duplicate-start",
            }
        )
        if scope == "full":
            required.update({"isolated-peer", "host-path", "signal-wait-INT", "signal-wait-TERM"})
    if "web" in targets:
        required.update(
            {
                "web-image-inspect",
                "web-default-nonroot",
                "web-pages",
                "web-assessment",
                "web-exports",
            }
        )
        if scope == "full":
            required.update({"web-volume-restart", "web-cancellation", "web-host-path"})
    if scope == "full":
        required.add("dev-offline-full")
    observed = {str(record["id"]) for record in records if record["status"] == "passed"}
    missing = sorted(required - observed)
    if any(record["status"] == "failed" for record in records):
        return "failed", missing
    if missing or not required or any(record["status"] == "blocked" for record in records):
        return "blocked", missing
    return "passed", []


def context_hash(root: Path) -> str:
    digest = hashlib.sha256()
    paths = [
        root / name
        for name in (
            "Dockerfile",
            "pyproject.toml",
            "uv.lock",
            ".dockerignore",
            ".python-version",
            "package.json",
            "package-lock.json",
            "compose.yaml",
            ".devcontainer/devcontainer.json",
            "docs/harness/web-toolchain.json",
        )
        if (root / name).is_file()
    ]
    paths.extend(
        p for p in (root / "src").rglob("*") if p.is_file() and "__pycache__" not in p.parts
    )
    for path in sorted(paths):
        digest.update(
            path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes() + b"\0"
        )
    return digest.hexdigest()


def wait_file(path: Path, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while not path.exists():
        if time.monotonic() >= deadline:
            raise RuntimeError("synthetic_peer_timeout:" + path.name)
        time.sleep(0.1)


class Acceptance:
    def __init__(
        self,
        output: Path,
        target_platform: str,
        scope: str,
        targets: tuple[str, ...] = ("runtime", "web"),
    ) -> None:
        self.output = output
        self.platform = target_platform
        self.scope = scope
        self.engine_architecture: str | None = None
        self.native_platform: str | None = None
        self.development_platform: str | None = None
        self.image_context = context_hash(ROOT)
        self.records: list[dict[str, object]] = []
        self.runtime = "anthropic-readiness-runtime:" + target_platform.split("/")[1]
        self.dev = "anthropic-readiness-dev:unselected"
        self.web = "anthropic-readiness-web:" + target_platform.split("/")[1]
        self.targets = targets
        self.token = "readiness-" + uuid.uuid4().hex[:12]
        self.web_network = self.token + "-web"
        self.containers: list[str] = []
        self.volumes: list[str] = []
        self.extra_networks: list[str] = []
        self.peer_state = output / "peer"
        self.peer_host_url = ""
        self.network_created = False
        self.sequence = 0

    def command(self, label: str, argv: list[str], expected: int = 0, timeout: float = 120) -> str:
        self.sequence += 1
        log = self.output / f"{self.sequence:02}-{label}.log"
        started = datetime.now(UTC).isoformat()
        print(label + ": started", flush=True)
        try:
            with log.open("w") as stream:
                result = subprocess.run(
                    argv,
                    cwd=ROOT,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    check=False,
                    timeout=timeout,
                )
            passed = result.returncode == expected
            unavailable = not passed and any(
                text in log.read_text().lower()
                for text in (
                    "exec format error",
                    "no matching manifest for",
                    "cannot connect to the docker daemon",
                )
            )
            self.records.append(
                {
                    "id": label,
                    "status": "passed" if passed else "blocked" if unavailable else "failed",
                    "expected_exit": expected,
                    "actual_exit": result.returncode,
                    "started_at": started,
                    "log": log.name,
                    "argv": argv,
                }
            )
            print(label + (": passed" if passed else ": failed"), flush=True)
            if not passed:
                if unavailable:
                    raise EnvironmentUnavailable(label + ": see " + str(log))
                raise RuntimeError(label + ": see " + str(log))
        except (OSError, subprocess.TimeoutExpired) as exc:
            self.records.append(
                {"id": label, "status": "blocked", "reason": type(exc).__name__, "log": log.name}
            )
            raise
        return log.read_text()

    def docker(self, label: str, args: list[str], expected: int = 0, timeout: float = 120) -> str:
        return self.command(label, ["docker", *args], expected, timeout)

    def runtime_args(self, network: str = "none") -> list[str]:
        return [
            "run",
            "--rm",
            "--platform",
            self.platform,
            "--read-only",
            "--tmpfs",
            "/tmp:rw,nosuid,noexec,size=64m",
            "--network",
            network,
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "-v",
            f"{self.output}:/output",
            "-v",
            f"{ROOT / 'tests/fixtures'}:/fixtures:ro",
            "-v",
            f"{ROOT / 'examples'}:/examples:ro",
        ]

    def run(self, skip_build: bool, host_url: str | None) -> None:
        commit = self.command("git-commit", ["git", "rev-parse", "HEAD"]).strip()
        self.engine_architecture = (
            self.docker("engine-architecture", ["info", "--format", "{{.Architecture}}"]).strip()
            or None
        )
        self.native_platform = {
            "aarch64": "linux/arm64",
            "arm64": "linux/arm64",
            "x86_64": "linux/amd64",
            "amd64": "linux/amd64",
        }.get(self.engine_architecture or "")
        if self.native_platform is None:
            raise EnvironmentUnavailable("docker_engine_architecture_unavailable")
        if self.scope == "full":
            self.development_platform = self.native_platform
            self.dev = "anthropic-readiness-dev:" + self.native_platform.split("/")[1]
        if not skip_build:
            targets = [(target, getattr(self, target), self.platform) for target in self.targets]
            if self.scope == "full":
                targets.append(("dev", self.dev, self.native_platform))
            for target, tag, selected_platform in targets:
                self.docker(
                    "build-" + target,
                    [
                        "buildx",
                        "build",
                        "--platform",
                        selected_platform,
                        "--target",
                        target,
                        "--load",
                        "--build-arg",
                        "VCS_REF=" + commit,
                        "--build-arg",
                        "IMAGE_CONTEXT_SHA=" + context_hash(ROOT),
                        "-t",
                        tag,
                        ".",
                    ],
                    timeout=7200,
                )
        if "runtime" in self.targets:
            self.run_runtime()
        if self.scope == "full":
            self.run_development()
        if "web" in self.targets or self.scope == "full":
            self.start_peer()
        if "runtime" in self.targets and self.scope == "full":
            self.run_cli_live(host_url or self.peer_host_url + "/cases")
        if "web" in self.targets:
            from scripts.web_image_checks import run_web_checks

            run_web_checks(self, host_url or self.peer_host_url + "/cases")

    def run_runtime(self) -> None:
        image = json.loads(
            self.docker(
                "image-inspect", ["image", "inspect", self.runtime, "--format", "{{json .}} "]
            )
        )
        if (
            image["Config"]["Labels"].get("io.anthropic-readiness.image-context")
            != self.image_context
        ):
            raise RuntimeError("runtime_image_context_mismatch")
        self.docker(
            "default-nonroot",
            [
                "run",
                "--rm",
                "--platform",
                self.platform,
                "--network",
                "none",
                "--read-only",
                "--entrypoint",
                "python",
                self.runtime,
                "-c",
                'import os,shutil,importlib.util; assert os.getuid()==10001; assert not any(shutil.which(x) for x in ("uv","git","node","npm","chromium","pytest")); assert all(importlib.util.find_spec(x) is None for x in ("pytest","fastapi","uvicorn")); assert not os.path.exists("/build"); print(os.getuid())',
            ],
        )
        self.docker(
            "runtime-os-packages",
            [
                "run",
                "--rm",
                "--platform",
                self.platform,
                "--network",
                "none",
                "--read-only",
                "--entrypoint",
                "dpkg-query",
                self.runtime,
                "-W",
                "-f=${Package}	${Version}\n",
            ],
        )
        self.docker(
            "runtime-python-packages",
            [
                "run",
                "--rm",
                "--platform",
                self.platform,
                "--network",
                "none",
                "--read-only",
                "--entrypoint",
                "python",
                self.runtime,
                "-c",
                'import json,platform; from importlib.metadata import distributions; print(json.dumps({"python":platform.python_version(),"packages":{d.metadata["Name"]:d.version for d in distributions()}},sort_keys=True))',
            ],
        )
        self.docker("runtime-help", [*self.runtime_args(), self.runtime, "--help"])
        target = "/examples/target.yaml"
        for name, expected in [("valid", 0), ("duplicate-start", 1)]:
            capture = (
                f"/fixtures/captures/{name}/evidence/ANT-TEXT-SSE-001/fixture-attempt/response.json"
            )
            self.docker(
                "replay-" + name,
                [
                    *self.runtime_args(),
                    self.runtime,
                    "replay",
                    "--target",
                    target,
                    "--capture",
                    capture,
                    "--case",
                    "ANT-TEXT-SSE-001",
                    "--out",
                    "/output/" + name,
                ],
                expected,
            )
            self.verify_output(name)

    def prepare_browser_cache(self) -> str:
        if self.development_platform is None:
            raise EnvironmentUnavailable("development_platform_unselected")
        toolchain = json.loads((ROOT / "docs/harness/web-toolchain.json").read_text())
        revision = str(
            next(
                item["revision"]
                for item in toolchain["selected_browsers"]
                if item["name"] == "chromium"
            )
        )
        if not revision.isascii() or not revision.isdecimal():
            raise ValueError("invalid_browser_revision")
        name = (
            "anthropic-readiness-playwright-"
            + self.development_platform.split("/")[1]
            + "-"
            + revision
        )
        labels = {
            "io.anthropic-readiness.kind": "browser-cache",
            "io.anthropic-readiness.platform": self.development_platform,
            "io.anthropic-readiness.revision": revision,
        }
        flags = [value for key, value in labels.items() for value in ("--label", key + "=" + value)]
        self.docker("dev-browser-cache-create", ["volume", "create", *flags, name])
        record = json.loads(
            self.docker(
                "dev-browser-cache-inspect", ["volume", "inspect", name, "--format", "{{json .}} "]
            )
        )
        actual = record.get("Labels") or {}
        if any(actual.get(key) != value for key, value in labels.items()):
            raise EnvironmentUnavailable("browser_cache_identity_mismatch")
        self.docker(
            "dev-browser-cache-owner",
            [
                "run",
                "--rm",
                "--platform",
                self.development_platform,
                "--network",
                "none",
                "--user",
                "0",
                "-v",
                name + ":/cache",
                "--entrypoint",
                "sh",
                self.dev,
                "-c",
                'chown -R "$(id -u developer):$(id -g developer)" /cache',
            ],
        )
        return name

    def run_development(self) -> None:
        if self.development_platform is None:
            raise EnvironmentUnavailable("development_platform_unselected")
        browser_cache = self.prepare_browser_cache()
        # The disposable dev environment is retained for the offline verification.
        name = self.token + "-dev"
        self.containers.append(name)
        image = json.loads(
            self.docker(
                "dev-image-inspect", ["image", "inspect", self.dev, "--format", "{{json .}} "]
            )
        )
        if image.get("Architecture") != self.development_platform.split("/")[1]:
            raise RuntimeError("development_image_platform_mismatch")
        self.docker(
            "dev-os-packages",
            [
                "run",
                "--rm",
                "--platform",
                self.development_platform,
                "--network",
                "none",
                self.dev,
                "dpkg-query",
                "-W",
                "-f=${Package}	${Version}\n",
            ],
        )
        self.docker(
            "dev-start",
            [
                "run",
                "-d",
                "--name",
                name,
                "--platform",
                self.development_platform,
                "-v",
                f"{ROOT}:/workspaces/anthropic-readiness",
                "-v",
                browser_cache + ":/home/developer/.cache/ms-playwright",
                self.dev,
            ],
        )
        self.docker(
            "dev-sync",
            [
                "exec",
                name,
                "env",
                "UV_HTTP_TIMEOUT=600",
                "UV_HTTP_RETRIES=5",
                "uv",
                "sync",
                "--locked",
            ],
            timeout=7200,
        )
        self.docker(
            "dev-frontend-prepare",
            [
                "exec",
                name,
                "sh",
                "-c",
                "npm ci --ignore-scripts && npx --no-install playwright install chromium",
            ],
            timeout=7200,
        )
        self.docker("dev-isolate", ["network", "disconnect", "bridge", name])
        networks = self.docker(
            "dev-network-inspect",
            ["inspect", name, "--format", "{{json .NetworkSettings.Networks}}"],
        )
        if json.loads(networks):
            raise RuntimeError("dev_network_not_isolated")
        self.docker(
            "dev-offline-full",
            [
                "exec",
                name,
                "env",
                "UV_OFFLINE=1",
                "uv",
                "run",
                "--frozen",
                "python",
                "scripts/check.py",
                "--suite",
                "full",
            ],
            timeout=1800,
        )

    def start_peer(self) -> None:
        binding = "127.0.0.1"
        if platform.system() == "Linux":
            value = self.docker(
                "host-gateway-resolve",
                [
                    "run",
                    "--rm",
                    "--platform",
                    self.platform,
                    "--network",
                    "bridge",
                    "--add-host",
                    "host.docker.internal:host-gateway",
                    "--entrypoint",
                    "python",
                    self.runtime if "runtime" in self.targets else self.web,
                    "-c",
                    "import socket; print(socket.gethostbyname('host.docker.internal'))",
                ],
            ).strip()
            try:
                address = ipaddress.ip_address(value)
            except ValueError as exc:
                raise EnvironmentUnavailable("private_host_gateway_unavailable") from exc
            if (
                not isinstance(address, ipaddress.IPv4Address)
                or not address.is_private
                or address.is_loopback
                or address.is_unspecified
                or address.is_multicast
            ):
                raise EnvironmentUnavailable("private_host_gateway_required")
            binding = str(address)
        self.docker("network-create", ["network", "create", "--internal", self.token])
        self.network_created = True
        self.extra_networks.append(self.web_network)
        self.docker("web-network-create", ["network", "create", self.web_network])
        state = self.output / "peer"
        state.mkdir()
        peer = self.token + "-peer"
        self.containers.append(peer)
        self.docker(
            "peer-start",
            [
                *self.runtime_args(self.token)[:1],
                "-d",
                "--name",
                peer,
                "--network",
                self.web_network,
                "--network-alias",
                "synthetic-peer",
                "-p",
                binding + "::8080",
                "--platform",
                self.platform,
                "--read-only",
                "--tmpfs",
                "/tmp:rw,nosuid,noexec,size=64m",
                "--user",
                f"{os.getuid()}:{os.getgid()}",
                "-v",
                f"{ROOT / 'tests/fixtures'}:/fixtures:ro",
                "-v",
                f"{state}:/state",
                "--entrypoint",
                "python",
                self.runtime if "runtime" in self.targets else self.web,
                "/fixtures/http/server.py",
                "--fixtures",
                "/fixtures",
                "--state",
                "/state",
            ],
        )
        wait_file(state / "ready")
        self.docker(
            "peer-internal-connect",
            ["network", "connect", "--alias", "synthetic-peer", self.token, peer],
        )
        host_port = (
            self.docker("peer-published-port", ["port", peer, "8080/tcp"]).strip().split(":")[-1]
        )
        self.peer_host_url = "http://host.docker.internal:" + host_port

    def run_cli_live(self, host_url: str) -> None:
        state = self.peer_state
        self.synthetic_run("isolated-peer", "http://synthetic-peer:8080/cases", self.token)
        for sig, expected in [("INT", 130), ("TERM", 143)]:
            (state / "request").unlink(missing_ok=True)
            target_path = self.output / ("signal-" + sig + ".yaml")
            target_path.write_text(
                (ROOT / "examples/target.yaml")
                .read_text()
                .replace("http://127.0.0.1:8000/v1/messages", "http://synthetic-peer:8080/pings")
            )
            tester = self.token + "-" + sig.lower()
            self.containers.append(tester)
            args = self.runtime_args(self.token)
            args.remove("--rm")
            self.docker(
                "signal-start-" + sig,
                [
                    *args[:1],
                    "-d",
                    "--name",
                    tester,
                    *args[1:],
                    self.runtime,
                    "run",
                    "--target",
                    "/output/" + target_path.name,
                    "--allow-live",
                    "--out",
                    "/output/signal-" + sig,
                ],
            )
            wait_file(state / "request")
            self.docker("signal-send-" + sig, ["kill", "--signal", sig, tester])
            actual = self.docker("signal-wait-" + sig, ["wait", tester]).strip()
            if actual != str(expected):
                raise RuntimeError("signal_exit:" + sig + ":" + actual)
            self.verify_output("signal-" + sig)
            document = json.loads((self.output / ("signal-" + sig) / "result.json").read_text())
            if document["execution_environment"]["interruption"] != expected - 128:
                raise RuntimeError("signal_partial_record")
        self.synthetic_run("host-path", host_url, "bridge")

    def synthetic_run(self, name: str, url: str, network: str) -> None:
        path = self.output / (name + ".yaml")
        path.write_text(
            (ROOT / "examples/target.yaml")
            .read_text()
            .replace("http://127.0.0.1:8000/v1/messages", url)
        )
        self.docker(
            name,
            [
                *self.runtime_args(network),
                *(
                    ["--add-host", "host.docker.internal:host-gateway"]
                    if network == "bridge" and platform.system() == "Linux"
                    else []
                ),
                self.runtime,
                "run",
                "--target",
                "/output/" + path.name,
                "--allow-live",
                "--out",
                "/output/" + name,
            ],
        )
        self.verify_output(name)
        document = json.loads((self.output / name / "result.json").read_text())
        if document["plan"]["actual_requests"] != 3:
            raise RuntimeError("synthetic_request_accounting")

    def verify_output(self, name: str) -> None:
        for file in ("result.json", "report.html", "report.md", "report-manifest.json"):
            if not (self.output / name / file).is_file():
                raise RuntimeError("missing_persisted_output:" + name + ":" + file)
        self.records.append({"id": "persisted-" + name, "status": "passed"})

    def cleanup(self) -> None:
        for name in reversed(self.containers):
            subprocess.run(
                ["docker", "rm", "-f", name], capture_output=True, check=False, timeout=30
            )
        for name in reversed(self.extra_networks):
            subprocess.run(
                ["docker", "network", "rm", name], capture_output=True, check=False, timeout=30
            )
        if self.network_created:
            subprocess.run(
                ["docker", "network", "rm", self.token],
                capture_output=True,
                check=False,
                timeout=30,
            )
        for name in reversed(self.volumes):
            subprocess.run(
                ["docker", "volume", "rm", name], capture_output=True, check=False, timeout=30
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=["linux/amd64", "linux/arm64"], required=True)
    parser.add_argument("--scope", choices=["smoke", "full"], default="full")
    parser.add_argument(
        "--targets", default="runtime,web", help="Comma-separated runtime,web image targets"
    )
    parser.add_argument(
        "--skip-build", action="store_true", help="Debug only; uses existing local image tags"
    )
    parser.add_argument(
        "--host-url", help="Explicit generic synthetic server URL; never a real target"
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    targets = tuple(args.targets.split(","))
    if not targets or len(set(targets)) != len(targets) or set(targets) - {"runtime", "web"}:
        parser.error("--targets requires unique runtime,web names")
    output = (
        args.out
        or ROOT / "artifacts/images" / (str(time.time_ns()) + "-" + args.platform.split("/")[1])
    ).resolve()
    output.mkdir(parents=True, exist_ok=False)
    acceptance = Acceptance(output, args.platform, args.scope, targets)
    started = datetime.now(UTC).isoformat()
    before = context_hash(ROOT)
    error: str | None = None
    unavailable = False
    try:
        acceptance.run(args.skip_build, args.host_url)
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError, KeyError) as exc:
        error = str(exc)
        unavailable = isinstance(exc, (OSError, subprocess.TimeoutExpired, EnvironmentUnavailable))
        print(error)
    finally:
        acceptance.cleanup()
    unchanged = before == context_hash(ROOT)
    status, missing = assess_image_checks(acceptance.records, targets, args.scope)
    if error is not None:
        status = "blocked" if unavailable else "failed"
    if not unchanged:
        status = "failed"
    if args.skip_build and status == "passed":
        status = "blocked"
        missing.append("build_not_observed_debug_only")
    payload = {
        "schema_version": "2.1",
        "targets": list(targets),
        "missing_checks": missing,
        "scope": args.scope,
        "platform": args.platform,
        "host_machine": platform.machine(),
        "engine_architecture": acceptance.engine_architecture,
        "execution": "native" if acceptance.native_platform == args.platform else "emulated",
        "development_platform": acceptance.development_platform,
        "development_execution": "native"
        if any(row["id"] == "dev-start" and row["status"] == "passed" for row in acceptance.records)
        else "not_run",
        "started_at": started,
        "finished_at": datetime.now(UTC).isoformat(),
        "image_context_fingerprint": before,
        "source_unchanged": unchanged,
        "skip_build": args.skip_build,
        "status": status,
        "error": error,
        "checks": acceptance.records,
    }
    (output / "image-result.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(str(output / "image-result.json"))
    return {"passed": 0, "failed": 1, "blocked": 2}[status]


if __name__ == "__main__":
    # Preserve the documented direct-script entry while sharing stdlib-only modules.
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
