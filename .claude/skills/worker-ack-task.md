---
name: worker-ack-task
description: "Worker skill: complete the 4-step intake sequence when picking up a new task from inbox. Covers ACK, user notify, manager notify, and status update — the repetitive boilerplate every worker runs on every task."
metadata:
  type: workflow
  generated_by: worker_builder
  date: 2026-06-24
---

# Worker Task Intake Sequence

## When to Use

Every time you pick up a new task from `eduflow inbox <your-name>`.

This is the standard 4-step intake protocol that all workers (worker_course, review_course, worker_builder, worker_qbank) follow identically. Automating this eliminates ~15 lines of boilerplate per task.

## Intake Steps

### Step 1: Read inbox

```bash
eduflow inbox <your-name>
```

### Step 2: ACK the task

Mark the message as read and acknowledge:

```bash
eduflow read <local_id> --ack accepted_task
```

Use `--ack accepted_revision` if this is a rework/fix task.

### Step 3: Notify user (one-line ACK)

```bash
eduflow say <your-name> "任务已接单：<one-line summary of the task>" --to user
```

### Step 4: Update status

```bash
eduflow status <your-name> 进行中 "<task description>"
```

### Step 5 (optional): Notify manager of acceptance

```bash
eduflow send manager <your-name> "已接单：<task summary>"
```

## Once Real Work Begins

After completing intake, when you actually start executing:

```bash
eduflow read <local_id> --ack started_task
```

And optionally:

```bash
eduflow say <your-name> "任务已开始处理：<current first step>" --to user
```

## Progress Pings (during long tasks)

Every ~10 minutes or at each stage boundary:

```bash
eduflow say <your-name> "阶段进度：<done/doing/next>" --to user
```

If no new results:

```bash
eduflow say <your-name> "阶段进度：暂无新结果，仍在<current action>" --to user
```

## Blocker Report

When blocked:

```bash
eduflow say <your-name> "当前卡在：<blocker>，已回报 manager" --to user
eduflow send manager <your-name> "<blocker detail>" 高
```

## Completion

```bash
eduflow say <your-name> "已交接：<artifact/object>，等待 <review/manager>" --to user
eduflow status <your-name> 已完成 "<task>"
```

## Important Notes

- Every `eduflow say` MUST include `--to user` or `--to manager`.
- Run all commands from your working directory — never `cd` elsewhere.
- Refer to your `identity.md` to confirm your agent name.
