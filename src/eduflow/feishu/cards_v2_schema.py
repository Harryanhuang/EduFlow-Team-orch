"""Card protocol v2 schema: card types, role allow-list, required fields.

Pure data — no I/O, no env reads, no parser / validator / renderer
logic.  Imported by `feishu/cards_v2.py` (the public surface) so the
schema tables stay in one place and tests can pin them without
pulling in the full validator.

Per plan 2026-07-01 §设计一:

    ACK           worker / review / watch / 功能型 agent     已接单
    START         worker / review / watch / 功能型 agent     正式开工
    PROGRESS      worker / review / watch / 功能型 agent     阶段完成 / 阶段切换
    HANDOFF       worker / review / watch / 功能型 agent     交接下游
    BLOCKED       worker / review / watch / manager          卡点 / 缺材料 / 缺决策
    REVIEW        worker_review / review_course               复核 verdict
    CLOSEOUT      manager                                    唯一正式业务收口
    ALERT         Sophon / auto_ops / manager                运行时 / 质量异常
    RECORDED      Luke_recorder                              已记录关键发言
    OPS_SNAPSHOT  manager / auto_ops                         运营看板快照

M9 note on OPS_SNAPSHOT:
    M3 already has `employee_snapshot_card` and `team_snapshot_card` in
    `feishu/cards.py`; those functions build raw Feishu card dicts
    directly (bypassing the v2 protocol) because they predate
    cards_v2.py. OPS_SNAPSHOT is the v2-protocol bridge for those
    snapshot surfaces: it lets `say --card OPS_SNAPSHOT` route through
    `validate_card` + `render_to_card_dict` so the snapshot cards get
    the same role gate and field validation as every other card type.
    If a snapshot surface does not yet exist (e.g. a future M2/M3
    dashboard card), using PROGRESS or ALERT as a temporary adapter is
    acceptable — but OPS_SNAPSHOT should be preferred once the surface
    is ready.
"""
from __future__ import annotations

from typing import Iterable


# ── card type namespace ────────────────────────────────────────


class CardType:
    ACK = "ACK"
    START = "START"
    PROGRESS = "PROGRESS"
    HANDOFF = "HANDOFF"
    BLOCKED = "BLOCKED"
    REVIEW = "REVIEW"
    CLOSEOUT = "CLOSEOUT"
    ALERT = "ALERT"
    RECORDED = "RECORDED"
    OPS_SNAPSHOT = "OPS_SNAPSHOT"

    ALL = ("ACK", "START", "PROGRESS", "HANDOFF", "BLOCKED",
           "REVIEW", "CLOSEOUT", "ALERT", "RECORDED",
           "OPS_SNAPSHOT")


# ── role → allowed card types ──────────────────────────────────
#
# Default (unknown agent) → restrictive worker-style allow-list.
# When `known_agents` is passed and the agent is not in it, the
# function returns an empty frozenset — fail-closed, so a typo in
# the CLI cannot accidentally grant CLOSEOUT privileges.

_ROLE_ALLOWED_TYPES: dict[str, frozenset[str]] = {
    "manager": frozenset({
        CardType.ACK, CardType.START, CardType.PROGRESS,
        CardType.HANDOFF, CardType.BLOCKED,
        CardType.CLOSEOUT, CardType.ALERT,
        CardType.OPS_SNAPSHOT,
    }),
    "worker_review": frozenset({
        CardType.ACK, CardType.START, CardType.PROGRESS,
        CardType.HANDOFF, CardType.BLOCKED,
        CardType.REVIEW,
    }),
    "Sophon": frozenset({
        CardType.ACK, CardType.START, CardType.PROGRESS,
        CardType.HANDOFF, CardType.BLOCKED,
        CardType.ALERT,
    }),
    # Historical aliases kept for backwards compatibility with old logs/fixtures.
    "review_course": frozenset({
        CardType.ACK, CardType.START, CardType.PROGRESS,
        CardType.HANDOFF, CardType.BLOCKED,
        CardType.REVIEW,
    }),
    "auto_ops": frozenset({
        CardType.ACK, CardType.START, CardType.PROGRESS,
        CardType.HANDOFF, CardType.BLOCKED,
        CardType.ALERT,
        CardType.OPS_SNAPSHOT,
    }),
    "Luke_recorder": frozenset({
        CardType.ACK, CardType.START, CardType.PROGRESS,
        CardType.HANDOFF, CardType.BLOCKED,
        CardType.RECORDED,
    }),
    "Hermes": frozenset({
        CardType.ACK, CardType.START, CardType.PROGRESS,
        CardType.HANDOFF, CardType.BLOCKED,
    }),
}

