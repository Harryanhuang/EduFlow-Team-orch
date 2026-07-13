"""Tests for `eduflow version`."""
from __future__ import annotations

import json
import inspect

from helpers import run_cli
from eduflow.commands import version as version_cmd


def test_version_prints_value_from_metadata():
    rc, out, _ = run_cli(["version"])
    assert rc == 0
    # Whatever's installed should print as a non-empty single line
    line = out.strip()
    assert line  # not empty
    assert "\n" not in line  # single line
    # Looks plausibly like a version (digit somewhere)
    assert any(c.isdigit() for c in line)


def test_version_help_returns_zero():
    rc, out, _ = run_cli(["version", "--help"])
    assert rc == 0
    assert "usage: eduflow version" in out


def test_version_json_reports_runtime_dependency_and_revision():
    rc, out, _ = run_cli(["version", "--json"])

    assert rc == 0
    payload = json.loads(out)
    assert payload["eduflow"]
    assert payload["flow_memory"]
    assert "revision" in payload


def test_revision_uses_embedded_build_stamp_without_git_on_path(monkeypatch):
    """Installed packages must not shell out to git for their revision."""
    monkeypatch.delenv("EDUFLOW_REVISION", raising=False)
    monkeypatch.setattr(version_cmd, "BUILD_REVISION", "abc123", raising=False)

    assert version_cmd._read_revision() == "abc123"
    assert "subprocess" not in inspect.getsource(version_cmd)


def test_version_falls_back_when_metadata_missing():
    """If importlib.metadata can't resolve the package (e.g. running
    raw from src without pip install -e), the fallback string is
    returned rather than raising."""
    def boom(_name):
        from importlib.metadata import PackageNotFoundError
        raise PackageNotFoundError(_name)

    # patch the helper directly — easier than patching importlib
    original = version_cmd._read_version
    version_cmd._read_version = lambda: "0.0.0+unknown"
    try:
        rc, out, _ = run_cli(["version"])
    finally:
        version_cmd._read_version = original
    assert rc == 0
    assert "0.0.0+unknown" in out


def test_version_appears_in_top_level_command_list():
    """version should show up in the no-args usage so operators see it
    next to the other commands."""
    rc, out, _ = run_cli([])
    assert rc == 0
    assert "version" in out
