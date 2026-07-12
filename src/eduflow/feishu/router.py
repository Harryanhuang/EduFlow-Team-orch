"""Pure routing decisions for inbound Feishu events.

Given a Feishu message event dict and the team's agent list, decide one of:
  - DROP:      dedup, cross-team, bot self-talk, empty text, no msg_id,
               oversized message, duplicate message_id,
               agent message with no @target
  - SLASH:     text starts with `/` after stripping any `[<sender>] `
               prefix → router-level zero-LLM dispatch
               (handled by `feishu/slash.dispatch`)
  - BROADCAST: `@team` / `@all` triggers fan-out to every
               non-sender agent (token-boundary handling includes
               ASCII period in the @-name terminator set)
  - ROUTE:     `@<agent>` mention → deliver to those agents, OR
               unrecognised sender (= human, defaults to `default_target`)

`commands/router.py` calls this once per event from the subscribe loop and
`feishu/deliver.apply` acts on the Decision. A module-level seen-message-id
set provides deduplication for callers that do not pass their own
`seen_msg_ids`; production callers should pass a bounded set.

Drop reasons (`Decision.reason`) are stable strings so log filters
can grep for them: `no_msg_id` / `dedup` / `cross_team` / `bot_self`
/ `empty` / `agent_no_target` / `message too long` / `duplicate message_id`.
"""
from __future__ import annotations

import re
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

from eduflow.runtime import tunables


class Action(str, Enum):
    DROP = "DROP"
    ROUTE = "ROUTE"
    SLASH = "SLASH"   # operator slash command, dispatched at router-level (zero LLM)
    BROADCAST = "BROADCAST"  # @team / @all / 全体成员 → every non-sender agent


@dataclass(frozen=True)
class Decision:
    action: Action
    targets: list[str] = field(default_factory=list)   # agents to deliver to
    sender: str = ""                                    # parsed agent sender, if recognised
    text: str = ""                                      # cleaned message text
    msg_id: str = ""
    reason: str = ""                                    # drop reason or "" on route
    create_time: str = ""                               # epoch ms (for catchup cursor)
    sender_id: str = ""                                 # Feishu open_id of the message sender
    user_language: str = ""                             # P5: "zh-CN" or "en-US"
    schedule_intent: bool = False                       # P5: tag for the manager skill

    def is_drop(self) -> bool:
        return self.action is Action.DROP


# Sender prefix is the bracketed form `[agent]` only.  `@agent` is treated
# as a mention regardless of position (so a human typing `@worker_cc do X`
# routes to worker_cc rather than being misread as worker_cc-as-sender).
_SENDER_RE = re.compile(r"^\s*\[([A-Za-z0-9_\-]+)\]\s*")
_MENTION_RE = re.compile(r"@([A-Za-z0-9_\-]+)")

# Broadcast trigger tokens. Routing no longer fans out on these —
# every human message goes to manager only. Kept so the manager
# identity template can teach: "when the boss says @team / @all,
# you (manager) dispatch each worker individually".
_BROADCAST_TOKENS = ("@team", "@all", "@everyone")

_MAX_MESSAGE_LEN = 4000
_SEEN_MESSAGE_IDS: set[str] = set()

_RATE_LIMIT_MAX = 10          # messages
_RATE_LIMIT_WINDOW_S = 60     # seconds
_SENDER_TIMESTAMPS = {}

# ── P5: per-sender language session state ───────────────────────────
# Bounded dict keyed by sender_id. The first message from a sender sets
# the language; subsequent messages reuse the cached value so mixed
# CN/EN lines don't flip the language. Test isolation is provided by
# `_reset_session_state()`.

_SESSION_LANGUAGE: dict[str, str] = {}
_SESSION_LANGUAGE_MAX = 4096
_CJK_RE = re.compile(r"[㐀-鿿]")

# Schedule-intent keywords. The router only FLAGS the intent; it never
# parses times or writes the scheduler store. The
# `eduflow-scheduled-task-manager` skill owns all parsing and P4 API calls.
_SCHEDULE_KEYWORDS = (
    "schedule", "recurring", "recurrence",
    "daily", "weekly", "monthly",
    "reminder", "remind",
    "定时", "日程", "周期", "每周", "每天", "每月",
    "提醒", "安排", "周报", "日报", "月报",
)


def _detect_language(text: str) -> str:
    """Return 'zh-CN' if the text contains CJK Unified Ideographs, else
    'en-US'.  Heuristic only; the manager skill can override."""
    if _CJK_RE.search(text or ""):
        return "zh-CN"
    return "en-US"


