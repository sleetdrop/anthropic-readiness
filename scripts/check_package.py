"""Compare the wheel's resource inventory and bytes with the checked source."""

import argparse
import zipfile
from pathlib import Path


def verify_wheel_resources(wheel: Path, root: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(wheel) as archive:
        for source in (root / "src/anthropic_readiness/resources").rglob("*"):
            if not source.is_file() or source.name == ".DS_Store":
                continue
            name = (
                "anthropic_readiness/"
                + source.relative_to(root / "src/anthropic_readiness").as_posix()
            )
            if name not in archive.namelist():
                errors.append("missing_resource:" + name)
            elif archive.read(name) != source.read_bytes():
                errors.append("resource_content_mismatch:" + name)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = verify_wheel_resources(args.wheel, args.root)
    print("\n".join(errors) if errors else "wheel_resources: passed")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
