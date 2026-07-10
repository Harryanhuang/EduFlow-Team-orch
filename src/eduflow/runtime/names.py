"""Shared validation for agent and model names."""
from __future__ import annotations

import re

VALID_AGENT_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")
VALID_MODEL_NAME_RE = re.compile(r"^[A-Za-z0-9_\-.]+$")


class InvalidNameError(ValueError):
    pass


def validate_agent_name(name: str) -> str:
    if not isinstance(name, str) or not VALID_AGENT_NAME_RE.match(name):
        raise InvalidNameError(f"invalid agent name: {name!r}")
    return name


def validate_model_name(name: str) -> str:
    if not isinstance(name, str) or not VALID_MODEL_NAME_RE.match(name):
        raise InvalidNameError(f"invalid model name: {name!r}")
    return name
