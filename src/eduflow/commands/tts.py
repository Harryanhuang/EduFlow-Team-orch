"""`eduflow tts say <text>` — text-to-speech via MiniMax t2a_v2, optional
Feishu send. Wraps the MiniMax TTS API used in T-158 (2026-07-09) and
saves a rediscovery path for anyone who needs a voice message without
re-deriving the curl incantation from `lark-cli` outputs.

The MiniMax TTS endpoint is HTTP-only (no published CLI subcommand in
the v0.0.2 minimax-cli drop shipped at 2026-07-09 15:49), so this
command uses stdlib urllib to POST. Auth comes from
$MINIMAX_AUTH_TOKEN (set in agent-home env files). Default model +
voice match what minimax-cli advertises in settings-manager.js
(speech-01-hd / female-yujie) but those strings failed against the
/api/v1/models listing — the t2a_v2 endpoint accepts `speech-01-hd`
directly, which is the path this command takes.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from eduflow.runtime import paths
from eduflow.util import (
    error_exit, maybe_print_help, pop_bool_flag, pop_flag, print_json,
    reject_extra_args, usage_error,
)


USAGE = (
    "usage: eduflow tts say <text> "
    "[--voice <voice_id>] [--pitch N] [--speed N] [--model <model>] "
    "[--agent <name>] [--to <chat_id>] "
    "[--output <path>] [--no-send] [--as bot|user] "
    "[--sample-rate 8000|16000|24000|32000]"
)


_TTS_URL = "https://api.minimaxi.com/v1/t2a_v2"
_DEFAULT_MODEL = "speech-01-hd"
_DEFAULT_VOICE = "female-yujie"
_DEFAULT_SAMPLE_RATE = 32000


def _auth_token() -> str:
    token = os.environ.get("MINIMAX_AUTH_TOKEN") or os.environ.get("MINIMAX_API_KEY")
    if not token:
        return ""  # caller decides whether to error
    return token


def _post_tts(text: str, voice: str, model: str, sample_rate: int,
              pitch: int = 0, speed: float = 1.0) -> bytes:
    """Call MiniMax t2a_v2, return raw MP3 bytes. Raises on non-zero
    base_resp.status_code (which is a *body-level* error, distinct from
    HTTP status — 200 with status_code != 0 is still a failure)."""
    token = _auth_token()
    if not token:
        raise RuntimeError(
            "MINIMAX_AUTH_TOKEN (or MINIMAX_API_KEY) not set; "
            "check agent-home env files"
        )
    payload = {
        "model": model,
        "text": text,
        "voice_setting": {
            "voice_id": voice,
            "speed": speed,
            "vol": 1.0,
            "pitch": pitch,
        },
        "audio_setting": {
            "format": "mp3",
            "sample_rate": sample_rate,
        },
    }
    req = urllib.request.Request(
        _TTS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read()
    parsed = json.loads(body)
    base = parsed.get("base_resp", {}) or {}
    if base.get("status_code", 0) != 0:
        raise RuntimeError(
            f"t2a_v2 error {base.get('status_code')}: {base.get('status_msg')}"
        )
    audio_hex = (parsed.get("data") or {}).get("audio") or ""
    if not audio_hex:
        raise RuntimeError("t2a_v2 returned empty audio payload")
    return bytes.fromhex(audio_hex)


def _send_feishu(chat_id: str, file_path: Path, as_identity: str) -> str:
    """Call lark-cli im +messages-send to deliver the MP3 as a file
    attachment. Returns the new message_id. Raises if lark-cli exits
    non-zero or returns ok:false.

    lark-cli 1.0.64+ requires a path relative to cwd (the `unsafe output
    path` validation), so we run inside a subshell that cd's to the
    file's directory first.
    """
    cmd = [
        "bash", "-c",
        (f"cd {shlex.quote(str(file_path.parent.resolve()))} && "
         f"lark-cli im +messages-send --chat-id {shlex.quote(chat_id)} "
         f"--file {shlex.quote(file_path.name)} --msg-type file "
         f"--as {shlex.quote(as_identity)}"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(
            f"lark-cli im +messages-send failed (rc={proc.returncode}): "
            f"{proc.stderr.strip()}"
        )
    parsed = json.loads(proc.stdout)
    if not parsed.get("ok"):
        raise RuntimeError(f"lark-cli returned ok=false: {proc.stdout.strip()}")
    return parsed.get("data", {}).get("message_id", "")


def _resolve_agent_voice(agent: str) -> tuple[str, int, float]:
    """Look up voice_id/pitch/speed from eduflow.toml [tts.voice.<agent>]."""
    from eduflow.runtime import tunables
    cfg = tunables.load() or {}
    table = cfg.get("tts", {}).get("voice", {}) or {}
    entry = table.get(agent)
    if not isinstance(entry, dict):
        return _DEFAULT_VOICE, 0, 1.0
    voice = entry.get("voice") or _DEFAULT_VOICE
    pitch = int(entry.get("pitch", 0) or 0)
    speed = float(entry.get("speed", 1.0) or 1.0)
    return voice, pitch, speed


def _say(argv: list[str]) -> int:
    if maybe_print_help(argv, USAGE):
        return 0
    rest = argv[:]
    voice = pop_flag(rest, "--voice")
    pitch_s = pop_flag(rest, "--pitch")
    speed_s = pop_flag(rest, "--speed")
    agent = pop_flag(rest, "--agent")
    model = pop_flag(rest, "--model") or _DEFAULT_MODEL
    chat_id = pop_flag(rest, "--to")
    output = pop_flag(rest, "--output")
    sample_rate = int(pop_flag(rest, "--sample-rate") or _DEFAULT_SAMPLE_RATE)
    as_identity = pop_flag(rest, "--as") or "bot"
    no_send = pop_bool_flag(rest, "--no-send")
    if not rest:
        return usage_error(USAGE)
    extra = reject_extra_args(rest[1:], USAGE)
    if extra is not None:
        return extra
    text = rest[0]
    # --agent takes precedence: pulls voice/pitch/speed from eduflow.toml
    pitch = int(pitch_s) if pitch_s is not None else 0
    speed = float(speed_s) if speed_s is not None else 1.0
    if agent:
        v, p, s = _resolve_agent_voice(agent)
        voice = voice or v
        if pitch_s is None:
            pitch = p
        if speed_s is None:
            speed = s
    voice = voice or _DEFAULT_VOICE
    if not chat_id and not no_send:
        # fall back to eduflow.toml chat_id (top-level, set by `eduflow init`)
        try:
            from eduflow.runtime import tunables
            cfg = tunables.load() or {}
            chat_id = str(cfg.get("chat_id") or cfg.get("feishu", {}).get("chat_id", "") or "")
        except Exception:
            chat_id = ""
        if not chat_id:
            return error_exit(
                "❌ no --to <chat_id> and no chat_id in eduflow.toml; "
                "pass --to or use --no-send"
            )
    try:
        audio = _post_tts(text, voice, model, sample_rate, pitch=pitch, speed=speed)
    except (urllib.error.URLError, RuntimeError, json.JSONDecodeError) as e:
        return error_exit(f"❌ TTS failed: {e}")
    out_path = Path(output) if output else (paths.state_dir() / "tts" / "last.mp3")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(audio)
    result = {
        "ok": True,
        "path": str(out_path),
        "bytes": len(audio),
        "voice": voice,
        "pitch": pitch,
        "speed": speed,
        "model": model,
        "sample_rate": sample_rate,
        "agent": agent,
    }
    if not no_send and chat_id:
        try:
            msg_id = _send_feishu(chat_id, out_path, as_identity)
            result["message_id"] = msg_id
            result["chat_id"] = chat_id
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            return error_exit(f"❌ TTS saved to {out_path} but Feishu send failed: {e}")
    print_json(result)
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(USAGE)
        return 0
    sub = argv[0]
    if sub == "say":
        return _say(argv[1:])
    print(f"❌ unknown subcommand: {sub}\n{USAGE}", file=sys.stderr)
    return 1
