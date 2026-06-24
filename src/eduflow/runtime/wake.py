"""Lazy wake: spawn an agent's CLI on demand.

Two ways an agent's pane can be in a state that's not yet ready to
receive a message:

1. Boss configured the agent as `lazy` in team.json — `eduflow start`
   created the window but didn't spawn the CLI.  The pane is just a
   shell.
2. The CLI exited — Ctrl-C, /clear, OOM, network blip — and the watchdog
   either hasn't noticed yet or doesn't supervise this pane.

Either way, the next time deliver.apply() wants to inject, it should
detect "no CLI ready" and bring it up.  This module is the detection +
spawn step, kept pure-ish (collaborators injectable for tests).
"""
from __future__ import annotations

import re
import time
from typing import Callable

from eduflow.agents.base import CliAdapter
from eduflow.runtime import tmux


def _has_marker(target: tmux.Target, markers: list[str],
                capture: Callable | None) -> bool:
    """Capture the pane (default tmux.capture_pane) and return True iff any
    string in `markers` appears. Empty marker list → always False (saves a
    capture call when the adapter declines to publish that marker class)."""
    if not markers:
        return False
    capture = capture or tmux.capture_pane
    text = capture(target, lines=80)
    return any(m in text for m in markers)


def is_ready(target: tmux.Target, adapter: CliAdapter, *,
             capture: Callable | None = None) -> bool:
    """True if the pane already shows one of the adapter's ready markers."""
    return _has_marker(target, adapter.ready_markers(), capture)


def is_rate_limited(target: tmux.Target, adapter: CliAdapter, *,
                    capture: Callable | None = None) -> bool:
    """True if the pane shows any rate-limit marker for this adapter.

    Empty marker list (default for codex/kimi historically) → always False.
    """
    return _has_marker(target, adapter.rate_limit_markers(), capture)


# Onboarding dialogs claude pops on fresh ~/.claude.json (ephemeral
# per-container since the host bind-mount was dropped). Each dialog
# blocks the `bypass permissions on` ready marker, so we auto-press
# Enter to accept the default highlighted choice. Settings.json
# silent-launch flags suppress most onboarding paths, but a few
# dialogs ALWAYS show on a fresh state file regardless of settings.
_FIRST_LAUNCH_DIALOG_MARKERS = (
    "Choose the text style",                  # syntax theme picker
    "Claude account with subscription",       # auth method picker
    "Choose an option:",                      # generic onboarding prompt
)

_STALE_PANE_MARKERS = (
    "stream disconnected before completion",
    "error sending request",
    "Invalid auth credentials",
    "Approaching usage limit",
    "provider unavailable",
    "service unavailable",
    "gateway timeout",
)

_SHELL_PROMPT_RE = re.compile(r"(?m)^[^\n]*[%$#]\s*$")


def is_clean_dormant_pane(text: str) -> bool:
    """Return True only for a shell-like pane that is safe to lazy-spawn into.

    A lazy window can contain stale CLI output after a disconnect or failed
    recovery. Treating that as a normal dormant shell makes health look green
    while the next dispatch lands in a broken TUI. Be conservative: blank
    shells are clean; panes with Codex/Claude transcript lines or known error
    markers must be respawned.
    """
    stripped = text.strip()
    if not stripped:
        return True
    low = stripped.lower()
    if any(marker.lower() in low for marker in _STALE_PANE_MARKERS):
        return False
    if any(token in stripped for token in ("• Ran ", "›", "────", "gpt-", "claude-code")):
        return False
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    if len(lines) <= 2 and all(line in {"$", "%", "#", ">", "$ ", "% ", "# "} or line.endswith(("$", "%", "#")) for line in lines):
        return True
    return False


def _dialog_is_current(text: str) -> bool:
    """Return False when an old onboarding dialog is only scrollback.

    tmux capture-pane includes history. If Claude exits after the dialog,
    the stale dialog remains above a fresh shell prompt; blindly sending
    "2 Enter" then just types `2` into zsh forever. Treat a shell prompt
    after the last dialog marker as proof that the dialog is no longer live.
    """
    markers = ("No, exit", "Yes, I accept", *_FIRST_LAUNCH_DIALOG_MARKERS)
    last_marker = max((text.rfind(marker) for marker in markers), default=-1)
    if last_marker < 0:
        return False
    last_prompt = -1
    for match in _SHELL_PROMPT_RE.finditer(text):
        last_prompt = match.start()
    if last_prompt > last_marker:
        return False
    if "zsh: command not found: 2" in text[last_marker:]:
        return False
    return True


