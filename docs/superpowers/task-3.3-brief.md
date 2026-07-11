### Task 3.3: Enforce validation in path resolution

**Files:**
- Modify: `src/eduflow/agents/identity.py`, `src/eduflow/store/memory.py`, `src/eduflow/runtime/lifecycle.py`
- Test: `tests/unit/test_paths_agent_validation.py` (new)

**Interfaces:**
- Consumes: `eduflow.runtime.names.validate_agent_name`
- Produces: Any function building `... / agent / ...` paths validates the agent name first.

- [ ] **Step 1: Find path-construction call sites**

Run:
```bash
grep -rn 'paths.state_dir() / "agents"' src/eduflow
grep -rn 'facts_dir() / agent' src/eduflow
```

- [ ] **Step 2: Write the failing test**

```python
# tests/unit/test_paths_agent_validation.py
import pytest
from eduflow.runtime.names import InvalidNameError
from eduflow.runtime import paths


def test_agents_path_rejects_traversal():
    with pytest.raises(InvalidNameError):
        # simulate what identity.py would do
        agent = "../etc"
        from eduflow.runtime.names import validate_agent_name
        validate_agent_name(agent)
        _ = paths.state_dir() / "agents" / agent / "identity.md"
```

- [ ] **Step 3: Add validation at each call site**

For each function that builds a path from an agent name, add at the entry:
```python
from eduflow.runtime.names import validate_agent_name
agent = validate_agent_name(agent)
```

Specific sites:
- `src/eduflow/agents/identity.py` before resolving `identity.md`
- `src/eduflow/store/memory.py` before resolving `facts/<agent>`
- `src/eduflow/runtime/lifecycle.py` before `agent_home(agent)`

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_paths_agent_validation.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/agents/identity.py src/eduflow/store/memory.py src/eduflow/runtime/lifecycle.py tests/unit/test_paths_agent_validation.py
git commit -m "security: validate agent names before building filesystem paths"
```
