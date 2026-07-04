"""Tests for the structured card protocol v2 (feishu/cards_v2.py).

Plan 2026-07-01 §设计一: nine card types, role → allowed-types table,
field validator with three failure categories (role / field / value),
`render_to_card_dict` produces Feishu card v2.

This file is the regression guard for Phase 1.  Adding a new card type,
tweaking an allow-list, or loosening the validator must all require
updating one of the tests below.
"""
from __future__ import annotations

import pytest

from eduflow.feishu import cards_v2
from eduflow.feishu.cards_v2_schema import (
    CardType, REQUIRED_FIELDS, _FIELD_VALUE_ALLOWED,
    _ROLE_ALLOWED_TYPES, _WORKER_DEFAULT_ALLOWED, agent_role_allowed,
)


# ── parse_body ─────────────────────────────────────────────────


def test_parse_body_returns_empty_dict_for_empty_input():
    assert cards_v2.parse_body("") == {}
    assert cards_v2.parse_body(None) == {}


def test_parse_body_extracts_simple_key_value_pairs():
    out = cards_v2.parse_body("任务:AP Physics\n负责人:worker_course")
    assert out == {"任务": "AP Physics", "负责人": "worker_course"}


def test_parse_body_accepts_chinese_full_width_colon():
    out = cards_v2.parse_body("任务：AP Physics\n负责人：worker_course")
    assert out == {"任务": "AP Physics", "负责人": "worker_course"}


def test_parse_body_accepts_mixed_colons_in_same_body():
    out = cards_v2.parse_body("任务:AP Physics\n负责人：worker_course")
    assert out == {"任务": "AP Physics", "负责人": "worker_course"}


def test_parse_body_skips_lines_without_separator():
    out = cards_v2.parse_body(
        "[CLOSEOUT] manager\n\n"
        "任务:AP Physics\n"
        "random prose line\n"
        "需要老板介入:否"
    )
    # The leading "[CLOSEOUT] manager" line is silently skipped because
    # it has no key/value separator; the prose line ditto.
    assert out == {"任务": "AP Physics", "需要老板介入": "否"}


def test_parse_body_keeps_last_value_on_duplicate_keys():
    out = cards_v2.parse_body("任务:first\n任务:second")
    assert out == {"任务": "second"}


def test_parse_body_strips_whitespace_around_key_and_value():
    out = cards_v2.parse_body("  任务 :  AP Physics  ")
    assert out == {"任务": "AP Physics"}


# ── agent_role_allowed ────────────────────────────────────────


def test_agent_role_allowed_manager_has_closout_and_alert():
    allowed = agent_role_allowed("manager")
    assert "CLOSEOUT" in allowed
    assert "ALERT" in allowed
    assert "REVIEW" not in allowed  # manager does not send REVIEW


def test_agent_role_allowed_review_course_has_review_only():
    allowed = agent_role_allowed("review_course")
    assert "REVIEW" in allowed
    assert "CLOSEOUT" not in allowed
    assert "ALERT" not in allowed


def test_agent_role_allowed_auto_ops_has_alert_only():
    allowed = agent_role_allowed("auto_ops")
    assert "ALERT" in allowed
    assert "CLOSEOUT" not in allowed
    assert "REVIEW" not in allowed


def test_agent_role_allowed_luke_recorder_has_recorded_only():
    allowed = agent_role_allowed("Luke_recorder")
    assert "RECORDED" in allowed
    assert "CLOSEOUT" not in allowed


def test_agent_role_allowed_hermes_excludes_closout_review_and_recorded():
    """Plan §设计一: ALERT is shared by auto_ops/manager only.
    Hermes (knowledge steward) is a worker-style role and does NOT
    send ALERT — anomaly reporting is auto_ops's job."""
    allowed = agent_role_allowed("Hermes")
    assert "CLOSEOUT" not in allowed
    assert "REVIEW" not in allowed
    assert "RECORDED" not in allowed
    assert "ALERT" not in allowed
    # Worker-style: ACK/START/PROGRESS/HANDOFF/BLOCKED
    assert "ACK" in allowed
    assert "HANDOFF" in allowed


def test_agent_role_allowed_unknown_without_known_agents_falls_back_to_worker():
    allowed = agent_role_allowed("worker_typo")
    assert allowed == _WORKER_DEFAULT_ALLOWED
    # Worker default is most restrictive
    assert "CLOSEOUT" not in allowed
    assert "REVIEW" not in allowed


def test_agent_role_allowed_unknown_with_known_agents_returns_empty_set():
    """Fail-closed: a typo in the agent name must not silently grant
    CLOSEOUT privileges when the validator knows the real team."""
    allowed = agent_role_allowed("worker_typo", known_agents=["manager", "worker_course"])
    assert allowed == frozenset()


def test_agent_role_allowed_includes_all_nine_types_in_combined_set():
    """Plan §设计一 union: every one of the 9 types is in some role's
    allow-list (no dead type).  This guards against typos in the
    _ROLE_ALLOWED_TYPES table."""
    union: set[str] = set()
    for allowed in _ROLE_ALLOWED_TYPES.values():
        union |= set(allowed)
    union |= set(_WORKER_DEFAULT_ALLOWED)
    for t in CardType.ALL:
        assert t in union, f"{t} is in no role's allow-list"


# ── validate_card: required fields ────────────────────────────


