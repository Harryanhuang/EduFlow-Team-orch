---
id: claude-task-prompt
name: claude 任务提示词
description: Generate Claude Code execution prompts from Codex tasks, repair packages, implementation plans, or review follow-ups, with required Claude agent-team/workflow usage and a final Codex review-and-repair handoff.
source: manual
triggers:
  - claude 任务提示词
  - claude-task-prompt
  - ccg
  - claude code prompt
  - 生成 claude 提示词
  - claude code 提示词
  - 给 claude 的提示词
  - 贴到 claude
  - 打开 claude
  - 发送给 claude
  - codex 回检
  - agent team
tags:
  - prompt
  - claude-code
  - codex-handoff
  - workflow
  - computer-use
---

# Claude 任务提示词

Use this skill to turn a Codex-side task into a paste-ready Claude Code prompt. The prompt must make Claude Code use its own strengths: agent team/subagents, workflow/planning, testing, verification, and an explicit handoff back to Codex for independent review and repair.

Default output: one copy-ready Chinese prompt for Claude Code. If the user asks to open Claude, paste into Claude, or send to Claude, generate the prompt first, then use Computer Use to operate the local Claude UI. Do not implement the task yourself unless the user explicitly asks.

## Core Workflow

1. Identify the task scope from the user's request and referenced files.
2. Extract only what Claude needs: repo path, goal, completed prerequisites, target files, boundaries, acceptance checks, and known risks.
3. Generate a bounded Claude Code prompt.
4. Require Claude Code to split work across agents such as `explore`, `test-engineer`, `executor`, and `verifier` when useful.
5. Require Claude Code to finish with a `Codex 回检交接` section so the user can paste the result back to Codex for diff review, failure repair, and final verification.
6. If the user requested Claude delivery, use the Computer Use delivery rules below after the prompt is generated.

## Prompt Template

Use this structure unless the user's task needs a narrower version:

```md
你现在负责【<task name>】。

请先阅读并遵守仓库根目录和子项目里的 AGENTS.md / CLAUDE.md。工作目录是：

<absolute repo path>

背景：
<brief context: completed packages, current dependency status, why this task is next>

请优先使用你自己的 Claude Code agent team / subagents / workflow 能力并行开展，但你作为主 agent 要负责整合、验收和最终报告。

建议拆成这些并行子任务：

1. explore agent：
   - <repo mapping, current behavior discovery, file/symbol search>
   - 重点读：
     - `<file>`

2. test-engineer agent：
   - <tests to add or update first>
   - 覆盖：
     - <behavior>
   - 不要只写 happy path。

3. executor agent：
   - <minimal implementation instructions>
   - 复用现有模式，不要新造大框架。

4. verifier agent：
   - <verification commands and failure feedback loop>
   - 如果失败，回传具体失败点给 executor 修。

本任务目标：

- <goal>

建议实现：

1. <step>
2. <step>

主改文件范围：

- `<file>`

边界：

- <do not do>

执行方式：

1. 先读代码和测试，给出一个极短实现计划。
2. 然后直接实现，不要停下来问我是否继续。
3. 优先测试先行：先写能表达目标行为的单测，再实现。
4. 小步修改，降低和并行任务/近期变更的冲突。
5. 完成后必须跑验收命令。

验收命令：

    <command>

如果某些命令因为本地数据、环境或依赖问题跑不了，要说明：
- 跑了什么
- 失败原因
- 是否是代码问题
- 还剩什么风险

Codex 回检交接：

完成后请额外输出一个独立小节，标题必须是 `Codex 回检交接`，包含：
- 建议 Codex 重点复查的文件和函数
- 你最不确定的 1-3 个点
- 可能需要 Codex 继续维修的失败测试、边界或冲突
- 你跑过的命令和关键结果
- 如果有未跑命令，说明原因

最终报告请用中文，包含：

- 改了哪些文件
- 新增/修复了哪些规则或行为
- 跑过哪些测试和命令
- 仍然存在的风险

注意：
<core warning: this task's main point and scope boundary>
```

## Context Rules

- Prefer absolute repo paths.
- Mention completed prerequisite packages when they affect sequencing.
- Keep the task bounded to one Claude Code session.
- Do not let Claude expand into adjacent packages unless the user asks.
- Use conservative language for risky state changes: recommend actions and gates; do not silently apply closeouts, imports, dedup, production mutations, or destructive repairs.
- Require tests before or alongside implementation.
- Require Claude to follow existing repo patterns and nearest AGENTS.md / CLAUDE.md.
- Require honest reporting for skipped or failed commands.

## Computer Use Delivery

Use this section when the user asks for the prompt to be opened, pasted, or sent in Claude.

Default behavior:

1. Generate the final Claude Code prompt exactly as usual.
2. Use Computer Use to find or open the local Claude app/window.
3. Paste the generated prompt into the active Claude input box.
4. Stop before submitting unless the user explicitly asked to send, run, execute, or press Enter.

Submission behavior:

- If the user explicitly asked to "发送给 Claude", "让 Claude 跑", "直接执行", "paste and send", or equivalent, paste the prompt and submit it.
- If the request only says "贴过去", "放到 Claude 窗口", or "打开 Claude", paste only and leave the final send action to the user.
- If the generated prompt includes sensitive data such as secrets, credentials, private personal data, unreleased business data, or file contents that were not clearly intended for Claude, stop before typing it and ask for confirmation.
- Never click through login, permission, payment, destructive, or account/security prompts unless the user has clearly authorized that exact action.

Computer Use procedure:

1. Call Computer Use for the Claude app/window state.
2. If Claude is not available as a native app, use the visible browser window only if it is already on Claude or the user asked for browser-based Claude.
3. Click or focus the message input area.
4. Paste/type the prompt.
5. If submit is authorized, press the normal send shortcut or click the send button.
6. Report whether the prompt was pasted only or pasted and submitted.

## Claude Code Capability Requirements

Every generated prompt should explicitly ask Claude Code to:

- Use agent team/subagents for independent discovery, testing, execution, and verification.
- Use workflow/planning features when useful.
- Keep the main agent responsible for integration and final report.
- Run verification after implementation.
- Feed verifier findings back to executor until passing or clearly blocked.

Do not mention Codex-only tools as if Claude has them. Say "Claude Code agent team / subagents / workflow".

## Codex Review Handoff

Every prompt must include `Codex 回检交接`. The handoff exists so Codex can:

1. Review Claude's diff and test changes independently.
2. Check whether Claude expanded scope or missed boundaries.
3. Repair remaining failures or edge cases.
4. Run final verification.

For high-risk tasks, add this stronger handoff instruction:

```md
在最终报告前，请先自查是否有：
- 未覆盖的边界
- 未跑的验收命令
- 和并行任务冲突的文件
- 可能需要 Codex 二次维修的地方
不要隐藏这些问题；把它们放进 `Codex 回检交接`。
```

## Output Style

Return one clean paste-ready Markdown prompt in Chinese unless Computer Use delivery was requested. A short lead-in is fine:

```text
下面这段可以直接贴给 Claude Code：
```

If Computer Use delivery was requested, still keep the generated prompt clean in context, then perform the UI delivery. In the final response, do not repeat the whole prompt unless useful; just say whether it was pasted or submitted.

Do not add a long explanation around the prompt.
