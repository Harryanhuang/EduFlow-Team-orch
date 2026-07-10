### Task 2.2: Fix command injection in `agents/kimi_code.py`

**Files:**
- Modify: `src/eduflow/agents/kimi_code.py:8-10`
- Test: `tests/unit/test_agents_kimi_code.py` (new)

**Interfaces:**
- Consumes: `shlex.quote`
- Produces: `KimiCodeAdapter.spawn_cmd()` returns a shell-safe command string.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_agents_kimi_code.py
import shlex
from eduflow.agents.kimi_code import KimiCodeAdapter


def test_spawn_cmd_quotes_agent_name():
    adapter = KimiCodeAdapter({})
    cmd = adapter.spawn_cmd(agent="worker; echo pwned", model="kimi")
    assert shlex.quote("worker; echo pwned") in cmd
    assert "KIMI_AGENT=worker; echo pwned" not in cmd
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_agents_kimi_code.py::test_spawn_cmd_quotes_agent_name`
Expected: FAIL.

- [ ] **Step 3: Patch `spawn_cmd`**

```python
import shlex

class KimiCodeAdapter(CliAdapter):
    def spawn_cmd(self, agent: str, model: str) -> str:
        return f"DISABLE_UPDATE_CHECK=1 KIMI_AGENT={shlex.quote(agent)} kimi --yolo"
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_agents_kimi_code.py::test_spawn_cmd_quotes_agent_name`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/agents/kimi_code.py tests/unit/test_agents_kimi_code.py
git commit -m "security: quote agent name in kimi spawn command"
```