def _session_language(sender_id: str, text: str) -> str:
    """Return the cached language for `sender_id`, computing + caching on
    first sight.  Empty / missing sender_id never reaches the cache."""
    if not sender_id:
        return _detect_language(text)
    cached = _SESSION_LANGUAGE.get(sender_id)
    if cached:
        return cached
    lang = _detect_language(text)
    if len(_SESSION_LANGUAGE) >= _SESSION_LANGUAGE_MAX:
        # Evict an arbitrary entry to keep the dict bounded.
        _SESSION_LANGUAGE.pop(next(iter(_SESSION_LANGUAGE)))
    _SESSION_LANGUAGE[sender_id] = lang
    return lang


def _detect_schedule_intent(text: str) -> bool:
    """Return True if `text` looks like a scheduling request.  Keyword
    match only — never parses times, never resolves fuzzy markers."""
    lowered = (text or "").lower()
    if not lowered.strip():
        return False
    return any(kw in lowered for kw in _SCHEDULE_KEYWORDS)


def _reset_session_state() -> None:
    """Clear session-language cache.  Exported for test isolation only."""
    _SESSION_LANGUAGE.clear()


def _rate_limit_ok(sender_id: str) -> bool:
    now = time.monotonic()
    window = _SENDER_TIMESTAMPS.setdefault(sender_id, deque())
    while window and window[0] < now - _RATE_LIMIT_WINDOW_S:
        window.popleft()
    if len(window) >= _RATE_LIMIT_MAX:
        return False
    window.append(now)
    return True


def _reset_rate_limit() -> None:
    """Clear sender rate-limit state. Exported for test isolation only."""
    _SENDER_TIMESTAMPS.clear()


def _max_message_len() -> int:
    cfg = tunables.load() or {}
    return int(cfg.get("feishu", {}).get("max_message_len", _MAX_MESSAGE_LEN))


def _record_seen(msg_id: str, seen_msg_ids: set[str] | None) -> None:
    """Remember a routed message id for callers without their own dedup set.

    Dropped messages are not recorded so that unrelated tests/fixtures that
    reuse the same message_id do not false-positive as duplicates."""
    if seen_msg_ids is None and msg_id:
        _SEEN_MESSAGE_IDS.add(msg_id)


def _parse_sender(text: str, agents: set[str]) -> tuple[str, str]:
    """If the message starts with `[agent]` and `agent` is on the team,
    strip it and return (agent, remaining_text); else ("", text)."""
    m = _SENDER_RE.match(text)
    if not m or m.group(1) not in agents:
        return "", text
    return m.group(1), text[m.end():].lstrip()



# Card-title sender-extraction. Worker `eduflow say` posts
# interactive cards with title `{emoji} {agent} · {role}`; the
# subscribe layer's text extractor embeds the card title at the
# start of the extracted text. Match it here so we can attribute a
# chat message to the originating worker even though the inbound
# `sender_id` is the bot's open_id (one app, all agents share it).
# Manager's own messages still get dropped to avoid self-loops.
_CARD_TITLE_AGENT_RE = re.compile(
    r"(?:^|<card title=\")[^\">\n]*?(?<![\w])([A-Za-z][A-Za-z0-9_\-]+)\s*·"
)


def _card_sender_agent(text: str, agents: set[str]) -> str:
    """Return the agent name parsed from a card-format `say` message,
    or "" if not a recognizable card. Used by router to attribute
    bot-sent messages to the originating worker so manager can see
    them in inbox."""
    for m in _CARD_TITLE_AGENT_RE.finditer(text):
        candidate = m.group(1)
        if candidate in agents:
            return candidate
    return ""


