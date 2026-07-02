"""`eduflow read <local_id>`

Mark a message as read by its local id.  Returns 1 if no such message.

On miss, runs `_diagnose_missing_message` to distinguish:
  - agent hallucination (bad format / no router activity)
  - router respawn loss (router.log shows restart events around that time)
  - cross-agent confusion (recent messages exist for OTHER agents)
  - clean miss (no signal at all)

The diagnostic prints hints to stderr so the operator / agent can decide
whether to retry, re-deliver, or just confirm the message never existed.
"""
from __future__ import annotations

import re

from eduflow.store import local_facts
from eduflow.util import error_exit, usage_error


USAGE = (
    "usage: eduflow read <local_id> "
    "[--ack accepted_task|started_task|accepted_revision|completed|reconciled] "
    "[--topic <topic>] [--file <path>] [--issue <text>]"
)


# local_id format: msg_<13-digit-ms>_<10-hex>. Total length is 4 + 13 + 1 + 10 = 28.
# Boss asked (2026-07-02): reject if length < 28 OR format doesn't match. We do both:
# the regex implicitly enforces length 28+, but checking length first gives a clearer
# hint when a peer id (e.g., om_xxx Feishu event id) is mistakenly used.
_MIN_LOCAL_ID_LEN = 28
_LOCAL_ID_RE = re.compile(r"^msg_\d{13}_[0-9a-f]{10}$")


def _pop_option(rest: list[str], flag: str) -> str | None:
    if flag not in rest:
        return None
    idx = rest.index(flag)
    if idx + 1 >= len(rest):
        return ""
    value = rest[idx + 1]
    del rest[idx:idx + 2]
    return value


def _diagnose_missing_message(local_id: str) -> list[str]:
    """Return one-or-more diagnostic hint lines when `local_id` isn't
    in the inbox. Each line ends with newline so the caller can join
    them into a multi-line stderr block.

    Cheap, best-effort — no I/O when the message already exists. Reads
    only the tail of router.log (≤ 50 lines) so this stays under 5ms.
    """
    hints: list[str] = []

    # Hint 1: format validation
    if not _LOCAL_ID_RE.match(local_id):
        if len(local_id) < _MIN_LOCAL_ID_LEN:
            hints.append(
                f"  hint: {local_id!r} is shorter than the minimum "
                f"{_MIN_LOCAL_ID_LEN} chars for a local_id. Did you pass a "
                "Feishu event id (om_xxx) or a peer's local_id by mistake?"
            )
        else:
            hints.append(
                f"  hint: {local_id!r} doesn't match expected format "
                "(msg_<13-digit-ms>_<10-hex>). Likely a typo or hallucinated id."
            )
        return hints

    # Hint 2: router.log tail — look for stall / respawn signals
    try:
        from eduflow.runtime.paths import state_file
        log_path = state_file("router.log")
        if log_path.exists():
            tail = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-50:]
            respawn_lines = [
                ln for ln in tail
                if "stalled, exiting for respawn" in ln
                or "another router already running" in ln
                or "lark-cli failed" in ln
            ]
            if respawn_lines:
                hints.append(
                    f"  hint: router.log shows {len(respawn_lines)} respawn/failure "
                    "event(s) in the last 50 lines. Message may have been "
                    "dropped during a respawn window."
                )
    except Exception:
        pass

    # Hint 3: cross-agent confusion — peek at recent rows for any agent
    # (we don't know the caller's own agent here; we just want *any*
    # recent activity to cross-check the operator's premise).
    try:
        from eduflow.runtime import config
        rows: list[dict] = []
        for agent_name in config.agent_names():
            rows.extend(local_facts.list_messages(agent_name, unread_only=False))
        rows.sort(key=lambda r: int(r.get("created_at", 0) or 0), reverse=True)
        recent_to_others = [
            r for r in rows[:5]
            if r.get("to") and r.get("local_id") != local_id
        ]
        if recent_to_others:
            sample = recent_to_others[0]
            hints.append(
                f"  hint: most recent inbox row across the team is "
                f"to={sample.get('to')!r} from={sample.get('from')!r} "
                f"id={sample.get('local_id')!r}. Confirm this message was "
                "actually addressed to you (not a peer's id)."
            )
    except Exception:
        pass

    if not hints:
        hints.append(
            "  hint: no router respawn signals and no recent peer messages. "
            "This id likely never existed — confirm the source."
        )
    return hints


def main(argv: list[str]) -> int:
    rest = list(argv)
    ack_kind = _pop_option(rest, "--ack")
    topic = _pop_option(rest, "--topic") or ""
    files = []
    issues = []
    while True:
        value = _pop_option(rest, "--file")
        if value is None:
            break
        files.append(value)
    while True:
        value = _pop_option(rest, "--issue")
        if value is None:
            break
        issues.append(value)
    if len(rest) < 1:
        return usage_error(USAGE)
    local_id = rest[0]
    if not local_facts.mark_read(local_id):
        for hint in _diagnose_missing_message(local_id):
            print(hint, file=__import__("sys").stderr)
        return error_exit(f"❌ no such message: {local_id}")
    if ack_kind:
        if not local_facts.record_message_ack(
            local_id,
            ack_kind,
            topic=topic,
            files=files,
            issues=issues,
        ):
            return error_exit(f"❌ could not record ack: {local_id}")
        print(f"✅ marked read: {local_id}  ack={ack_kind}")
    else:
        print(f"✅ marked read: {local_id}")
    return 0
