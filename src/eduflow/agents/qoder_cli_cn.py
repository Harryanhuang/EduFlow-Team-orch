"""Qoder CLI CN adapter."""
from __future__ import annotations

import shlex
import shutil

from .base import CliAdapter, MULTILINE_SUBMIT_KEYS, OPENAI_COMPAT_AUTH, SPINNER_CHARS


class QoderCliCnAdapter(CliAdapter):
    def spawn_cmd(self, agent: str, model: str) -> str:
        qoder_bin = shutil.which("qoderclicn") or "qoderclicn"
        args = [
            qoder_bin,
            "--dangerously-skip-permissions",
            "--name", agent,
        ]
        if model:
            args.extend(["--model", model])
        return " ".join(shlex.quote(a) for a in args)

    def ready_markers(self) -> list[str]:
        return [
            "Qoder CLI CN",
            "Type your request",
            "Qwen3.7-Max Model",
            "❯",
        ]

    def busy_markers(self) -> list[str]:
        return [
            *SPINNER_CHARS,
            "Thinking",
            "Calling tool",
            "Running",
            "Working",
        ]

    def process_name(self) -> str:
        return "qoderclicn"

    def submit_keys(self) -> list[str]:
        return list(MULTILINE_SUBMIT_KEYS)

    def rate_limit_markers(self) -> list[str]:
        return [
            "rate limit",
            "quota exceeded",
            "请求过于频繁",
            "429",
        ]

    def auth_slots(self):
        return OPENAI_COMPAT_AUTH
