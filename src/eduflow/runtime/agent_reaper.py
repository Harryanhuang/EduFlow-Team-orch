"""Respawn agents whose CLI has exited.

The watchdog supervises the router daemon (process-level) but NOT the agent
CLIs running in tmux panes. When an agent's CLI exits (crash, rate-limit, OOM,
network blip), its pane drops to a bare shell and stays dead until the next
message lazily wakes it — to a watching operator the agent "exited on its
own". This module lets the watchdog detect that and bring the agent back
proactively.

Ported from claudeteam's `runtime/agent_reaper.py`. claudeteam probes via a
dedicated `pane_probe` module (process foreground + pane motion). eduflow has
no `pane_probe`; instead it exposes the same two raw signals through
`runtime/tmux.py`:

  - liveness  : the pane's foreground process, read from
                `tmux.list_panes(...).current_command` (the
                `#{pane_current_command}` field). A shell (bash / zsh / …) in
                the foreground means the CLI has exited; anything else (node /
                python / … = the running CLI) means it's up.
  - busy/idle : whether the pane is *changing*. Capture twice a short interval
                apart; if the tail changed, the CLI is producing output
                (busy); if static, it's idle.

So a shell foreground that is still churning (the CLI shelled out for a tool)
reads BUSY, not DEAD — only a shell sitting STATIC is a genuinely dead pane.
This is the marker-free probe approach from claudeteam, re-expressed over
eduflow's tmux primitives rather than hard-importing pane_probe.

Conservative: only a genuinely DEAD pane (CLI exited, shell sitting static)
is respawned. A CLI still showing a login / auth screen is *alive* (its
process is up, not a shell), so the probe reports it BUSY/IDLE — not DEAD —
and it's left alone (respawning can't fix expired creds, and would loop; that
is the runtime guard's job, not the reaper's). Lazy agents are skipped, and a
per-agent cooldown prevents thrashing.

Boundary: this reaper handles agent-CLI process-level recovery (kill window +
provision a fresh CLI). The watchdog's flap-backoff governs the router daemon
process. The agent runtime guard (`commands/watchdog._guard_agent_runtimes`)
handles provider/runtime failover on a *live* pane. The three are
complementary — the reaper only fires on a dead (shell) pane, which the guard
explicitly does not act on.
"""
from __future__ import annotations

import time
from typing import Callable

from eduflow.runtime import tmux


NO_WINDOW = "no_window"   # pane / window / session gone
DEAD = "dead"             # CLI exited — pane sitting static at a shell prompt
BUSY = "busy"             # pane is changing (producing output)
IDLE = "idle"             # CLI up, pane static (waiting for input)


# Foreground commands that mean "no CLI running" (back at a shell). tmux may
# prefix a login shell with '-'.
_SHELLS = frozenset({
    "bash", "zsh", "sh", "fish", "dash", "ash", "csh", "tcsh", "ksh",
})


def _is_shell(cmd: str) -> bool:
    return cmd.strip().lstrip("-").lower() in _SHELLS


def _foreground_command(target: tmux.Target, *,
                        run: Callable | None = None) -> str:
    """The pane's foreground process command, or "" if the window is gone.

    Uses `tmux.preferred_pane_target` + `tmux.list_panes` so we read the
    agent's actual work surface (not an OMX HUD pane) and the
    `#{pane_current_command}` field eduflow already parses into `PaneInfo`.
    """
    kw = {"run": run} if run is not None else {}
    try:
        chosen = tmux.preferred_pane_target(target, **kw)
    except TypeError:
        chosen = tmux.preferred_pane_target(target)
    panes = tmux.list_panes(chosen, **kw)
    if not panes:
        # preferred_pane_target may have appended a `.<index>` suffix; fall
        # back to the window target to read its panes.
        panes = tmux.list_panes(target, **kw)
    if not panes:
        return ""
    active = next((p for p in panes if p.active), panes[0])
    return active.current_command


def _changed(target: tmux.Target, *, interval_s: float = 0.4,
             capture: Callable | None = None,
             sleep: Callable | None = None) -> bool:
    """True if the pane tail changed over `interval_s` — the CLI is emitting
    output (busy). Two captures, one short sleep apart."""
    capture = capture or tmux.capture_pane
    sleep = sleep or time.sleep
    before = capture(target, lines=40)
    sleep(interval_s)
    after = capture(target, lines=40)
    return before != after


def _classify(fg: str, busy: bool) -> str:
    """Foreground process + busy(motion) → state. Empty fg = no pane. A shell
    that's churning is BUSY (a tool is running), not DEAD — only a static
    shell prompt is DEAD."""
    if not fg:
        return NO_WINDOW
    if _is_shell(fg):
        return BUSY if busy else DEAD
    return BUSY if busy else IDLE


def probe(target: tmux.Target, *, interval_s: float = 0.4,
          run: Callable | None = None,
          capture: Callable | None = None,
          sleep: Callable | None = None) -> str:
    """Classify a pane as NO_WINDOW / DEAD / BUSY / IDLE without matching any
    TUI content string (marker-free)."""
    fg = _foreground_command(target, run=run)
    if not fg:
        return NO_WINDOW
    busy = _changed(target, interval_s=interval_s, capture=capture, sleep=sleep)
    return _classify(fg, busy)


def find_dead_agents(agents, *, session: str,
                     run: Callable | None = None,
                     capture: Callable | None = None,
                     sleep: Callable | None = None,
                     is_retired: Callable[[str], bool] | None = None,
                     lazy=frozenset()) -> list[str]:
    """Agents whose CLI has exited (`probe` == DEAD), excluding lazy
    (never-woken = also a shell) and retired/fired agents.

    `is_retired` is optional — eduflow has no built-in retired registry, so
    callers that track fired agents (e.g. via status "已停止") may pass a
    predicate; when None, no agents are excluded on that basis."""
    dead = []
    for a in agents:
        if a in lazy:
            continue
        if is_retired is not None and is_retired(a):
            continue
        if probe(tmux.Target(session, a), run=run, capture=capture,
                 sleep=sleep) == DEAD:
            dead.append(a)
    return dead


def reap(agents, *, session: str, respawn: Callable[[str], bool],
         cooldown_s: float = 300.0,
         last_respawn: dict | None = None,
         now: Callable[[], float] | None = None,
         run: Callable | None = None,
         capture: Callable | None = None,
         sleep: Callable | None = None,
         is_retired: Callable[[str], bool] | None = None,
         lazy=frozenset(),
         log: Callable[[str], None] = print) -> list[str]:
    """Respawn DEAD agents that are past their per-agent cooldown.

    `last_respawn` is a dict mutated in place (agent → last respawn time);
    the caller keeps it across cycles so the cooldown survives. Returns the
    names respawned this call. `respawn(agent) -> bool` does the rebuild."""
    now = now or time.monotonic
    last_respawn = last_respawn if last_respawn is not None else {}
    out = []
    for a in find_dead_agents(agents, session=session, run=run, capture=capture,
                              sleep=sleep, is_retired=is_retired, lazy=lazy):
        t = now()
        prev = last_respawn.get(a)
        if prev is not None and (t - prev) < cooldown_s:
            log(f"  ⏳ {a} dead but within respawn cooldown "
                f"({cooldown_s:.0f}s) — leaving for lazy-wake")
            continue
        try:
            if respawn(a):
                last_respawn[a] = t
                out.append(a)
                log(f"  ♻️  respawned dead agent {a}")
            else:
                log(f"  ⚠️ respawn {a} returned failure")
        except Exception as e:
            log(f"  ⚠️ respawn {a} raised: {e}")
    return out
