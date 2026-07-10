import eduflow.feishu.router as router
from eduflow.feishu.router import classify_event, _reset_rate_limit


def test_sender_rate_limit(monkeypatch):
    _reset_rate_limit()
    # Allow 2 messages per 10 seconds for testing.
    monkeypatch.setattr(router, "_RATE_LIMIT_MAX", 2)
    monkeypatch.setattr(router, "_RATE_LIMIT_WINDOW_S", 10)

    base = {"sender_type": "user", "sender_id": "u1", "chat_id": "c1", "text": "hi"}
    assert classify_event({**base, "message_id": "rl_m1"}, agents=[], manager=None, chat_id="c1").action != "DROP"
    assert classify_event({**base, "message_id": "rl_m2"}, agents=[], manager=None, chat_id="c1").action != "DROP"
    assert classify_event({**base, "message_id": "rl_m3"}, agents=[], manager=None, chat_id="c1").action == "DROP"
