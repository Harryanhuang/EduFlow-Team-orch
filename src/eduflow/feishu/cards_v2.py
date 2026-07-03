"""Structured card protocol v2 — public surface.

Boss pain point 2026-07-01: 主群外显不稳定 — sometimes 状态卡, sometimes
worker 日志, sometimes 静默.  This module is the system-side
validator that makes every visible card conform to one of nine
types with explicit fields.  Prompt-level instructions in agent
`notes` are advisory; this module is enforcement.

Three categories of failure, distinguished by prefix:
  - "role:<msg>"        → role violation (e.g. worker → CLOSEOUT).
                         Caller SHOULD block (exit 1) — the agent is
                         trying to do something it cannot.
  - "field:<key>:<msg>" → missing or empty required field.
                         Caller SHOULD degrade to internal (exit 0)
                         so the agent's intent is captured in audit
                         but the chat stays clean.
  - "value:<key>:<msg>" → controlled-vocabulary violation.
                         Same degrade-to-internal semantics as field
                         errors.

The data tables (card types, role allow-list, required fields,
controlled vocabulary) live in `cards_v2_schema.py` so this file
stays focused on parsing / validating / rendering.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from eduflow.feishu.cards_v2_schema import (
    CardType, REQUIRED_FIELDS, _BOSS_INTERVENTION_YES,
    _FIELD_VALUE_ALLOWED, agent_role_allowed,
    severity_to_color,
)


__all__ = [
    "Card", "ValidationResult",
    "build_card", "parse_body", "validate_card", "render_to_card_dict",
    "needs_boss_intervention",
    "CardType", "agent_role_allowed", "REQUIRED_FIELDS",
]


# ── body parser ─────────────────────────────────────────────────
#
# Accept `key: value` and `key：value` (Chinese full-width colon),
# with optional whitespace.  Lines without a recognised separator
# are silently skipped so the body can carry a leading
# "[CLOSEOUT] manager" header that the caller strips before passing
# the rest to the parser.  Values are stripped; empty values are
# kept so `validate_card` can flag `任务:\n` as missing-evidence.

_BODY_SEP_RE = re.compile(r"^\s*([^：:]+?)\s*[：:]\s*(.*?)\s*$")


def parse_body(body: str) -> dict[str, str]:
    """Parse a multi-line structured body into a {key: value} dict.

    Lines without a `:` or `：` separator are silently skipped.
    Repeated keys keep the last value.  Keys are returned case-
    preserved but matched case-insensitively against REQUIRED_FIELDS
    by `_field_lookup` inside `validate_card` — so a body that says
    "Task: ..." still satisfies the `任务` requirement.
    """
    out: dict[str, str] = {}
    if not body:
        return out
    for line in str(body).splitlines():
        match = _BODY_SEP_RE.match(line)
        if not match:
            continue
        key, value = match.group(1).strip(), match.group(2).strip()
        if not key:
            continue
        out[key] = value
    return out


def _field_lookup(fields: dict[str, str], required: str) -> str | None:
    """Case-insensitive key lookup.  Returns the first non-empty
    value among all case-equivalent keys, or None when absent."""
    if required in fields and fields[required].strip():
        return fields[required]
    lower = required.lower()
    for key, value in fields.items():
        if key.lower() == lower and value.strip():
            return value
    return None


# ── card dataclass ──────────────────────────────────────────────


@dataclass(frozen=True)
class Card:
    card_type: str
    sender: str
    fields: dict[str, str] = field(default_factory=dict)
    color: str = "blue"
    severity: str | None = None

    def title_prefix(self) -> str:
        """`[CLOSEOUT] manager` — the visible card-type tag used in
        the header before the agent identity line."""
        return f"[{self.card_type}] {self.sender}"


# ── validator ───────────────────────────────────────────────────


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...] = ()
    is_role_violation: bool = False

    def __bool__(self) -> bool:
        return self.ok


def validate_card(card: Card, *,
                  known_agents: list[str] | tuple[str, ...] = ()) -> ValidationResult:
    """Validate a parsed Card.

    Returns ValidationResult.ok=True when the card passes every
    gate; ValidationResult.errors is a tuple of "<category>:<detail>"
    strings.  `is_role_violation` is True iff the only failures are
    role-based — callers use that to distinguish "block" (exit 1)
    from "degrade to internal" (exit 0).
    """
    if card.card_type not in CardType.ALL:
        return ValidationResult(
            ok=False,
            errors=(f"role:unknown_card_type:{card.card_type}",),
            is_role_violation=True,
        )

    allowed = agent_role_allowed(card.sender, known_agents=known_agents)
    if card.card_type not in allowed:
        return ValidationResult(
            ok=False,
            errors=(f"role:{card.sender}_cannot_send_{card.card_type}",),
            is_role_violation=True,
        )

    errors: list[str] = []
    for required in REQUIRED_FIELDS.get(card.card_type, ()):
        value = _field_lookup(card.fields, required)
        if value is None or not value.strip():
            errors.append(f"field:{required}:missing")
            continue
        allowed_values = _FIELD_VALUE_ALLOWED.get((card.card_type, required))
        if allowed_values is not None and value not in allowed_values:
            errors.append(
                f"value:{required}:not_in:{','.join(sorted(allowed_values))}",
            )
    return ValidationResult(
        ok=not errors,
        errors=tuple(errors),
        is_role_violation=False,
    )


def needs_boss_intervention(card: Card) -> bool:
    """True iff `需要老板介入` is one of the affirmative values
    (`是 / yes / true / y / 1`).  Default False when the field is
    absent — the ALERT type always carries the value explicitly so
    escalation signals are not lost on missing-field degradation."""
    value = _field_lookup(card.fields, "需要老板介入")
    if not value:
        return False
    return value.strip().lower() in _BOSS_INTERVENTION_YES


# ── builder / renderer ──────────────────────────────────────────


def build_card(card_type: str, sender: str, body: str,
               *, color: str = "blue", severity: str | None = None) -> Card:
    """Parse `body` and return a Card.  Does NOT validate — callers
    should run `validate_card()` and decide block-vs-degrade."""
    return Card(
        card_type=str(card_type or "").strip().upper(),
        sender=str(sender or "").strip(),
        fields=parse_body(body),
        color=str(color or "blue").strip() or "blue",
        severity=str(severity).strip().lower() if severity else None,
    )


def render_to_card_dict(card: Card, *, header_title: str | None = None,
                        footer: str = "") -> dict:
    """Format a validated Card as a Feishu card v2 dict compatible
    with `feishu/cards.simple_card` callers.

    `header_title` is the full pre-built title (caller is expected
    to have prepended `[TYPE]` to the agent identity).  When omitted,
    the header falls back to `[{TYPE}] {sender}` so a programmatic
    caller (e.g. a test) can skip the identity composition.

    Body: bold key + full-width colon + value, one field per line.
    The `需要老板介入` field gets an emoji prefix when affirmative
    so the boss can scan the bottom of the card without reading
    every body line.

    Color resolution order (highest priority first):
      1. explicit `card.color` when it is a known template name
         (set by the caller, e.g. `color="green"`)
      2. `severity_to_color(card.severity)` when card.severity is
         set and maps to a canonical color
      3. fallback to "blue"
    """
    from eduflow.feishu.cards import _normalised_color
    title = header_title if header_title else card.title_prefix()
    body_lines: list[str] = []
    for key, value in card.fields.items():
        if not value.strip():
            continue
        prefix = "🚨 " if key == "需要老板介入" and needs_boss_intervention(card) else ""
        body_lines.append(f"**{key}**：{prefix}{value}")
    if footer:
        body_lines.append("")
        body_lines.append(footer)
    body_text = "\n".join(body_lines) if body_lines else "(无内容)"
    # Color resolution: severity overrides only when the caller did
    # not set an explicit color (i.e. the Card uses the default "blue").
    # This prevents a `severity="warning"` from silently overriding a
    # deliberate `color="green"` choice.
    if card.severity and card.color == "blue":
        resolved = severity_to_color(card.severity)
        if resolved:
            template_color = _normalised_color(resolved)
        else:
            template_color = _normalised_color(card.color)
    else:
        template_color = _normalised_color(card.color)
    return {
        "schema": "2.0",
        "header": {
            "title": {"content": title, "tag": "plain_text"},
            "template": template_color,
        },
        "body": {"elements": [
            {"tag": "markdown", "content": body_text},
        ]},
    }
