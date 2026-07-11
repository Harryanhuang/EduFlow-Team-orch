#!/usr/bin/env python3
"""Project test gate.

Runs the suite through pytest so the gate supports the fixtures and
parametrization used by the tests, while retaining the historic
``python3 tests/run.py [filter]`` entrypoint and final summary format.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"


def _targets(filt: str) -> list[str]:
    """Translate the legacy substring filter into pytest targets."""
    if not filt:
        return [str(TESTS)]

    path_part = filt.split("::", 1)[0]
    candidate = ROOT / path_part
    if candidate.exists():
        return [str(ROOT / filt)]

    matches = [
        str(path)
        for sub in ("unit", "integration")
        for path in sorted((TESTS / sub).glob("test_*.py"))
        if filt in path.stem
    ]
    if not matches:
        raise ValueError(f"no test modules match filter {filt!r}")
    return matches


def _summary(output: str) -> tuple[int, int]:
    """Return pytest's passed count and failures/errors as gate failures."""
    passed = sum(int(value) for value in re.findall(r"(\d+) passed", output))
    failed = sum(
        int(value)
        for value in re.findall(r"(\d+) (?:failed|error|errors)", output)
    )
    return passed, failed


def main() -> int:
    filt = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        targets = _targets(filt)
    except ValueError as exc:
        print(exc)
        print("tests: 0 passed, 1 failed")
        return 1

    result = subprocess.run(
        [sys.executable, "-m", "pytest", *targets],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    passed, failed = _summary(result.stdout + result.stderr)
    if result.returncode and not failed:
        failed = 1
    print(f"tests: {passed} passed, {failed} failed")
    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
