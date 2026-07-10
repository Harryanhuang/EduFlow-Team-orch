### Task 2.3: Fix command injection in `agents/claude_code.py`

**Files:**
- Modify: `src/eduflow/agents/claude_code.py` (around `--model` / `--name`)
- Test: `tests/unit/test_agents_claude_code.py` (new or extend)

**Interfaces:**
- Consumes: `shlex.quote`
- Produces: `ClaudeCodeAdapter.spawn_cmd()` returns a shell-safe command string.

- [ ] **Step 1: Find the exact `spawn_cmd` string construction**

Read `src/eduflow/agents/claude_code.py` and locate the line containing `--model {model} --name {agent}`.

- [ ] **Step 2: Write the failing test**

```python
# tests/unit/test_agents_claude_code.py
import shlex
from eduflow.agents.claude_code import ClaudeCodeAdapter


def test_spawn_cmd_quotes_model_and_agent():
    adapter = ClaudeCodeAdapter({})
    cmd = adapter.spawn_cmd(agent="a; echo pwned", model="claude-sonnet-5; echo pwned")
    assert shlex.quote("a; echo pwned") in cmd
    assert shlex.quote("claude-sonnet-5; echo pwned") in cmd
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_agents_claude_code.py::test_spawn_cmd_quotes_model_and_agent`
Expected: FAIL.

- [ ] **Step 4: Patch `spawn_cmd`**

Use `shlex.quote` around `agent` and `model` wherever they appear in the spawn command string.

Example pattern:
```python
import shlex

cmd = (
    f"HOME={shlex.quote(home)} "
    f"CLAUDE_CODE_OAUTH_TOKEN={shlex.quote(token)} "
    f"claude --dangerously-skip-permissions "
    f"--model {shlex.quote(model)} --name {shlex.quote(agent)}"
)
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_agents_claude_code.py::test_spawn_cmd_quotes_model_and_agent`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/eduflow/agents/claude_code.py tests/unit/test_agents_claude_code.py
git commit -m "security: quote model and agent names in claude spawn command"
```
