"""Build and verify one architecture locally, retaining honest image evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def context_hash(root: Path) -> str:
    digest = hashlib.sha256()
    paths = [root / name for name in ("Dockerfile", "pyproject.toml", "uv.lock", ".dockerignore")]
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
    def __init__(self, output: Path, target_platform: str, scope: str) -> None:
        self.output = output
        self.platform = target_platform
        self.scope = scope
        self.records: list[dict[str, object]] = []
        self.runtime = "anthropic-readiness-runtime:" + target_platform.split("/")[1]
        self.dev = "anthropic-readiness-dev:" + target_platform.split("/")[1]
        self.token = "readiness-" + uuid.uuid4().hex[:12]
        self.containers: list[str] = []
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
            self.records.append(
                {
                    "id": label,
                    "status": "passed" if passed else "failed",
                    "expected_exit": expected,
                    "actual_exit": result.returncode,
                    "started_at": started,
                    "log": log.name,
                    "argv": argv,
                }
            )
            print(label + (": passed" if passed else ": failed"), flush=True)
            if not passed:
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
        if not skip_build:
            targets = [("runtime", self.runtime)]
            if self.scope == "full":
                targets.append(("dev", self.dev))
            for target, tag in targets:
                self.docker(
                    "build-" + target,
                    [
                        "buildx",
                        "build",
                        "--platform",
                        self.platform,
                        "--target",
                        target,
                        "--load",
                        "--build-arg",
                        "VCS_REF=" + commit,
                        "-t",
                        tag,
                        ".",
                    ],
                    timeout=7200,
                )
        self.docker("image-inspect", ["image", "inspect", self.runtime, "--format", "{{json .}}"])
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
                'import os,shutil,importlib.util; assert os.getuid()==10001; assert not any(shutil.which(x) for x in ("uv","git","pytest")); assert importlib.util.find_spec("pytest") is None; assert not os.path.exists("/build"); print(os.getuid())',
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
        if self.scope != "full":
            return
        # The disposable dev environment is retained for the offline verification.
        name = self.token + "-dev"
        self.containers.append(name)
        self.docker("dev-image-inspect", ["image", "inspect", self.dev, "--format", "{{json .}}"])
        self.docker(
            "dev-os-packages",
            [
                "run",
                "--rm",
                "--platform",
                self.platform,
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
                self.platform,
                "-v",
                f"{ROOT}:/workspaces/anthropic-readiness",
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
        self.docker("network-create", ["network", "create", "--internal", self.token])
        self.network_created = True
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
                self.token,
                "--network-alias",
                "synthetic-peer",
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
                self.runtime,
                "/fixtures/http/server.py",
                "--fixtures",
                "/fixtures",
                "--state",
                "/state",
            ],
        )
        wait_file(state / "ready")
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
        if host_url:
            self.synthetic_run("host-path", host_url, "bridge")
        else:
            self.records.append(
                {"id": "host-path", "status": "not_run", "reason": "no_explicit_host_url"}
            )

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
        if self.network_created:
            subprocess.run(
                ["docker", "network", "rm", self.token],
                capture_output=True,
                check=False,
                timeout=30,
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=["linux/amd64", "linux/arm64"], required=True)
    parser.add_argument("--scope", choices=["smoke", "full"], default="full")
    parser.add_argument(
        "--skip-build", action="store_true", help="Debug only; uses existing local image tags"
    )
    parser.add_argument(
        "--host-url", help="Explicit generic synthetic server URL; never a real target"
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    output = (
        args.out
        or ROOT / "artifacts/images" / (str(time.time_ns()) + "-" + args.platform.split("/")[1])
    ).resolve()
    output.mkdir(parents=True, exist_ok=False)
    acceptance = Acceptance(output, args.platform, args.scope)
    started = datetime.now(UTC).isoformat()
    before = context_hash(ROOT)
    error: str | None = None
    try:
        acceptance.run(args.skip_build, args.host_url)
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError, KeyError) as exc:
        error = str(exc)
        print(error)
    finally:
        acceptance.cleanup()
    unchanged = before == context_hash(ROOT)
    passed = error is None and unchanged
    payload = {
        "schema_version": "1.0",
        "scope": args.scope,
        "platform": args.platform,
        "host_machine": platform.machine(),
        "execution": "native"
        if (platform.machine() in {"arm64", "aarch64"}) == args.platform.endswith("arm64")
        else "emulated",
        "started_at": started,
        "finished_at": datetime.now(UTC).isoformat(),
        "image_context_fingerprint": before,
        "source_unchanged": unchanged,
        "skip_build": args.skip_build,
        "status": "passed" if passed else "failed",
        "error": error,
        "checks": acceptance.records,
    }
    (output / "image-result.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(str(output / "image-result.json"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
