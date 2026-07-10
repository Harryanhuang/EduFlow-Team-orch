# Scenario — `eduflow tts say` end-to-end voice delivery

> **Owners**: operator (manual regression)
> **Triggers**: T-158 (2026-07-09). Spawned by `manager` after MiniMax TTS
> integration + per-agent voice mapping was commissioned by boss.

This scenario exercises the full text-to-voice path: API call → ffmpeg
mp3→opus transcode → Feishu `--audio` send. Run against a real deployment
because the gappy areas are (a) MiniMax auth token presence and (b)
lark-cli opus upload shape.

## Pre-conditions

- `MINIMAX_AUTH_TOKEN` set in agent-home env (or `~/.zshenv`).
- `ffmpeg` 4.x+ on `$PATH` (`brew install ffmpeg`).
- `lark-cli` ≥ 1.0.64 logged in as bot OR user identity.
- `eduflow.toml` contains `[tts]` and `[tts.voice]` sections with at
  least one agent entry (e.g. `manager`).

## Cases

### Case 1 — `eduflow tts say --help`

**Given** the rebuild is installed (`pip install -e .`)
**When** `eduflow tts say --help`
**Then** stdout shows usage with `--agent`, `--pitch`, `--speed`,
`--voice`, `--to`, `--no-send` flags.

### Case 2 — Generate MP3 to disk (no Feishu send)

**Given** `MINIMAX_AUTH_TOKEN` is set
**When** `eduflow tts say "巡检完毕, 全员正常" --agent manager --no-send`
**Then** exit 0, stdout JSON has `"voice": "male-qn-daxuesheng"`,
`"pitch": 3`, `"speed": 1.25`, `"path"` ends in `.mp3`, file size > 0.

### Case 3 — Send voice to test chat

**Given** chat_id `oc_31f0f00378bea36dd5e8f69256cc7a5e` (test_a)
**When** `eduflow tts say "Hello world" --agent worker_qbank --to <chat_id> --as bot`
**Then** exit 0, stdout JSON has a `message_id` (e.g. `om_x...`), and the
voice clip arrives in the chat as an Opus "red dot voice" message.

### Case 4 — Unknown agent falls back to default voice

**When** `eduflow tts say "test" --agent nonexistent_agent --no-send`
**Then** exit 0, stdout `"voice": "female-yujie"` (the default), `"pitch": 0`,
`"speed": 1.0`. No crash.

### Case 5 — Missing token errors loudly

**Given** `MINIMAX_AUTH_TOKEN` unset
**When** `eduflow tts say "test" --agent manager --no-send`
**Then** exit ≠ 0, stderr mentions `MINIMAX_AUTH_TOKEN`.

### Case 6 — mp3 → opus transcode for Feishu

**Given** a generated MP3 from Case 2
**When** `ffmpeg -i <mp3> -c:a libopus -b:a 32k -ac 1 -application voip <opus>`
**Then** opus file plays in any browser. The same transcode is invoked
inside `lark-cli im +messages-send --audio`.

## Cleanup

Generated artefacts live under `.eduflow-team-state/tts/last.mp3` and
`/tmp/voice-demo/`. Safe to `rm` between scenarios.

## Files exercised

- `src/eduflow/commands/tts.py` — `_post_tts`, `_send_feishu`,
  `_resolve_agent_voice`, `_say`, `main`
- `eduflow.toml` `[tts]`, `[tts.voice]`
- `src/eduflow/cli.py` `[voice tts]` group registration