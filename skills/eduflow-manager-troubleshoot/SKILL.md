---
name: eduflow-manager-troubleshoot
description: Diagnose EduFlow manager failures when user messages may be lost, only acknowledged internally, not dispatched, or not visibly replied to in the main Feishu/Lark chat. Use when the user says manager is broken, asks whether a recent message was normal, reports no reply, or asks to verify manager/router/inbox/say behavior.
---

# EduFlow Manager Troubleshoot

Use this skill from the EduFlow project root. The job is to prove the full visible loop for recent user messages, not merely prove that the router or inbox is alive.

## First Rule

Do not ask the user for a `message_id`. Locate it yourself from the latest `from=user` messages by time window and content snippet.

Treat "normal" as two separate verdicts:

- **Delivery verdict**: did the message enter manager inbox and get read or acknowledged?
- **Visible reply verdict**: did manager send a user-visible `say --to user` that answers that message?

`read=True`, `manager ack`, or worker dispatch is not a user-visible reply.

## Fast Check

Run these first:

```bash
./scripts/eduflowteam health --json
./scripts/eduflowteam inbox manager
tail -80 .eduflow-team-state/router.log
tail -80 .eduflow-team-state/facts/logs.jsonl
```

Then extract the latest user messages:

```bash
python3 - <<'PY'
import json, datetime
data=json.load(open('.eduflow-team-state/facts/inbox.json'))
msgs=[m for m in data.get('messages',[]) if m.get('to')=='manager' and m.get('from')=='user']
for m in msgs[-10:]:
    ts=datetime.datetime.fromtimestamp(m['created_at']/1000).strftime('%Y-%m-%d %H:%M:%S')
    print(ts, m.get('local_id'), 'read='+str(m.get('read')), 'delivery='+str(m.get('delivery_state') or m.get('delivery')))
    print((m.get('content') or '').replace('\n',' ')[:260])
    print('---')
PY
```

If the user says "刚发了一条", default to the last 5-10 minutes. If several messages match, list them briefly and inspect each one.

## Single Message Trace

For each candidate `local_id`, prove this chain:

1. **Inbox**: message exists, sender is `user`, recipient is `manager`, delivery state is present.
2. **Manager ack/read**: logs contain `manager` `ack` with `ref=inbox:<local_id>` or inbox has `read=True`.
3. **Dispatch if needed**: if the message asks for work, logs/inbox show the correct worker received and acknowledged the task.
4. **Visible reply**: logs contain a later `manager` `say` that answers the user-visible request. Do not accept unrelated `say` lines from nearby tasks.
5. **Runtime/router health**: router pid exists, router log is not stuck only on keychain/subscriber failures, and manager runtime verify is ready when needed.

Treat `pid file present but process dead` as a real runtime failure even if
`manager` itself is pane-ready. In that case new group messages may stop
entering the manager loop until daemons are restarted.

Also capture the live manager pane when a latest user message is unread or
unanswered:

```bash
tmux capture-pane -t EduFlowTeam:manager -p -S -120
```

`health --json` and runtime readiness can still say `proved_ready` while the
pane just hit a provider/API error. If the pane shows `API Error`, `429`,
`Token Plan`, `rate_limit`, or quota wording, classify the missing link as
`manager_runtime_provider_blocked` for that turn. Do not call GPT/OpenAI
globally down unless a separate low-risk proof shows global GPT is failing;
this can be a single manager runtime/pool/session error that later recovers.

Useful focused trace:

```bash
python3 - <<'PY'
import json, datetime
target='msg_xxx'
for line in open('.eduflow-team-state/facts/logs.jsonl'):
    try: l=json.loads(line)
    except Exception: continue
    text=(l.get('content') or '').replace('\n',' ')
    ref=l.get('ref') or ''
    if target in ref or target in text:
        ts=datetime.datetime.fromtimestamp(l.get('created_at',0)/1000).strftime('%Y-%m-%d %H:%M:%S')
        print(ts, l.get('agent'), l.get('type'), 'ref='+ref)
        print(text[:1000])
        print('---')
PY
```

Replace `msg_xxx` with the candidate `local_id`.

## Verdict Language

Use precise verdicts:

- `投递正常，回复正常`: inbox/read/ack and matching user-visible `manager say` are both present.
- `投递正常，回复异常`: message arrived and may have been acked/dispatched, but no matching user-visible `manager say`.
- `投递异常`: no recent `from=user -> manager` inbox row, router/catchup failed, or cursor/log suggests loss.
- `派工正常，主群确认缺失`: worker accepted, but manager skipped the visible confirmation.

Always state the specific missing link.

## Repair Ladder

Use the lowest safe repair:

1. If only visible confirmation is missing, send a short manager `say --to user` acknowledging the exact task and noting it is a补充确认.
2. If dispatch is missing but the user asked for worker action, send the manager dispatch to the correct worker, then send the user-visible confirmation.
3. If the message is not in inbox, inspect router pid/log/cursor before asking the user to resend.
4. If `health --json` reports router/task-publish pid files present but processes dead, use `./scripts/eduflowteam daemon restart --all`, then re-check `health --json`, inbox, and router cursor.
5. If router pid is stale or absent, use `./scripts/eduflowteam daemon restart --all`, then re-check inbox and router log.
6. If router logs still show repeated `keychain Get failed`, first run `lark-cli --profile eduflow-team doctor` and `lark-cli --profile eduflow-team whoami`. If those are ready, prefer daemon restart over re-auth. If they still fail, report it as unresolved infra root cause and route repair to `worker_builder`; do not call the message "normal" unless visible reply is proven.
7. If the latest user instruction is safe and unambiguous but manager is blocked by a provider/API error, do the smallest manager substitute action: send the needed worker instruction, send a visible `manager say --to user`, and mark only that current user inbox row read.
8. For flow-task cancellation, do not use legacy `task update --status cancelled`; use `./scripts/eduflowteam task flow-transition <task_id> --to cancelled --actor manager`.
9. If the provider/API error persists after a retry window, switch manager to the next known-ready runtime in its chain and re-check with a live pane capture, not only `health --json`.
10. After a manager `say` answers the current user message, mark the corresponding current inbox rows read. Do not clear unrelated old backlog unless it is obviously polluting the active line.

## Output Template

```markdown
- latest_user_message:
- delivery_verdict:
- visible_reply_verdict:
- dispatch_verdict:
- evidence:
- missing_link:
- repair_done:
- remaining_risk:
```

## Common Trap

Do not scan global logs and infer success from any nearby `manager say`. Match the visible reply to the target user message by time, content, and task intent. If unsure, say "delivery is proven; visible reply is not proven."