def _valid_body(card_type: str) -> str:
    """Return a body that satisfies the required fields for `card_type`.

    Fields with controlled vocabulary (`verdict` for REVIEW,
    `需要老板介入` for BLOCKED/ALERT) are filled with the canonical
    allowed value, not the generic `x`, so the validator's vocabulary
    check does not trip.
    """
    required = REQUIRED_FIELDS[card_type]
    lines: list[str] = []
    for field in required:
        allowed = _FIELD_VALUE_ALLOWED.get((card_type, field))
        if allowed:
            lines.append(f"{field}:{sorted(allowed)[0]}")
        else:
            lines.append(f"{field}:x")
    return "\n".join(lines)


@pytest.mark.parametrize("card_type", list(CardType.ALL))
def test_validate_card_passes_when_all_required_fields_present(card_type):
    # Pick a known agent that is allowed for this card_type. The card
    # must be built with the SAME sender — validate_card uses
    # card.sender, not a separate arg.
    sender = next(
        (name for name, allowed in _ROLE_ALLOWED_TYPES.items()
         if card_type in allowed),
        "worker_course",
    )
    known = list(_ROLE_ALLOWED_TYPES.keys()) + ["worker_course"]
    if sender == "worker_course":
        known = ["worker_course", *_ROLE_ALLOWED_TYPES.keys()]
    card = cards_v2.build_card(card_type, sender, _valid_body(card_type))
    result = cards_v2.validate_card(card, known_agents=known)
    assert result.ok, f"{card_type} should pass: {result.errors}"
    assert not result.is_role_violation


@pytest.mark.parametrize("card_type,required_field", [
    (CardType.PROGRESS, "证据"),
    (CardType.HANDOFF, "证据"),
    (CardType.REVIEW, "证据"),
    (CardType.CLOSEOUT, "证据"),
    (CardType.BLOCKED, "卡点"),
    (CardType.ACK, "任务"),
    (CardType.START, "执行路线"),
    (CardType.ALERT, "异常类型"),
    (CardType.RECORDED, "已记录内容一句话摘要"),
])
def test_validate_card_flags_missing_required_field(card_type, required_field):
    body = _valid_body(card_type).replace(f"{required_field}:x", f"{required_field}:")
    sender = next(
        (name for name, allowed in _ROLE_ALLOWED_TYPES.items()
         if card_type in allowed),
        "worker_course",
    )
    known = list(_ROLE_ALLOWED_TYPES.keys()) + ["worker_course"]
    card = cards_v2.build_card(card_type, sender, body)
    result = cards_v2.validate_card(card, known_agents=known)
    assert not result.ok
    assert any(f"field:{required_field}" in e for e in result.errors)
    assert not result.is_role_violation


# ── validate_card: role enforcement ───────────────────────────


def test_validate_card_blocks_worker_trying_to_send_closout():
    body = _valid_body(CardType.CLOSEOUT)
    card = cards_v2.build_card(CardType.CLOSEOUT, "worker_course", body)
    result = cards_v2.validate_card(
        card, known_agents=["worker_course", "manager"],
    )
    assert not result.ok
    assert result.is_role_violation
    assert any("role:worker_course_cannot_send_CLOSEOUT" in e for e in result.errors)


def test_validate_card_blocks_worker_trying_to_send_review():
    body = _valid_body(CardType.REVIEW)
    card = cards_v2.build_card(CardType.REVIEW, "worker_course", body)
    result = cards_v2.validate_card(
        card, known_agents=["worker_course", "review_course"],
    )
    assert not result.ok
    assert result.is_role_violation
    assert any("role:worker_course_cannot_send_REVIEW" in e for e in result.errors)


def test_validate_card_blocks_manager_trying_to_send_review():
    body = _valid_body(CardType.REVIEW)
    card = cards_v2.build_card(CardType.REVIEW, "manager", body)
    result = cards_v2.validate_card(card, known_agents=["manager"])
    assert not result.ok
    assert result.is_role_violation
    assert any("role:manager_cannot_send_REVIEW" in e for e in result.errors)


def test_validate_card_blocks_review_course_trying_to_send_closout():
    body = _valid_body(CardType.CLOSEOUT)
    card = cards_v2.build_card(CardType.CLOSEOUT, "review_course", body)
    result = cards_v2.validate_card(
        card, known_agents=["review_course", "manager"],
    )
    assert not result.ok
    assert result.is_role_violation


def test_validate_card_blocks_unknown_agent():
    body = _valid_body(CardType.ACK)
    card = cards_v2.build_card(CardType.ACK, "ghost_agent", body)
    result = cards_v2.validate_card(
        card, known_agents=["manager", "worker_course"],
    )
    assert not result.ok
    assert result.is_role_violation


def test_validate_card_blocks_unknown_card_type():
    card = cards_v2.Card(
        card_type="BOGUS", sender="manager", fields={"任务": "x"},
    )
    result = cards_v2.validate_card(card, known_agents=["manager"])
    assert not result.ok
    assert result.is_role_violation
    assert any("unknown_card_type" in e for e in result.errors)


# ── validate_card: controlled vocabulary ──────────────────────


def test_validate_card_rejects_invalid_review_verdict():
    # Build a REVIEW body with all required fields satisfied except
    # verdict which gets an invalid value.  We can't just .replace() the
    # body because _valid_body may now use a controlled-vocab value;
    # rebuild from scratch.
    body_lines: list[str] = []
    for field in REQUIRED_FIELDS[CardType.REVIEW]:
        if field == "verdict":
            body_lines.append("verdict:invalid_value")
        else:
            allowed = _FIELD_VALUE_ALLOWED.get((CardType.REVIEW, field))
            if allowed:
                body_lines.append(f"{field}:{sorted(allowed)[0]}")
            else:
                body_lines.append(f"{field}:x")
    body = "\n".join(body_lines)
    card = cards_v2.build_card(CardType.REVIEW, "review_course", body)
    result = cards_v2.validate_card(card, known_agents=["review_course"])
    assert not result.ok
    assert any("value:verdict" in e for e in result.errors)


