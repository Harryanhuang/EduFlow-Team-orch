"""Tests for `eduflow tts say` — MiniMax TTS wrapper + agent voice lookup.

Per CLAUDE.md "Building rules" rule 1: every new command ships its own
unit test. These cover:
  - USAGE on --help / no args
  - _auth_token fall-back (MINIMAX_AUTH_TOKEN > MINIMAX_API_KEY)
  - _resolve_agent_voice from eduflow.toml [tts.voice.<agent>]
  - _resolve_agent_voice default fallback for unknown agents
  - main() dispatch: `say` → _say; unknown subcommand → error
  - _say rejects extra args after the text
"""
from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from eduflow.commands import tts as tts_mod
from eduflow.commands.tts import (
    _auth_token,
    _DEFAULT_VOICE,
    _post_tts,
    _resolve_agent_voice,
    main,
)


# ──── _auth_token ────────────────────────────────────────────────

def test_auth_token_prefers_minimax_auth_token():
    with mock.patch.dict("os.environ",
                         {"MINIMAX_AUTH_TOKEN": "tok-A", "MINIMAX_API_KEY": "tok-B"},
                         clear=True):
        assert _auth_token() == "tok-A"


def test_auth_token_falls_back_to_minimax_api_key():
    with mock.patch.dict("os.environ",
                         {"MINIMAX_API_KEY": "tok-B"}, clear=True):
        assert _auth_token() == "tok-B"


def test_auth_token_empty_when_unset():
    with mock.patch.dict("os.environ", {}, clear=True):
        assert _auth_token() == ""


# ──── _resolve_agent_voice ────────────────────────────────────────

def test_resolve_known_agent_returns_mapped_voice():
    voice, pitch, speed = _resolve_agent_voice("manager")
    assert voice == "male-qn-daxuesheng"
    assert pitch == 3
    assert speed == 1.25


def test_resolve_known_agent_worker_qbank():
    voice, pitch, speed = _resolve_agent_voice("worker_qbank")
    assert voice == "female-yujie"
    assert pitch == 0
    assert speed == 1.0


def test_resolve_unknown_agent_returns_default():
    voice, pitch, speed = _resolve_agent_voice("nonsense-agent")
    assert voice == _DEFAULT_VOICE
    assert pitch == 0
    assert speed == 1.0


# ──── _post_tts ──────────────────────────────────────────────────

def test_post_tts_raises_when_no_token():
    with mock.patch.dict("os.environ", {}, clear=True):
        try:
            _post_tts("hi", "female-yujie", "speech-01-hd", 32000)
        except RuntimeError as e:
            assert "MINIMAX_AUTH_TOKEN" in str(e)
        else:
            assert False, "expected RuntimeError"


def test_post_tts_passes_pitch_and_speed_to_payload():
    captured: dict = {}

    def fake_urlopen(req, timeout=60):
        body = json.loads(req.data.decode("utf-8"))
        captured.update(body)
        # Return a fake "audio" hex payload so _post_tts decodes it
        return mock.MagicMock(
            read=lambda: json.dumps({
                "data": {"audio": "deadbeef"},
                "base_resp": {"status_code": 0, "status_msg": "ok"},
            }).encode("utf-8"),
            __enter__=lambda s: s,
            __exit__=lambda s, *a: None,
        )

    with mock.patch.dict("os.environ", {"MINIMAX_AUTH_TOKEN": "tok"}, clear=True):
        with mock.patch.object(tts_mod.urllib.request, "urlopen", fake_urlopen):
            audio = _post_tts("hi", "male-qn-daxuesheng", "speech-01-hd",
                              32000, pitch=3, speed=1.25)
    assert audio == b"\xde\xad\xbe\xef"
    vs = captured["voice_setting"]
    assert vs["voice_id"] == "male-qn-daxuesheng"
    assert vs["pitch"] == 3
    assert vs["speed"] == 1.25


