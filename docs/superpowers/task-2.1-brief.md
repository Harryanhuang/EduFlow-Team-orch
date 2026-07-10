### Task 2.1: Fix command injection in `commands/tts.py`

**Files:**
- Modify: `src/eduflow/commands/tts.py:111-117`
- Test: `tests/unit/test_commands_tts.py` (new or extend existing)

**Interfaces:**
- Consumes: `shlex.quote`
- Produces: `_send_feishu()` builds a safe `bash -c` string.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_commands_tts.py
import shlex
from pathlib import Path


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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_commands_tts.py::test_send_feishu_quotes_injection_attempts`
Expected: FAIL (assertion on quoted string).

- [ ] **Step 3: Patch `_send_feishu`**

Replace lines 111–117 with:

```python
import shlex

cmd = [
    "bash", "-c",
    (f"cd {shlex.quote(str(file_path.parent.resolve()))} && "
     f"lark-cli im +messages-send --chat-id {shlex.quote(chat_id)} "
     f"--file {shlex.quote(file_path.name)} --msg-type file "
     f"--as {shlex.quote(as_identity)}"),
]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_commands_tts.py::test_send_feishu_quotes_injection_attempts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/commands/tts.py tests/unit/test_commands_tts.py
git commit -m "security: quote shell args in tts feishu send path"
```
