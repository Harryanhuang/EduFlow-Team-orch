"""Hermes Agent CLI adapter.

Hermes is a Knowledge Steward lane, not a generic coding worker. The
runtime may switch Hermes-compatible models, but the CLI base must remain
`hermes-agent`.
"""
from __future__ import annotations

import shlex
import shutil

from .base import CliAdapter, MULTILINE_SUBMIT_KEYS, SPINNER_CHARS


HERMES_WORKDIR = "/Volumes/Halobster/Obsidian Edu"


class HermesAgentAdapter(CliAdapter):
    def spawn_cmd(self, agent: str, model: str) -> str:
        hermes_bin = shutil.which("hermes") or "hermes"
        args = [hermes_bin, "chat", "--cli"]
        if model:
            args.extend(["--model", model])
        command = " ".join(shlex.quote(a) for a in args)
        command += ' --provider "${HERMES_PROVIDER:-minimax}"'
        args = []
        args.extend(["--source", f"eduflow-{agent.lower()}"])
        if args:
            command += " " + " ".join(shlex.quote(a) for a in args)
        return f"cd {shlex.quote(HERMES_WORKDIR)} && {command}"

    def ready_markers(self) -> list[str]:
        return [
            "Hermes Agent",
            "hermes>",
            "Ready",
            "欢迎！输入你的问题",
            "⚕ ❯",
            "❯",
        ]

    def busy_markers(self) -> list[str]:
        return [
            *SPINNER_CHARS,
            "Thinking",
            "Running tool",
            "Working",
        ]

    def process_name(self) -> str:
        return "hermes"

    def submit_keys(self) -> list[str]:
        return list(MULTILINE_SUBMIT_KEYS)

    def rate_limit_markers(self) -> list[str]:
        return [
            "rate limit",
            "quota exceeded",
            "429",
            "too many requests",
        ]