@pytest.mark.parametrize("verdict", ["通过", "打回", "需补充"])
def test_validate_card_accepts_each_allowed_review_verdict(verdict):
    body = _valid_body(CardType.REVIEW).replace("verdict:x", f"verdict:{verdict}")
    card = cards_v2.build_card(CardType.REVIEW, "review_course", body)
    result = cards_v2.validate_card(card, known_agents=["review_course"])
    assert result.ok, f"verdict={verdict} should pass: {result.errors}"


# ── needs_boss_intervention ───────────────────────────────────


@pytest.mark.parametrize("value,expected", [
    ("是", True), ("否", False), ("yes", True), ("true", True),
    ("y", True), ("1", True), ("no", False), ("", False),
    ("maybe", False),
])
def test_needs_boss_intervention_recognises_affirmative_values(value, expected):
    card = cards_v2.Card(
        card_type=CardType.ALERT, sender="auto_ops",
        fields={"需要老板介入": value},
    )
    assert cards_v2.needs_boss_intervention(card) is expected


def test_needs_boss_intervention_default_false_when_field_absent():
    card = cards_v2.Card(card_type=CardType.ACK, sender="worker_course", fields={})
    assert cards_v2.needs_boss_intervention(card) is False


# ── render_to_card_dict ───────────────────────────────────────


def test_render_to_card_dict_emits_v2_schema():
    body = (
        "任务:AP Physics C syllabus skill\n"
        "正式结论:已完成 v1,可进入试用\n"
        "需要老板介入:否"
    )
    card = cards_v2.build_card(CardType.CLOSEOUT, "manager", body, color="blue")
    rendered = cards_v2.render_to_card_dict(
        card, header_title="[CLOSEOUT] manager · 唯一业务入口",
    )
    assert rendered["schema"] == "2.0"
    assert rendered["header"]["title"]["content"] == "[CLOSEOUT] manager · 唯一业务入口"
    assert rendered["header"]["template"] == "blue"
    elements = rendered["body"]["elements"]
    assert elements[0]["tag"] == "markdown"
    body_text = elements[0]["content"]
    assert "**任务**" in body_text
    assert "**正式结论**" in body_text
    assert "**需要老板介入**" in body_text


def test_render_to_card_dict_prefixes_boss_intervention_yes_with_emoji():
    body = "任务:x\n正式结论:x\n证据:x\n剩余风险:x\n下一步:x\n需要老板介入:是"
    card = cards_v2.build_card(CardType.CLOSEOUT, "manager", body)
    rendered = cards_v2.render_to_card_dict(card)
    body_text = rendered["body"]["elements"][0]["content"]
    # When 需要老板介入=是, the value should get the 🚨 prefix so
    # the boss can spot the escalation at a glance.
    assert "**需要老板介入**：🚨 是" in body_text


def test_render_to_card_dict_falls_back_to_sender_when_no_header_title():
    card = cards_v2.build_card(CardType.ACK, "worker_course", "任务:x\n负责人:x\n当前阶段:x\n下一步:x\n需要老板介入:否")
    rendered = cards_v2.render_to_card_dict(card)
    assert rendered["header"]["title"]["content"] == "[ACK] worker_course"


def test_render_to_card_dict_skips_empty_field_values():
    card = cards_v2.build_card(
        CardType.ACK, "worker_course",
        "任务:foo\n负责人:\n当前阶段:bar\n下一步:baz\n需要老板介入:否",
    )
    rendered = cards_v2.render_to_card_dict(card)
    body_text = rendered["body"]["elements"][0]["content"]
    # Empty `负责人:` value should NOT show up in the rendered body
    assert "**负责人**" not in body_text
    assert "**任务**" in body_text


# ── integration: say.py --card path ───────────────────────────


def test_say_with_card_closout_renders_structured_card_via_send_card():
    """End-to-end through `eduflow say --card CLOSEOUT`: validator
    passes, render produces a v2 card, feishu_chat.send_card is called."""
    from helpers import attr_patch, isolated_env, run_cli
    from eduflow.feishu import chat as feishu_chat

    calls: list[dict] = []

    def fake_send_card(chat_id, card, **kw):
        calls.append({"chat_id": chat_id, "card": card, "kw": kw})
        return {"message_id": "om_test"}

    body = (
        "任务:AP Physics C syllabus skill\n"
        "正式结论:已完成 v1\n"
        "产物:skills/SKILL.md\n"
        "证据:validator 通过\n"
        "剩余风险:无\n"
        "下一步:下一次任务试用\n"
        "需要老板介入:否"
    )
    with isolated_env(
        team={"agents": {"manager": {
            "role": "唯一业务入口", "emoji": "🎯", "color": "blue",
        }}},
        runtime_config={"chat_id": "oc_test", "lark_profile": ""},
    ):
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, _, _ = run_cli(["say", "manager", body, "--card", "CLOSEOUT"])
    assert rc == 0
    assert len(calls) == 1
    card = calls[0]["card"]
    assert card["schema"] == "2.0"
    assert "[CLOSEOUT]" in card["header"]["title"]["content"]
    assert "manager" in card["header"]["title"]["content"]
    body_text = card["body"]["elements"][0]["content"]
    assert "**任务**" in body_text
    assert "**正式结论**" in body_text


