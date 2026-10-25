"""Identity for packaged UI resources, independent of endpoint or stored run data."""

import hashlib
from dataclasses import dataclass
from importlib.resources import files
from importlib.resources.abc import Traversable


@dataclass(frozen=True)
class UIAssets:
    revision: str
    versions: dict[str, str]

    def url(self, path: str) -> str:
        return f"/assets/{path}?v={self.versions[path]}"


def load_ui_assets() -> UIAssets:
    root = files("anthropic_readiness").joinpath("resources")
    content: dict[str, bytes] = {}

    def collect(directory: Traversable, prefix: str) -> None:
        for entry in sorted(directory.iterdir(), key=lambda item: item.name):
            path = prefix + entry.name
            if entry.is_dir():
                collect(entry, path + "/")
            elif entry.name.endswith((".html", ".css", ".js", ".svg", ".json")):
                content[path] = entry.read_bytes()

    collect(root.joinpath("web"), "web/")
    collect(root.joinpath("locales"), "locales/")
    content["themes.css"] = root.joinpath("themes.css").read_bytes()
    digest = hashlib.sha256()
    for path, value in sorted(content.items()):
        digest.update(path.encode() + b"\0" + value + b"\0")
    return UIAssets(
        revision=digest.hexdigest(),
        versions={path: hashlib.sha256(value).hexdigest() for path, value in content.items()},
    )
