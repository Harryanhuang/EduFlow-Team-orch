---
name: content-review-orchestration
description: "Content review entrypoint for review_course. Routes article/course copy through fact, structure, voice, platform-fit, and verdict gates using installed writing/content skills."
metadata:
  type: workflow
  generated_by: Codex
  date: 2026-07-01
---

# Content Review Orchestration

## When to Use

Use this before issuing a verdict on article-like content, including:

- WeChat articles, school/course introductions, marketing copy
- Xiaohongshu notes, social posts, short-form promotional copy
- Long-form education explainers, research-backed articles, analysis drafts
- Teacher/student profile copy where natural style and trust matter

If the artifact is a question bank, schema file, or code change, keep using the domain review skill first. Use this skill only for the prose/content layer inside that artifact.

## Routing Stack

Review in this order. Do not skip a gate unless it is clearly not applicable, and say why in the evidence packet.

| Gate | Purpose | Preferred Skill / Reference | Blocks Verdict When |
|------|---------|-----------------------------|---------------------|
| 1. Scope intake | Identify audience, platform, source files, intended publish channel | `submit-to-review` handoff | scope or target channel is missing |
| 2. Source and claim audit | Check factual claims, statistics, citations, school/program facts, time-sensitive statements | `content-research-writer`, `academic-deep-research` | unsupported or likely false claims remain |
| 3. Structure and logic | Check thesis, section flow, redundancy, reader path, CTA fit | `writing-skills`, `chinese-writing` | article is incoherent or materially incomplete |
| 4. Voice and AI residue | Remove AI cliches, empty transitions, over-polished generic claims, self-negation | `shuorenhua`, `tone-scan-pre-review` | visible AI residue or thinking-out-loud text remains |
| 5. Platform fit | Check channel-specific title, hook, length, compliance, keywords, formatting | `wechat-converter`, `wechat-article-writer`, `xiaohongshu-note-analyzer`, `social-media` | platform mismatch would damage publication quality |
| 6. Final publishability | Decide pass / repair / reject with exact file evidence | `review-verdict` | evidence packet is not specific enough |

## Verdict Policy

Use the canonical vocabulary from `review-verdict.md`:

| Verdict | Use When |
|---------|----------|
| `pass` / `approved` | Facts are supported, prose is publishable, platform fit is acceptable, and no blocking issues remain |
| `minor_required` | Draft is directionally usable but has bounded fixes such as missing sources, weak hook, repeated claims, or small style issues |
| `reject` | Core facts, positioning, structure, or platform strategy are wrong enough that patching would be misleading |
| `conditional_pass` | Publishable only after explicit mechanical conditions are applied, such as replacing a title or removing specific claims |

## Evidence Packet

Every content verdict must include:

```
content-review verdict for <artifact/channel>:
Verdict: <pass / minor_required / reject / conditional_pass>
Scope reviewed: <file paths, draft sections, platform/channel>
Gates run:
- Source/claim audit: <pass / issues / skipped with reason>
- Structure/logic: <pass / issues>
- Voice/AI residue: <pass / issues>
- Platform fit: <pass / issues / skipped with reason>
Evidence:
- <file:line or section evidence>
- <source/citation check if applicable>
Blocking issues: <none / issue list with owner-action>
Repair instructions: <exact edits required, or none>
Manager action needed: <publish / send minor repair / reject / request source clarification>
```

## Minimum Checks by Content Type

### WeChat / Long-Form Article

- Title promises match body delivery.
- Opening hook states a concrete reader problem or tension.
- Each important claim has either a source, example, or explicit framing as opinion.
- No generic paragraphs that can fit any school, course, or topic.
- CTA does not introduce claims unsupported by the article.

### Xiaohongshu / Short-Form Social

- Title is specific, searchable, and not exaggerated beyond the content.
- First three lines carry the practical value.
- Keywords/tags match the topic and audience.
- Sensitive or overpromising language is flagged.
- Formatting is scannable on mobile.

### Education / Course Copy

- Audience, level, exam board, outcome, and constraints are clear.
- Course claims do not promise guaranteed results.
- Teacher/school facts are not invented.
- Tone is natural and consultative, not salesy filler.
- Any comparison or ranking claim has evidence or is removed.

## Hard Fail Patterns

Return `minor_required` or `reject` instead of pass when any of these remain:

- Unsupported data, rankings, prices, dates, or institution facts
- Hallucinated citations or vague "research shows" claims
- AI boilerplate such as "in today's fast-paced world", "unlock your potential", or empty summary paragraphs
- Contradictory advice across sections
- Platform-inappropriate tone, length, or compliance risk
- Missing source material for claims that cannot be verified from the draft

## Handoff Examples

Worker to review_course:

```bash
eduflow send review_course worker_course "请按 content-review-orchestration 复核公众号文章。
范围:
- content/school/学校介绍结构方案-方案A.md
目标渠道: WeChat
需要 verdict:
- pass / minor_required / reject / conditional_pass
请覆盖事实核查、结构逻辑、AI 味、平台适配，并给 file-level evidence packet。"
```

Review result:

```bash
eduflow send manager review_course "content-review verdict for WeChat article:
Verdict: minor_required
Scope reviewed: content/school/学校介绍结构方案-方案A.md
Gates run:
- Source/claim audit: issues
- Structure/logic: pass
- Voice/AI residue: issues
- Platform fit: pass
Evidence:
- Section '学校优势' contains unsupported ranking language.
- Closing CTA introduces outcome claims not evidenced in body.
Blocking issues: CR-1 remove/verify ranking claim; CR-2 rewrite CTA outcome promise.
Repair instructions: worker_course fix CR-1/CR-2, then resubmit same file only.
Manager action needed: send minor repair"
```

## Related Skills

- `submit-to-review` — worker handoff format
- `review-verdict` — formal verdict protocol
- `review-criteria` — shared review vocabulary
- `tone-scan-pre-review` — hard tone pollution scan
- `teacher-profile-natural-style` — natural teacher/profile copy standards
