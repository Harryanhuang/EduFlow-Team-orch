"""Tests for feishu/catchup.py — cursor + replay-on-restart."""
from __future__ import annotations

import json

from helpers import isolated_env
from eduflow.feishu import catchup
from eduflow.feishu.deliver import DeliveryReport
from eduflow.feishu.router import Action, Decision
from eduflow.feishu.subscribe import process_lines
from eduflow.runtime import paths


# ── cursor I/O ──────────────────────────────────────────────────


def _durable_append(rows: list):
    def _apply(decision):
        rows.append(decision)
        return DeliveryReport(durable_success=True)
    return _apply


def test_read_cursor_empty_when_file_missing():
    with isolated_env():
        assert catchup.read_cursor() == {}


def test_write_then_read_roundtrip():
    with isolated_env():
        catchup.write_cursor("om_42", "1719000000000")
        cur = catchup.read_cursor()
        assert cur["message_id"] == "om_42"
        assert cur["create_time"] == "1719000000000"


def test_cursor_never_moves_backwards_when_old_ack_finishes_late():
    with isolated_env():
        catchup.write_cursor("om_new", "200")
        catchup.write_cursor("om_old", "100")
        cur = catchup.read_cursor()
    assert cur == {"message_id": "om_new", "create_time": "200"}


def test_write_cursor_skips_when_either_field_blank():
    with isolated_env():
        catchup.write_cursor("", "1234")
        catchup.write_cursor("om_x", "")
        assert not paths.router_cursor_file().exists()


def test_read_cursor_returns_empty_on_garbage_json():
    with isolated_env():
        paths.ensure_state_dir()
        paths.router_cursor_file().write_text("not json", encoding="utf-8")
        assert catchup.read_cursor() == {}


def test_record_decision_advances_cursor_for_route():
    decision = Decision(action=Action.ROUTE, targets=["m"], text="x",
                        msg_id="om_99", create_time="1719999999000")
    with isolated_env():
        catchup.record_decision(decision)
        cur = catchup.read_cursor()
        assert cur["message_id"] == "om_99"


def test_record_decision_advances_cursor_for_drop_with_msg_id():
    decision = Decision(action=Action.DROP, msg_id="om_drop",
                        create_time="1720000000000", reason="empty")
    with isolated_env():
        catchup.record_decision(decision)
        cur = catchup.read_cursor()
        assert cur["message_id"] == "om_drop"


def test_record_decision_skips_when_no_msg_id_or_create_time():
    decision = Decision(action=Action.DROP, reason="no_msg_id")
    with isolated_env():
        catchup.record_decision(decision)
        assert not paths.router_cursor_file().exists()


# ── pending_lines ───────────────────────────────────────────────


def _msg(msg_id, create_time, *, text="hi", chat_id="oc_x", sender="ou_user"):
    return {
        "message_id": msg_id,
        "create_time": create_time,
        "chat_id": chat_id,
        "msg_type": "text",
        "sender": {"id": sender, "id_type": "open_id"},
        "body": {"content": json.dumps({"text": text})},
    }


def test_pending_lines_returns_only_messages_at_or_after_cursor_minute():
    """`>=` minute-floor semantics. Cutoff is floored to the minute so
    REST minute-precision messages aligned with the cursor's minute are
    included. Documented in feishu/catchup._newer_than."""
    # Use real minute-aligned epoch ms so the floor doesn't collapse to 0
    minute_a = "1778047620000"   # 2026-05-06 14:07:00
    minute_b = "1778047680000"   # 2026-05-06 14:08:00
    minute_c = "1778047740000"   # 2026-05-06 14:09:00
    history = [
        _msg("om_a1", minute_a),                 # before cursor minute → drop
        _msg("om_b1", minute_b),                 # at cursor minute → keep
        _msg("om_b2", "1778047712000"),          # cursor itself, sub-minute → keep
        _msg("om_c1", minute_c),                 # after cursor → keep
    ]
    with isolated_env():
        catchup.write_cursor("om_b2", "1778047712000")  # 14:08:32
        lines = catchup.pending_lines("oc_x", list_fn=lambda: history)
    import json
    ids = sorted(json.loads(line)["event"]["message"]["message_id"] for line in lines)
    # om_a1 (14:07) drops; om_b1, om_b2 (both 14:08), om_c1 (14:09) keep
    assert ids == ["om_b1", "om_b2", "om_c1"]


