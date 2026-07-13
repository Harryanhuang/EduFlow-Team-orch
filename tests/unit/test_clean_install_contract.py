"""G1.D2 packaging contract tests."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_clean_install_surfaces_are_standard_installable():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    smoke = ROOT / "scripts" / "clean-install-smoke.sh"

    assert "pip install --no-cache-dir ." in dockerfile
    assert "pip install --no-cache-dir -e ." not in dockerfile
    assert "ARG EDUFLOW_REVISION" in dockerfile
    assert "COPY setup.py ./" in dockerfile
    assert "EDUFLOW_BUILD_REVISION" in dockerfile
    assert "sha256sum" in dockerfile
    assert "pip install ." in readme
    assert smoke.is_file()
    assert "-m venv" in smoke.read_text(encoding="utf-8")
    assert 'pip install "$ROOT"' in smoke.read_text(encoding="utf-8")
    assert "EDUFLOW_STATE_DIR" in smoke.read_text(encoding="utf-8")
    assert 'eduflow" version --json' in smoke.read_text(encoding="utf-8")


def test_clean_install_smoke_exercises_memory_router_and_health_contract():
    smoke = (ROOT / "scripts" / "clean-install-smoke.sh").read_text(encoding="utf-8")

    assert 'health --json || true' not in smoke
    assert "from eduflow.memory import init_schema" in smoke
    assert "init_schema()" in smoke
    assert "from eduflow.commands import router" in smoke
    assert "health JSON must be valid" in smoke