def test_say_with_card_worker_trying_closout_exits_one_with_role_error():
    """Worker → CLOSEOUT is a role violation: hard-fail with exit 1."""
    from helpers import attr_patch, isolated_env, run_cli
    from eduflow.feishu import chat as feishu_chat

    calls: list[dict] = []

    def fake_send_card(chat_id, card, **kw):
        calls.append({"chat_id": chat_id, "card": card})
        return {"message_id": "om_test"}

    body = (
        "任务:foo\n正式结论:x\n产物:x\n证据:x\n剩余风险:x\n下一步:x\n需要老板介入:否"
    )
    with isolated_env(
        team={"agents": {
            "manager": {"role": "manager"},
            "worker_course": {"role": "course", "color": "purple"},
        }},
        runtime_config={"chat_id": "oc_test", "lark_profile": ""},
    ):
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, _, err = run_cli(
                ["say", "worker_course", body, "--card", "CLOSEOUT"]
            )
    assert rc == 1
    assert "worker_course_cannot_send_CLOSEOUT" in err
    # No chat send happened
    assert calls == []


def test_say_with_card_missing_evidence_degrades_to_internal():
    """Worker → HANDOFF without 证据: field violation, NOT role
    violation.  Caller degrades to internal: audit-only, exit 0."""
    from helpers import attr_patch, isolated_env, run_cli
    from eduflow.feishu import chat as feishu_chat

    calls: list[dict] = []

    def fake_send_card(chat_id, card, **kw):
        calls.append({"chat_id": chat_id, "card": card})
        return {"message_id": "om_test"}

    body = (
        "任务:AP Physics C syllabus skill\n"
        "交接对象:review_course\n"
        "交接内容:syllabus skill 初稿\n"
        "待检查点:考纲边界\n"
        "运行状态变化:active -> warm\n"
        "需要老板介入:否"
    )
    with isolated_env(
        team={"agents": {
            "worker_course": {"role": "course", "color": "purple"},
            "review_course": {"role": "review", "color": "green"},
        }},
        runtime_config={"chat_id": "oc_test", "lark_profile": ""},
    ):
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, _, err = run_cli(
                ["say", "worker_course", body, "--card", "HANDOFF"]
            )
    assert rc == 0
    assert "field:证据" in err
    assert "degraded to internal" in err
    # No chat send happened
    assert calls == []


def test_say_without_card_keeps_legacy_path_unchanged():
    """Backward compat: `eduflow say X "msg"` (no --card) still uses
    simple_card with the original `{emoji} {agent} · {role}` title."""
    from helpers import attr_patch, isolated_env, run_cli
    from eduflow.feishu import chat as feishu_chat

    calls: list[dict] = []

    def fake_send_card(chat_id, card, **kw):
        calls.append({"chat_id": chat_id, "card": card})
        return {"message_id": "om_test"}

    with isolated_env(
        team={"agents": {
            "manager": {"role": "团队主管", "emoji": "🎯", "color": "blue"},
        }},
        runtime_config={"chat_id": "oc_test", "lark_profile": ""},
    ):
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, _, _ = run_cli(["say", "manager", "重要决策已落地"])
    assert rc == 0
    card = calls[0]["card"]
    # Legacy title is the {emoji} {agent} · {role} shape, no [TYPE] prefix
    assert card["header"]["title"]["content"] == "🎯 manager · 团队主管"


def test_say_with_card_unknown_type_exits_one():
    """`--card BOGUS` is an unknown type — hard-fail with exit 1."""
    from helpers import attr_patch, isolated_env, run_cli
    from eduflow.feishu import chat as feishu_chat

    calls: list[dict] = []

    def fake_send_card(chat_id, card, **kw):
        calls.append({"chat_id": chat_id, "card": card})
        return {"message_id": "om_test"}

    with isolated_env(
        team={"agents": {"manager": {"role": "manager"}}},
        runtime_config={"chat_id": "oc_test", "lark_profile": ""},
    ):
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, _, err = run_cli(["say", "manager", "x", "--card", "BOGUS"])
    assert rc == 1
    assert "unknown card type" in err
    assert calls == []


def test_say_with_card_legacy_no_arg_form_still_works():
    """`--card` (no value, legacy boolean) is consumed as no-op so
    the old `eduflow say X --card` operator pattern keeps working."""
    from helpers import attr_patch, isolated_env, run_cli
    from eduflow.feishu import chat as feishu_chat

    calls: list[dict] = []

    def fake_send_card(chat_id, card, **kw):
        calls.append({"chat_id": chat_id, "card": card})
        return {"message_id": "om_test"}

    with isolated_env(
        team={"agents": {
            "manager": {"role": "团队主管", "emoji": "🎯", "color": "blue"},
        }},
        runtime_config={"chat_id": "oc_test", "lark_profile": ""},
    ):
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, _, _ = run_cli([
                "say", "manager", "重要决策已落地", "--card",
            ])
    assert rc == 0
    card = calls[0]["card"]
    # No [TYPE] prefix in the title
    assert "[" not in card["header"]["title"]["content"]
    assert "重要决策已落地" in card["body"]["elements"][0]["content"]


# ── M9: OPS_SNAPSHOT card type ──────────────────────────────────


