"""CliAdapter — abstract base for agent CLI integrations.

Each concrete adapter knows how to:
  - build the shell command that spawns the CLI in a tmux pane,
  - declare which strings indicate the CLI is ready vs. busy,
  - declare its process name (for /proc walkers),
  - declare which keys submit a queued line of input.

Stripped of the old-tree extras (env_overrides, thinking_init_hint,
CliCapabilities dataclass, proxy prefix wiring).  Those return when a
concrete capability needs them, not before.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


# Braille-pattern spinner glyphs that every Ink/Rich/Bubbletea-style CLI
# uses for "I'm busy" indication. Concrete adapters splice this into their
# own busy_markers() return.
SPINNER_CHARS = ("⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷")


# Submit-key sequence for multi-line CLIs (Codex / Kimi use Ink + prompt_toolkit
# style multi-line input where Enter inserts a newline, M-Enter commits the
# buffer). Plain `Enter` is kept as a fallback for single-line edge cases.
MULTILINE_SUBMIT_KEYS = ("M-Enter", "Enter", "C-m", "C-j")


class CliAdapter(ABC):
    @abstractmethod
    def spawn_cmd(self, agent: str, model: str) -> str:
        """Full shell command (will be sent to a tmux pane via send-keys)."""

    @abstractmethod
    def ready_markers(self) -> list[str]:
        """If any string here appears in the pane, CLI UI is ready."""

    @abstractmethod
    def busy_markers(self) -> list[str]:
        """If any string here appears at the pane tail, the agent is busy."""

    @abstractmethod
    def process_name(self) -> str:
        """/proc/<pid>/comm value; used to find the CLI process under a pane."""

    def submit_keys(self) -> list[str]:
        """Tmux keys to try in order to commit a line of input.

        Default: plain Enter / C-m / C-j.  Multi-line CLIs (Codex, Kimi)
        override to lead with M-Enter.
        """
        return ["Enter", "C-m", "C-j"]

    def rate_limit_markers(self) -> list[str]:
        """Strings that, if present in the pane tail, mean the CLI is
        currently rate-limited and won't process new input. Empty by
        default; per-CLI adapters override with provider-specific text.
        """
        return []

    def auth_slots(self) -> "AuthSlot | None":
        """Declare which credential vars / creds file this CLI uses.

        Returns None (unmanaged) by default — adapters that support
        per-agent credential isolation override with their specific
        env var names and creds file path.  agent_auth.resolve() uses
        this to pick the highest-priority credential for each spawn.
        """
        return None


@dataclass(frozen=True)
class AuthSlot:
    """Per-CLI credential slots consumed by agent_auth.resolve().

    Fields:
      token_env      — env var for a long-term API token (highest priority).
      login_credfile — path (relative to agent HOME) of a creds JSON file
                       written by the CLI's own login flow (middle priority).
      login_token_env — env var to set when using login mode (e.g. the
                        OAuth access token extracted from credfile).
      api_key_envs   — tuple of env var names for API keys (lowest priority);
                       first one found in secrets/environ wins.
    """
    token_env: str | None = None
    login_credfile: str | None = None
    login_token_env: str | None = None
    api_key_envs: tuple[str, ...] = ()


OPENAI_COMPAT_AUTH = AuthSlot(
    token_env=None,
    api_key_envs=("OPENAI_API_KEY",),
    login_credfile=None,
)