def test_pending_lines_recovers_messages_when_cursor_has_subminute_precision():
    """REGRESSION: 2026-05-06 host_smoke caught the deeper bug — cursor
    written from live events has millisecond precision, REST API
    list_recent returns minute precision strings. A bare `>=` still
    loses same-minute messages because REST 14:08:00 < cursor 14:08:32.
    Cutoff must floor to minute boundary."""
    cursor_ms = "1778047712107"  # 2026-05-06 14:08:32.107
    rest_minute = "2026-05-06 14:08"  # REST API shape, parses to 14:08:00
    history = [
        _msg("om_processed_via_live", cursor_ms),
        _msg("om_missed_a", rest_minute),
        _msg("om_missed_b", rest_minute),
    ]
    with isolated_env():
        catchup.write_cursor("om_processed_via_live", cursor_ms)
        lines = catchup.pending_lines("oc_x", list_fn=lambda: history)
    parsed = [json.loads(line) for line in lines]
    ids = sorted(p["event"]["message"]["message_id"] for p in parsed)
    # Both REST-precision missed messages must be returned despite REST
    # parsing to 14:08:00 < cursor's 14:08:32.107
    assert "om_missed_a" in ids
    assert "om_missed_b" in ids


def test_pending_lines_recovers_messages_at_same_minute_as_cursor():
    """REGRESSION: 2026-05-06 host_smoke caught lark WebSocket missing
    4 of 9 slash commands all sharing the same minute as the cursor.
    Strict `>` cutoff lost them permanently. With `>=`, they come back
    via catchup. Same minute simulated here as same epoch-ms."""
    same_minute = "1778047200000"
    history = [
        _msg("om_processed", same_minute),   # cursor lands here after live event
        _msg("om_missed_a", same_minute),    # lark WebSocket missed; same minute
        _msg("om_missed_b", same_minute),    # ditto
    ]
    with isolated_env():
        catchup.write_cursor("om_processed", same_minute)
        lines = catchup.pending_lines("oc_x", list_fn=lambda: history)
    # All 3 returned (cursor itself + 2 missed) so the missed ones get
    # a second chance; in-process dedup will skip om_processed if it's
    # still in seen_msg_ids.
    assert len(lines) == 3
    parsed = [json.loads(line) for line in lines]
    ids = [p["event"]["message"]["message_id"] for p in parsed]
    assert sorted(ids) == ["om_missed_a", "om_missed_b", "om_processed"]


def test_pending_lines_returns_empty_when_no_cursor():
    """Fresh deploy: catchup must NOT replay arbitrary chat history.
    Otherwise `eduflow up` re-fires every recent message including
    old dispatches from a previous team. Round 2 host smoke caught
    this 2026-05-07: a fresh up replayed a 30-min-old r1-mix dispatch
    and manager re-dispatched workers for a task the boss had cleared.
    Live subscribe picks up from "now" forward; first live event
    writes the cursor so subsequent restarts catch up only the gap."""
    history = [_msg("om_a", "100"), _msg("om_b", "200")]
    with isolated_env():
        lines = catchup.pending_lines("oc_x", list_fn=lambda: history)
    assert lines == []


def test_pending_lines_sorts_oldest_first_even_when_history_newest_first():
    history = [_msg("om_c", "300"), _msg("om_a", "100"), _msg("om_b", "200")]
    # Need a cursor so pending_lines doesn't take the fresh-deploy
    # short-circuit; cursor at create_time=50 keeps everything.
    with isolated_env():
        catchup.write_cursor("om_seed", "50")
        lines = catchup.pending_lines("oc_x", list_fn=lambda: history)
    parsed = [json.loads(line) for line in lines]
    cts = [p["event"]["message"]["create_time"] for p in parsed]
    assert cts == ["100", "200", "300"]