def classify_event(event: dict, *,
                   agents: list[str] | None = None,
                   team_agents: list[str] | None = None,
                   manager=None,
                   chat_id: str = "",
                   bot_id: str = "",
                   seen_msg_ids: set[str] | None = None,
                   default_target: str = "manager") -> Decision:
    """Classify one inbound Feishu message event.

    Single-interface routing model: ALL human chat messages route to
    `default_target` (manager). `@worker_cc` / `@team` no longer fan
    out at the router — manager is the sole interface to the boss
    and dispatches workers via `eduflow send` herself. Bot-sent
    interactive cards from non-manager workers also route to
    manager's inbox so she can see worker chat replies and
    summarize. Manager's own bot messages still drop (avoid loop).

    Args:
        event: dict with keys message_id, chat_id, sender_id, text, msg_type
        agents: list of agent names known to this deployment (preferred)
        team_agents: backward-compatible alias for `agents`
        manager: ignored (legacy parameter)
        chat_id: this team's chat — events from other chats get dropped
        bot_id: this app's bot open_id — bot self-talk gets dropped UNLESS
                it parses as a non-manager worker card (then routed to manager)
        seen_msg_ids: optional dedup set; populate as you process
        default_target: agent that receives all routed messages (manager)

    Decision rules (first match wins):
        oversized text         → DROP "message too long"
        no message_id          → DROP "no_msg_id"
        seen msg_id            → DROP "dedup" (caller-supplied set)
                               or DROP "duplicate message_id" (module set)
        wrong chat_id          → DROP "cross_team"
        sender == bot_id AND
          card sender is manager
            (or unidentifiable) → DROP "bot_self"
        sender == bot_id AND
          card sender is worker → ROUTE to [manager] (manager sees worker say)
        empty text             → DROP "empty"
        text starts with `/`   → SLASH (operator command, zero-LLM dispatch)
        agent-tagged sender + no @target → DROP "agent_no_target"
        else (human sender)    → ROUTE to [default_target]
    """
    if agents is not None and team_agents is not None:
        raise TypeError("classify_event() got multiple values for agent list argument")
    if agents is not None:
        team_agents = agents
    if team_agents is None:
        team_agents = []

    _ = manager  # legacy/ignored parameter

    agents = set(team_agents)
    msg_id = event.get("message_id", "")
    text = event.get("text") or ""
    common = {
        "msg_id": msg_id,
        "create_time": str(event.get("create_time", "")),
        "sender_id": event.get("sender_id", ""),
    }
    if len(text) > _max_message_len():
        return Decision(Action.DROP, reason="message too long", **common)
    if not msg_id:
        return Decision(Action.DROP, reason="no_msg_id", **common)
    if seen_msg_ids is not None and msg_id in seen_msg_ids:
        return Decision(Action.DROP, reason="dedup", **common)
    if msg_id in _SEEN_MESSAGE_IDS:
        return Decision(Action.DROP, reason="duplicate message_id", **common)
    if chat_id and event.get("chat_id") and event["chat_id"] != chat_id:
        return Decision(Action.DROP, reason="cross_team", **common)

    if not _rate_limit_ok(event.get("sender_id", "")):
        return Decision(Action.DROP, reason="rate limit exceeded", **common)

    raw_text = (event.get("text") or "").strip()

    # Bot self-talk: the app sent this. Default = drop. Exception:
    # if the card was posted by a NON-manager worker (per card-title
    # parse), route to manager's inbox so manager has visibility into
    # worker chat replies. Self-loop guard: manager's own cards always
    # drop here.
    #
    # Bot detection: `sender_type in {"app", "app_id"}` covers both
    # live lark-cli `--compact` payloads (sender_type=app) and
    # chat-messages-list responses (id_type=app_id). `bot_id ==
    # sender_id` kept as fallback for fixtures / legacy callers.
    sender_type = event.get("sender_type", "")
    is_bot = (sender_type in ("app", "app_id")
              or (bot_id and event.get("sender_id") == bot_id))
    if is_bot:
        card_agent = _card_sender_agent(raw_text, agents) if raw_text else ""
        if card_agent and card_agent != default_target:
            _record_seen(msg_id, seen_msg_ids)
            lang = _session_language(event.get("sender_id", ""), raw_text)
            return Decision(Action.ROUTE, targets=[default_target],
                            sender=card_agent, text=raw_text,
                            user_language=lang,
                            schedule_intent=_detect_schedule_intent(raw_text),
                            **common)
        return Decision(Action.DROP, reason="bot_self", **common)

    if not raw_text:
        return Decision(Action.DROP, reason="empty", **common)

    # Slash command: matched at router level, NOT injected into any pane.
    # Deliver layer runs the registered handler and posts the result back
    # to chat as a bot reply. Zero LLM involvement.
    slash_text = re.sub(r"^\s*\[[^\]]+\]\s*", "", raw_text)
    if slash_text.startswith("/"):
        _record_seen(msg_id, seen_msg_ids)
        return Decision(Action.SLASH, text=slash_text, **common)

    sender, text = _parse_sender(raw_text, agents)

    # P5: detect user language and schedule intent BEFORE the route
    # decision so the manager skill sees them in the Decision object.
    # The router MUST NOT parse times or write the scheduler store
    # itself — that is the skill's job (calls P4 manager_ops APIs).
    lang = _session_language(event.get("sender_id", ""), text)
    intent = _detect_schedule_intent(text)

    # Human / unknown sender → manager only. `@worker_cc` and
    # `@team` are no longer routing instructions; they're text
    # content for manager to read and decide how to dispatch.
    if not sender:
        _record_seen(msg_id, seen_msg_ids)
        return Decision(Action.ROUTE, targets=[default_target], text=text,
                        user_language=lang, schedule_intent=intent, **common)

    # agent-tagged message with no @-target → broadcast with nobody to hear it
    return Decision(Action.DROP, sender=sender, text=text,
                    reason="agent_no_target", **common)
