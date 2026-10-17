"""Prepare the frozen official Linux Node archive for CI; run before offline checks."""

import hashlib
import json
import os
import platform
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    lock = json.loads((root / "docs/harness/web-toolchain.json").read_text())
    architecture = {"x86_64": "x64", "aarch64": "arm64"}[platform.machine()]
    archive = lock["archives"][architecture]
    destination = Path(os.environ["RUNNER_TEMP"]) / "readiness-node"
    destination.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="readiness-node-") as temporary:
        path = Path(temporary) / "node.tar.xz"
        urllib.request.urlretrieve(archive["url"], path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != archive["sha256"]:
            raise ValueError("node_archive_hash_mismatch")
        # Python 3.11 supports filter= via its maintained security backport.
        with tarfile.open(path) as source:
            source.extractall(destination, filter="data")
    binary = next(destination.glob("node-*/bin"))
    env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ["PATH"])
    with Path(os.environ["GITHUB_PATH"]).open("a") as output:
        output.write(str(binary) + "\n")
    subprocess.run([str(binary / "npm"), "ci", "--ignore-scripts"], cwd=root, env=env, check=True)


if __name__ == "__main__":
    main()