def test_post_tts_raises_on_api_error_status_code():
    def fake_urlopen(req, timeout=60):
        return mock.MagicMock(
            read=lambda: json.dumps({
                "base_resp": {"status_code": 2037, "status_msg": "voice duration too short"},
            }).encode("utf-8"),
            __enter__=lambda s: s,
            __exit__=lambda s, *a: None,
        )

    with mock.patch.dict("os.environ", {"MINIMAX_AUTH_TOKEN": "tok"}, clear=True):
        with mock.patch.object(tts_mod.urllib.request, "urlopen", fake_urlopen):
            try:
                _post_tts("hi", "v", "speech-01-hd", 32000)
            except RuntimeError as e:
                assert "2037" in str(e)
                assert "voice duration too short" in str(e)
            else:
                assert False, "expected RuntimeError"


# ──── main() dispatch ────────────────────────────────────────────

def test_main_no_args_prints_usage(capsys):
    rc = main([])
    captured = capsys.readouterr()
    assert rc == 0
    assert "usage:" in captured.out


def test_main_help_flag(capsys):
    rc = main(["--help"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "--agent" in captured.out
    assert "--pitch" in captured.out


def test_main_unknown_subcommand(capsys):
    rc = main(["bogus", "text"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "unknown subcommand" in captured.err


def test_say_no_text_returns_usage_error(capsys):
    rc = tts_mod._say([])
    captured = capsys.readouterr()
    assert rc != 0
    assert "usage:" in (captured.out + captured.err)


def test_say_rejects_extra_args(capsys):
    rc = tts_mod._say(["hi", "extra1"])
    captured = capsys.readouterr()
    assert rc != 0


def test_say_with_agent_uses_mapped_voice(tmp_path):
    captured: dict = {}

    def fake_urlopen(req, timeout=60):
        body = json.loads(req.data.decode("utf-8"))
        captured.update(body)
        return mock.MagicMock(
            read=lambda: json.dumps({
                "data": {"audio": "abcd"},
                "base_resp": {"status_code": 0, "status_msg": "ok"},
            }).encode("utf-8"),
            __enter__=lambda s: s,
            __exit__=lambda s, *a: None,
        )

    with mock.patch.dict("os.environ", {"MINIMAX_AUTH_TOKEN": "tok"}, clear=True):
        with mock.patch.object(tts_mod.urllib.request, "urlopen", fake_urlopen):
            with mock.patch.object(tts_mod.paths, "state_dir",
                                   lambda: tmp_path):
                rc = tts_mod._say(["hello", "--agent", "manager", "--no-send"])
    assert rc == 0
    vs = captured["voice_setting"]
    assert vs["voice_id"] == "male-qn-daxuesheng"
    assert vs["pitch"] == 3
    assert vs["speed"] == 1.25
    # The mp3 should have been written under tmp_path/tts/last.mp3
    out = tmp_path / "tts" / "last.mp3"
    assert out.exists()
    assert out.read_bytes() == b"\xab\xcd"

# ──── _send_feishu shell quoting ─────────────────────────────────

def test_send_feishu_quotes_injection_attempts(monkeypatch):
    """Verify that shell metacharacters in chat_id / file name / identity
    are quoted and not executed."""
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        class R:
            returncode = 0
            stderr = ""
            stdout = '{"ok": true, "data": {"message_id": "m1"}}'
        return R()

    from eduflow.commands import tts
    monkeypatch.setattr(tts.subprocess, "run", fake_run)

    tts._send_feishu(
        chat_id="oc_x; echo pwned",
        file_path=Path("/tmp/x; echo pwned.mp3"),
        as_identity="bot; echo pwned",
    )

    shell = captured["cmd"][2]
    assert shlex.quote("oc_x; echo pwned") in shell
    assert shlex.quote("bot; echo pwned") in shell
    # The literal semicolon should not appear outside a quote.
    assert "oc_x; echo pwned" not in shell.replace(shlex.quote("oc_x; echo pwned"), "")
