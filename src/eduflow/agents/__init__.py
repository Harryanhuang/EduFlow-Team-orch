"""CLI adapter registry — maps a `cli` identifier to its CliAdapter."""
from __future__ import annotations

from eduflow.runtime.config import resolved_agent_config

from .base import CliAdapter
from .claude_code import ClaudeCodeAdapter
from .codex_cli import CodexCliAdapter
from .gemini_cli import GeminiCliAdapter
from .hermes_agent import HermesAgentAdapter
from .kimi_code import KimiCodeAdapter
from .mimo_code import MimoCodeAdapter
from .qoder_cli_cn import QoderCliCnAdapter
from .qwen_code import QwenCodeAdapter


_kimi = KimiCodeAdapter()
_mimo = MimoCodeAdapter()
_qoder_cn = QoderCliCnAdapter()
_qwen = QwenCodeAdapter()
_hermes = HermesAgentAdapter()
_REGISTRY: dict[str, CliAdapter] = {
    "claude-code": ClaudeCodeAdapter(),
    "codex-cli": CodexCliAdapter(),
    "gemini-cli": GeminiCliAdapter(),
    "hermes-agent": _hermes,
    "hermes-cli": _hermes,
    "kimi-code": _kimi,
    "kimi-cli": _kimi,  # alias: upstream package name
    "mimo-code": _mimo,
    "mimo-cli": _mimo,
    "qoderclicn": _qoder_cn,
    "qoder-cli-cn": _qoder_cn,
    "qwen-code": _qwen,
    "qwen-cli": _qwen,  # alias for symmetry with kimi
}


def known_clis() -> tuple[str, ...]:
    return tuple(_REGISTRY)


def get_adapter(cli_name: str) -> CliAdapter:
    """Return the adapter for `cli_name`. Raises KeyError if not registered."""
    if cli_name not in _REGISTRY:
        raise KeyError(
            f"unknown cli: {cli_name!r} (known: {', '.join(_REGISTRY)})")
    return _REGISTRY[cli_name]


def adapter_for_agent(agent: str, runtime_name: str | None = None) -> CliAdapter:
    """Look up the agent's effective CLI and return its adapter.

    `runtime_name` lets callers resolve the adapter for the runtime that is
    actually live in the pane, not just the chain primary.
    """
    cli = resolved_agent_config(agent, runtime_name=runtime_name).get("cli", "claude-code")
    return get_adapter(cli)
