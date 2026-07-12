"""P5: router forwards user language to the scheduled-task manager skill.

The router does NOT guess times, parse schedules, or mutate the scheduler
store.  It only:
  * tags the Decision with the detected `user_language`
  * tags the Decision with `schedule_intent` when the user text matches
    the obvious scheduling keyword set
  * remembers the language for the same sender across messages via a
    bounded session-state dict so re-detection is stable

The actual schedule parsing and draft creation live in the
`eduflow-scheduled-task-manager` skill body (markdown), which is loaded
by the manager agent and calls P4 manager_ops APIs.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from eduflow.feishu.router import Action, classify_event


_AGENTS = ["manager", "worker_cc"]


# ── helpers ──────────────────────────────────────────────────────────


_EV_COUNTER = 0


def _ev(text: str, **overrides) -> dict:
    """Build a Feishu message event with a globally-unique message_id so
    dedup does not flake across messages that share the same text."""
    global _EV_COUNTER
    _EV_COUNTER += 1
    base = {
        "message_id": f"om_p5_{_EV_COUNTER}",
        "chat_id": "oc_team",
        "sender_id": "ou_user",
        "text": text,
        "msg_type": "text",
        "sender_type": "user",
    }
    base.update(overrides)
    return base


@pytest.fixture(autouse=True)
def _reset_router_session_state():
    """Clear the router's per-sender language cache AND rate-limit /
    seen-id state before each test so module-level counters do not
    leak across the file."""
    from eduflow.feishu import router

    if hasattr(router, "_reset_session_state"):
        router._reset_session_state()
    if hasattr(router, "_reset_rate_limit"):
        router._reset_rate_limit()
    # `_SEEN_MESSAGE_IDS` is module-level — reset it directly.
    if hasattr(router, "_SEEN_MESSAGE_IDS"):
        router._SEEN_MESSAGE_IDS.clear()
    yield
    if hasattr(router, "_reset_session_state"):
        router._reset_session_state()
    if hasattr(router, "_reset_rate_limit"):
        router._reset_rate_limit()
    if hasattr(router, "_SEEN_MESSAGE_IDS"):
        router._SEEN_MESSAGE_IDS.clear()


# ── language detection ──────────────────────────────────────────────


def test_router_tags_chinese_text_as_zh_cn():
    d = classify_event(_ev("帮我每周一早上9点生成周报"), team_agents=_AGENTS)
    assert d.user_language == "zh-CN"
    assert d.action is Action.ROUTE
    assert d.targets == ["manager"]


def test_router_tags_english_text_as_en_us():
    d = classify_event(_ev("please schedule a daily standup reminder"), team_agents=_AGENTS)
    assert d.user_language == "en-US"
    assert d.action is Action.ROUTE


def test_router_falls_back_to_en_us_for_unknown_script():
    """Mixed ASCII / no clear script → en-US default; never blank."""
    d = classify_event(_ev("123 go"), team_agents=_AGENTS)
    assert d.user_language == "en-US"


# ── session-state caching ───────────────────────────────────────────


def test_router_reme检测edmbers_language_for_same_sender():
    """Once the sender's language is detected, subsequent ROUTE decisions
    reuse it even if a single line has only ASCII chars (mixed CN/EN)."""
    first = classify_event(
        _ev("帮我设置一个定时任务", sender_id="ou_alice"),
        team_agents=_AGENTS,
    )
    assert first.user_language == "zh-CN"

    second = classify_event(
        _ev("hi", sender_id="ou_alice"),
        team_agents=_AGENTS,
    )
    assert second.user_language == "zh-CN"


def test_router_keeps_per_sender_language_isolated():
    """Alice speaks Chinese; Bob speaks English; their languages must not
    leak across senders."""
    classify_event(
        _ev("帮我安排明天的事", sender_id="ou_alice"),
        team_agents=_AGENTS,
    )
    classify_event(
        _ev("please schedule this", sender_id="ou_bob"),
        team_agents=_AGENTS,
    )
    a = classify_event(_ev("x", sender_id="ou_alice"), team_agents=_AGENTS)
    b = classify_event(_ev("x", sender_id="ou_bob"), team_agents=_AGENTS)
    assert a.user_language == "zh-CN"
    assert b.user_language == "en-US"


# ── schedule intent tagging (router only flags, never parses) ───────


@pytest.mark.parametrize("text", [
    "帮我设个每周一早9点的周报提醒",
    "schedule a weekly report",
    "每日提醒我喝水",
    "daily reminder at 9am",
])
def test_router_flags_schedule_intent_for_keyword_text(text):
    d = classify_event(_ev(text), team_agents=_AGENTS)
    assert d.schedule_intent is True


@pytest.mark.parametrize("text", [
    "今天天气怎么样",
    "what's the weather",
    "随机一句话",
    "hi",
])
def test_router_does_not_flag_non_schedule_text(text):
    d = classify_event(_ev(text), team_agents=_AGENTS)
    assert d.schedule_intent is False


def test_router_does_not_parse_times_in_text():
    """The router MUST NOT attempt to parse 下周/下午/9:00.  It only
    forwards the raw text; the manager skill decides what is fuzzy."""
    d = classify_event(_ev("下周一下午帮我开个周会"), team_agents=_AGENTS)
    # No scheduler fields on Decision — only the raw text.
    assert getattr(d, "next_due_utc", None) is None
    assert getattr(d, "frequency", None) is None
    assert d.text == "下周一下午帮我开个周会"


# ── router MUST NOT mutate the scheduler store ──────────────────────


def test_router_does_not_create_scheduler_rule_or_occurrence():
    """P5 contract: the router never touches scheduler store.  Classifying
    an event must not produce any D rules or D occurrences."""
    from eduflow.runtime import paths
    from eduflow.store import scheduled_tasks

    with_paths = paths.state_dir()
    # State dir doesn't matter here; what matters is that classify_event
    # does not import scheduled_tasks or call any of its mutators.
    classify_event(
        _ev("帮我每周一生成周报", sender_id="ou_alice"),
        team_agents=_AGENTS,
    )
    # No scheduler dir created as a side effect of routing.
    assert not (with_paths / "scheduler" / "rules.json").exists()
    assert scheduled_tasks.list_rules() == []


def test_router_decision_carries_msg_id_and_sender_for_skill_consumption():
    """The manager skill needs the message context to reply.  Router
    must propagate msg_id and sender_id intact."""
    d = classify_event(
        _ev("schedule this please", message_id="om_xyz", sender_id="ou_alice"),
        team_agents=_AGENTS,
    )
    assert d.msg_id == "om_xyz"
    assert d.sender_id == "ou_alice"


# ── skill file contract ─────────────────────────────────────────────


def _skill_path() -> Path:
    """Locate the manager skill body.  Skills live under skills/."""
    return Path(__file__).resolve().parents[2] / "skills" / "eduflow-scheduled-task-manager" / "SKILL.md"


def test_skill_file_exists():
    p = _skill_path()
    assert p.exists(), f"missing skill file: {p}"


def test_skill_documents_required_fields():
    """All required fields (target, artifact, frequency, timezone, due time,
    suggested agent) must appear in the skill body so the manager knows
    what to fill in before invoking P4."""
    body = _skill_path().read_text(encoding="utf-8").lower()
    for field in ("target", "artifact", "frequency", "timezone", "due time", "suggested agent"):
        assert field in body, f"required field missing from skill: {field!r}"


def test_skill_lists_fuzzy_time_markers_that_require_clarification():
    """下周/周末/下午/每隔一段时间/明天 etc. must be explicitly listed in
    the clarification policy so the manager always asks back."""
    body = _skill_path().read_text(encoding="utf-8")
    for marker in ("下周", "周末", "下午", "每隔", "明天"):
        assert marker in body, f"fuzzy marker missing from skill: {marker!r}"


def test_skill_documents_due_confirmation_packet_format():
    """The skill must show the user-facing packet shape used to confirm a
    rule before P4 commit (id, target, frequency, due local, timezone,
    agent, version)."""
    body = _skill_path().read_text(encoding="utf-8").lower()
    assert "confirmation packet" in body or "due confirmation" in body or "确认包" in body


def test_skill_documents_authorization_matrix():
    """Authorization matrix must include user / manager / worker roles
    and the operations each may perform."""
    body = _skill_path().read_text(encoding="utf-8").lower()
    assert "authorization" in body or "权限" in body
    for role in ("user", "manager", "worker"):
        assert role in body, f"role missing from skill auth matrix: {role}"


def test_skill_documents_notification_cadence():
    """Manager reminder cadence (30 min) and user notification cadence
    (2 hours) must be explicit so the manager does not invent its own."""
    body = _skill_path().read_text(encoding="utf-8").lower()
    assert "30" in body and "manager" in body
    assert ("2 hour" in body) or ("2-hour" in body) or ("2 小时" in body) or ("2小时" in body) or ("two hour" in body)


def test_skill_lists_allowed_notification_kinds():
    """Only create / supplement-or-confirm / start / result-or-failure
    must be listed as the kinds that produce notifications."""
    body = _skill_path().read_text(encoding="utf-8").lower()
    assert "create" in body
    assert "supplement" in body or "confirm" in body
    assert "start" in body
    assert "result" in body or "failure" in body


def test_skill_explicitly_forbids_router_or_nl_direct_store_writes():
    """The skill must state that natural language and the router do NOT
    mutate the scheduler store directly; everything goes through P4
    manager_ops APIs."""
    body = _skill_path().read_text(encoding="utf-8").lower()
    assert "manager_ops" in body
    assert "not" in body or "never" in body or "must not" in body or "禁止" in body or "不得" in body


def test_skill_references_p4_api_specifically():
    """The skill must reference the P4 manager_ops entry points that it
    will call after user confirmation."""
    body = _skill_path().read_text(encoding="utf-8").lower()
    assert "create_draft_rule" in body
    assert "confirm_draft_rule" in body
    assert "pause_rule" in body
    assert "resume_rule" in body
    assert "cancel_rule" in body