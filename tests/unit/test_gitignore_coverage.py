import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _gitignore_lines():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]


def test_env_files_ignored():
    lines = _gitignore_lines()
    assert ".env" in lines
    assert ".env.*" in lines


def test_backup_stash_ignored():
    lines = _gitignore_lines()
    assert any(re.fullmatch(r"\.bak-stash\*/", ln) for ln in lines)


def test_bak_files_ignored():
    lines = _gitignore_lines()
    assert any(re.fullmatch(r"\*\.bak", ln) for ln in lines)