def test_ops_snapshot_in_card_type_all():
    """M9: OPS_SNAPSHOT is a recognized card type."""
    assert "OPS_SNAPSHOT" in CardType.ALL
    assert CardType.OPS_SNAPSHOT == "OPS_SNAPSHOT"


def test_ops_snapshot_has_required_fields():
    """M9: OPS_SNAPSHOT requires 看板类型/当前状态/顶行动/证据引用/
    常驻摘要/需要老板介入."""
    required = REQUIRED_FIELDS[CardType.OPS_SNAPSHOT]
    assert "看板类型" in required
    assert "当前状态" in required
    assert "顶行动" in required
    assert "证据引用" in required
    assert "常驻摘要" in required
    assert "需要老板介入" in required


def test_agent_role_allowed_manager_can_send_ops_snapshot():
    """M9: manager can send OPS_SNAPSHOT."""
    allowed = agent_role_allowed("manager")
    assert "OPS_SNAPSHOT" in allowed


def test_agent_role_allowed_auto_ops_can_send_ops_snapshot():
    """M9: auto_ops can send OPS_SNAPSHOT."""
    allowed = agent_role_allowed("auto_ops")
    assert "OPS_SNAPSHOT" in allowed


def test_agent_role_allowed_worker_cannot_send_ops_snapshot():
    """M9: worker_course cannot send OPS_SNAPSHOT."""
    allowed = agent_role_allowed("worker_course")
    assert "OPS_SNAPSHOT" not in allowed


def test_agent_role_allowed_review_cannot_send_ops_snapshot():
    """M9: review_course cannot send OPS_SNAPSHOT."""
    allowed = agent_role_allowed("review_course")
    assert "OPS_SNAPSHOT" not in allowed


def test_validate_ops_snapshot_passes_when_all_fields_present():
    """M9: a valid OPS_SNAPSHOT card passes validation."""
    body = _valid_body(CardType.OPS_SNAPSHOT)
    card = cards_v2.build_card(CardType.OPS_SNAPSHOT, "manager", body)
    result = cards_v2.validate_card(card, known_agents=["manager"])
    assert result.ok, f"should pass: {result.errors}"


def test_validate_ops_snapshot_flags_missing_top_actions():
    """M9: missing 顶行动 is a field violation, not a role violation."""
    body = _valid_body(CardType.OPS_SNAPSHOT).replace("顶行动:x", "顶行动:")
    card = cards_v2.build_card(CardType.OPS_SNAPSHOT, "manager", body)
    result = cards_v2.validate_card(card, known_agents=["manager"])
    assert not result.ok
    assert any("field:顶行动" in e for e in result.errors)
    assert not result.is_role_violation


def test_validate_ops_snapshot_flags_missing_evidence_refs():
    """M9: missing 证据引用 is caught."""
    body = _valid_body(CardType.OPS_SNAPSHOT).replace("证据引用:x", "证据引用:")
    card = cards_v2.build_card(CardType.OPS_SNAPSHOT, "manager", body)
    result = cards_v2.validate_card(card, known_agents=["manager"])
    assert not result.ok
    assert any("field:证据引用" in e for e in result.errors)


# ── M9: severity → color mapping ───────────────────────────────


def test_severity_to_color_maps_all_known_severities():
    from eduflow.feishu.cards_v2_schema import severity_to_color, SEVERITY_COLOR_MAP
    assert SEVERITY_COLOR_MAP["success"] == "green"
    assert SEVERITY_COLOR_MAP["info"] == "blue"
    assert SEVERITY_COLOR_MAP["warning"] == "orange"
    assert SEVERITY_COLOR_MAP["critical"] == "red"
    # function lookup
    assert severity_to_color("success") == "green"
    assert severity_to_color("info") == "blue"
    assert severity_to_color("warning") == "orange"
    assert severity_to_color("critical") == "red"


def test_severity_to_color_returns_none_for_unknown():
    from eduflow.feishu.cards_v2_schema import severity_to_color
    assert severity_to_color("bogus") is None
    assert severity_to_color("") is None
    assert severity_to_color(None) is None


def test_render_card_with_severity_warning_overrides_default_blue():
    """M9: when color is default blue and severity is set, color
    is resolved from the severity map."""
    card = cards_v2.Card(
        card_type=CardType.ACK, sender="worker_course",
        fields={"任务": "x", "负责人": "x", "当前阶段": "x",
                "下一步": "x", "需要老板介入": "否"},
        severity="warning",
    )
    rendered = cards_v2.render_to_card_dict(card)
    assert rendered["header"]["template"] == "orange"


def test_render_card_with_severity_critical_uses_red():
    card = cards_v2.Card(
        card_type=CardType.ACK, sender="worker_course",
        fields={"任务": "x", "负责人": "x", "当前阶段": "x",
                "下一步": "x", "需要老板介入": "否"},
        severity="critical",
    )
    rendered = cards_v2.render_to_card_dict(card)
    assert rendered["header"]["template"] == "red"


def test_render_card_with_explicit_color_ignores_severity():
    """M9: explicit color=green overrides severity=warning."""
    card = cards_v2.Card(
        card_type=CardType.ACK, sender="worker_course",
        fields={"任务": "x", "负责人": "x", "当前阶段": "x",
                "下一步": "x", "需要老板介入": "否"},
        color="green",
        severity="warning",
    )
    rendered = cards_v2.render_to_card_dict(card)
    assert rendered["header"]["template"] == "green"


