"""Tests for the CLI adapter registry + each adapter's spawn / markers contract."""
from __future__ import annotations

from eduflow.agents import get_adapter, known_clis
from eduflow.agents.base import CliAdapter
from eduflow.agents.claude_code import ClaudeCodeAdapter
from eduflow.agents.codex_cli import CodexCliAdapter
from eduflow.agents.hermes_agent import HermesAgentAdapter
from eduflow.agents.kimi_code import KimiCodeAdapter
from eduflow.agents.mimo_code import MimoCodeAdapter
from eduflow.agents.qoder_cli_cn import QoderCliCnAdapter


# ── registry ──────────────────────────────────────────────────────


def test_registry_lists_known_clis_plus_kimi_and_qwen_aliases():
    """Round-85 added gemini-cli; round-101 added qwen-code (+qwen-cli
    alias). kimi-cli + qwen-cli are aliases so both forms in team.json
    work."""
    names = set(known_clis())
    assert names == {
        "claude-code", "codex-cli", "gemini-cli",
        "hermes-agent", "hermes-cli",
        "kimi-code", "kimi-cli",
        "mimo-code", "mimo-cli",
        "qoderclicn", "qoder-cli-cn",
        "qwen-code", "qwen-cli",
    }


def test_get_adapter_returns_matching_concrete_type():
    assert isinstance(get_adapter("claude-code"), ClaudeCodeAdapter)
    assert isinstance(get_adapter("codex-cli"), CodexCliAdapter)
    assert isinstance(get_adapter("hermes-agent"), HermesAgentAdapter)
    assert isinstance(get_adapter("kimi-code"), KimiCodeAdapter)
    assert isinstance(get_adapter("mimo-code"), MimoCodeAdapter)
    assert isinstance(get_adapter("qoderclicn"), QoderCliCnAdapter)


def test_kimi_alias_returns_same_instance():
    assert get_adapter("kimi-code") is get_adapter("kimi-cli")


def test_qoder_cn_alias_returns_same_instance():
    assert get_adapter("qoderclicn") is get_adapter("qoder-cli-cn")


def test_mimo_alias_returns_same_instance():
    assert get_adapter("mimo-code") is get_adapter("mimo-cli")


def test_hermes_alias_returns_same_instance():
    assert get_adapter("hermes-agent") is get_adapter("hermes-cli")


def test_get_adapter_unknown_raises_keyerror_with_known_list():
    try:
        get_adapter("not-a-cli")
    except KeyError as exc:
        msg = str(exc)
        assert "unknown cli" in msg
        for name in ("claude-code", "codex-cli", "kimi-code"):
            assert name in msg
    else:
        raise AssertionError("expected KeyError for unknown cli")


# ── base + interface compliance ──────────────────────────────────


def _all_adapters() -> list[CliAdapter]:
    return [ClaudeCodeAdapter(), CodexCliAdapter(), KimiCodeAdapter(), QoderCliCnAdapter()]


def test_every_adapter_implements_required_methods():
    for adapter in _all_adapters():
        assert isinstance(adapter, CliAdapter)
        cmd = adapter.spawn_cmd("worker_x", "sonnet")
        assert isinstance(cmd, str) and cmd.strip()
        ready = adapter.ready_markers()
        assert ready and isinstance(ready, list)
        busy = adapter.busy_markers()
        assert busy and isinstance(busy, list)
        assert adapter.process_name()
        assert adapter.submit_keys()


def test_default_submit_keys_are_enter_variants():
    # base default lists Enter / C-m / C-j; ClaudeCode keeps it, Codex/Kimi prepend M-Enter
    cc = ClaudeCodeAdapter().submit_keys()
    assert cc[0] == "Enter"
    for adapter in (CodexCliAdapter(), KimiCodeAdapter()):
        keys = adapter.submit_keys()
        assert keys[0] == "M-Enter"
        assert "Enter" in keys


# ── per-adapter spawn shape ──────────────────────────────────────


def test_claude_code_spawn_is_dangerously_skip_permissions_with_model():
    cmd = ClaudeCodeAdapter().spawn_cmd("worker_cc", "sonnet-4-6")
    assert "--dangerously-skip-permissions" in cmd
    assert "--model sonnet-4-6" in cmd
    assert "--name worker_cc" in cmd
    assert "IS_SANDBOX=1" in cmd


def test_claude_code_spawn_prefers_resolved_binary_path():
    import shutil
    real_which = shutil.which
    try:
        shutil.which = lambda name: "/opt/homebrew/bin/claude" if name == "claude" else None
        cmd = ClaudeCodeAdapter().spawn_cmd("worker_cc", "sonnet-4-6")
        assert "/opt/homebrew/bin/claude --dangerously-skip-permissions" in cmd
    finally:
        shutil.which = real_which


def test_claude_code_rate_limit_markers_cover_proxy_429s():
    markers = ClaudeCodeAdapter().rate_limit_markers()
    assert "429" in markers
    assert "too many requests" in markers
    assert "RESOURCE_EXHAUSTED" in markers
    assert "quota exceeded" in markers


