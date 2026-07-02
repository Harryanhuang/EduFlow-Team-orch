"""Unified runtime failure detection — single source of truth for markers
and detection logic used by both ``feishu/deliver.py`` and
``commands/watchdog.py``.

Eliminates the duplicated marker tuples and divergent matching logic
that previously lived in each consumer independently.
"""
from __future__ import annotations

import time
from typing import Callable

from eduflow.runtime import paths, tmux, wake
from eduflow.util import read_json


# ---------------------------------------------------------------------------
# Marker sets — union of deliver + watchdog definitions.
# ---------------------------------------------------------------------------

_AUTH_FAILURE_MARKERS = (
    "Invalid auth credentials",
    "auth required",
    "Unauthorized",
    "401",
    "/login",
    # Quota / billing / subscription expired — access denied even though
    # credentials are valid.  Treat as auth_failure so the runtime guard /
    # deliver can switch to a fallback.
    "FORBIDDEN",
    "quota exceeded",
    "billing required",
    "subscription expired",
    'code":"112',
)

_PROVIDER_UNAVAILABLE_MARKERS = (
    "provider unavailable",
    "service unavailable",
    "temporarily unavailable",
    "502",
    "503",
    "504",
    "gateway timeout",
    "connection refused",
    # 403 with rate-limit connotation — distinct from auth/quota.
    "403",
)

_CONVERSATION_HISTORY_CORRUPT_MARKERS = (
    "Repetitive tool calls detected",
    "InternalError.Algo.InvalidParameter",
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _adapter_ready_markers(adapter) -> list[str]:
    try:
        return list(adapter.ready_markers())
    except AttributeError:
        return []


def _current_pane_text(text: str, ready_markers: list[str]) -> str:
    """Return only the text *after* the last ready marker (the live CLI
    output), or the full text if no ready marker is found."""
    ready_at = max((text.rfind(m) for m in ready_markers), default=-1)
    return text[ready_at:] if ready_at >= 0 else text


def _has_marker_after_ready(text: str, markers: tuple[str, ...],
                            ready_markers: list[str], *,
                            case_insensitive: bool = True) -> bool:
    """True if any *marker* appears in the post-ready portion of *text*.

    When *case_insensitive* is True (default), comparison folds both
    sides to lowercase — this matches the historical watchdog behaviour
    and avoids false negatives on mixed-case provider error strings.
    """
    if case_insensitive:
        low = text.lower()
        ready_at = max((low.rfind(m.lower()) for m in ready_markers), default=-1)
        marker_at = max((low.rfind(m.lower()) for m in markers), default=-1)
    else:
        ready_at = max((text.rfind(m) for m in ready_markers), default=-1)
        marker_at = max((text.rfind(m) for m in markers), default=-1)
    return marker_at >= 0 and marker_at > ready_at


# ---------------------------------------------------------------------------
# Cooldown check (shared by deliver + watchdog)
# ---------------------------------------------------------------------------

def agent_in_cooldown(agent: str, now_s: float | None = None) -> bool:
    """True if *agent* is still inside its runtime-guard cooldown window.

    Reads ``runtime_guard_state.json`` via ``paths.runtime_guard_state_file``.
    """
    if now_s is None:
        now_s = time.time()
    path = paths.runtime_guard_state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = read_json(path, {"agents": {}})
    row = data.get("agents", {}).get(agent, {})
    return float(row.get("cooldown_until", 0) or 0) > now_s


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def detect_failure(
    target,
    adapter,
    *,
    capture_fn: Callable | None = None,
    pane_text: str | None = None,
    lines: int = 80,
) -> str:
    """Return the failure reason string, or ``""`` if no failure is detected.

    Detection order (deliberate):
      1. ``rate_limit``             — quota / throttling (fastest to confirm)
      2. ``auth_failure``           — credentials / billing (must switch away)
      3. ``conversation_history_corrupt`` — corrupt context (costly to ignore)
      4. ``provider_unavailable``   — transient infra (may self-heal)

    Parameters
    ----------
    target : tmux.Target
        Pane target (passed through to ``wake.is_rate_limited``).
    adapter : CliAdapter
        Provides ``ready_markers()`` and ``rate_limit_markers()``.
    capture_fn : callable, optional
        ``(target, lines=80) -> str`` used to capture pane text.
        Falls back to ``tmux.capture_pane``.
    pane_text : str, optional
        Pre-captured pane text.  When supplied the function skips the
        internal capture call.  ``capture_fn`` is still used when
        ``pane_text`` is ``None``.
    lines : int
        Number of tail lines to capture when *pane_text* is not supplied.
        Defaults to 80; pass 120 to match the historical watchdog depth.
    """
    capture = capture_fn or tmux.capture_pane

    if pane_text is None:
        pane_text = capture(target, lines=lines)

    ready_markers = _adapter_ready_markers(adapter)
    current_text = _current_pane_text(pane_text, ready_markers)

    # 1. rate_limit (delegates to wake which uses adapter.rate_limit_markers())
    if wake.is_rate_limited(target, adapter,
                            capture=lambda *_a, **_kw: current_text):
        return "rate_limit"

    # 2. auth_failure — case-insensitive to catch mixed-case provider errors
    if _has_marker_after_ready(current_text, _AUTH_FAILURE_MARKERS,
                               ready_markers, case_insensitive=True):
        return "auth_failure"

    # 3. conversation_history_corrupt
    if _has_marker_after_ready(current_text, _CONVERSATION_HISTORY_CORRUPT_MARKERS,
                               ready_markers, case_insensitive=True):
        return "conversation_history_corrupt"

    # 4. provider_unavailable
    if _has_marker_after_ready(current_text, _PROVIDER_UNAVAILABLE_MARKERS,
                               ready_markers, case_insensitive=True):
        return "provider_unavailable"

    return ""
