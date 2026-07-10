#!/usr/bin/env python3
"""Generate a MiniMax TTS mp3 file.

Stdlib-only helper for EduFlow agents. Credentials come from the current
environment; `scripts/eduflow-team-env.sh` maps MINIMAX_AUTH_TOKEN to
MINIMAX_API_KEY.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_BASE_URL = "https://api.minimaxi.com"
DEFAULT_MODEL = "speech-02-turbo"
DEFAULT_VOICE = "Chinese (Mandarin)_Warm_Bestie"


def _post_json(url: str, token: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise SystemExit(f"MiniMax TTS HTTP {e.code}: {body[:1000]}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"MiniMax TTS network error: {e}") from e


def synthesize(text: str, output: Path, *, voice: str, model: str, base_url: str) -> Path:
    token = os.environ.get("MINIMAX_API_KEY") or os.environ.get("MINIMAX_AUTH_TOKEN")
    if not token:
        raise SystemExit("MINIMAX_API_KEY or MINIMAX_AUTH_TOKEN is required")
    if not text.strip():
        raise SystemExit("text is required")

    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": voice,
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
    }
    data = _post_json(f"{base_url.rstrip('/')}/v1/t2a_v2", token, payload)
    audio_hex = ((data.get("data") or {}).get("audio") or "").strip()
    if not audio_hex:
        raise SystemExit(f"MiniMax TTS returned no audio: {json.dumps(data, ensure_ascii=False)[:1000]}")
    try:
        audio = bytes.fromhex(audio_hex)
    except ValueError as e:
        raise SystemExit("MiniMax TTS audio was not hex-encoded mp3 data") from e

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(audio)
    return output


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate a MiniMax TTS mp3 file")
    p.add_argument("text", nargs="?", help="Text to synthesize")
    p.add_argument("-o", "--output", default=".eduflow-team-state/out/minimax-reply.mp3")
    p.add_argument("--voice", default=os.environ.get("MINIMAX_TTS_VOICE", DEFAULT_VOICE))
    p.add_argument("--model", default=os.environ.get("MINIMAX_TTS_MODEL", DEFAULT_MODEL))
    p.add_argument("--base-url", default=os.environ.get("MINIMAX_TTS_BASE_URL", DEFAULT_BASE_URL))
    p.add_argument("--self-test", action="store_true", help="Check parser/defaults without calling the API")
    args = p.parse_args(argv)

    if args.self_test:
        assert args.voice
        assert args.model
        assert args.base_url.startswith("http")
        print("self-test ok")
        return 0

    out = synthesize(
        args.text or sys.stdin.read(),
        Path(args.output),
        voice=args.voice,
        model=args.model,
        base_url=args.base_url,
    )
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
