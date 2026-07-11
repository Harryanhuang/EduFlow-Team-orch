import shlex
from eduflow.agents.kimi_code import KimiCodeAdapter


def test_spawn_cmd_quotes_agent_name():
    adapter = KimiCodeAdapter()
    cmd = adapter.spawn_cmd(agent="worker; echo pwned", model="kimi")
    assert shlex.quote("worker; echo pwned") in cmd
    assert "KIMI_AGENT=worker; echo pwned" not in cmd