def test_pending_lines_emits_subscribe_compatible_shape():
    history = [_msg("om_x", "500", text="hello world", sender="ou_42")]
    with isolated_env():
        catchup.write_cursor("seed", "1")
        lines = catchup.pending_lines("oc_chat", list_fn=lambda: history)
    line = json.loads(lines[0])
    msg = line["event"]["message"]
    assert msg["message_id"] == "om_x"
    assert msg["chat_id"] == "oc_x"
    assert msg["create_time"] == "500"
    assert json.loads(msg["content"])["text"] == "hello world"
    assert line["event"]["sender"]["sender_id"]["open_id"] == "ou_42"


def test_pending_lines_carries_post_message_through_to_subscribe():
    """Catchup 拉历史时遇到 post (图+文混合) 消息也要转成 subscribe NDJSON
    形状, msg_type=post 被 subscribe._normalise → _extract_text 处理."""
    post_content = json.dumps({
        "title": "",
        "content": [[
            {"tag": "text", "text": "看这个 "},
            {"tag": "img", "image_key": "img_screenshot"},
        ]],
    })
    history = [{
        "message_id": "om_post",
        "create_time": "1000",
        "chat_id": "oc_x",
        "msg_type": "post",
        "sender": {"id": "ou_boss", "id_type": "user"},
        "body": {"content": post_content},
    }]
    with isolated_env():
        catchup.write_cursor("seed", "1")
        lines = catchup.pending_lines("oc_chat", list_fn=lambda: history)
    line = json.loads(lines[0])
    msg = line["event"]["message"]
    assert msg["message_type"] == "post"
    # subscribe._normalise + _extract_text 已经在 subscribe 单测里覆盖
    # 把 post content → "[image: image_key=...]" + 文字, 这里 catchup
    # 只要保证 content 透传即可
    assert "img_screenshot" in msg["content"]


def test_pending_lines_default_list_fn_uses_bot_when_env_says_bot():
    """Bot-only deploys (no `lark-cli auth login` user) trip
    `need_user_authorization` from chat.list_recent's historical
    as_user=True default. Honor EDUFLOW_LARK_SEND_AS=bot like
    `say` does so the router catchup actually fetches."""
    captured = {}
    from eduflow.feishu import chat as _chat
    real_list_recent = _chat.list_recent
    def spy(chat_id, **kw):
        captured["as_user"] = kw.get("as_user")
        return []
    _chat.list_recent = spy
    try:
        from helpers import env_patch
        with isolated_env(), env_patch(EDUFLOW_LARK_SEND_AS="bot"):
            catchup.write_cursor("seed", "1")
            catchup.pending_lines("oc_x")
        assert captured["as_user"] is False
    finally:
        _chat.list_recent = real_list_recent


def test_pending_lines_default_list_fn_honors_toml_send_as_bot():
    """Container deploy without env EDUFLOW_LARK_SEND_AS but with
    [feishu] send_as = "bot" in eduflow.toml: catchup must respect
    the tunable and use bot identity. Boss-flagged 2026-05-06 host_smoke:
    bot-only container catchup got rc=2 because env var wasn't pinned
    in docker-compose; tunables fallback should cover that."""
    captured = {}
    from eduflow.feishu import chat as _chat
    real_list_recent = _chat.list_recent
    def spy(chat_id, **kw):
        captured["as_user"] = kw.get("as_user")
        return []
    _chat.list_recent = spy
    try:
        from helpers import env_patch
        with isolated_env() as tmp:
            (tmp / "eduflow.toml").write_text(
                '[feishu]\nsend_as = "bot"\n', encoding="utf-8")
            from eduflow.runtime import tunables
            tunables.reset_cache()
            with env_patch(EDUFLOW_LARK_SEND_AS=None,
                            EDUFLOW_CONFIG_FILE=str(tmp / "eduflow.toml")):
                catchup.write_cursor("seed", "1")
                catchup.pending_lines("oc_x")
        assert captured["as_user"] is False
    finally:
        _chat.list_recent = real_list_recent


