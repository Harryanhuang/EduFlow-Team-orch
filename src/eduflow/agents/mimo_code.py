"""Xiaomi MiMoCode adapter."""
from __future__ import annotations

import shlex

from .base import CliAdapter, MULTILINE_SUBMIT_KEYS, OPENAI_COMPAT_AUTH, SPINNER_CHARS


class MimoCodeAdapter(CliAdapter):
    def spawn_cmd(self, agent: str, model: str) -> str:
        args = [
            "mimo",
            "--trust",
            "--never-ask",
        ]
        if model:
            args.extend(["--model", model])
        return " ".join(
            [f"MIMO_AGENT={shlex.quote(agent)}"]
            + [shlex.quote(a) for a in args]
        )

    def ready_markers(self) -> list[str]:
        return [
            "MiMoCode",
            "Xiaomi",
            "❯",
        ]

    def busy_markers(self) -> list[str]:
        return [
            *SPINNER_CHARS,
            "Thinking",
            "Running",
            "Working",
            "Generating",
        ]

    def process_name(self) -> str:
        return "mimo"

    def submit_keys(self) -> list[str]:
        return list(MULTILINE_SUBMIT_KEYS)

    def rate_limit_markers(self) -> list[str]:
        return [
            "rate limit",
            "quota exceeded",
            "429",
            "too many requests",
        ]

    def auth_slots(self):
        return OPENAI_COMPAT_AUTH
