"""Installed execution identity from an audited file/resource/import closure."""

from __future__ import annotations

import ast
import hashlib
import platform
import sys
from collections import deque
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, distribution
from importlib.resources import files
from pathlib import Path

from packaging.markers import default_environment
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

from anthropic_readiness.config import fingerprint, strings
from anthropic_readiness.diagnostics.core_contracts import validate_core
from anthropic_readiness.diagnostics.models import ImplementationIdentity
from anthropic_readiness.models import JsonObject, object_value, strict_json


@dataclass(frozen=True)
class DistributionInfo:
    version: str
    requirements: tuple[str, ...]


def _package_root() -> Path:
    return Path(str(files("anthropic_readiness")))


def _distribution_info(name: str) -> DistributionInfo:
    value = distribution(name)
    return DistributionInfo(value.version, tuple(value.requires or ()))


def _runtime_nodes(tree: ast.Module) -> list[ast.AST]:
    flags = {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "typing"
        for alias in node.names
        if alias.name == "TYPE_CHECKING"
    }
    rebound = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    } | {node.arg for node in ast.walk(tree) if isinstance(node, ast.arg)}
    flags -= rebound
    result: list[ast.AST] = []
    pending: list[ast.AST] = list(tree.body)
    while pending:
        node = pending.pop()
        result.append(node)
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id in flags:
            pending.extend(node.orelse)
        else:
            pending.extend(ast.iter_child_nodes(node))
    return result


