"""Moonshot Kimi Code adapter."""
from __future__ import annotations

import shlex

from .base import CliAdapter, MULTILINE_SUBMIT_KEYS, SPINNER_CHARS


class KimiCodeAdapter(CliAdapter):
    def spawn_cmd(self, agent: str, model: str) -> str:
        return f"DISABLE_UPDATE_CHECK=1 KIMI_AGENT={shlex.quote(agent)} kimi --yolo"

    def ready_markers(self) -> list[str]:
        return [
            "Welcome to Kimi Code CLI",
            "Send /help for help information",
            "── input",
            "context:",
        ]

    def busy_markers(self) -> list[str]:
        return [*SPINNER_CHARS, "Thinking", "Using Shell", "Booting"]

    def process_name(self) -> str:
        return "kimi"

    def submit_keys(self) -> list[str]:
        return list(MULTILINE_SUBMIT_KEYS)

    def rate_limit_markers(self) -> list[str]:
        return ["rate limit", "429", "quota exceeded"]
