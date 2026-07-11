### Task 3.1: Add a shared validation utility

**Files:**
- Create: `src/eduflow/runtime/names.py`
- Test: `tests/unit/test_runtime_names.py`

**Interfaces:**
- Consumes: `re`
- Produces:
  - `VALID_AGENT_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")`
  - `VALID_MODEL_NAME_RE = re.compile(r"^[A-Za-z0-9_\-.:/]+$")`
  - `validate_agent_name(name: str) -> str`
  - `validate_model_name(name: str) -> str`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_runtime_names.py
import pytest
from eduflow.runtime.names import validate_agent_name, validate_model_name


def test_validate_agent_name_accepts_valid():
    assert validate_agent_name("worker_cc") == "worker_cc"
    assert validate_agent_name("manager-1") == "manager-1"


@pytest.mark.parametrize("bad", ["../etc", "a;b", "", "a b", "a\t"])
def test_validate_agent_name_rejects_invalid(bad):
    with pytest.raises(ValueError):
        validate_agent_name(bad)


def test_validate_model_name_accepts_valid():
    assert validate_model_name("claude-sonnet-5") == "claude-sonnet-5"


@pytest.mark.parametrize("bad", ["../etc", "a;b", "", "a b"])
def test_validate_model_name_rejects_invalid(bad):
    with pytest.raises(ValueError):
        validate_model_name(bad)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_runtime_names.py`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement `src/eduflow/runtime/names.py`**

```python
"""Shared validation for agent and model names."""
from __future__ import annotations

import re

VALID_AGENT_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")
VALID_MODEL_NAME_RE = re.compile(r"^[A-Za-z0-9_\-.:/]+$")


class InvalidNameError(ValueError):
    pass


def validate_agent_name(name: str) -> str:
    if not isinstance(name, str) or not VALID_AGENT_NAME_RE.match(name):
        raise InvalidNameError(f"invalid agent name: {name!r}")
    return name


def validate_model_name(name: str) -> str:
    if not isinstance(name, str) or not VALID_MODEL_NAME_RE.match(name):
        raise InvalidNameError(f"invalid model name: {name!r}")
    return name
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_runtime_names.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/runtime/names.py tests/unit/test_runtime_names.py
git commit -m "feat: add shared agent/model name validator"
```