def test_build_card_accepts_severity_parameter():
    card = cards_v2.build_card(
        CardType.ACK, "worker_course",
        "任务:x\n负责人:x\n当前阶段:x\n下一步:x\n需要老板介入:否",
        severity="info",
    )
    assert card.severity == "info"


def test_build_card_default_severity_is_none():
    card = cards_v2.build_card(
        CardType.ACK, "worker_course",
        "任务:x\n负责人:x\n当前阶段:x\n下一步:x\n需要老板介入:否",
    )
    assert card.severity is None


# ── M9: all card types render v2 schema ────────────────────────


@pytest.mark.parametrize("card_type", list(CardType.ALL))
def test_render_to_card_dict_emits_v2_schema_for_all_types(card_type):
    sender = next(
        (name for name, allowed in _ROLE_ALLOWED_TYPES.items()
         if card_type in allowed),
        "worker_course",
    )
    body = _valid_body(card_type)
    card = cards_v2.build_card(card_type, sender, body)
    rendered = cards_v2.render_to_card_dict(card)
    assert rendered["schema"] == "2.0"
    assert rendered["header"]["title"]["content"].startswith(f"[{card_type}]")
    assert rendered["header"]["template"] in (
        "blue", "green", "red", "yellow", "grey",
        "purple", "orange", "turquoise", "pink",
    )
    assert rendered["body"]["elements"][0]["tag"] == "markdown"


# ── M9: normalize tests for missing fields ────────────────────


def test_validate_card_normalizes_missing_optional_fields():
    """M9: when a body has only the required fields, it still passes.
    Optional fields are simply absent — no error, no degraded state."""
    body = _valid_body(CardType.PROGRESS)
    card = cards_v2.build_card(CardType.PROGRESS, "worker_course", body)
    result = cards_v2.validate_card(
        card, known_agents=["worker_course"],
    )
    assert result.ok
    assert not result.is_role_violation


def test_validate_card_normalize_handles_case_insensitive_keys():
    """M9: field lookup is case-insensitive — body says '任务'
    (with different casing) but the required field is '任务'.
    _field_lookup matches case-insensitively."""
    # The field names are Chinese; case-sensitivity test here means
    # different-spacing/colon variants.  Use the Chinese names as
    # required; all required fields must be present for a pass.
    body = "任务:AP Physics\n当前阶段:review\n已完成:1\n证据:ok\n下一阶段:closeout\n需要老板介入:否"
    card = cards_v2.build_card(CardType.PROGRESS, "worker_course", body)
    result = cards_v2.validate_card(card, known_agents=["worker_course"])
    assert result.ok


def test_validate_card_reports_multiple_missing_fields():
    """M9: when multiple required fields are missing, all are reported."""
    body = "任务:only\n负责人:only"
    card = cards_v2.build_card(CardType.PROGRESS, "worker_course", body)
    result = cards_v2.validate_card(card, known_agents=["worker_course"])
    assert not result.ok
    # PROGRESS requires: 任务, 当前阶段, 已完成, 证据, 下一阶段, 需要老板介入
    # Two are present (任务, 负责人 maps to nothing), four should be missing.
    assert len(result.errors) >= 3


def test_validate_card_unknown_card_type_with_known_agents_is_role_violation():
    """M9: unknown card_type is always a role violation."""
    card = cards_v2.Card(card_type="FAKE", sender="worker_course", fields={"任务": "x"})
    result = cards_v2.validate_card(card, known_agents=["worker_course"])
    assert not result.ok
    assert result.is_role_violation


def test_say_with_ops_snapshot_card_works_end_to_end():
    """M9: say --card OPS_SNAPSHOT routes through v2 validator."""
    from helpers import attr_patch, isolated_env, run_cli
    from eduflow.feishu import chat as feishu_chat

    calls: list[dict] = []

    def fake_send_card(chat_id, card, **kw):
        calls.append({"chat_id": chat_id, "card": card})
        return {"message_id": "om_test"}

    body = (
        "看板类型:ops\n当前状态:all clear\n顶行动:none\n"
        "证据引用:ops-dashboard.json\n常驻摘要:resident=2\n需要老板介入:否"
    )
    with isolated_env(
        team={"agents": {"auto_ops": {"role": "ops", "color": "red"}}},
        runtime_config={"chat_id": "oc_test", "lark_profile": ""},
    ):
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, _, _ = run_cli(["say", "auto_ops", body, "--card", "OPS_SNAPSHOT"])
    assert rc == 0
    assert len(calls) == 1
    card = calls[0]["card"]
    assert card["schema"] == "2.0"
    assert "[OPS_SNAPSHOT]" in card["header"]["title"]["content"]
    body_text = card["body"]["elements"][0]["content"]
    assert "**看板类型**" in body_text
    assert "**顶行动**" in body_text
    assert "**证据引用**" in body_text
    assert "**常驻摘要**" in body_text


def test_say_with_ops_snapshot_worker_blocked():
    """M9: worker_course cannot send OPS_SNAPSHOT — role violation."""
    from helpers import attr_patch, isolated_env, run_cli
    from eduflow.feishu import chat as feishu_chat

    calls: list[dict] = []

    def fake_send_card(chat_id, card, **kw):
        calls.append({"chat_id": chat_id, "card": card})
        return {"message_id": "om_test"}

    body = (
        "看板类型:ops\n当前状态:ok\n顶行动:none\n"
        "证据引用:ops-dashboard.json\n常驻摘要:resident=2\n需要老板介入:否"
    )
    with isolated_env(
        team={"agents": {"worker_course": {"role": "course", "color": "purple"}}},
        runtime_config={"chat_id": "oc_test", "lark_profile": ""},
    ):
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, _, err = run_cli(
                ["say", "worker_course", body, "--card", "OPS_SNAPSHOT"]
            )
    assert rc == 1
    assert "worker_course_cannot_send_OPS_SNAPSHOT" in err
    assert calls == []


