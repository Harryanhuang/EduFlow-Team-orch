"""Spawn-cmd injection safety audit for all CLI adapters.

The stdlib test runner (tests/run.py) does not expand pytest parametrization,
so we loop over adapters inside a single test function.

We use shlex.split() to verify that shell-metacharacter payloads in agent or
model names are kept inside quoted tokens and cannot break out into a new
command.  Adapters that legitimately drop or transform a value (e.g. prefix it
with "eduflow-") are still covered: if the transformed value were interpolated
without quoting, shlex.split would expose "echo" / "pwned" as separate tokens.
"""
from __future__ import annotations

import shlex

ADAPTERS = [
    ("codex", "eduflow.agents.codex_cli", "CodexCliAdapter"),
    ("gemini", "eduflow.agents.gemini_cli", "GeminiCliAdapter"),
    ("qwen", "eduflow.agents.qwen_code", "QwenCodeAdapter"),
    ("mimo", "eduflow.agents.mimo_code", "MimoCodeAdapter"),
    ("qoder", "eduflow.agents.qoder_cli_cn", "QoderCliCnAdapter"),
    ("hermes", "eduflow.agents.hermes_agent", "HermesAgentAdapter"),
]


def test_spawn_cmd_quotes_injection():
    failures = []
    for label, module, cls in ADAPTERS:
        mod = __import__(module, fromlist=[cls])
        adapter = getattr(mod, cls)()
        cmd = adapter.spawn_cmd(agent="a; echo pwned", model="m; echo pwned")

        tokens = shlex.split(cmd)
        if "echo" in tokens or "pwned" in tokens:
            failures.append(
                f"{label}: shell injection payload escaped quoting:\n  {cmd}\n  tokens={tokens}"
            )

    if failures:
        raise AssertionError("\n\n".join(failures))