def test_codex_spawn_passes_openai_model_through():
    cmd = CodexCliAdapter().spawn_cmd("worker_codex", "gpt-5.5")
    assert "codex" in cmd
    assert "--dangerously-bypass-approvals-and-sandbox" in cmd
    assert "--model gpt-5.5" in cmd
    assert "HOME=" in cmd
    assert "CODEX_HOME=" in cmd
    assert "CODEX_AGENT=worker_codex" in cmd


def test_codex_spawn_drops_non_openai_model():
    cmd = CodexCliAdapter().spawn_cmd("worker_codex", "sonnet")
    assert "--model" not in cmd  # silently dropped
    assert "--dangerously-bypass-approvals-and-sandbox" in cmd


def test_codex_spawn_quotes_agent_name_with_special_chars():
    cmd = CodexCliAdapter().spawn_cmd("worker x", "")
    assert "'worker x'" in cmd  # shlex.quote


def test_kimi_spawn_uses_yolo_flag_and_disable_update():
    cmd = KimiCodeAdapter().spawn_cmd("worker_kimi", "")
    assert "kimi --yolo" in cmd
    assert "DISABLE_UPDATE_CHECK=1" in cmd
    assert "KIMI_AGENT=worker_kimi" in cmd


def test_mimo_spawn_uses_trust_never_ask_and_model():
    cmd = MimoCodeAdapter().spawn_cmd("worker_mimo", "openai/gpt-5.5")
    assert "mimo" in cmd
    assert "--trust" in cmd
    assert "--never-ask" in cmd
    assert "--model openai/gpt-5.5" in cmd
    assert "MIMO_AGENT=worker_mimo" in cmd


def test_hermes_spawn_uses_fixed_cli_and_model():
    cmd = HermesAgentAdapter().spawn_cmd("Hermes", "minimax-m3")
    assert "cd '/Volumes/Halobster/Obsidian Edu' &&" in cmd
    assert "hermes chat" in cmd
    assert "--cli" in cmd
    assert "--model minimax-m3" in cmd
    assert '--provider "${HERMES_PROVIDER:-minimax}"' in cmd
    assert "--source eduflow-hermes" in cmd


def test_hermes_ready_markers_cover_current_tui_prompt():
    markers = HermesAgentAdapter().ready_markers()
    assert "欢迎！输入你的问题" in markers
    assert "⚕ ❯" in markers
    assert "❯" in markers


# ── markers ──────────────────────────────────────────────────────


def test_codex_busy_markers_include_boot_phase():
    """R-busy fix carries over: Booting MCP server must be a busy marker so
    inject_when_idle waits past the boot race."""
    assert "Booting MCP server" in CodexCliAdapter().busy_markers()


def test_codex_ready_markers_cover_current_footer():
    markers = CodexCliAdapter().ready_markers()
    assert "bypass permissions on" in markers


def test_kimi_busy_markers_include_using_shell():
    assert "Using Shell" in KimiCodeAdapter().busy_markers()
    assert "Booting" in KimiCodeAdapter().busy_markers()


def test_process_names_match_expected_binaries():
    assert ClaudeCodeAdapter().process_name() == "claude"
    assert CodexCliAdapter().process_name() == "codex"
    assert HermesAgentAdapter().process_name() == "hermes"
    assert KimiCodeAdapter().process_name() == "kimi"
    assert MimoCodeAdapter().process_name() == "mimo"


# ── codex_cli.ensure_workdir_trusted ─────────────────────────────


def test_ensure_workdir_trusted_writes_entry_when_config_missing(tmp_path=None):
    import tempfile
    from pathlib import Path
    from eduflow.agents.codex_cli import ensure_workdir_trusted

    with tempfile.TemporaryDirectory() as tmp:
        cfg = Path(tmp) / "codex" / "config.toml"
        workdir = Path("/some/work/dir")
        ensure_workdir_trusted(workdir, config_path=cfg)
        text = cfg.read_text(encoding="utf-8")
        assert '[projects."/some/work/dir"]' in text
        assert 'trust_level = "trusted"' in text


def test_ensure_workdir_trusted_appends_when_other_entries_present():
    import tempfile
    from pathlib import Path
    from eduflow.agents.codex_cli import ensure_workdir_trusted

    with tempfile.TemporaryDirectory() as tmp:
        cfg = Path(tmp) / "config.toml"
        cfg.write_text('[projects."/other/dir"]\ntrust_level = "trusted"\n', encoding="utf-8")
        ensure_workdir_trusted(Path("/new/dir"), config_path=cfg)
        text = cfg.read_text(encoding="utf-8")
        assert '[projects."/other/dir"]' in text
        assert '[projects."/new/dir"]' in text


def test_ensure_workdir_trusted_idempotent_when_entry_exists():
    import tempfile
    from pathlib import Path
    from eduflow.agents.codex_cli import ensure_workdir_trusted

    with tempfile.TemporaryDirectory() as tmp:
        cfg = Path(tmp) / "config.toml"
        original = '[projects."/already/here"]\ntrust_level = "trusted"\n'
        cfg.write_text(original, encoding="utf-8")
        ensure_workdir_trusted(Path("/already/here"), config_path=cfg)
        # File unchanged
        assert cfg.read_text(encoding="utf-8") == original
