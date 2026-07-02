"""Agent residency policy: resident / warm / cold.

Per plan 2026-07-01 §设计二:

    resident   tmux pane + CLI both up; never auto-sleeps
    warm       tmux pane kept, CLI may exit on idle timeout
    cold       no pane at all (v1 reserved; not auto-enabled)

Phase 2 (this commit) implements the CONFIG side only — schema,
loaders, and `/team` display.  Phase 3 will add the runtime
side: `sleep_if_idle`, `wake`, and the periodic sweep that
actually retires / resurrects CLIs.

This module is pure: no I/O, no env reads, no `local_facts`. The
config-side helpers in `runtime/config.py` are the only callers,
and they return a `ResidencyPolicy` for the caller to display /
use for routing decisions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


# ── mode constants ────────────────────────────────────────────


class ResidencyMode:
    RESIDENT = "resident"  # always-on
    WARM = "warm"          # pane kept, CLI may sleep on idle
    COLD = "cold"          # no pane (v1 reserved)

    ALL = ("resident", "warm", "cold")


# ── dataclass ─────────────────────────────────────────────────


@dataclass(frozen=True)
class ResidencyPolicy:
    mode: str
    idle_timeout_s: int
    handoff_buffer_s: int
    wake_timeout_s: int
    source: str  # "default" / "agent_override" — for audit / debug

    def __post_init__(self) -> None:
        if self.mode not in ResidencyMode.ALL:
            raise ValueError(
                f"invalid residency mode: {self.mode!r} "
                f"(allowed: {', '.join(ResidencyMode.ALL)})"
            )
        if self.idle_timeout_s < 0:
            raise ValueError(
                f"idle_timeout_s must be >= 0, got {self.idle_timeout_s}"
            )
        if self.handoff_buffer_s < 0:
            raise ValueError(
                f"handoff_buffer_s must be >= 0, got {self.handoff_buffer_s}"
            )
        if self.wake_timeout_s <= 0:
            raise ValueError(
                f"wake_timeout_s must be > 0, got {self.wake_timeout_s}"
            )


# ── defaults ──────────────────────────────────────────────────
#
# Per plan 2026-07-01 §设计二 v1 驻留配置:
#   default_mode = "warm"
#   warm_idle_timeout_s = 600
#   handoff_buffer_s = 300
#   wake_timeout_s = 60
#   resident_agents = ["manager", "auto_ops", "Luke_recorder"]
#   warm_agents = (everything else, listed for audit clarity)

DEFAULT_IDLE_TIMEOUT_S = 600
DEFAULT_HANDOFF_BUFFER_S = 300
DEFAULT_WAKE_TIMEOUT_S = 60
DEFAULT_MODE = ResidencyMode.WARM

DEFAULT_RESIDENT_AGENTS: tuple[str, ...] = (
    "manager", "auto_ops", "Luke_recorder",
)

DEFAULT_WARM_AGENTS: tuple[str, ...] = (
    "worker_course", "review_course", "worker_builder",
    "worker_qbank", "Hermes", "worker_syllabus",
)


# ── merging helpers ───────────────────────────────────────────


def _coerce_int(value, default: int, *, min_value: int = 0) -> int:
    """Best-effort int coercion for toml values.  Falls back to
    `default` on TypeError / ValueError so a typo in a single
    agent's `idle_timeout_s = "abc"` does not blow up `/team`."""
    if value is None:
        return default
    try:
        coerced = int(value)
    except (TypeError, ValueError):
        return default
    return max(coerced, min_value)


def _coerce_mode(value, default: str = DEFAULT_MODE) -> str:
    if value is None:
        return default
    text = str(value or "").strip().lower()
    if text not in ResidencyMode.ALL:
        return default
    return text


def _coerce_resident_list(value, fallback: Iterable[str]) -> tuple[str, ...]:
    """Pull a list of agent names from a toml value. Accepts either
    a list (preferred) or a comma-separated string (legacy)."""
    if value is None:
        return tuple(fallback)
    if isinstance(value, str):
        names = [n.strip() for n in value.split(",") if n.strip()]
    elif isinstance(value, (list, tuple)):
        names = [str(n).strip() for n in value if str(n or "").strip()]
    else:
        return tuple(fallback)
    return tuple(names)


