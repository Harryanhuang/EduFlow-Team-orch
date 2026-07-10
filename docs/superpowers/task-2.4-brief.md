### Task 2.4: Audit and fix remaining adapters

**Files:**
- Modify: `src/eduflow/agents/codex_cli.py`, `gemini_cli.py`, `qwen_code.py`, `mimo_code.py`, `qoder_cli_cn.py`, `hermes_agent.py`
- Test: `tests/unit/test_agents_spawn_safety.py` (new)

**Interfaces:**
- Consumes: `shlex.quote`
- Produces: All adapters pass a spawn-cmd safety test.

- [ ] **Step 1: Read every adapter's `spawn_cmd`**

Run:
```bash
grep -n "spawn_cmd" src/eduflow/agents/*.py
```

- [ ] **Step 2: Write the failing parameterized test**

```python
# tests/unit/test_agents_spawn_safety.py
import shlex
import pytest
from eduflow.agents import adapter_for_agent
from eduflow.agents.base import CliAdapter

ADAPTERS = [
    ("codex", "eduflow.agents.codex_cli", "CodexCliAdapter"),
    ("gemini", "eduflow.agents.gemini_cli", "GeminiCliAdapter"),
    ("qwen", "eduflow.agents.qwen_code", "QwenCodeAdapter"),
    ("mimo", "eduflow.agents.mimo_code", "MimoCodeAdapter"),
]


@pytest.mark.parametrize("_,module,cls", ADAPTERS)
def test_spawn_cmd_quotes_injection(_, module, cls):
    mod = __import__(module, fromlist=[cls])
    adapter = getattr(mod, cls)({})
    cmd = adapter.spawn_cmd(agent="a; echo pwned", model="m; echo pwned")
    assert shlex.quote("a; echo pwned") in cmd
    assert shlex.quote("m; echo pwned") in cmd
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_agents_spawn_safety.py`
Expected: FAIL for any adapter that does not quote.

- [ ] **Step 4: Patch each failing adapter**

For each adapter, add `import shlex` and wrap `agent` and `model` with `shlex.quote()` in `spawn_cmd`.

- [ ] **Step 5: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_agents_spawn_safety.py`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/eduflow/agents/*.py tests/unit/test_agents_spawn_safety.py
git commit -m "security: quote agent/model names in all remaining adapters"
```