def _poll_until_ready(target: tmux.Target, adapter: CliAdapter, *,
                      timeout_s: float, poll_interval_s: float,
                      capture: Callable, sleep: Callable, now: Callable) -> bool:
    """Loop `is_ready` checks until a ready marker shows up or `timeout_s`
    elapses. claude pops a chain of first-launch dialogs (theme
    picker, auth-method picker, bypass-perms confirm). Each dialog
    blocks the next, so we auto-press Enter every time we see ANY
    known dialog marker, throttled to once per second so we don't
    spam-press during a single dialog. Default-highlighted choice
    gets accepted; the next dialog appears; we Enter again until the
    bypass-permissions ready marker shows."""
    ready_markers = adapter.ready_markers()
    deadline = now() + timeout_s
    last_dismiss_at = 0.0
    while now() < deadline:
        text = capture(target, lines=80)
        if any(m in text for m in ready_markers):
            return True
        dialog_live = _dialog_is_current(text)
        if dialog_live and "No, exit" in text and "Yes, I accept" in text:
            t = now()
            if t - last_dismiss_at >= 1.0:
                tmux.send_keys(target, "2", "Enter")
                last_dismiss_at = t
        elif dialog_live and "Bypass Permissions mode" in text:
            # Wait for the explicit Yes/No options. Pressing Enter on the
            # partially-rendered bypass banner accepts the default "No, exit".
            pass
        elif dialog_live and any(m in text for m in _FIRST_LAUNCH_DIALOG_MARKERS):
            t = now()
            if t - last_dismiss_at >= 1.0:
                tmux.send_keys(target, "Enter")
                last_dismiss_at = t
        sleep(poll_interval_s)
    return False


def wait_until_ready(target: tmux.Target, adapter: CliAdapter, *,
                     timeout_s: float = 20.0,
                     poll_interval_s: float = 0.5,
                     capture: Callable | None = None,
                     sleep: Callable | None = None,
                     now: Callable | None = None) -> bool:
    """Poll the pane until a ready marker shows up. Does NOT spawn — use
    after a fresh `tmux.spawn_agent` to wait for the CLI banner before
    the next inject. Returns True if a marker appeared in time.
    """
    return _poll_until_ready(
        target, adapter,
        timeout_s=timeout_s, poll_interval_s=poll_interval_s,
        capture=capture or tmux.capture_pane,
        sleep=sleep or time.sleep,
        now=now or time.monotonic,
    )


def wake_if_dormant(target: tmux.Target, adapter: CliAdapter, *,
                    spawn_cmd: str,
                    init_msg: str | None = None,
                    on_woken: Callable[[], None] | None = None,
                    timeout_s: float = 30.0,
                    poll_interval_s: float = 0.5,
                    capture: Callable | None = None,
                    spawn: Callable | None = None,
                    respawn: Callable | None = None,
                    inject: Callable | None = None,
                    sleep: Callable | None = None,
                    now: Callable | None = None) -> bool:
    """Ensure the agent's CLI is ready to receive input.

    Returns True iff the pane shows a ready marker (already awake, or
    woken in time).  Returns False on timeout — caller decides whether
    to inject anyway, queue, or surface to boss.

    When the function had to actually spawn (pane was dormant on entry)
    AND `init_msg` is provided, it injects the identity/init prompt
    after the CLI shows ready, then calls `on_woken` (typically used
    to flip the agent's status row from "待命" to "进行中").
    """
    capture = capture or tmux.capture_pane
    spawn = spawn or tmux.spawn_agent
    respawn = respawn or tmux.respawn_agent
    inject = inject or tmux.inject
    sleep = sleep or time.sleep
    now = now or time.monotonic

    if is_ready(target, adapter, capture=capture):
        return True  # already awake — caller already handled identity at start

    pane_text = capture(target, lines=80)
    spawn_fn = spawn if is_clean_dormant_pane(pane_text) else respawn
    if not spawn_fn(target, spawn_cmd):
        return False

    # Give the CLI a beat to boot before checking — the pane was just
    # spawned; an immediate is_ready will always be False and burns a
    # capture-pane call.
    sleep(poll_interval_s)
    if not _poll_until_ready(target, adapter,
                             timeout_s=timeout_s, poll_interval_s=poll_interval_s,
                             capture=capture, sleep=sleep, now=now):
        return False

    # CLI just came up. Feed it the identity init prompt before whatever
    # real message follows, so the agent starts knowing who it is.
    if init_msg:
        inject(target, init_msg, submit_keys=adapter.submit_keys())
        sleep(poll_interval_s)
    if on_woken is not None:
        on_woken()
    return True
