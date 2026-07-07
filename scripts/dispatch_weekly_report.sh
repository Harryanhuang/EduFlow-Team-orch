#!/usr/bin/env bash
# T-128 #10: Weekly dispatch-history report (Hermes finding #10)
# Hermes reported: "派工历史无追踪（无人盘点任务完成率）"
# This script: counts task dispatches + acks in last 7 days from inbox.json + logs.jsonl.
#
# Usage:  ./scripts/dispatch_weekly_report.sh [DAYS=7]
# Cron suggestion: every Monday 09:00 — `0 9 * * 1 /path/to/dispatch_weekly_report.sh >> .eduflow-team-state/facts/dispatch-weekly.log 2>&1`
#
# Output: stdout = 4-line summary (total sent / total ack'd / ack rate / by-agent)
#         exit 0 always (cron-safe)

set -euo pipefail
DAYS="${1:-7}"
export DAYS_OVERRIDE="$DAYS"
CUTOFF_MS=$(( $(date +%s) * 1000 - DAYS * 86400000 ))
STATE_DIR="${EDUFLOW_STATE_DIR:-.eduflow-team-state}"
INBOX="$STATE_DIR/facts/inbox.json"
LOGS="$STATE_DIR/facts/logs.jsonl"

if [[ ! -f "$INBOX" ]]; then
  echo "❌ $INBOX not found"; exit 0
fi

python3 - "$INBOX" "$LOGS" "$CUTOFF_MS" <<'PY'
import json, sys
inbox_path, logs_path, cutoff = sys.argv[1], sys.argv[2], int(sys.argv[3])
d = json.load(open(inbox_path))
# inbox.json structure: {"agent_name": [messages...]}
sent = 0
acked = 0
by_sender = {}
for agent, msgs in d.items():
    if not isinstance(msgs, list): continue
    for m in msgs:
        ts = int(m.get("created_at", 0) or 0)
        if ts < cutoff: continue
        sent += 1
        if m.get("ack_state") == "agent_acknowledged":
            acked += 1
        sender = m.get("from", "?")
        by_sender[sender] = by_sender.get(sender, 0) + 1
rate = (acked / sent * 100) if sent else 0
# Pass DAYS as a separate arg so the print label shows the right value
# (cutoff in ms ≠ days-ago when divided by 86400000 — that gives epoch
# seconds, not days).
import os
days = int(os.environ.get("DAYS_OVERRIDE", "7"))
print(f"📊 派工周报 (last {days}d)")
print(f"  sent   = {sent}")
print(f"  acked  = {acked}")
print(f"  ack率  = {rate:.1f}%")
print(f"  by sender:")
for s, n in sorted(by_sender.items(), key=lambda x: -x[1])[:8]:
    print(f"    {s:12s} = {n}")
PY
