"""Deterministic, read-only risk classifier for EduFlow command surfaces.

Package 3 of the 2026-07-06 production-contract pilot. The classifier
NEVER mutates command behavior. It only returns a structured verdict
so manager/operator surfaces can warn before destructive intents.

The classification rules live in `docs/templates/TOOL_RISK_MATRIX.md`.
Levels:

- Low: read-only / status / search / evidence explain
- Medium: local file creation or non-critical local write
- High: coordination / runtime write or external-but-reversible
- Critical: destructive / external production / state delete

When the command combines multiple intents (e.g. ``task get T-1 && rm -rf ...``)
the highest level wins. This matches the TOOL_RISK_MATRIX rule that
``requires_preflight`` is advisory output: the caller decides whether
to actually require preflight.
"""
from __future__ import annotations

import re
import shlex
from typing import Any


# ── intent matchers ───────────────────────────────────────────────
# Each matcher returns a (level, reason) tuple when it fires. Order does
# not matter: `classify` collects all matches and picks the highest level.

_LOW_INTENTS: tuple[tuple[str, str], ...] = (
    (r"^eduflow\s+task\s+(loop-status|loop-list|loop-contract|evidence-explain|evidence-account|loop-check|get|list|read|subject-inventory)\b",
     "task read-only surface"),
    (r"^eduflow\s+(status|read|team|list|version|usage|recall)\b",
     "eduflow read-only surface"),
    (r"^eduflow\s+task\s+tool-risk\b",
     "tool-risk classifier (read-only)"),
    (r"^eduflow\s+task\s+evolution-packet\b",
     "evolution-packet read model (read-only)"),
    (r"^eduflow\s+task\s+readiness-check\b",
     "readiness-check read model (read-only)"),
    (r"^eduflow\s+(peek|inbox|recall)\b",
     "read-only inbox/peek"),
    (r"^eduflow\s+(task\s+)?(grep|search)\b",
     "search surface"),
    (r"^\s*(cat|less|head|tail|rg|grep|find|ls)\b",
     "shell read-only"),
)

_MEDIUM_INTENTS: tuple[tuple[str, str], ...] = (
    (r"^eduflow\s+task\s+(create|create-flow|dispatch|update|done|flow-create|flow-transition)\b",
     "task create/update"),
    (r"^eduflow\s+(remember|log)\b",
     "eduflow memory/log write"),
    (r"^eduflow\s+say\b(?!\s+.*--to\s+user)",
     "internal say (not to user)"),
    (r"^eduflow\s+task\s+correct\b",
     "task correct (manager -> worker correction)"),
)

_HIGH_INTENTS: tuple[tuple[str, str], ...] = (
    (r"^eduflow\s+send\b",
     "send: cross-agent coordination write"),
    (r"^eduflow\s+say\b[^|;&]*--to\s+user",
     "say --to user: external-facing"),
    (r"^eduflow\s+task\s+(dispatch|review|assign-reviewer|submit-review|reidentify|manager-action-apply|correct)\b",
     "task coordination write"),
    (r"^eduflow\s+runtime\s+switch\b",
     "runtime switch: coordination write"),
    (r"^eduflow\s+task\s+manager-actions\b",
     "manager actions: coordination write"),
    (r"^eduflow\s+task\s+(publish-check|publish-scan|publish-run)\b",
     "publish intent: cross-agent coordination write"),
)

