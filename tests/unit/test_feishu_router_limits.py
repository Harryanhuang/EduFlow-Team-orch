from eduflow.feishu.router import classify_event, Decision, _reset_rate_limit


def test_oversized_message_is_dropped():
    _reset_rate_limit()
    event = {
        "message_id": "m1",
        "sender_type": "user",
        "sender_id": "u1",
        "chat_id": "c1",
        "text": "x" * 4001,
    }
    decision = classify_event(event, agents=[], manager=None, chat_id="c1")
    assert decision.action == "DROP"


def test_duplicate_message_is_dropped():
    _reset_rate_limit()
    event = {"message_id": "m1", "sender_type": "user", "sender_id": "u1", "chat_id": "c1", "text": "hi"}
    classify_event(event, agents=[], manager=None, chat_id="c1")
    _reset_rate_limit()
    decision = classify_event(event, agents=[], manager=None, chat_id="c1")
    assert decision.action == "DROP"
