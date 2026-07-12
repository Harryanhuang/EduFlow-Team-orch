import stat


def test_state_dir_is_created_with_700(tmp_path, monkeypatch):
    monkeypatch.setenv("EDUFLOW_STATE_DIR", str(tmp_path / "state"))
    from eduflow.runtime import paths

    p = paths.state_dir()
    assert p.exists()
    mode = stat.S_IMODE(p.stat().st_mode)
    assert mode == 0o700


def test_facts_dir_is_created_with_700(tmp_path, monkeypatch):
    monkeypatch.setenv("EDUFLOW_STATE_DIR", str(tmp_path / "state"))
    from eduflow.runtime import paths

    p = paths.facts_dir()
    assert p.exists()
    mode = stat.S_IMODE(p.stat().st_mode)
    assert mode == 0o700
