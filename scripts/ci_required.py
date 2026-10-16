"""Fail the aggregate CI check unless every required child actually succeeded."""

import argparse
import json
import os
from collections.abc import Sequence


def required_jobs_pass(needs: object, required: Sequence[str]) -> bool:
    if not isinstance(needs, dict) or not required:
        return False
    return all(
        isinstance(needs.get(name), dict) and needs[name].get("result") == "success"
        for name in required
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--required", nargs="+", required=True)
    args = parser.parse_args()
    return (
        0
        if required_jobs_pass(json.loads(os.environ.get("NEEDS_JSON", "{}")), args.required)
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