_CRITICAL_INTENTS: tuple[tuple[str, str], ...] = (
    (r"^eduflow\s+(reset|down)\b",
     "runtime shutdown: state wipe risk"),
    (r"^eduflow\s+fire\b",
     "fire agent: state deletion"),
    (r"^eduflow\s+hire\b",
     "hire: roster mutation (manager-only)"),
    (r"^eduflow\s+task\s+(archive|archive-schedule)\b",
     "task archive: state deletion"),
    (r"^eduflow\s+forget\b",
     "forget: memory deletion"),
    (r"^eduflow\s+runtime\s+(reset|down|kill)\b",
     "runtime destructive"),
    (r"\brm\s+-rf\b",
     "shell rm -rf: destructive"),
    (r"\brm\s+-fr\b",
     "shell rm -fr: destructive"),
    (r"\brm\s+-r\b",
     "shell rm -r: destructive"),
    (r"\b(deploy|publish)\b.*\b(prod|production|external)\b",
     "external production deploy/publish"),
    (r"\b(kubectl|helm|terraform)\s+(apply|create|destroy|delete)\b",
     "external deploy tooling"),
    (r"\bgit\s+push\s+(origin\s+)?(main|master|production|prod)\b",
     "external production branch push"),
    (r"\bdd\s+if=.*\s+of=/dev/",
     "raw disk write"),
)


_LEVEL_ORDER = ("Low", "Medium", "High", "Critical")
_LEVEL_TO_ACCESS_MODE = {
    "Low": "auto",
    "Medium": "auto",
    "High": "auto_review",
    "Critical": "manager_only",
}


# ── helpers ───────────────────────────────────────────────────────


def _split_intents(command: str) -> list[str]:
    """Split a shell-ish command into atomic intents.

    Recognizes ``&&``, ``||``, ``;`` and newlines. Pipes (``|``) are
    treated as a single intent because they form a data-flow pipeline
    that should be classified together.
    """
    text = str(command or "").strip()
    if not text:
        return []
    # Split on chain operators but not on pipes.
    pieces = re.split(r"\s*(?:&&|\|\||;|\n)\s*", text)
    return [p.strip() for p in pieces if p.strip()]


def _match_intent(intent: str, table: tuple[tuple[str, str], ...]) -> str | None:
    for pattern, reason in table:
        if re.search(pattern, intent, re.IGNORECASE):
            return reason
    return None


def _classify_one_intent(intent: str) -> tuple[str, str]:
    """Return (level, reason) for a single intent string."""
    # Critical first (highest wins), then High, Medium, Low.
    reason = _match_intent(intent, _CRITICAL_INTENTS)
    if reason is not None:
        return "Critical", reason
    reason = _match_intent(intent, _HIGH_INTENTS)
    if reason is not None:
        return "High", reason
    reason = _match_intent(intent, _MEDIUM_INTENTS)
    if reason is not None:
        return "Medium", reason
    reason = _match_intent(intent, _LOW_INTENTS)
    if reason is not None:
        return "Low", reason
    return "Medium", "unrecognized eduflow command (default Medium)"


# ── public API ────────────────────────────────────────────────────


def classify(command: str) -> dict[str, Any]:
    """Return the risk verdict for `command`.

    Strictly read-only. Never mutates command behavior.

    Output schema (stable):
        risk_level: Low | Medium | High | Critical
        access_mode: auto | auto_review | manager_only
        reason: short human-readable string
        requires_preflight: bool
        requires_human_confirm: bool
    """
    raw = str(command or "").strip()
    if not raw:
        return {
            "risk_level": "Low",
            "access_mode": "auto",
            "reason": "empty command",
            "requires_preflight": False,
            "requires_human_confirm": False,
        }
    intents = _split_intents(raw)
    if not intents:
        return {
            "risk_level": "Low",
            "access_mode": "auto",
            "reason": "empty command (after split)",
            "requires_preflight": False,
            "requires_human_confirm": False,
        }
    highest_level: str | None = None
    matched_reasons: list[str] = []
    for intent in intents:
        level, reason = _classify_one_intent(intent)
        matched_reasons.append(reason)
        if highest_level is None or _LEVEL_ORDER.index(level) > _LEVEL_ORDER.index(highest_level):
            highest_level = level
    final_level = highest_level or "Medium"
    access_mode = _LEVEL_TO_ACCESS_MODE[final_level]
    return {
        "risk_level": final_level,
        "access_mode": access_mode,
        "reason": "; ".join(matched_reasons),
        "requires_preflight": final_level in {"High", "Critical"},
        "requires_human_confirm": final_level == "Critical",
    }