_WORKER_DEFAULT_ALLOWED = frozenset({
    CardType.ACK, CardType.START, CardType.PROGRESS,
    CardType.HANDOFF, CardType.BLOCKED,
})


def agent_role_allowed(agent: str,
                       known_agents: Iterable[str] = ()) -> frozenset[str]:
    if known_agents and agent not in set(known_agents):
        return frozenset()
    if agent in _ROLE_ALLOWED_TYPES:
        return _ROLE_ALLOWED_TYPES[agent]
    return _WORKER_DEFAULT_ALLOWED


# ── required fields per card type ─────────────────────────────
#
# Plan 2026-07-01 §设计一 必填字段 table.  RECORDED is the only
# type without `需要老板介入` — Luke_recorder's job is to ack
# "已记录", not to ask the boss for input.

REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    CardType.ACK: (
        "任务", "负责人", "当前阶段", "下一步", "需要老板介入",
    ),
    CardType.START: (
        "任务", "执行路线", "首个检查点", "预计交接对象", "需要老板介入",
    ),
    CardType.PROGRESS: (
        "任务", "当前阶段", "已完成", "证据", "下一阶段", "需要老板介入",
    ),
    CardType.HANDOFF: (
        "任务", "交接对象", "交接内容", "证据", "待检查点",
        "运行状态变化", "需要老板介入",
    ),
    CardType.BLOCKED: (
        "任务", "卡点", "已尝试", "需要谁处理", "默认处理方案",
        "需要老板介入",
    ),
    CardType.REVIEW: (
        "任务", "verdict", "证据", "问题项", "下一步", "需要老板介入",
    ),
    CardType.CLOSEOUT: (
        "任务", "正式结论", "产物", "证据", "剩余风险", "下一步",
        "需要老板介入",
    ),
    CardType.ALERT: (
        "异常类型", "影响范围", "已自动处理", "当前状态",
        "需要谁处理", "需要老板介入",
    ),
    CardType.RECORDED: (
        "已记录内容一句话摘要", "来源", "去向",
    ),
    CardType.OPS_SNAPSHOT: (
        "看板类型", "当前状态", "顶行动", "证据引用",
        "常驻摘要", "需要老板介入",
    ),
}

# Controlled-vocabulary per (card_type, field).  Empty = accept any
# non-empty string.  Plan only pins `verdict` for REVIEW today;
# extend here as the boss pins more vocabulary.
_FIELD_VALUE_ALLOWED: dict[tuple[str, str], frozenset[str]] = {
    (CardType.REVIEW, "verdict"): frozenset({"通过", "打回", "需补充"}),
    (CardType.BLOCKED, "需要老板介入"): frozenset({"是", "否"}),
    (CardType.ALERT, "需要老板介入"): frozenset({"是", "否"}),
    (CardType.OPS_SNAPSHOT, "需要老板介入"): frozenset({"是", "否"}),
}

# "需要老板介入" affirmative values, used by `needs_boss_intervention`
# in cards_v2.py and by the publish filter / ALERT priority hints.
_BOSS_INTERVENTION_YES = frozenset({"是", "yes", "true", "y", "1"})


# ── severity → color mapping (M9) ─────────────────────────────
#
# Used by `render_to_card_dict` when the caller specifies a severity
# rather than an explicit color.  The mapping is intentionally
# conservative: "info" and "success" are the common light-weight
# cards; "warning" uses orange (more attention than yellow but less
# alarming than red); "critical" is reserved for ALERT / BLOCKED
# where the boss must act.
#
# The mapping only covers severity values.  When the caller passes
# an explicit color (e.g. `color="green"`), it is not overridden
# by severity — the color takes precedence.

SEVERITY_COLOR_MAP: dict[str, str] = {
    "success": "green",
    "info": "blue",
    "warning": "orange",
    "critical": "red",
}


def severity_to_color(severity: str | None) -> str | None:
    """Map a severity string to the canonical Feishu template color.

    Returns the color name or None when the severity is not in the
    map (caller should fall back to the card's own `color` field).
    Returns None for empty/None input.
    """
    return SEVERITY_COLOR_MAP.get(str(severity or "").lower())
