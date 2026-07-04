"""Deterministic loop verification specs."""
from __future__ import annotations

import copy


SPECS = {
    "code-repair": {
        "name": "code-repair",
        "allowed_stages": {"builder"},
        "commands": [
            ["pytest", "-q"],
            ["python3", "-m", "compileall", "-q", "src"],
        ],
    },
}


def resolve(name: str) -> dict:
    try:
        return copy.deepcopy(SPECS[str(name or "").strip()])
    except KeyError:
        raise ValueError(f"unknown loop spec: {name}") from None
