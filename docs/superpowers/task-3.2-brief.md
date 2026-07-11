### Task 3.2: Enforce validation at adapter spawn boundaries

**Files:**
- Modify: `src/eduflow/runtime/lifecycle.py` (around pane spawn command assembly)
- Test: `tests/unit/test_runtime_lifecycle_spawn_validation.py` (new)

**Interfaces:**
- Consumes: `eduflow.runtime.names.validate_agent_name`, `validate_model_name`
- Produces: `lifecycle.py` raises `InvalidNameError` before building any spawn command.

- [ ] **Step 1: Locate the spawn command assembly**

Read `src/eduflow/runtime/lifecycle.py` and find where `adapter.spawn_cmd(agent, model)` is called.

- [ ] **Step 2: Write the failing test**

```python
# tests/unit/test_runtime_lifecycle_spawn_validation.py
import pytest
from eduflow.runtime.names import InvalidNameError


def test_spawn_rejects_bad_agent_name(monkeypatch):
    from eduflow import runtime
    # Patch to avoid full tmux spawn; just verify validation runs.
    calls = []

    def fake_spawn(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(runtime.lifecycle.tmux, "spawn_agent", fake_spawn)

    with pytest.raises(InvalidNameError):
        runtime.lifecycle.provision_pane("bad;agent", "claude-sonnet-5")

    assert not calls
```

- [ ] **Step 3: Patch `lifecycle.py`**

At the top of `lifecycle.py`, add:
```python
from eduflow.runtime.names import validate_agent_name, validate_model_name
```

Inside the function that builds the spawn command (e.g., `provision_pane` or equivalent), before calling `adapter.spawn_cmd`, add:
```python
agent = validate_agent_name(agent)
model = validate_model_name(model)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_runtime_lifecycle_spawn_validation.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/runtime/lifecycle.py tests/unit/test_runtime_lifecycle_spawn_validation.py
git commit -m "security: validate agent/model names before pane spawn"
```
