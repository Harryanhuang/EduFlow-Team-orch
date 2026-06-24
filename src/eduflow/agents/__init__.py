"""CLI adapter registry — maps a `cli` identifier to its CliAdapter."""
from __future__ import annotations

from eduflow.runtime.config import agent_cli

from .base import CliAdapter
from .claude_code import ClaudeCodeAdapter
from .codex_cli import CodexCliAdapter
from .gemini_cli import GeminiCliAdapter
from .hermes_agent import HermesAgentAdapter
from .kimi_code import KimiCodeAdapter
from .qoder_cli_cn import QoderCliCnAdapter
from .qwen_code import QwenCodeAdapter


_kimi = KimiCodeAdapter()
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


def adapter_for_agent(agent: str) -> CliAdapter:
    """Look up the agent's `cli` from team.json and return its adapter.

    Convenience over `get_adapter(config.agent_cli(agent))`; the routing
    layer reaches for this whenever it needs to spawn or inspect a pane.
    """
    return get_adapter(agent_cli(agent))