def test_pending_lines_default_list_fn_keeps_user_default_when_env_unset():
    captured = {}
    from eduflow.feishu import chat as _chat
    real_list_recent = _chat.list_recent
    def spy(chat_id, **kw):
        captured["as_user"] = kw.get("as_user")
        return []
    _chat.list_recent = spy
    try:
        from helpers import env_patch
        with isolated_env(), env_patch(EDUFLOW_LARK_SEND_AS=None):
            catchup.write_cursor("seed", "1")
            catchup.pending_lines("oc_x")
        assert captured["as_user"] is True
    finally:
        _chat.list_recent = real_list_recent


def test_pending_lines_returns_empty_when_history_empty():
    with isolated_env():
        catchup.write_cursor("om_anchor", "1000")
        lines = catchup.pending_lines("oc_x", list_fn=lambda: [])
    assert lines == []


def test_pending_lines_skips_messages_with_bad_create_time():
    history = [
        _msg("om_ok", "1000"),
        {"message_id": "om_bad", "create_time": "not-a-number",
         "chat_id": "oc_x", "msg_type": "text",
         "sender": {"id": "ou_x"}, "body": {"content": "{}"}},
    ]
    with isolated_env():
        catchup.write_cursor("seed", "1")
        lines = catchup.pending_lines("oc_x", list_fn=lambda: history)
    parsed = [json.loads(line) for line in lines]
    ids = [p["event"]["message"]["message_id"] for p in parsed]
    assert ids == ["om_ok"]


# ── round-trip via subscribe.process_lines ──────────────────────


def test_pending_lines_round_trip_through_process_lines():
    """Ensure the lines we emit can be eaten by subscribe.process_lines."""
    history = [_msg("om_replay", "5000", text="catch this")]
    with isolated_env():
        catchup.write_cursor("seed", "1")
        lines = catchup.pending_lines("oc_x", list_fn=lambda: history)
        applies = []
        stats = process_lines(
            lines,
            team_agents=["manager"],
            chat_id="oc_x",
            apply_fn=_durable_append(applies),
        )
    assert stats.handled == 1
    assert applies[0].text == "catch this"
    assert applies[0].create_time == "5000"


# ── live lark-cli 1.0.21 response shape (REGRESSION ROUND-56) ───
#
# `lark-cli im +chat-messages-list` emits messages with content at TOP
# LEVEL (not under .body.content) AND create_time as a human-readable
# string ("2026-05-03 18:53"), not epoch ms. Prior to round-56,
# catchup silently dropped every replayed message because:
#   - body.get("content") returned "" (no .body key in live shape)
#   - int("2026-05-03 ...") raised ValueError → message skipped
# Tests below pin the live shape so we don't regress.


def _msg_live(msg_id, create_time_iso, *, text="hi", chat_id="oc_x", sender="ou_user"):
    """Mirror lark-cli 1.0.21+ chat-messages-list shape: content at top
    level, create_time as 'YYYY-MM-DD HH:MM[:SS]'."""
    return {
        "message_id": msg_id,
        "create_time": create_time_iso,
        "chat_id": chat_id,
        "msg_type": "text",
        "sender": {"id": sender, "id_type": "open_id"},
        "content": json.dumps({"text": text}),
    }


def test_pending_lines_handles_live_lark_cli_shape():
    """REGRESSION: live shape has content at top + ISO create_time. Old
    catchup silently dropped these as 'empty' / unparseable."""
    history = [
        _msg_live("om_live_1", "2026-05-03 18:50",
                  text="hello from live shape"),
    ]
    with isolated_env():
        catchup.write_cursor("om_old", "1700000000000")  # in 2023
        lines = catchup.pending_lines("oc_x", list_fn=lambda: history)
    assert len(lines) == 1, (
        f"live-shape message should be kept; got {len(lines)} lines")
    payload = json.loads(lines[0])
    msg = payload["event"]["message"]
    assert msg["message_id"] == "om_live_1"
    # Content survives the conversion
    assert "hello from live shape" in msg["content"]


