# handoff-template: loop-engineering-execution-layer

## Builder Repair Handoff

```text
Builder handoff
task_id: <T-id>
loop_id: <L-id>
failed_commands: <command list>
failure_summary: <short failure excerpt>
evidence_ref: loop_runs/<L-id>/meta.json
red_lines: Do not weaken tests; do not delete tests; do not skip tests; do not edit unrelated files.
please re-run: eduflow task loop-check <T-id> --background
```

## Manager Followup

```text
eduflow task loop-status <T-id>
eduflow task evidence-explain <T-id> --json
```

Loop evidence can support closeout review, but it never replaces reviewer verdict or manager closeout.
