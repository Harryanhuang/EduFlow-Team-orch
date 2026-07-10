# Task 3.1 Report: Add shared agent/model name validator

## What was implemented

- Created `src/eduflow/runtime/names.py` with:
  - `VALID_AGENT_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")`
  - `VALID_MODEL_NAME_RE = re.compile(r"^[A-Za-z0-9_\-.]+$")`
  - `InvalidNameError(ValueError)`
  - `validate_agent_name(name: str) -> str`
  - `validate_model_name(name: str) -> str`

- Created `tests/unit/test_runtime_names.py` covering valid acceptance and invalid rejection for both validators.

## Note on deviation from brief

The brief specified `VALID_MODEL_NAME_RE = re.compile(r"^[A-Za-z0-9_\-.:/]+$")` and expected `../etc` to be rejected. That regex actually accepts `/`, so `../etc` matches and the brief's own test would fail. To satisfy the security goal (no path separators) and the specified test cases, the model regex was tightened to remove `/` and `:`. Agent regex matches the brief exactly.

Also, the brief's test used `@pytest.mark.parametrize`, but the project's stdlib test runner (`tests/run.py`) does not support `parametrize` and fails with `TypeError: missing required positional argument`. The test cases were kept identical; only the `parametrize` decoration was converted to inline `for` loops, matching the pattern used elsewhere in the codebase (e.g. `tests/unit/test_tool_risk.py`).

## RED/GREEN TDD evidence

### RED (source file missing)

```bash
$ python3 tests/run.py runtime_names
Traceback (most recent call last):
  ...
ModuleNotFoundError: No module named 'eduflow.runtime.names'
```

### GREEN (after implementation)

```bash
$ python3 tests/run.py runtime_names
OK  unit/test_runtime_names: 4 passed

tests: 4 passed, 0 failed
```

## Full suite test results

```bash
$ python3 tests/run.py
...
tests: 2275 passed, 37 failed
```

Baseline is 37 pre-existing failures; no new failures were introduced.

## Files changed

- `src/eduflow/runtime/names.py` (new)
- `tests/unit/test_runtime_names.py` (new)

## Commit

Pending user approval; auto-mode classifier blocked `git commit`. Staged files are ready:

```bash
git add src/eduflow/runtime/names.py tests/unit/test_runtime_names.py
git commit -m "feat: add shared agent/model name validator" \
           -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

## Self-review findings

- Validation logic is pure, stdlib-only, and follows the simple function shape used elsewhere.
- Error messages include the offending value via `!r` for safe diagnostics.
- `InvalidNameError` subclasses `ValueError`, so callers can catch either.
- Tests cover valid names, path traversal, shell metacharacters, whitespace, and empty strings.
- Full suite confirms no regression.

## Concerns

- The brief's model regex contained `/` and `:` which conflicted with both the test expectation (`../etc` rejected) and the stated security goal (no path separators). I tightened the regex; this should be reviewed.
- Commit could not be completed automatically due to the auto-mode classifier; user action is required.
