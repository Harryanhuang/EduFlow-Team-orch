"""Deterministic loop checker runner."""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path


def _cmd_text(args: list[str]) -> str:
    return " ".join(str(part) for part in args)


def fingerprint_failure(text: str) -> str:
    normalized = str(text or "")
    normalized = re.sub(r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}\b", "<timestamp>", normalized)
    normalized = re.sub(r"0x[0-9a-fA-F]+", "0x<addr>", normalized)
    normalized = re.sub(r", line \d+", ", line <n>", normalized)
    normalized = re.sub(r"\bpid[ =:]+\d+\b", "pid=<n>", normalized, flags=re.I)
    normalized = re.sub(
        r"/Users/[^ \n:'\"]+/(?=(?:src|tests|content)/)",
        "<repo>/",
        normalized,
    )
    normalized = re.sub(
        r"/(?:Volumes|private|tmp|var)/[^ \n:'\"]+/(?=(?:src|tests|content)/)",
        "<repo>/",
        normalized,
    )
    lines = [" ".join(line.split()) for line in normalized.splitlines()]
    payload = "\n".join(line for line in lines if line)[-12000:]
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def run_checker_cycle(
    *,
    commands: list[list[str]],
    cwd: Path,
    run=subprocess.run,
    check_mode: str = "self_check",
) -> dict:
    outputs: list[str] = []
    passed_commands: list[str] = []
    failed_commands: list[str] = []
    checker_unavailable = False

    for command in commands:
        command_text = _cmd_text(command)
        try:
            proc = run(
                command,
                cwd=str(cwd),
                text=True,
                capture_output=True,
                timeout=1800,
            )
        except Exception as exc:
            checker_unavailable = True
            failed_commands.append(command_text)
            outputs.append(f"$ {command_text}\nchecker unavailable: {exc}")
            break
        chunk = (
            f"$ {command_text}\n"
            f"{getattr(proc, 'stdout', '') or ''}"
            f"{getattr(proc, 'stderr', '') or ''}"
        )
        outputs.append(chunk)
        if getattr(proc, "returncode", 1) == 0:
            passed_commands.append(command_text)
            continue
        failed_commands.append(command_text)
        break

    output = "\n".join(outputs)
    return {
        "passed": not failed_commands and not checker_unavailable,
        "checker_unavailable": checker_unavailable,
        "check_mode": check_mode,
        "passed_commands": passed_commands,
        "failed_commands": failed_commands,
        "checker_output": output,
        "failure_fingerprint": fingerprint_failure(
            "\n".join(failed_commands[-1:] + output.splitlines()[-80:])
        ) if failed_commands else "",
    }


def decide_stop(
    current: dict,
    previous: dict | None,
    *,
    cycle: int,
    max_cycles: int,
) -> dict:
    if current.get("passed"):
        return {"status": "passed", "stop_reason": "all_green"}
    if current.get("checker_unavailable"):
        return {"status": "failed", "stop_reason": "checker_unavailable"}
    if max_cycles and cycle >= max_cycles:
        return {"status": "stopped", "stop_reason": "max_cycles"}
    failed = set(current.get("failed_commands") or [])
    if previous:
        previous_failed = set(previous.get("failed_commands") or [])
        previous_passed = set(previous.get("passed_commands") or [])
        if failed & previous_passed:
            return {"status": "stopped", "stop_reason": "regression_detected"}
        if (
            current.get("failure_fingerprint")
            and current.get("failure_fingerprint") == previous.get("failure_fingerprint")
        ):
            return {"status": "stopped", "stop_reason": "same_failure_repeated"}
        if len(failed) >= len(previous_failed):
            return {"status": "stopped", "stop_reason": "no_failure_reduction"}
    return {"status": "repair_needed", "stop_reason": ""}
