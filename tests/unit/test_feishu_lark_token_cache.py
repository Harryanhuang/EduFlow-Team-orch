import os
import stat
from pathlib import Path


def test_tenant_token_cache_uses_state_dir_and_600(tmp_path, monkeypatch):
    monkeypatch.setenv("EDUFLOW_STATE_DIR", str(tmp_path / "state"))
    from eduflow.feishu import lark
    from eduflow.runtime import paths

    cache_path = lark._tenant_token_cache_path()
    assert cache_path.parent == paths.state_dir()

    # Simulate a write
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text('{"token": "x"}', encoding="utf-8")
    os.chmod(cache_path, 0o600)

    mode = stat.S_IMODE(cache_path.stat().st_mode)
    assert mode == 0o600