def merge_with_default(
    *,
    default_policy: ResidencyPolicy,
    override: dict | None,
) -> ResidencyPolicy:
    """Merge a per-agent override dict on top of `default_policy`.

    Only the keys present in `override` win; missing keys fall
    through to the default.  Returns a NEW ResidencyPolicy with
    `source="agent_override"`.
    """
    if not override:
        return default_policy
    return ResidencyPolicy(
        mode=_coerce_mode(override.get("mode"), default_policy.mode),
        idle_timeout_s=_coerce_int(
            override.get("idle_timeout_s"), default_policy.idle_timeout_s,
        ),
        handoff_buffer_s=_coerce_int(
            override.get("handoff_buffer_s"), default_policy.handoff_buffer_s,
        ),
        wake_timeout_s=_coerce_int(
            override.get("wake_timeout_s"), default_policy.wake_timeout_s,
            min_value=1,
        ),
        source="agent_override",
    )


# ── display labels ────────────────────────────────────────────
#
# /team panel uses these to render the residency column. Kept here
# (not in `commands/team.py`) so the schema and the display live
# in one file and a rename of "常驻" / "温备" doesn't fork.

DISPLAY_LABELS: dict[str, str] = {
    ResidencyMode.RESIDENT: "常驻",
    ResidencyMode.WARM: "温备",
    ResidencyMode.COLD: "cold",
}


def display_label(mode: str) -> str:
    return DISPLAY_LABELS.get(str(mode or "").strip().lower(), "未配置")


# ── sleep decision (Phase 3) ──────────────────────────────────
#
# `should_sleep` is the pure gate that the runtime sweep consults
# before retiring a warm agent's CLI.  It takes already-collected
# signals (not `local_facts` handles) so it stays testable without
# I/O.  Every guard here maps directly to a plan §设计二 "不得
# sleep" rule:
#
#   - resident agents never sleep
#   - active task           → not idle
#   - unread inbox          → not idle
#   - cooldown / fallback / repair → runtime is mid-recovery
#   - within handoff buffer → just handed off, may get a revision
#   - under idle timeout    → not idle long enough yet


@dataclass(frozen=True)
class SleepSignals:
    """Everything `should_sleep` needs, collected by the caller."""
    has_active_task: bool
    has_unread_inbox: bool
    in_cooldown: bool         # runtime fallback / repair / rate-limit cooldown
    idle_age_s: float         # seconds since last direct activity signal
    since_handoff_s: float    # seconds since last HANDOFF/CLOSEOUT (inf if none)


# Reason strings returned by `sleep_decision`. Stable identifiers so
# the sweep can log / count them without parsing prose.
SLEEP_OK = "sleep_ok"
KEEP_RESIDENT = "keep_resident"
KEEP_COLD = "keep_cold"
KEEP_ACTIVE_TASK = "keep_active_task"
KEEP_UNREAD_INBOX = "keep_unread_inbox"
KEEP_COOLDOWN = "keep_cooldown"
KEEP_HANDOFF_BUFFER = "keep_handoff_buffer"
KEEP_UNDER_IDLE_TIMEOUT = "keep_under_idle_timeout"


def sleep_decision(policy: ResidencyPolicy, signals: SleepSignals) -> str:
    """Return one of the SLEEP_* / KEEP_* reason strings.

    `SLEEP_OK` means the caller MAY retire this agent's CLI. Every
    other value is a reason to keep it running. Order matters: the
    hard "never sleep" rules (resident, active work, unread inbox,
    cooldown) are checked before the time-based ones so a busy agent
    is never sleep-eligible regardless of its idle clock.
    """
    if policy.mode == ResidencyMode.RESIDENT:
        return KEEP_RESIDENT
    if policy.mode == ResidencyMode.COLD:
        # cold agents have no pane to retire; the sweep should skip
        # them rather than try to graceful-exit a non-existent CLI.
        return KEEP_COLD
    if signals.has_active_task:
        return KEEP_ACTIVE_TASK
    if signals.has_unread_inbox:
        return KEEP_UNREAD_INBOX
    if signals.in_cooldown:
        return KEEP_COOLDOWN
    if signals.since_handoff_s < policy.handoff_buffer_s:
        return KEEP_HANDOFF_BUFFER
    if signals.idle_age_s < policy.idle_timeout_s:
        return KEEP_UNDER_IDLE_TIMEOUT
    return SLEEP_OK


def should_sleep(policy: ResidencyPolicy, signals: SleepSignals) -> bool:
    """Boolean convenience wrapper over `sleep_decision`."""
    return sleep_decision(policy, signals) == SLEEP_OK