def test_pending_lines_iso_time_compared_correctly_against_epoch_cursor():
    """The cursor stores epoch ms (set by record_decision from subscribe
    events), but list_recent returns ISO strings. The comparator must
    coerce both to the same scale."""
    # 2026-05-03 18:50 local ≈ 1777805400000 ish
    history = [
        _msg_live("om_before", "2026-05-03 17:00"),
        _msg_live("om_after", "2026-05-03 19:00"),
    ]
    with isolated_env():
        # cursor in epoch ms, between the two ISO times above
        # 2026-05-03 18:00 local = ~1777801200000
        catchup.write_cursor("om_cursor", "1777801200000")
        lines = catchup.pending_lines("oc_x", list_fn=lambda: history)
    parsed = [json.loads(line) for line in lines]
    ids = [p["event"]["message"]["message_id"] for p in parsed]
    # only om_after should survive (newer than cursor's epoch)
    assert ids == ["om_after"], f"expected only om_after, got {ids}"


def test_pending_lines_round_trip_with_live_shape_through_process_lines():
    """End-to-end: replay using the live shape, the events go through
    subscribe.process_lines and produce a real handled Decision (not
    silently dropped as 'empty')."""
    history = [_msg_live("om_replay_live", "2026-05-03 19:00",
                          text="catch this live")]
    with isolated_env():
        catchup.write_cursor("seed", "1")
        lines = catchup.pending_lines("oc_x", list_fn=lambda: history)
        applies = []
        stats = process_lines(
            lines,
            team_agents=["manager"],
            chat_id="oc_x",
            apply_fn=_durable_append(applies),
        )
    assert stats.handled == 1, (
        f"live-shape replay should produce 1 handled, got {dict(stats.drops_by_reason)}")
    assert applies[0].text == "catch this live"


# ── Package 2: Catchup mini-proof for /home boss-decision lane ──
#
# Three replay cases that prove /home's "boss decisions needed" lane
# will not silently lose or duplicate a manager/boss decision message
# after router restart. Each test pins one replay path so future
# regressions in catchup or subscribe show up here, not in production.


def test_mini_proof_router_restart_keeps_same_minute_boss_decision():
    """Case 1: router restart + same-minute REST history.

    The cursor (epoch-ms 14:08:32) is in the same minute as the REST
    history's only row (14:08:00). The boss decision message MUST come
    back via catchup and route through to manager. Without the minute-
    floor cutoff this row would be dropped (caught 2026-05-06 host
    smoke)."""
    cursor_ms = "1778047712107"  # 14:08:32.107 — sub-minute cursor
    history = [
        # Same minute as cursor; minute-floor must keep it.
        _msg_live("om_boss_decision", "2026-05-06 14:08",
                  text="approve and dispatch next batch",
                  chat_id="oc_team"),
    ]
    with isolated_env():
        catchup.write_cursor("om_prior_event", cursor_ms)
        lines = catchup.pending_lines("oc_team", list_fn=lambda: history)
        applies = []
        stats = process_lines(
            lines,
            team_agents=["manager"],
            chat_id="oc_team",
            apply_fn=_durable_append(applies),
        )
    # The boss decision survives catchup AND routes to manager
    assert stats.handled == 1, (
        f"boss decision must be handled after router restart; "
        f"got handled={stats.handled} drops={dict(stats.drops_by_reason)}")
    assert len(applies) == 1
    assert applies[0].msg_id == "om_boss_decision"
    assert applies[0].text == "approve and dispatch next batch"
    assert applies[0].targets == ["manager"]


def test_mini_proof_websocket_miss_recovered_by_catchup():
    """Case 2: websocket miss + catchup replay.

    The live WebSocket missed `om_missed_boss_decision` (it never
    reached the router's in-memory stream). The cursor is on the prior
    event's minute; REST history includes the missed row. Catchup must
    return the missed row so it gets a second chance to route to
    manager — never silently dropped."""
    cursor_iso = "2026-05-06 14:07"  # cursor at 14:07 (REST shape)
    history = [
        _msg_live("om_missed_boss_decision", "2026-05-06 14:08",
                  text="revert that closeout decision",
                  chat_id="oc_team"),
    ]
    with isolated_env():
        catchup.write_cursor("om_prior_event", cursor_iso)
        lines = catchup.pending_lines("oc_team", list_fn=lambda: history)
        assert len(lines) >= 1, (
            "missed websocket row must surface in catchup; "
            "if lines==[] the boss decision was silently dropped")
        # Round-trip through the router: missed row must apply once.
        applies = []
        stats = process_lines(
            lines,
            team_agents=["manager"],
            chat_id="oc_team",
            apply_fn=_durable_append(applies),
        )
    assert stats.handled >= 1
    handled_ids = [a.msg_id for a in applies]
    assert "om_missed_boss_decision" in handled_ids, (
        f"missed boss decision must apply via catchup; got {handled_ids}")
    assert applies[handled_ids.index("om_missed_boss_decision")].text \
        == "revert that closeout decision"


