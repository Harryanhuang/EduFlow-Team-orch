"""`eduflow version` — print the installed package version.

Reads version from the installed distribution metadata (set in
pyproject.toml `[project] version`). Useful in shell scripts:

    if [ "$(eduflow version)" != "0.1.0" ]; then ...

and in smoke conductors that want to assert they're testing the
checkout they think they're testing.
"""
from __future__ import annotations

import json

from eduflow._build_info import BUILD_REVISION
from eduflow.util import maybe_print_help


def _read_version() -> str:
    """Read installed-distribution version with two fallbacks:

    1. `importlib.metadata.version("eduflow")` — what `pip install -e .`
       and `pyproject.toml` set up.
    2. Hardcoded "0.0.0+unknown" — if the package somehow isn't on
       sys.path under that name (e.g. running directly from src/ in
       a fresh venv before `pip install -e`).
    """
    try:
        from importlib.metadata import version, PackageNotFoundError
        return version("eduflow")
    except (PackageNotFoundError, ImportError):
        return "0.0.0+unknown"


def _read_dependency_version(name: str) -> str:
    try:
        from importlib.metadata import version
        return version(name)
    except Exception:
        return "unknown"


def _read_revision() -> str:
    """Return the revision embedded while the installed wheel was built."""
    return BUILD_REVISION


def main(argv: list[str]) -> int:
    if maybe_print_help(argv, "usage: eduflow version"):
        return 0
    if argv == ["--json"]:
        print(json.dumps({
            "eduflow": _read_version(),
            "flow_memory": _read_dependency_version("flow-memory"),
            "revision": _read_revision(),
        }, sort_keys=True))
        return 0
    print(_read_version())
    return 0