def test_say_with_ops_snapshot_missing_top_actions_degrades_to_internal():
    """M9: OPS_SNAPSHOT with missing 顶行动 degrades to internal."""
    from helpers import attr_patch, isolated_env, run_cli
    from eduflow.feishu import chat as feishu_chat

    calls: list[dict] = []

    def fake_send_card(chat_id, card, **kw):
        calls.append({"chat_id": chat_id, "card": card})
        return {"message_id": "om_test"}

    body = (
        "看板类型:ops\n当前状态:ok\n顶行动:\n"
        "证据引用:ops-dashboard.json\n常驻摘要:resident=2\n需要老板介入:否"
    )
    with isolated_env(
        team={"agents": {"auto_ops": {"role": "ops", "color": "red"}}},
        runtime_config={"chat_id": "oc_test", "lark_profile": ""},
    ):
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, _, err = run_cli(
                ["say", "auto_ops", body, "--card", "OPS_SNAPSHOT"]
            )
    assert rc == 0  # field violation → degrade to internal, not role violation
    assert "field:顶行动" in err
    assert "degraded to internal" in err
    assert calls == []


# ── INV-1: pin coexistence of M3 snapshot path + M9 v2 path ──


def test_employee_snapshot_card_produces_v2_schema():
    """INV-1: the legacy M3 employee_snapshot_card still emits
    schema=2.0; v1 fields (`config.wide_screen_mode`) are gone.
    """
    from eduflow.feishu.cards import employee_snapshot_card
    card = employee_snapshot_card(
        {"agent": "worker_course", "display_verdict": "active"},
    )
    assert card["schema"] == "2.0"
    assert "header" in card
    assert "body" in card
    # The M3 path uses display verdict → color (not severity).
    assert card["header"]["template"] in {
        "blue", "green", "red", "yellow", "grey",
        "purple", "orange", "turquoise", "pink",
    }


def test_team_snapshot_card_produces_v2_schema():
    """INV-1: the legacy M3 team_snapshot_card still emits schema=2.0."""
    from eduflow.feishu.cards import team_snapshot_card
    card = team_snapshot_card({
        "summary": {"agents_total": 3, "active": 2, "blocked": 0,
                     "stale_display": 0, "waiting_inbox": 0, "idle": 1,
                     "warm_idle": 0, "unknown": 0},
        "top_actions": [],
        "employees": [],
        "degraded": [],
    })
    assert card["schema"] == "2.0"
    assert "header" in card
    body_text = card["body"]["elements"][0]["content"]
    assert "总计" in body_text


def test_employee_snapshot_card_field_names_differ_from_ops_snapshot():
    """INV-1: M3 path uses 状态/驻留/下一步/建议动作; M9 v2 path
    uses 看板类型/当前状态/顶行动/证据引用/常驻摘要.  This pins the
    two paths as distinct so future readers don't accidentally
    collapse them."""
    from eduflow.feishu.cards import employee_snapshot_card
    snapshot_card = employee_snapshot_card(
        {"agent": "worker_course", "display_verdict": "active",
         "residency_label": "常驻", "residency_mode": "resident",
         "current_task_title": "AP Physics 0625",
         "workflow_id": "igcse-subject-launch",
         "workflow_next_action": "review_handoff",
         "recommended_next_action": "continue dispatch"},
    )
    body_text = snapshot_card["body"]["elements"][0]["content"]
    # M3 field names
    assert "**状态**" in body_text
    assert "**驻留**" in body_text
    assert "**下一步**" in body_text
    assert "**建议动作**" in body_text
    # M9 OPS_SNAPSHOT field names are NOT in M3 path
    assert "**看板类型**" not in body_text
    assert "**顶行动**" not in body_text
    assert "**证据引用**" not in body_text
    assert "**常驻摘要**" not in body_text


def test_ops_snapshot_field_names_differ_from_employee_snapshot():
    """INV-1: M9 v2 OPS_SNAPSHOT uses 看板类型/顶行动/证据引用/
    常驻摘要; M3 employee_snapshot uses 状态/驻留/下一步/建议动作.
    """
    from eduflow.feishu.cards_v2 import build_card
    from eduflow.feishu.cards_v2_schema import CardType

    body = (
        "看板类型:ops\n当前状态:all clear\n顶行动:none\n"
        "证据引用:ops-dashboard.json\n常驻摘要:resident=2\n需要老板介入:否"
    )
    card = build_card(CardType.OPS_SNAPSHOT, "manager", body)
    rendered = cards_v2.render_to_card_dict(card)
    body_text = rendered["body"]["elements"][0]["content"]
    # M9 field names
    assert "**看板类型**" in body_text
    assert "**顶行动**" in body_text
    assert "**证据引用**" in body_text
    assert "**常驻摘要**" in body_text
    # M3 field names are NOT in M9 path
    assert "**状态**" not in body_text
    assert "**驻留**" not in body_text
    assert "**下一步**" not in body_text
    assert "**建议动作**" not in body_text


# ── INV-3: pin severity color design ─────────────────────────


