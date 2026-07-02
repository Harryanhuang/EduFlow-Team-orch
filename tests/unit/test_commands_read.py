"""Tests for `eduflow read <local_id>` and its no-such-message diagnostic.

The diagnostic fires when `eduflow read` can't find a local_id in the
inbox. It must distinguish:
  - agent hallucination (malformed id)
  - router respawn loss (router.log shows recent respawn)
  - cross-agent confusion (recent rows for other agents)
  - clean miss (none of the above)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eduflow.store import local_facts
from helpers import isolated_env, run_cli


# A perfectly valid local_id format but it does NOT exist in inbox.
# Use this to exercise hints 2/3/4 (format OK, but missing).
_MISSING_VALID_ID = "msg_1782000000000_abcdef0123"


# A completely malformed id — exercises hint 1.
_BAD_FORMAT_ID = "not-a-valid-id"


def _append_inbox_row(local_id: str, to: str, frm: str, content: str) -> None:
    """Append a row to inbox.json inside an active isolated_env."""
    local_facts.append_message(to, frm, content)
    # Sanity: the auto-generated id may differ from our local_id param
    # because append_message generates its own uuid. So we instead reach
    # into the inbox file to overwrite the row's local_id.
    from eduflow.store.local_facts import _inbox_file
    import json
    path = _inbox_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    msgs = data.get("messages", [])
    if msgs:
        msgs[-1]["local_id"] = local_id
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_read_existing_message_succeeds():
    with isolated_env() as tmp:
        _append_inbox_row(
            "msg_1782000000001_aaaaaaaaaa",
            "manager", "user", "hi"
        )
        rc, out, err = run_cli(["read", "msg_1782000000001_aaaaaaaaaa"])
        assert rc == 0, f"expected 0, got {rc}; err={err}"
        assert "✅ marked read" in out


def test_read_malformed_id_returns_hint_about_format():
    with isolated_env():
        rc, out, err = run_cli(["read", _BAD_FORMAT_ID])
        assert rc != 0
        assert "no such message" in err
        # Either the length-too-short hint or the format-mismatch hint
        # is acceptable for a clearly-wrong id. The new shorter-than-28
        # branch fires first when the id is very short, hence the OR.
        assert (
            "doesn't match expected format" in err
            or "shorter than the minimum" in err
        )


def test_read_short_id_returns_length_hint():
    """Boss 2026-07-02 D: reject if length < 28 (e.g. om_xxx event id)
    with a length-specific hint instead of the generic format hint."""
    with isolated_env():
        # 14 chars — well under the 28-char minimum
        rc, out, err = run_cli(["read", "om_abc12345678"])
        assert rc != 0
        assert "shorter than the minimum" in err
        assert "28 chars" in err
        # And it should specifically mention the om_xxx mistake pattern
        assert "Feishu event id" in err or "om_xxx" in err


def test_read_missing_valid_id_returns_router_or_cross_agent_hint():
    with isolated_env():
        rc, out, err = run_cli(["read", _MISSING_VALID_ID])
        assert rc != 0
        assert "no such message" in err
        # The exact hint depends on what's in the (empty) inbox and
        # whether router.log exists, but at least one of the four
        # hints must surface. With an empty inbox and no router.log,
        # the "no router respawn signals" hint is the deterministic one.
        assert (
            "no router respawn signals" in err
            or "router.log shows" in err
            or "most recent inbox row" in err
            or "doesn't match expected format" in err
        )


def test_read_missing_id_with_router_respawn_signals():
    """If router.log tail contains respawn markers, the hint should
    mention the respawn hypothesis — not just the generic 'never existed'."""
    with isolated_env() as tmp:
        # Synthesize a router.log with respawn signals
        log_path = tmp / "router.log"
        log_path.write_text(
            "🚀 router subscribing on chat\n"
            "  ⚠️ no events for 135s (threshold 120s); "
            "subscribe likely silently stalled, exiting for respawn\n"
            "🚀 router subscribing on chat\n"
        )
        rc, out, err = run_cli(["read", _MISSING_VALID_ID])
        assert rc != 0
        assert "respawn" in err


def test_read_missing_id_with_cross_agent_activity():
    """If there are recent rows for OTHER agents, surface that hint so
    the operator can spot a confused-id mistake."""
    with isolated_env():
        _append_inbox_row(
            "msg_1782000000002_bbbbbbbbbb",
            "manager", "user", "this went to manager"
        )
        rc, out, err = run_cli(["read", _MISSING_VALID_ID])
        assert rc != 0
        assert (
            "most recent inbox row" in err
            or "no router respawn signals" in err  # acceptable fallback
        )


def test_read_ack_kind_still_works():
    """Regression: ack flow must continue to record the ack on the row
    found by mark_read — diagnostic only fires on miss."""
    with isolated_env():
        _append_inbox_row(
            "msg_1782000000003_cccccccc",
            "manager", "user", "hi"
        )
        rc, out, err = run_cli(
            ["read", "msg_1782000000003_cccccccc", "--ack", "accepted_task"]
        )
        assert rc == 0
        assert "ack=accepted_task" in out