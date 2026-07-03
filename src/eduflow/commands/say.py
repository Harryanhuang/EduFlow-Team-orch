"""`eduflow say <agent> <message> [--reply <message_id>]`

Post a chat message as `<agent>`.  Default identity is bot; pass
`--as user` to post as the logged-in lark-cli user.  A persistent default
can be set via `EDUFLOW_LARK_SEND_AS=user|bot` for the whole shell.

The message is also mirrored to the local inbox (so the audit log keeps
a copy) — pass `--no-local` to skip that.

Phase-1 (2026-07-01): optional `--card <TYPE>` flag routes the body
through the structured card protocol v2 (see `feishu.cards_v2`).
Without `--card`, the legacy `simple_card` path is unchanged so
existing operators / docs / agents keep working.

Exits non-zero if `chat_id` is unset (run setup or set runtime_config.json).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

from eduflow.feishu import chat as feishu_chat
from eduflow.feishu.cards import simple_card
from eduflow.runtime import config
from eduflow.store import local_facts
from eduflow.util import env_str, error_exit, pop_bool_flag, pop_flag, usage_error


USAGE = (
    "usage: eduflow say <agent> <message> "
    "[--body <message>] [--reply <message_id>] [--as user|bot] [--no-local] "
    "[--to user|manager|worker_<name>] [--channel main|supervisor] "
    "[--card ACK|START|PROGRESS|HANDOFF|BLOCKED|REVIEW|CLOSEOUT|ALERT|RECORDED|OPS_SNAPSHOT]"
)


# Card colors per agent. manager → blue (fixed visual weight, "boss
# answer" channel). Workers auto-cycle through _WORKER_PALETTE in
# team-config order so each worker reads as a distinct color in chat —
# 2026-05-09: previously every worker fell back to "green", making
# multi-worker dispatch cards visually indistinguishable. Per-agent
# `card_color` in eduflow.toml still wins (override).
#
# Package 8: explicit per-agent-name color mapping so each role is
# visually stable regardless of team-config order.
_AGENT_CARD_COLORS = {
    "manager": "blue",
    "Anna": "yellow",
    "auto_ops": "red",
}
_WORKER_PALETTE = ("green", "purple", "orange", "yellow")

# Package 8: explicit color map for known agent names. Checked first in
# _color_for(); unknown agents fall back to the safe default (blue).
_AGENT_COLOR_MAP = {
    "manager": "blue",
    "worker_course": "purple",
    "review_course": "green",
    "auto_ops": "red",
    "worker_builder": "orange",
    "Anna": "yellow",
    "worker_qbank": "turquoise",
    "Hermes": "grey",
}

# Default emoji per agent name. Used when eduflow.toml doesn't
# provide an explicit `emoji` field. The card sender header
# (`{emoji} {agent} · {role}`) signals who's talking at a glance.
_DEFAULT_AGENT_EMOJI = {
    "manager": "🎯",
    "Hermes": "📚",
    "worker_cc": "💎",
    "worker_codex": "🟦",
    "worker_kimi": "🟧",
    "worker_gemini": "🟩",
    "worker_qwen": "🟪",
}


def _role_of(name: str) -> str:
    """Map agent name → role bucket used by chat.publish keys.
    Convention: 'manager' → manager; 'worker_*' → worker; 'user' → user;
    anything else → user (safe default; "对老板说" is the most common
    intent when receiver is unrecognized)."""
    if name == "manager":
        return "manager"
    if name == "user" or not name:
        return "user"
    if name.startswith("worker") or name in {"auto_ops", "review_course", "Hermes"}:
        return "worker"
    return "user"


def _publish_allowed(sender: str, to_target: str) -> bool:
    """Look up publish rule for sender→receiver, with agent-level override.

    Priority:
      1. team.agents.<sender>.publish_overrides.{key}  (single-agent override)
      2. chat.publish.{key}                             (team-wide tunable)
      3. default True                                    (preserves pre-Step-3 behavior)

    `key` = "{sender_role}_to_{receiver_role}".

    "always" is treated as True — schema uses it as a "don't silence"
    hint but the runtime semantic is just "send".

    Agent-level override is for cases like "I want worker_cc 完工卡进群,
    but worker_codex 完工卡静默" — set worker_codex.publish_overrides
    = {worker_to_user = false} without touching the global rule.
    """
    from eduflow.runtime import tunables
    sender_role = _role_of(sender)
    receiver_role = _role_of(to_target)
    key = f"{sender_role}_to_{receiver_role}"

    # 1. Agent-level override
    try:
        agent_cfg = config.agent_config(sender)
    except KeyError:
        agent_cfg = {}
    overrides = agent_cfg.get("publish_overrides") or {}
    if key in overrides:
        v = overrides[key]
        return v == "always" or bool(v)

    # 2. Global tunable
    val = tunables.tunable(f"chat.publish.{key}", True)
    if val == "always":
        return True
    return bool(val)


def _worker_reason_override(sender: str, to_target: str, message: str) -> bool:
    """Allow a small, explicit subset of worker reassurance through even when
    `chat.publish.worker_to_user=false`.

    Phase 5 (2026-07-01) 主群体验收敛: the whitelist was trimmed. Low-
    value "still-alive / no-news" reassurances are now DROPPED from the
    main chat (they go to `/team` panel + internal log only), keeping
    only genuine stage-change signals.  Removed markers:
      - "暂无新结果"  (no news → not a stage change)
      - "处理中但卡在" (superseded by BLOCKED card)
      - "盯盘中" / "盯盘正常" / "巡检正常" / "运行态简报"
        (auto_ops periodic presence — Phase 5 turned this off; now
        stage-driven only, see [auto_ops].stage_driven)
    Kept markers are all real transitions (接单 / 开工 / 交接 /
    卡点 / verdict) that a boss scanning the group in 30s needs.
    """
    if _role_of(sender) != "worker" or _role_of(to_target) != "user":
        return False
    text = str(message or "")
    allowed_markers = (
        "任务已接单",
        "任务已开始处理",
        "接单确认",
        "在岗确认",
        "开始处理",
        "阶段进度",
        "当前卡在",
        "已交接",
        "已回交 manager",
        "开始生产",
        "已开始生产",
        "开始复核",
        "已开始复核",
        "已完成并交给 manager",
        "已接到当前学科任务",
        "正在处理当前学科",
        "已交给 review",
        "当前学科待 review 接手",
        "正在 review 当前学科",
        "review 已接单",
        "review 已开始",
        "review 开始复核",
        "review 当前卡在",
        "已要求 minor fix",
        "review 已通过，待 manager 收口",
        "builder 已接单",
        "builder 已开始处理",
        "builder 当前卡在",
        "builder 产物已回交",
        "qbank 校验已接单",
        "qbank 校验已开始",
        "qbank 当前卡在",
        "qbank 首个 verdict 已就绪",
        "题库验证",
        "题库校验",
        "qbank readiness",
        "验证工具",
        "统一 manifest",
        "验证报告",
        "发现异常",
        "已收到当前高优监督任务",
    )
    return any(marker in text for marker in allowed_markers)


def _color_for(agent: str, cfg_color: str | None = None) -> str:
    """Resolve card header color. Per-agent `card_color` (or legacy
    `color`) in eduflow.toml wins; else check explicit
    ``_AGENT_COLOR_MAP``; else ``_AGENT_CARD_COLORS``; else worker_*
    cycle through ``_WORKER_PALETTE`` in team-config order; else
    fallback blue. Never raises on unknown agent name."""
    if cfg_color:
        return cfg_color
    # Package 8: explicit agent-name color map takes priority over
    # palette cycling so each role is visually stable.
    if agent in _AGENT_COLOR_MAP:
        return _AGENT_COLOR_MAP[agent]
    if agent in _AGENT_CARD_COLORS:
        return _AGENT_CARD_COLORS[agent]
    if agent.startswith("worker"):
        try:
            agents = config.load_team().get("agents", {}) or {}
            workers = [n for n in agents if n != "manager" and n.startswith("worker")]
            idx = workers.index(agent) if agent in workers else 0
        except Exception:
            idx = 0
        return _WORKER_PALETTE[idx % len(_WORKER_PALETTE)]
    # Safe default for unknown agents — never error
    return "blue"


def _emoji_for(agent: str, cfg_emoji: str | None = None) -> str:
    """Resolve sender emoji. team.json `emoji` field wins, otherwise
    fall back to `_DEFAULT_AGENT_EMOJI`, otherwise ⚙️ (system)."""
    if cfg_emoji:
        return cfg_emoji
    return _DEFAULT_AGENT_EMOJI.get(agent, "⚙️")


def _agent_card_title(agent: str, cfg: dict) -> str:
    """Card title format ported from `main`'s `_agent_card_title`:
    `{emoji} {agent} · {role}` — English agent id + Chinese role at a
    glance, no more bare `[agent]` brackets that boss flagged as too
    bland."""
    emoji = _emoji_for(agent, cfg.get("emoji"))
    role = cfg.get("role") or "系统"
    return f"{emoji} {agent} · {role}"


def _channel_card_identity(agent: str, agent_cfg: dict, channel: str) -> tuple[str, str]:
    """Resolve the visible sender title/color for the target channel.

    Supervisor channel may use a display-only identity from
    `[feishu.supervisor]` without requiring a team-local agent slot.
    """
    if channel != "supervisor":
        cfg_color = agent_cfg.get("card_color") or agent_cfg.get("color")
        return _agent_card_title(agent, agent_cfg), _color_for(agent, cfg_color)

    supervisor_cfg = config.supervisor_sender_config()
    if not supervisor_cfg:
        cfg_color = agent_cfg.get("card_color") or agent_cfg.get("color")
        return _agent_card_title(agent, agent_cfg), _color_for(agent, cfg_color)

    display_name = supervisor_cfg.get("sender_name", agent)
    display_role = supervisor_cfg.get("sender_role", "监督通道")
    display_emoji = supervisor_cfg.get("sender_emoji", "🛡️")
    title = f"{display_emoji} {display_name} · {display_role}"
    color = supervisor_cfg.get("sender_color") or "red"
    return title, color


@dataclass(frozen=True)
class _Args:
    agent: str
    message: str
    reply_to: str = ""
    as_user: bool = False
    local: bool = True
    to: str = "user"   # receiver hint for chat.publish filter; default
                       # "user" preserves backwards-compat for callers
                       # that don't pass --to (manager → user is the
                       # typical case)
    channel: str = "main"
    card_type: str = ""  # structured-card v2 type; empty = legacy path


def _parse(argv: list[str]) -> _Args | None:
    if len(argv) < 2:
        return None
    rest = list(argv)
    # `--no-card` is the legacy way to opt out of card rendering. It is
    # still accepted (and ignored — every `eduflow say` posts a v2 card)
    # for backwards-compat with operators / docs that still pass it.
    pop_bool_flag(rest, "--no-card")
    # `--card` is dual-purpose:
    #   - `--card TYPE` (new): structured v2 card protocol.  TYPE may
    #     be one of the nine known types OR a typo (BOGUS / CLOSEOUTT) —
    #     unknown types fall through to the validator which returns
    #     exit 1 with a clear error.  We do NOT silently treat unknown
    #     values as legacy no-op, because that would hide typos.
    #   - `--card` alone (legacy): boolean no-op (every say already
    #     sent a card; R99 left the flag as a stable no-op sentinel
    #     so older operators / docs / agents keep working)
    card_type = ""
    if "--card" in rest:
        i = rest.index("--card")
        if i + 1 < len(rest):
            card_type = rest[i + 1].strip().upper()
            del rest[i:i + 2]
        else:
            # Legacy `--card` boolean — consume silently.
            rest.remove("--card")
    no_local = pop_bool_flag(rest, "--no-local")
    body_explicit = pop_flag(rest, "--body")
    reply_to = pop_flag(rest, "--reply") or ""
    as_explicit = pop_flag(rest, "--as")
    to_explicit = pop_flag(rest, "--to") or "user"
    channel = pop_flag(rest, "--channel") or "main"
    if (
        "--body" in rest
        or "--reply" in rest
        or "--as" in rest
        or "--to" in rest
        or "--channel" in rest
    ):
        return None  # flag present but value missing
    if len(rest) < 1 or (len(rest) < 2 and body_explicit is None):
        return None
    agent = rest[0]
    rest = rest[1:]
    # `feishu.send_as` cascade: --as flag > legacy env > tunable > "bot" default.
    if as_explicit is not None:
        as_value = as_explicit
    else:
        legacy = env_str("EDUFLOW_LARK_SEND_AS")
        if legacy:
            as_value = legacy
        else:
            from eduflow.runtime import tunables
            as_value = str(tunables.tunable("feishu.send_as", "bot"))
    if body_explicit is None and not rest:
        return None
    return _Args(
        agent=agent,
        message=str(body_explicit) if body_explicit is not None else " ".join(rest),
        reply_to=reply_to,
        as_user=(as_value == "user"),
        local=not no_local,
        to=to_explicit,
        channel=channel,
        card_type=card_type.strip().upper(),
    )


def _resolve_delivery_channel(channel: str) -> tuple[str, str, str]:
    normalized = str(channel or "main").strip() or "main"
    if normalized == "main":
        chat = config.chat_id()
        profile = config.lark_profile()
        return normalized, chat, profile
    if normalized == "supervisor":
        chat = config.supervisor_chat_id()
        profile = config.supervisor_lark_profile()
        return normalized, chat, profile
    return normalized, "", ""


def main(argv: list[str]) -> int:
    args = _parse(argv)
    if args is None:
        return usage_error(USAGE)

    channel_name, chat, profile = _resolve_delivery_channel(args.channel)
    if channel_name not in {"main", "supervisor"}:
        return error_exit(f"❌ unknown channel: {args.channel}")
    if not chat:
        if channel_name == "supervisor":
            return error_exit("❌ supervisor chat_id not set")
        return error_exit("❌ chat_id not set in runtime_config.json")

    local_facts.touch_heartbeat(args.agent)
    if args.local:
        # Audit log is best-effort — a disk-full or permission-denied
        # error here should NOT block the chat send (the boss is
        # waiting for the message to land in the group; losing the
        # local audit row is a smaller cost than losing the message).
        try:
            local_facts.append_log(args.agent, "say", args.message)
        except OSError as e:
            print(f"  ⚠️ audit log write failed for {args.agent}: {e}",
                  file=sys.stderr)

    # Resolve agent's role + emoji + color from eduflow.toml. Used
    # for the card title (`{emoji} {agent} · {role}`) and for color
    # override. Missing config falls back to the per-agent default
    # tables defined at the top of this file.
    try:
        agent_cfg = config.agent_config(args.agent)
    except KeyError:
        agent_cfg = {}

    # Every `eduflow say` sends a v2 card. `reply_to` is silently
    # ignored because Feishu interactive cards don't thread.
    if args.reply_to:
        print(f"  ⚠️ --reply ignored (Feishu cards don't thread)",
              file=sys.stderr)
    title, card_color = _channel_card_identity(args.agent, agent_cfg, channel_name)

    # Phase-1 structured-card path: validate role + required fields
    # before render.  Role violations block (exit 1) — the agent
    # attempted something outside its scope.  Field/value violations
    # degrade to internal (exit 0) — the audit log already captured
    # the intent (line 355), the chat stays clean, and the operator
    # sees a warning explaining what was missing.  Plan 2026-07-01
    # §设计一.
    if args.card_type:
        from eduflow.feishu import cards_v2
        from eduflow.feishu.cards_v2_schema import CardType as _CT
        if args.card_type not in _CT.ALL:
            print(
                f"❌ {args.agent} --card {args.card_type}: unknown card type "
                f"(allowed: {', '.join(_CT.ALL)})",
                file=sys.stderr,
            )
            return 1
        try:
            known_agents = config.agent_names()
        except Exception:
            known_agents = []
        card_obj = cards_v2.build_card(
            args.card_type, args.agent, args.message, color=card_color,
        )
        validation = cards_v2.validate_card(card_obj, known_agents=known_agents)
        if not validation:
            if validation.is_role_violation:
                print(
                    f"❌ {args.agent} --card {args.card_type}: "
                    + "; ".join(validation.errors),
                    file=sys.stderr,
                )
                return 1
            print(
                f"📝 {args.agent} --card {args.card_type} validation failed, "
                f"degraded to internal: {'; '.join(validation.errors)}",
                file=sys.stderr,
            )
            return 0
        # Render the validated card with `[TYPE]` prepended to the
        # existing identity title so the chat header carries both the
        # type tag and the agent identity.
        typed_title = f"[{args.card_type}] {title}"
        card = cards_v2.render_to_card_dict(
            card_obj, header_title=typed_title,
        )
    else:
        card = simple_card(title, args.message, color=card_color)

    # Step 3: chat.publish filter — operator can silence specific
    # sender→receiver channels via toml (default all true = preserve
    # pre-Step-3 behavior). Audit log was already written above
    # regardless of publish state, so silenced messages still leave a
    # trail.
    if not _publish_allowed(args.agent, args.to):
        if _worker_reason_override(args.agent, args.to, args.message):
            pass
        else:
            from eduflow.runtime import tunables
            sender_role = _role_of(args.agent)
            receiver_role = _role_of(args.to)
            key = f"chat.publish.{sender_role}_to_{receiver_role}"
            print(f"📝 {args.agent} → silenced by [{key}]=false; logged only")
            return 0

    result = feishu_chat.send_card(
        chat, card,
        profile=profile,
        as_user=args.as_user,
    )
    if result is None:
        return error_exit(f"❌ Feishu send failed for {args.agent}")

    msg_id = result.get("message_id", "")
    print(f"✅ {args.agent} → {channel_name} chat (message_id={msg_id})")
    return 0
