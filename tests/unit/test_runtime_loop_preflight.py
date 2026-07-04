from eduflow.runtime import loop_preflight


def test_worktree_mode_requires_existing_path(tmp_path):
    result = loop_preflight.check_workspace(
        workspace_mode="worktree",
        workspace_path=str(tmp_path / "missing"),
        allow_unscoped=False,
        cwd=tmp_path,
        run=lambda *a, **k: None,
    )
    assert result["ok"] is False
    assert result["reason"] == "workspace_path_missing"


def test_shared_mode_allows_check_but_flags_risk(tmp_path):
    result = loop_preflight.check_workspace(
        workspace_mode="shared",
        workspace_path="",
        allow_unscoped=False,
        cwd=tmp_path,
        run=lambda *a, **k: None,
    )
    assert result["ok"] is True
    assert result["shared_workspace_risk"] is True


def test_missing_mode_refuses_without_escape_hatch(tmp_path):
    result = loop_preflight.check_workspace(
        workspace_mode="",
        workspace_path="",
        allow_unscoped=False,
        cwd=tmp_path,
        run=lambda *a, **k: None,
    )
    assert result["ok"] is False
    assert result["reason"] == "workspace_policy_missing"
