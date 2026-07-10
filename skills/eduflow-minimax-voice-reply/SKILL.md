---
name: eduflow-minimax-voice-reply
description: Generate a MiniMax TTS voice reply for EduFlow. Use when the user asks for 语音回复, voice reply, TTS, mp3, audio response, or MiniMax voice output. Produces a local mp3 file; does not send Feishu audio by itself.
---

# EduFlow MiniMax Voice Reply

Use this when a user asks an EduFlow agent to reply with voice/audio instead of plain text.

## Boundary

- `minimax` CLI is installed for text agent prompts, but it has no TTS subcommand.
- Voice reply uses the MiniMax T2A HTTP endpoint through `scripts/minimax_tts.py`.
- This skill only creates a local mp3. Sending it into Feishu as a real voice/file message is a separate Feishu upload step.

## Command

Always source the EduFlow env first so the MiniMax key/model mapping is present:

```bash
source scripts/eduflow-team-env.sh
python3 scripts/minimax_tts.py "收到，我现在用语音回复你。" -o .eduflow-team-state/out/manager-reply.mp3
```

The script prints the output path on success.

## Defaults

- API key: `MINIMAX_API_KEY`, falling back to `MINIMAX_AUTH_TOKEN`.
- TTS endpoint: `https://api.minimaxi.com/v1/t2a_v2`.
- TTS model: `speech-02-turbo`.
- Voice: `Chinese (Mandarin)_Warm_Bestie`.
- Output format: mono mp3, 32000 Hz, 128 kbps.

Override only when needed:

```bash
MINIMAX_TTS_VOICE="Chinese (Mandarin)_Warm_Bestie" \
MINIMAX_TTS_MODEL="speech-02-turbo" \
python3 scripts/minimax_tts.py "文本" -o .eduflow-team-state/out/reply.mp3
```

## Manager Procedure

0. Send a visible ACK before any TTS, upload, clone, or voice search work:

```bash
eduflow say manager "收到，正在处理语音回复：先生成音频，再回报发送结果。" --to user
```

Then mark the inbox item accepted/started. Never mark `read --ack` before a visible `say --to user` for a boss message.

1. Draft the exact text that should be spoken.
2. Generate the mp3 with `scripts/minimax_tts.py`.
3. Verify the file exists and is non-empty:

```bash
test -s .eduflow-team-state/out/manager-reply.mp3
```

4. If Feishu audio/file upload is not wired, tell the user the mp3 path and send a short text fallback with `eduflow say ... --to user`.

Do not claim "I sent a voice message" until Feishu upload/send succeeds.

For work longer than two minutes, send a short visible progress line before continuing:

```bash
eduflow say manager "语音任务进展：TTS 已生成，正在测试飞书发送/音色克隆。" --to user
```

If voice cloning fails, report the exact actionable reason to the user immediately. Example: `voice_clone returned duration too short; please send a clean >=10s sample`.

## Failure Handling

- Missing key: source `scripts/eduflow-team-env.sh`.
- `unknown model`: use the script default `speech-02-turbo`, not the chat model `MiniMax-M3`.
- No audio in response: print the API error and fall back to text.
- `voice duration too short`: ask for a clean sample of at least 10 seconds before retrying.
- User explicitly wants a real Feishu voice message: generate the mp3 first, then route the upload/send integration to `worker_builder`.