def _module_paths(root: Path) -> dict[str, str]:
    paths: dict[str, str] = {}
    for path in root.rglob("*.py"):
        relative = path.relative_to(root).as_posix()
        parts = list(Path(relative).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        paths[".".join(("anthropic_readiness", *parts))] = relative
    return paths


def _imports(node: ast.AST, module: str, package: str) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    if any(alias.name == "*" for alias in node.names):
        raise ValueError("identity_wildcard_import:" + module)
    if node.level:
        parent = package.split(".")
        if node.level > len(parent):
            raise ValueError("identity_relative_import:" + module)
        base = ".".join(parent[: len(parent) - node.level + 1])
        imported = base + ("." + node.module if node.module else "")
    else:
        imported = node.module or ""
    return [imported, *(imported + "." + alias.name for alias in node.names)]


def _resource_template(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            part.value if isinstance(part, ast.Constant) and isinstance(part.value, str) else "{}"
            for part in node.values
        )
    return None


def _check_calls(nodes: list[ast.AST], relative: str, manifest: JsonObject) -> None:
    resources = set(strings(manifest["resources"]))
    patterns = object_value(manifest["resource_patterns"])
    permitted_patterns = set(strings(patterns.get(relative, [])))
    dynamic_loaders = set(strings(manifest["dynamic_schema_loaders"]))
    dynamic_imports = manifest["dynamic_imports"]
    assert isinstance(dynamic_imports, list)
    import_aliases = {"__import__"}
    code_aliases = {"eval", "exec", "compile"}
    builtins_aliases = {"builtins"}
    for node in nodes:
        if isinstance(node, ast.ImportFrom) and node.module == "importlib":
            import_aliases.update(
                a.asname or a.name for a in node.names if a.name == "import_module"
            )
        if isinstance(node, ast.Import):
            builtins_aliases.update(a.asname or a.name for a in node.names if a.name == "builtins")
        if isinstance(node, ast.ImportFrom) and node.module == "builtins":
            code_aliases.update(a.asname or a.name for a in node.names if a.name in code_aliases)
    for node in nodes:
        candidates: list[ast.AST] = []
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            candidates.append(node.right)
        if isinstance(node, ast.Call):
            function = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            code_call = isinstance(node.func, ast.Name) and function in code_aliases
            qualified_code_call = (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in builtins_aliases
                and function in {"eval", "exec", "compile"}
            )
            if code_call or qualified_code_call:
                raise ValueError("identity_dynamic_import:" + relative)
            if function in import_aliases or function == "import_module":
                target = _resource_template(node.args[0]) if node.args else None
                allowed = any(
                    object_value(entry)
                    == {"module": relative, "function": function, "target": target}
                    for entry in dynamic_imports
                )
                if (
                    not allowed
                    or target is None
                    or target.split(".")[0] not in sys.stdlib_module_names
                ):
                    raise ValueError("identity_dynamic_import:" + relative)
            if function == "joinpath":
                candidates.extend(node.args)
            if function in {"load_schema", "validate_core", "validate_operational"}:
                index = 0 if function == "load_schema" else 1
                argument = node.args[index] if len(node.args) > index else None
                name = _resource_template(argument) if argument is not None else None
                if name is not None and "{}" not in name:
                    candidates.append(ast.Constant(value=f"resources/schemas/{name}.schema.json"))
                elif relative not in dynamic_loaders:
                    raise ValueError("identity_dynamic_schema:" + relative)
        for candidate in candidates:
            template = _resource_template(candidate)
            if template is None or not template.startswith("resources/"):
                continue
            if "{}" in template:
                if template not in permitted_patterns:
                    raise ValueError("identity_unlisted_resource_pattern:" + relative)
            elif template not in resources:
                raise ValueError("identity_unlisted_resource:" + template)


def _closure(root: Path, manifest: JsonObject) -> tuple[set[str], set[str]]:
    paths = _module_paths(root)
    modules = set(strings(manifest["modules"]))
    external_map = object_value(manifest["external_modules"])
    roots = list(strings(manifest["roots"]))
    roots.extend(path for path in strings(manifest["optional_roots"]) if (root / path).exists())
    queue = deque(roots)
    visited: set[str] = set()
    external: set[str] = set()
    reverse = {value: key for key, value in paths.items()}
    while queue:
        relative = queue.popleft()
        if relative in visited:
            continue
        if relative not in modules:
            raise ValueError("identity_unlisted_module:" + relative)
        if relative not in reverse:
            raise ValueError("identity_missing_module:" + relative)
        visited.add(relative)
        source = root / relative
        if not source.resolve().is_relative_to(root.resolve()):
            raise ValueError("identity_module_path")
        try:
            tree = ast.parse(source.read_text())
        except (OSError, SyntaxError) as exc:
            raise ValueError("identity_module_invalid:" + relative) from exc
        nodes = _runtime_nodes(tree)
        _check_calls(nodes, relative, manifest)
        module = reverse[relative]
        package = module if relative.endswith("__init__.py") else module.rsplit(".", 1)[0]
        for node in nodes:
            for imported in _imports(node, module, package):
                top = imported.split(".")[0]
                if top == "anthropic_readiness":
                    if imported in paths:
                        queue.append(paths[imported])
                    elif isinstance(node, ast.Import):
                        raise ValueError("identity_missing_module:" + imported)
                    # Dotted parents execute their package initializers too.
                    parent = imported
                    while "." in parent:
                        parent = parent.rsplit(".", 1)[0]
                        if parent in paths:
                            queue.append(paths[parent])
                elif top and top not in sys.stdlib_module_names:
                    dependency = external_map.get(top)
                    if not isinstance(dependency, str):
                        raise ValueError("identity_unlisted_external_module:" + top)
                    external.add(dependency)
    return visited, external


def _dependencies(roots: set[str]) -> JsonObject:
    pending = deque(Requirement(name) for name in sorted(roots))
    versions: JsonObject = {}
    processed: dict[str, set[str]] = {}
    environment: dict[str, str] = {}
    for key, value in default_environment().items():
        if not isinstance(value, str):
            raise ValueError("identity_marker_environment")
        environment[key] = value
    while pending:
        requirement = pending.popleft()
        name = canonicalize_name(requirement.name)
        try:
            info = _distribution_info(name)
            parsed_version = Version(info.version)
        except PackageNotFoundError as exc:
            raise ValueError("identity_missing_distribution:" + name) from exc
        except InvalidVersion as exc:
            raise ValueError("identity_distribution_version:" + name) from exc
        if parsed_version not in requirement.specifier:
            raise ValueError("identity_distribution_version:" + name)
        extras = set(requirement.extras) | {""}
        if name in processed and extras <= processed[name]:
            continue
        processed.setdefault(name, set()).update(extras)
        versions[name] = info.version
        if len(versions) > 1024:
            raise ValueError("identity_dependency_limit")
        for raw in info.requirements:
            try:
                child = Requirement(raw)
            except InvalidRequirement as exc:
                raise ValueError("identity_distribution_requirement:" + name) from exc
            if child.marker is None or any(
                child.marker.evaluate({**environment, "extra": extra}) for extra in processed[name]
            ):
                if child.url is not None:
                    raise ValueError("identity_distribution_direct_url:" + name)
                pending.append(child)
    return dict(sorted(versions.items()))


def _identity_from_root(root: Path) -> ImplementationIdentity:
    manifest = object_value(strict_json((root / "resources/diagnostic-identity.json").read_text()))
    validate_core(manifest, "diagnostic-identity-manifest")
    modules, external = _closure(root, manifest)
    resources = set(strings(manifest["resources"]))
    for directory in strings(manifest["resource_roots"]):
        owned = root / directory
        if not owned.is_dir():
            raise ValueError("identity_missing_resource:" + directory)
        for path in owned.rglob("*"):
            if path.is_file() and path.relative_to(root).as_posix() not in resources:
                raise ValueError("identity_unlisted_resource:" + path.relative_to(root).as_posix())
    hashes: JsonObject = {}
    for relative in sorted(modules | resources):
        path = root / relative
        if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("identity_missing_resource:" + relative)
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    document: JsonObject = {
        "schema_version": "1.0",
        "semantic_revision": manifest["semantic_revision"],
        "python": {
            "implementation": platform.python_implementation(),
            "version": f"{sys.version_info.major}.{sys.version_info.minor}",
        },
        "file_hashes": hashes,
        "dependencies": _dependencies(external),
    }
    document["content_sha256"] = fingerprint(document)
    validate_core(document, "implementation-identity")
    return ImplementationIdentity(document)


def installed_identity() -> ImplementationIdentity:
    return _identity_from_root(_package_root())


def check_identity(
    expected: ImplementationIdentity, actual: ImplementationIdentity
) -> tuple[str, ...]:
    for value in (expected, actual):
        validate_core(value.document, "implementation-identity")
        body = {key: item for key, item in value.document.items() if key != "content_sha256"}
        if fingerprint(body) != value.document["content_sha256"]:
            raise ValueError("identity_digest")
    reasons = {
        "semantic_revision": "semantic_revision_changed",
        "python": "python_runtime_changed",
        "file_hashes": "implementation_files_changed",
        "dependencies": "dependency_versions_changed",
    }
    return tuple(
        reason
        for field, reason in reasons.items()
        if expected.document[field] != actual.document[field]
    )