def test_severity_resolution_priority_documented_in_render():
    """INV-3: render_to_card_dict uses the documented resolution
    order — explicit color wins over severity.  This test pins the
    design so a future refactor cannot silently flip the priority."""
    # severity=warning, color=green → color wins (green)
    card = cards_v2.Card(
        card_type=CardType.ACK, sender="worker_course",
        fields={"任务": "x", "负责人": "x", "当前阶段": "x",
                "下一步": "x", "需要老板介入": "否"},
        color="green", severity="warning",
    )
    rendered = cards_v2.render_to_card_dict(card)
    assert rendered["header"]["template"] == "green"

    # severity=critical, color=red → color wins (red)
    card = cards_v2.Card(
        card_type=CardType.ACK, sender="worker_course",
        fields={"任务": "x", "负责人": "x", "当前阶段": "x",
                "下一步": "x", "需要老板介入": "否"},
        color="red", severity="critical",
    )
    rendered = cards_v2.render_to_card_dict(card)
    assert rendered["header"]["template"] == "red"

    # severity=info, color=blue (default) → severity wins (blue)
    card = cards_v2.Card(
        card_type=CardType.ACK, sender="worker_course",
        fields={"任务": "x", "负责人": "x", "当前阶段": "x",
                "下一步": "x", "需要老板介入": "否"},
        severity="info",
    )
    rendered = cards_v2.render_to_card_dict(card)
    assert rendered["header"]["template"] == "blue"


def test_severity_unknown_does_not_change_default_blue():
    """INV-3: when severity is unknown to the map and color is the
    default blue, the card stays blue.  No accidental orange/red."""
    card = cards_v2.Card(
        card_type=CardType.ACK, sender="worker_course",
        fields={"任务": "x", "负责人": "x", "当前阶段": "x",
                "下一步": "x", "需要老板介入": "否"},
        severity="fictional",
    )
    rendered = cards_v2.render_to_card_dict(card)
    assert rendered["header"]["template"] == "blue"


def test_severity_color_map_is_stable():
    """INV-3: SEVERITY_COLOR_MAP is the canonical severity-to-color
    mapping.  Adding a new severity requires a test update — this
    test pins the existing 4 entries."""
    from eduflow.feishu.cards_v2_schema import SEVERITY_COLOR_MAP
    assert set(SEVERITY_COLOR_MAP) == {"success", "info", "warning", "critical"}
    # Each value must be a Feishu template color.
    valid = {"blue", "green", "red", "yellow", "grey",
             "purple", "orange", "turquoise", "pink"}
    for sev, color in SEVERITY_COLOR_MAP.items():
        assert color in valid, \
            f"severity {sev!r} maps to invalid color {color!r}"


def test_verdict_color_is_separate_from_severity_color():
    """INV-3: _verdict_color in feishu/cards.py is a separate
    mapping from SEVERITY_COLOR_MAP.  blocked→red in verdict
    space corresponds to critical→red in severity space, but
    stale_display→yellow has no severity equivalent.  The two
    mappings are intentionally separate."""
    from eduflow.feishu.cards import _verdict_color
    from eduflow.feishu.cards_v2_schema import SEVERITY_COLOR_MAP
    # Same color for the most-urgent bucket:
    assert _verdict_color("blocked") == "red"
    assert SEVERITY_COLOR_MAP["critical"] == "red"
    # Divergence: verdict has yellow (stale_display), severity has
    # orange (warning) — they are NOT the same mapping.
    assert _verdict_color("stale_display") == "yellow"
    assert SEVERITY_COLOR_MAP["warning"] == "orange"


def test_render_to_card_dict_escapes_body_field_values():
    """Audit-4: card body values are markdown-escaped.  Field KEYS
    (from REQUIRED_FIELDS) are trusted, field VALUES (from user
    input via `say --card BODY`) are not.  Without escape, a
    worker could inject `[click](http://evil)` or `**bold**` and
    change the card's appearance / links."""
    card = cards_v2.build_card(
        CardType.ACK, "worker_course",
        "任务:[click](http://evil)\n"
        "负责人:**bold**\n"
        "当前阶段:`code`\n"
        "下一步:[x]\n"
        "需要老板介入:否",
    )
    rendered = cards_v2.render_to_card_dict(card)
    body_text = rendered["body"]["elements"][0]["content"]
    # Field values are escaped: brackets, asterisks, backticks are
    # all escaped by _escape_md.  The KEY is still rendered as **key**.
    assert "\\[click\\](http://evil)" in body_text
    assert "\\*\\*bold\\*\\*" in body_text
    assert "\\`code\\`" in body_text
    assert "\\[x\\]" in body_text
    # The key wrapping `**...**` is still present (NOT escaped).
    assert "**任务**" in body_text
    assert "**负责人**" in body_text


def test_render_to_card_dict_escapes_footer():
    """Audit-4: footer is escaped too.  Footer is set by the caller
    (not the user), but defense-in-depth: a future caller passing
    untrusted text as footer should not bypass the escape."""
    card = cards_v2.build_card(
        CardType.ACK, "worker_course",
        "任务:x\n负责人:x\n当前阶段:x\n下一步:x\n需要老板介入:否",
    )
    rendered = cards_v2.render_to_card_dict(
        card, footer="**unsafe** [link](http://evil)",
    )
    body_text = rendered["body"]["elements"][0]["content"]
    assert "\\*\\*unsafe\\*\\*" in body_text
    assert "\\[link\\](http://evil)" in body_text