def test_mini_proof_duplicate_live_and_catchup_apply_once():
    """Case 3: duplicate live + catchup — same msg_id applies once.

    Simulate the production cross-restart path: a boss decision
    message_id was applied live before the router died, persisted to
    `seen_msg_ids`, and the same row also returns via catchup after
    restart. The router MUST apply it exactly once — the catchup-side
    duplicate is dropped by `seen_msg_ids`."""
    shared_msg_id = "om_dup_boss_decision"
    history = [_msg_live(shared_msg_id, "2026-05-06 14:00",
                         text="ship the closeout",
                         chat_id="oc_team")]
    # Pre-seed the seen-set as if the live path already applied it.
    pre_seen = {shared_msg_id}
    with isolated_env():
        catchup.write_cursor("om_prior", "1778047199000")  # 13:59:59
        lines = catchup.pending_lines("oc_team", list_fn=lambda: history)
        applies = []
        stats = process_lines(
            lines,
            team_agents=["manager"],
            chat_id="oc_team",
            seen_msg_ids=pre_seen,
            apply_fn=_durable_append(applies),
        )
    # Catchup should still surface the row (it is in the history and
    # newer than the cursor) — visibility is required so the router
    # gets a chance to dedup. But apply_fn must NOT be called for it.
    assert any(shared_msg_id in line for line in lines), (
        "catchup must still surface the row; "
        "visibility is what enables dedup, not the other way round")
    assert len(applies) == 0, (
        f"duplicate msg_id must NOT be re-applied; got {len(applies)} "
        f"applies: {[a.msg_id for a in applies]}")
    assert stats.dropped == 1
    assert stats.drops_by_reason.get("dedup", 0) == 1



def test_mini_proof_boss_decision_wires_into_manager_action_bucket():
    """Case 4 (end-to-end wiring): a blocked task with
    needs_manager_action=True must appear in the manager_action bucket
    (the /home data source). Without this wiring /home's
    boss_decisions_needed card would be empty even though the manager
    actually received a decision message. The 3 catchup mini-proofs above
    prove the router path; this one pins the source-of-truth map
    connection to the card."""
    from helpers import isolated_env
    from eduflow.store import tasks as _tasks_mod

    team = {
        "session": "EduFlow",
        "agents": {
            "manager": {"cli": "claude-code"},
            "worker_cc": {"cli": "claude-code"},
        },
    }
    with isolated_env(team=team):
        tid = _tasks_mod.create_flow(
            "worker_cc",
            "Approve batch scope",
            stage="curriculum",
            owner="worker_cc",
            creator="manager",
        )
        _tasks_mod.transition_flow(tid, to_status="assigned", actor="manager")
        _tasks_mod.transition_flow(tid, to_status="in_progress", actor="worker_cc")
        _tasks_mod.transition_flow(tid, to_status="blocked", actor="worker_cc")
        # Mark needs_manager_action — production router path.
        with _tasks_mod._locked():
            data = _tasks_mod._load()
            for t in data["tasks"]:
                if t["id"] == tid:
                    t["needs_manager_action"] = True
                    t["manager_action_type"] = "manager_review_needed"
            _tasks_mod._save(data)

        # Assert: the task shows up in manager_action bucket (the /home
        # boss_decisions_needed data source).
        overview = _tasks_mod.manager_overview()
        manager_action_ids = [t["id"] for t in overview["manager_action"]]
        assert tid in manager_action_ids, (
            f"blocked task must be in manager_action bucket — this is "
            f"the /home boss_decisions_needed source; "
            f"got {manager_action_ids}")
