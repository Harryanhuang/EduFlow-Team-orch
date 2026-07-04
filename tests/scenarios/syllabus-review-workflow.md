# syllabus-review-workflow — operator playbook (Given/When/Then) (v2.4.3)

## 目的

Regression sweep for the **end-to-end IGCSE KQA sprint workflow**. Operator runs each scenario in order; if any Then clause fails, the workflow has regressed and must be re-fixed before the next subject dispatch.

Distilled from the 2026-07-03 5-subject sprint (Math 0580 / Physics 0625 / Chemistry 0620 / Biology 0610 / Business 0450) and the lessons learned.

**Single source of truth for KQA results**: Feishu doc `ArZJd17OyoUlK3xsFmRcIK0EnAe` (one section per subject, 4-section structure).

## 适用范围

- Manager dispatches a new IGCSE subject KQA (CS 0478 / Add Math 0606 / Chinese 0509 / History 0470 / Economics 0455 / + more).
- A previous KQA sprint needs re-validation after syllabus version mismatch (e.g. Business 0450 2026 v2 vs MVP 2023 reprint).
- An operator wants to manually re-run the workflow to confirm it works after a refactor.

## 前置条件

```bash
cd /Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch
source .venv/bin/activate 2>/dev/null
export EDUFLOW_STATE_DIR="$PWD/.eduflow-team-state"
export LARK_CLI_NO_PROXY=1

# 确认基础设施健康
eduflow health   # 应全绿: 9 agents, router alive, watchdog alive
```

---

## Scenario 1 — MVP pre-flight (mandatory before any dispatch) (v2.1)

**Given** manager dispatches a new IGCSE subject KQA with `{subject, code, manager_expected: {year, total_pages, topic_count}}`
**When** review_course starts step[1] pre-flight
**Then**
- §1a Read `pilot-output/source-bundles/<bundle>-guide/source-index.md` → extract pdf_version + total_pages
- §1b Read `pilot-output/source-bundles/<bundle>-guide/page-map.json` → extract topic list + page-map total_pages
- §1c Compare to `manager_expected`; if mismatch → `send manager review_course "VERSION_MISMATCH: pdf=X, expected=Y" 高` and HALT questions.md write
- §1c.1 **NEW (v2.1)** Compute `total_pages_delta` = `pdf_actual_total - page_map_total`. If |delta| > 0 → flag `page_map_incomplete` (e.g. Add Math 0606: page-map=38, PDF=31, delta=-7)
- §1c.2 **NEW (v2.1)** Compute `topic_count_delta` = `pdf_topic_count - mvp_topic_count`. If != 0 → flag `topic_count_mismatch` (e.g. Add Math 0606: PDF=14, MVP=12, delta=+2)
- §1d Detect pattern (one of: `chemistry_minus_2` / `biology_plus_2` / `reprint_1_to_4_pages` / `version_mismatch` / `topic_deletion` / `page_map_incomplete` / **NEW (v2.1) `depth_incomplete`** / **NEW (v2.1) `formula_table_1to1`**)
- §1d.1 **NEW (v2.1)** If PDF contains "List of formulas" / "Formulae list" section → flag `formula_table_1to1` (e.g. Add Math 0606 p.22); worker MUST cite formulas 1:1
- §1d.2 **NEW (v2.1)** If MVP assumes deep coverage but PDF is shallow → flag `depth_incomplete` (e.g. dot product / 5 derivative rules for Add Math 0606)
- §1e Write `questions.md` using **PDF actual page + PDF actual topic**; do NOT copy page-map numbers
- §1f Tag each Q with `(MVP p.M / PDF actual p.X, offset ±K)` for downstream traceability

**Verified by**: `head -20 .eduflow-team-state/agents/review_course/qa-batch/T-IGCSE-KQA/<subject>_<code>/questions.md` shows PDF actual page citations, not page-map placeholders.

---

## Scenario 1B — Structural refactor detector (v2.1, dispatch-time)

**Given** review_course is about to dispatch questions to worker_syllabus
**When** review_course runs the structural refactor detector before dispatch
**Then**
- §1B.1 Read PDF Assessment overview section (typically p.7-9) → extract `papers_count`, `aos_count`, `grade_scale`, `core_extended`
- §1B.2 Compare against MVP expectations in dispatch message
- §1B.3 If any structural refactor detected:
  - Papers count changed (e.g. 5 → 2): flag in dispatch message
  - AO count changed (e.g. 3 → 2 / 3 → 4): flag in dispatch message
  - Grade scale changed (e.g. A*-G → A*-E): flag in dispatch message
  - Core/Extended collapsed: flag in dispatch message
- §1B.4 Add Math 0606 case: PDF 2028-2030 v1 = 2 AOs (AO1 45-55% + AO2 45-55%) + A*-E + 2 papers no Core/Extended. MVP was 3 AOs 50/30/20 + A*-G.
- §1B.5 Mark probe Qs with `⚠️ MVP structural refactor expected` flag in dispatch
- §1B.6 Worker MUST answer PDF actual, NOT MVP structural assumption

**Verified by**: Dispatch message includes `structural_refactors: [<list>]` field; worker's answer.md Q20b-style Qs show `⚠️ MVP 错误` annotation.

---

## Scenario 2 — Q&A loop (review ↔ worker_syllabus)

**Given** `questions.md` exists with 20 Qs spanning the syllabus
**When** review_course dispatches to worker_syllabus
**Then**
- §2a `eduflow send worker_syllabus review_course "KQA sprint ready, pattern=<tag>, N=20"` (priority 高)
- §2b worker_syllabus replies within 5 min with "已开始" or "BLOCKED: <reason>"
- §2c worker_syllabus writes `answer.md` with 1:1 PDF citations; each Q cites `p.X, Topic Y, item N` or marks `PDF 未显式列 [thing], standard 知识补: [truth]`
- §2d `answer.md` top includes `⚠️ PAGE-DISCREPANCY` summary if MVP page ≠ PDF actual
- §2e review_course receives, verifies each citation by re-opening PDF; if any wrong → returns for fix; if all correct → writes `verdict.md`

**Verified by**: `cat verdict.md | grep -E "(PASS|FAIL|WARN)"` shows pass verdict for ≥90% of subjects.

---

## Scenario 3 — Version mismatch (Business 0450 type case)

**Given** MVP declares year 2023-2025 but PDF is 2026 v2
**When** worker_syllabus / review_course detect the mismatch in step[1] or step[4]
**Then**
- §3a Halt the workflow if mismatch found in step[1] pre-flight
- §3b If found in step[4] verification (worker already answered), mark each affected Q with `⚠️ MVP 错误`
- §3c Worker answers **PDF actual** for those Qs, not MVP expected answer
- §3d Review verdict records mismatch explicitly: `MVP 假设 (2023-2025) vs PDF 实际 (2026 v2)`
- §3e Feishu doc section §四 Review self-critique documents the mismatch + how it was handled
- §3f Manager is informed; if MVP needs full rewrite, dispatch new MVP questions and re-run

**Verified by**: For Business 0450 case, `verdict.md` must mention `2026 v2`, `2 papers`, `4 AOs`, `PED 不考`, `4 production → 3`.

---

## Scenario 4 — Page-map offset detection (Chemistry / Biology / Business pattern)

**Given** worker finds PDF Topic N does not match MVP Subject Topic N
**When** worker identifies the offset pattern
**Then**
- §4a Worker documents offset in `answer.md` per-Q: `(MVP Subject Topic N = PDF Topic N+2)` or similar
- §4b Review collects all offsets into a per-subject `page_discrepancy` table in `verdict.md`
- §4c Pattern tag is one of:
  - `chemistry_minus_2` — preface occupies t001/t002 (Chemistry 0620)
  - `biology_plus_2` — preface + 2 short topics occupy t001/t002 (Biology 0610)
  - `business_plus_2` — preface + 2 short topics (Business 0450)
- §4d Feishu doc §四 Review self-critique records the pattern for downstream subjects
- §4e Worker_builder / luke_recorder accumulate cross-subject patterns for page-map rewrite

**Verified by**: `cat verdict.md | grep -E "(offset|pattern|Topic N\+)"` shows offset summary per subject.

---

## Scenario 5 — PDF gap handling (worker主动标识 + 3 options)

**Given** worker_syllabus finds N places where PDF lacks full content (e.g. only lists "Identify the products formed" without naming them)
**When** worker encounters the gap during answering
**Then**
- §5a Worker does NOT fabricate. Marks: `PDF 未显式列 [thing], standard 知识补: [truth]`
- §5b Gap counted in `verdict.md` summary: `Worker 主动标注 PDF 缺口: N`
- §5c For each gap, manager picks one of:
  - **Option A** — `worker_course` writes `supplements.md` with the missing content (preferred for recurring gaps)
  - **Option B** — `worker_course` or `worker_builder` finds alternative source (prior syllabus / textbook / CAIE FAQ)
  - **Option C** — Mark as `known gap` in section §四 Review self-critique, continue
- §5d Default: if A or B is expensive (>30 min), default to C and continue the workflow
- §5e Feishu doc §四 Review self-critique lists all gaps as bullet points

**Verified by**: `cat verdict.md | grep "PDF 缺口"` returns count ≥ number of gaps in `answer.md`.

---

## Scenario 6 — Pause misjudgment (Chemistry 0620 type)

**Given** worker pauses believing a "QA 暂停" directive is in effect
**When** pause is suspected of being a misjudgment
**Then**
- §6a Worker_builder verifies pause scope: read manager workspace + boss directive; check if current subject is in suspension list
- §6b Common false-positive: worker reads global "暂停 KQA" as covering all subjects when only original 2 (e.g. Math 0580 / Physics 0625) were suspended
- §6c If uncertain: dispatch worker_builder to do `eduflow runtime switch <agent> <same_runtime> --reason "force_respawn_after_pause_misjudgment" --no-smoke`
- §6d Verify runtime = `proved_ready` and review pane shows progress
- §6e Log pause verification to audit log so next sprint knows what to check

**Verified by**: After respawn, `eduflow runtime verify review_course` shows `proved_ready` and Chemistry todo list shows actual work in progress.

---

## Scenario 7 — Feishu doc append (worker_builder)

**Given** `verdict.md` shows PASS / WARN verdict and manager dispatches worker_builder
**When** worker_builder formats and appends the Feishu section
**Then**
- §7a Re-format into 4 sections (统计总览 / 20 题逐项 / Worker 评估 / Review self-critique)
- §7b Each Q in §二 shows: 题号 / 题目 / 答案 / 验证 ✓/✗ / 源 PDF 实际页码
- §7c Use `@filepath` syntax: `lark-cli docs +update --doc ArZJd17OyoUlK3xsFmRcIK0EnAe --markdown @<section>.md --as bot --mode append`
- §7d Verify length grew: `lark-cli docs +fetch --as bot | grep length` shows expected delta (e.g. +18K for Business)
- §7e Post chat: `eduflow say worker_builder "KQA-DOC <subject> 段已追加 ✅ 20 题 / N 子题 全 ✓ PASS" --to user`
- §7f Send manager with summary + known issues

**Verified by**: Doc length grows by ~15-20K chars per subject; chat message has user-visible confirmation.

---

## Scenario 8 — 5-min cadence (hard constraint, all roles)

**Given** any role is in the middle of a KQA step
**When** 5 minutes elapse without a new progress signal
**Then**
- §8a worker_syllabus → review_course: send "5 min 无新进展, 当前在 <step>" within the 5-6 min window
- §8b review_course → manager: send "5 min 无新进展, 当前在 <step>"
- §8c manager → boss: send "5 min 无新进展, 当前在 <subject> KQA, <state>" to chat
- §8d worker_builder → manager + chat: every 5 min during Feishu append
- §8e If 2 consecutive 5-min windows missed, watchdog escalates to manager

**Verified by**: `eduflow workspace <agent>` shows cadence messages at ≤5-6 min intervals during active work.

---

## Scenario 9 — Lessons distillation (closes the loop)

**Given** subject PASS and Feishu doc section appended
**When** worker_builder closes the subject
**Then**
- §9a Append any new lessons to Feishu doc §四 Review self-critique (page-map offset, version mismatch, PDF gap patterns)
- §9b For high-value cross-subject lessons, run `eduflow remember worker_builder learning "repeat_work::igcse_kqa::<lesson>"`
- §9c If 3+ subjects share the same lesson → promote to SKILL update (edit `.claude/skills/igcse-kqa-workflow/SKILL.md`)
- §9d luke_recorder captures cross-team lessons (manager misjudgment, worker dispatch patterns)

**Verified by**: `grep -c "repeat_work::igcse_kqa" .eduflow-team-state/agent-home/worker_builder/.claude/memory/` shows ≥1 entry per sprint.

---

## Scenario 10 — MVP validator script invocation (future)

**Given** the `scripts/mvp_validator.py` is implemented (step[1] script spec)
**When** operator runs `python3 scripts/mvp_validator.py <bundle_path>`
**Then**
- §10a Script reads `source-index.md` and `page-map.json`
- §10b Script detects pattern (chemistry_minus_2 / biology_plus_2 / reprint / version_mismatch / etc)
- §10c Script prints pre-flight report: `{pdf_version, pdf_pages, topic_count, pattern, advice}`
- §10d If pattern is `version_mismatch` or `topic_deletion`, exit code 2 (operator must escalate)
- §10e If pattern is `chemistry_minus_2` / `biology_plus_2` / `reprint_1_to_4_pages`, exit code 0 with offset advice

**Verified by**: `python3 scripts/mvp_validator.py pilot-output/source-bundles/caie-igcse-biology-0610-guide/` returns `biology_plus_2` advice.

---

## 闭环验证 (end-to-end smoke)

**Given** all 10 scenarios pass individually
**When** an operator runs the full workflow for a new subject (e.g. CS 0478)
**Then**
- §E1 Pre-flight pattern detected correctly within 1 min
- §E2 20 Qs dispatched, answered, verified within 60-90 min
- §E3 Feishu doc appended, length grows by ~15-20K chars
- §E4 Chat message posted with "KQA-DOC <subject> 段已追加 ✅"
- §E5 Manager CLOSEOUT card sent to user
- §E6 Lessons added to memory; if 3+ shared, SKILL.md updated
- §E7 5-min cadence held throughout (no >10-min silence)

**Pass criterion**: §E1-E7 all true. Any failure → workflow regression; fix before next subject.

---

## 时间预算 (per subject)

| Step | Time budget |
|------|-------------|
| Pre-flight | 5 min |
| Q&A loop | 30-60 min |
| Verdict write | 10 min |
| Feishu append | 10 min |
| Lessons distillation | 5 min |
| **Total** | **60-90 min per subject** |

5 subjects in parallel-serial: ~5-7 hours wall clock with 2 reviewers + 1 worker_syllabus + 1 worker_builder.

## Reference: 2026-07-03 to 2026-07-04 sprint outcomes

| Subject | Verdict | Time | Known issues / Lessons |
|---------|---------|------|------------------------|
| Math 0580 | ✅ PASS 36/36 | 10 min | clean baseline |
| Physics 0625 | ✅ PASS 39/39 | — | Topic 5/6 not covered; worker主动识别 review Q1 笔误 5/6→6/7 |
| Chemistry 0620 | ✅ PASS 37/37 | — | 6 PDF gaps + page-map -2; pause misjudgment (verifier root cause was misjudgment, not API) |
| Biology 0610 | ✅ PASS 40/40 | 30 min | 5 PDF gaps + page-map +2; MVP 占位符全部替换, Q14a 跨 topic 引用 |
| Business 0450 | ✅ PASS 40/40 (按 PDF actual) | 30 min | MAJOR version mismatch (2026 v2 vs MVP 2023); 5 papers→2, 3 AO→4, PED 不考, 4 production→3, Topic +2 |
| Psychology 0266 REDO | ✅ PASS 16/20 strict + 4 known | 15 min | 双重 pattern (biology_plus_2 + page_map_incomplete); workflow v2 试水 |
| Add Math 0606 | ✅ PASS 13/20 strict + 7 known + 1 MVP catch | 10 min | depth_incomplete (数学科) + formula_table_1to1 + topic count delta (14 vs 12) + Q20b MVP |
| CS 0478 | ✅ PASS 13 strict + 6 known + 1 major MVP | 18 min | 9 worker catches 史上最高; do_not_speculate_rule + file_name_misleading + redundancy_catch 第 1 activation |
| Chinese 0509 | ✅ PASS 20/20 strict + 0 缺口 + 0 MVP error (cleanest) | 25 min (2-stage: 10+13) | autopromote_2_stage 第 1 activation |
| History 0470 | ✅ PASS 20/20 strict + 0 缺口 + 0 MVP error | 45 min (2-stage: 25+20, 9 学科最长) | autopromote_2_stage 第 2 activation + history_syllabus_3_components_complexity (新 pattern); 4 worker catches (17 sub-units / 3 components / 3 AOs / A*-G) |
| Economics 0455 | ✅ PASS 20/20 strict + 0 缺口 + 7 MVP errors | **~11 min (fastest of 11 学科)** | chemistry_minus_2 + reprint + topic_count_delta (page-map partial; source-index T1/T2 labelled misleading); trigger data for v2.4 (autopromote trigger + source_index_misleading + per-subject AO table) |
| **Math 9709 (A-Level)** | ✅ PASS 20/20 strict + 0 缺口 + 0 MVP error (A-Level 第 1 闭环, cleanest) | **~50 min (2-stage: Stage 1 30 + Stage 2 20)** | **page_map -36 (most severe ever) + autopromote_default_for_alevel 首次 activation + 6 papers+3 routes+2 AOs+MF19+A*-E/a-e**; 10 worker catches; trigger data for v2.4.1 (alevel_cycle_features + autopromote default + grade scale table) |
| **Econ 9708 (A-Level)** | ✅ PASS 20/20 strict + 0 缺口 + 0 MVP error + T4 anomaly decode (A-Level 第 2 闭环) | **~50 min (2-stage: Stage 1 25 + Stage 2 25)** | **T4 missing extraction artifact decode + 4 papers+3 routes+3 AOs+NO MF19+A*-E/a-e**; 10 worker catches; trigger data for v2.4.2 (t_gap_decode_recipe + alevel_econ_vs_math_diff + A-Level cadence confirmation) |
| **Phys 9702 (A-Level)** | ✅ PASS 20/20 strict + 0 缺口 + 0 MVP error + t_gap_decode_recipe verify (A-Level 第 3 闭环) | **~60 min (2-stage: Stage 1 25 + Stage 2 30, LARGEST)** | **t_gap_decode_recipe verify 11 gaps ALL extraction artifacts + 5 papers 含 2 practical P3+P5 (AO3 100%) + Data booklet P1+P2+P4 only + 25 main topics LARGEST**; 9+ worker catches; trigger data for v2.4.3 (t_gap_decode_recipe confirm + alevel_phys_practical_focus + data_booklet_per_paper_verify + AO3 100% on practical eval pattern) |

## Reference: Feishu doc length progression

| After subject | Length (chars) | Delta |
|---------------|----------------|-------|
| (empty) | 0 | — |
| Math 0580 | 14,357 | +14,357 |
| Physics 0625 | 44,295 | +29,938 |
| Chemistry 0620 | 61,890 | +17,595 |
| Biology 0610 | 81,732 | +19,842 |
| Business 0450 | 100,181 | +18,449 |
| Psychology 0266 REDO | 122,488 | +22,307 |
| Add Math 0606 | 142,959 | +20,471 |
| CS 0478 | 164,710 | +21,751 |
| Chinese 0509 | (TBD — not yet appended to doc as of v2.3 ship) | TBD |
| **History 0470** | **177,712** | **+13,002** |
| **Economics 0455** | **201,275** | **+23,563** |
| **Math 9709 (A-Level)** | **224,685** | **+23,410** |
| **Econ 9708 (A-Level)** | **246,092** | **+21,407** |
| **Phys 9702 (A-Level)** | **272,698** | **+26,606** |

**Average per subject**: ~17-23K chars. Plan Feishu doc capacity accordingly.

**Note on lark-cli API change (2026-07-03 → 2026-07-04)**: v1 API (`--markdown @file --mode append`) was deprecated; v2 API is now `--command append --doc-format markdown --content @<file>.md --as bot`. 详见 step[6].

## 🎉 11 学科 T-IGCSE-KQA 全闭环完成 (2026-07-04 01:36) + A-Level Math 9709 第 1 闭环 (2026-07-04 11:00)

**12 学科 (11 IGCSE + 1 A-Level) 综合状态**:
- 5 原始 IGCSE PASS (Math / Physics / Chem / Bio / Business)
- 1 IGCSE REDO (Psychology 0266)
- 5 新 IGCSE KQA 全 PASS (Add Math / CS / Chinese / History / Economics)
- **1 A-Level PASS** (Math 9709 — cleanest A-Level first run)

**13 学科 (11 IGCSE + 2 A-Level) 综合状态**:
- 上述 12 学科 +
- **Econ 9708 (A-Level 第 2)** — cleanest A-Level 2nd + T4 anomaly decode 救场 + 4 papers + 3 AOs + NO MF19

**Total Feishu doc**: 272,698 chars
**Workflow versions**: v1 → v2 → v2.1 → v2.2 → v2.3 → v2.4 → v2.4.1 → v2.4.2 → **v2.4.3** (current)
**Next step**: 7 A-Level KQA 学科 继续 (Chemistry 9701 待派工 = 3 scientific 第 2; Biology 9700 = 第 3 scientific; +4 others = 21 学科齐 400K+ 字符). v2.4.3 expansion candidates 全部已落地.

## Reference: invoke method

| Action | Command |
|--------|---------|
| Read skill (operator) | Open `.claude/skills/syllabus-review-workflow/SKILL.md` |
| Read playbook (operator) | Open `tests/scenarios/syllabus-review-workflow.md` |
| Invoke by AI agent | `/skill syllabus-review-workflow` (when Claude Code is dispatched for KQA) |
| Feishu doc | https://www.feishu.cn/docx/ArZJd17OyoUlK3xsFmRcIK0EnAe |
| MVP validator (future) | `python3 scripts/mvp_validator.py <bundle_path>` |

---

## Scenario 11 — do-not-speculate rule (v2.2)

**Given** worker dispatches and finds `page_map_incomplete` pattern (page-map missing topics) AND topic inventory list is also incomplete
**When** worker encounters a Q that references a topic not in any pre-dispatch source
**Then**
- §11a Worker MUST `pdftotext -f <page>` to read actual PDF content before answering
- §11b If Q asks about a topic that PDF doesn't have (e.g. CS 0478 Q8 Ethics — PDF has no Ethics topic):
  - Worker MUST flag `⚠️ MVP 推测错: PDF 无 [topic] topic, standard 知识补`
  - Worker MUST NOT fabricate PDF content for the missing topic
- §11c Review MUST verify by re-opening PDF; if Q actually does exist in PDF, mark as false positive
- §11d Manager may dispatch worker_builder to re-write the affected Q to match actual PDF

**Verified by**: `cat answer.md | grep "PDF 无 .* topic"` returns ≥1 entry per missing-topic case.

**Verified by**: `cat verdict.md | grep "MVP 推测错"` records the speculation failures.

**Reference**: CS 0478 Q8 case — review originally speculated Q8 = T007 Ethics (based on standard structure); worker 实读 PDF found T007 actual = Algorithm design; PDF has no Ethics topic at all.

---

## Scenario 12 — file_name_misleading detection (v2.2)

**Given** worker dispatches and source-index.md metadata declares a version
**When** worker answers any Q
**Then**
- §12a Worker MUST cross-check PDF internal version stamp via `pdfinfo <file>.pdf` or first-page Content overview
- §12b If source-index.md says "2025-2026 reprint of 2023-2025" but PDF internal says "2023-2025 syllabus", trust PDF internal
- §12c Worker records `⚠️ file_name_misleading: source-index.md declares X, PDF actual Y` in answer.md top
- §12d Review may flag for downstream re-check of source-index.md accuracy

**Verified by**: `cat answer.md | grep "file_name_misleading"` returns ≥1 entry per mismatch case.

**Reference**: CS 0478 case — source-index.md said "2025-2026 reprint"; PDF filename was `CAIE_ComputerScience_0478_Syllabus_2025-2026.pdf`; PDF Content overview + internal version stamp said "2023-2025 syllabus" — actual is 2023-2025, filename misleading.

---

## Scenario 13 — redundancy catch (v2.2)

**Given** worker answers 20 Qs and 2+ Qs reference the same PDF section with essentially the same answer
**When** worker detects same-content answers
**Then**
- §13a Worker MUST flag in answer.md: `⚠️ Redundancy detected: Qn + Qm same answer (PDF [section])`
- §13b Worker should still cite the actual PDF section in both answers (1:1 compliance)
- §13c Review should consider whether MVP questions should be consolidated or differentiated
- §13d Manager may rewrite future MVP to avoid redundancy

**Verified by**: `cat answer.md | grep "Redundancy detected"` returns ≥1 entry per redundant pair.

**Reference**: CS 0478 Q7 + Q18 case — both asked about Cyber security threats; same PDF T5.3 p.20; same answer (9 threats).

---

## Scenario 14 — per-subject type budget + depth budget (v2.2)

**Given** a new IGCSE subject KQA sprint is dispatched
**When** manager estimates total budget
**Then**
- §14a Total sprint time budget per subject type:

  | Subject type | Budget | Reasoning |
  |---|---|---|
  | Math (0580 / 0606) | 10-15 min | Formula strict 1:1 cite; minimal PDF-gap because List of formulas covers most |
  | Science (Physics / Chemistry / Biology) | 25-30 min | PDF-gap common; experiments explicit; topic cross-references needed |
  | Computer Science (0478) | 15-25 min | depth_incomplete common (SQL / sort / topics); page_map_incomplete common |
  | Business (0450) | 20-30 min | Version mismatch common (PED / 2 papers vs 5); structural refactor check |
  | Language (Chinese 0509) | TBD | First run |
  | Humanities (History 0470 / Psychology 0266) | 15-30 min | Version mismatch common; multi-pattern common |

- §14b Per-subject depth budget — worker should know shallow areas:

  | Subject | Known shallow areas |
  |---|---|
  | Math 0580 | none observed |
  | Math 0606 | dot product / 5 derivative rules / interpolation (T13-T14) |
  | Physics 0625 | Topic 5/6 (Nuclear / Space) — 卷长未覆盖 |
  | Chemistry 0620 | 6 PDF gaps observed; PED formula not tested |
  | Biology 0610 | 5 PDF gaps; Piaget stages no age range |
  | Business 0450 | PED formula not tested; 4 production → 3 |
  | Psychology 0266 | sleep stages not tested; lab-field experiment not tested; "explicit/implicit" → "declarative/procedural" |
  | CS 0478 | SQL only 6 cmds; sort only bubble + linear; no Ethics topic |
  | Chinese 0509 | TBD |
  | History 0470 | TBD |

- §14c If a sprint exceeds 1.5× the budget, manager should escalate to boss (`5 min cadence budget overrun` card) and decide whether to dispatch worker_builder help or accept overrun.

**Verified by**: total sprint time ≤ 1.5× budget per §14a; `verdict.md` records actual elapsed time for budget tracking.

---

## Scenario 14b — history_syllabus_3_components_complexity (v2.3)

**Given** a new History 0470 KQA sprint is dispatched (or any future History / source-investigation-heavy IGCSE subject that follows the 3-components + source-based investigation pattern)
**When** review_course runs step[1] pre-flight
**Then**
- §14b.1 Surface detection — scan PDF for 3 unique signals:
  - Signal A: PDF contains a "Component 3" section header (e.g. History 0470 p.30 "Component 3 – Coursework")
  - Signal B: PDF contains "Alternative to Coursework" or "Coursework" + "Alternative" pair (e.g. History 0470 p.31 "Paper 4 – Alternative to Coursework")
  - Signal C: PDF contains "prescribed topic" or "prescribed subjects" + "per exam series" language (e.g. History 0470 p.30 "The prescribed topic changes in each exam series")
- §14b.2 If all 3 signals detected → flag `history_syllabus_3_components_complexity` pattern in step[1]
- §14b.3 Worker MUST NOT speculate which component (P1/P2/C3/P4) a Q probes — read PDF Assessment overview (typically p.9) for component breakdown before answering
- §14b.4 Worker MUST treat each of the 3 components as independent for sub-question mapping:
  - Component A (e.g. Paper 1 = structured essay): Qs about (a)(b)(c) structured essay parts
  - Component B (e.g. Paper 2 = source-based): Qs about source investigation (max N sources per Q, M parts per Q)
  - Component C (e.g. Component 3 OR Paper 4 二选一): Worker notes the 二选一 but answers the actual sub-Q based on the Q wording
- §14b.5 Cross-component AOs distribution MUST be 1:1 cited from PDF (e.g. History 0470 p.10: P1 33/67/0, P2 20/0/80, C3-P4 38/62/0 — reflects question-type focus)
- §14b.6 Prescribed topic changes per exam series — Worker MUST cite current + next exam series topics 1:1 from PDF (e.g. History 0470 p.30: 2027 Option A = 1848 / Imperialism / 1848; 2028 Option A = Italy / WWI / Italy)
- §14b.7 Component 3 vs Paper 4 二选一 — Worker notes center-devised flexibility for Component 3 (Coursework up to 2000 字, internally assessed + externally moderated) vs Paper 4 (1h, externally assessed, 1 essay from 5 depth studies)

**Verified by**:
- `cat verdict.md | grep "history_syllabus_3_components_complexity"` returns ≥1 entry for any History KQA sprint
- `cat answer.md | grep "Component 3 OR Paper 4"` records the 二选一 explicitly
- `cat answer.md | grep "prescribed topic"` records exam-series specific topics verbatim

**Reference**: History 0470 (2026-07-04 00:35) — 3 components verified at PDF p.9 (P1 2h 60m 40% + P2 1h45m 40m 30% + C3/P4 30% 40m); prescribed topics 2027 + 2028 verbatim cited from PDF p.30; Component 3 vs Paper 4 二选一 verified at PDF p.30-31; 4 worker catches (17 sub-units / 3 components / 3 AOs / A*-G).

---

## Scenario 15 — autopromote 2-stage workflow (v2.3)

**Given** step[1] pre-flight detects `page_map_incomplete` AND source-index topic inventory list is also incomplete (双 source 缺)
**When** manager decides to dispatch a KQA sprint
**Then**
- §15a Manager dispatch message MUST include `autopromote_2_stage: true` flag when ALL of these are true:
  1. `page_map_incomplete` flagged in step[1] (page-map topic list does not match PDF topic count, |delta| ≥ 1)
  2. `source_index` topic inventory list is also incomplete (e.g. CS 0478 page-map missing T1/T2 + Inventory doesn't help; History 0470 page-map + source-index 双 source 5 entries vs actual 17 sub-units)
  3. Either `history_syllabus_3_components_complexity` OR `version_mismatch` pattern also detected
- §15b Stage 1 (PDF 实读, estimated time ≈ `pages × 0.5 min`):
  - Worker reads the full PDF (NOT just the topics in source-index)
  - Worker produces `pdf-structure-recovery.md` capturing all topics, components, AOs, page layout, structural elements
  - Stage 1 serves as structural QA gate BEFORE questions.md is written
- §15c Stage 2 (Answer):
  - Reviewer uses Stage 1 report to **rewrite** `questions.md` from placeholder to PDF-actual content
  - Worker answers the rewritten Qs 1:1 cite against actual PDF (not MVP placeholders)
- §15d Total sprint time is ~1.5× of 1-stage workflow, but rework cost of 1-stage error is +20 min, so 2-stage ROI is positive
- §15e Cross-validation reference (4 subjects verified):
  - CS 0478: Stage 1 caught 9 worker catches (file name misleading + 10 topics vs 8 + Q7 实际位置 T5.3 + AOs 3 vs 2 + papers 1h45min vs 1h15min + SQL 6 cmd vs 5+ + sort 仅 bubble+linear + Q7+Q18 redundancy + Q8 Ethics 不在 PDF)
  - Add Math 0606: Stage 1 caught 1 MVP catch (Q20b 2 AOs vs 3) + depth_incomplete + topic count delta (14 vs 12) + total pages delta (-7)
  - Chinese 0509: Stage 1 caught first perfect sprint (20/20 + 0 缺口 + 0 MVP error)
  - History 0470: Stage 1 caught 4 worker catches (17 sub-units / 3 components / 3 AOs / A*-G) + autopromote 第 2 activation

**Verified by**:
- Manager dispatch message contains `autopromote_2_stage: true` field
- `qa-batch/<subject>_<code>/pdf-structure-recovery.md` exists with full topic/component/AO table
- `qa-batch/<subject>_<code>/questions.md` was rewritten by reviewer using Stage 1 report (not original MVP placeholder)
- Sprint time tracked separately: Stage 1 time + Stage 2 time = total (both visible in `verdict.md`)

**Reference**: CS 0478 (2026-07-03 17:10-17:30, 18 min), Chinese 0509 (2026-07-03 ~17:50-18:14, 25 min = Stage 1 10 min + Stage 2 13 min), History 0470 (2026-07-03 23:30-2026-07-04 00:35, 45 min = Stage 1 25 min + Stage 2 20 min, 9 学科最长).

---

## Scenario 16 — topic_count_delta >= 3 autopromote trigger (v2.4)

**Given** step[1] pre-flight computes `topic_count_delta = pdf_topic_count - mvp_topic_count` AND `|delta| >= 3`
**When** review_course detects a large topic count gap even if page-map appears complete
**Then**
- §16a Worker MUST autopromote to 2-stage workflow EVEN IF source-index Topic Inventory count appears to match page-map count
- §16b The trigger fires when:
  1. `|topic_count_delta| >= 3` (e.g. Economics 0455: MVP assumed 4 topics, PDF actual 6 topics, delta=+2... actually wait, let me check: page-map had 4 topics T3-T6 but PDF actual was 6 T1-T6; source-index had 6 entries but T1/T2 labels were preface names not real content. The delta is 2 in topic count but 2 actual topics SKIPPED in MVP. v2.4 trigger uses both: `|topic_count_delta| >= 3` OR source_index labels mismatch PDF actual section titles)
- §16c Stage 1 实读 (estimated ≈ pages × 0.5 min) produces `pdf-structure-recovery.md` BEFORE questions.md is written
- §16d Stage 2 answer uses Stage 1 report to rewrite questions.md from MVP placeholder to PDF actual content
- §16e ROI positive: 2-stage ~1.5× time of 1-stage, but rework cost of 1-stage late catch is +20 min, so 2-stage saves time on subjects with topic_count_delta >= 3

**Verified by**:
- Manager dispatch message contains `autopromote_2_stage: topic_count_delta>=3` flag
- `qa-batch/<subject>_<code>/pdf-structure-recovery.md` exists
- `verdict.md` shows worker caught MVP errors in Stage 1 (not late in Stage 2)

**Reference**: Economics 0455 (2026-07-04 01:18-01:29, ~11 min) — page-map appeared complete (4 entries) but actually skipped Topic 1 (basic economic problem) + Topic 2 (allocation of resources); worker 1-stage Stage 2 catch 7 MVP errors late; v2.4 trigger would have promoted to 2-stage with Stage 1 early catch.

---

## Scenario 17 — source_index_metadata_misleading detection (v2.4)

**Given** source-index.md Topic Inventory has N entries with labels
**When** worker cross-checks source_index labels against PDF actual section titles
**Then**
- §17a Worker MUST for each Topic N entry: read source-index N title, then read PDF actual Topic N title (printed page or Assessment overview); compare
- §17b If source-index N title ≠ PDF actual Topic N title (materially different, e.g. "Why choose?" vs "The basic economic problem"), flag `source_index_metadata_misleading: T<N> = <source_index_title> ≠ <pdf_actual_title>`
- §17c If ≥1 entry flagged → escalate to manager for source-index.md rewrite
- §17d Worker MUST NOT trust source-index labels as PDF ground truth; PDF actual is always source of truth (consistent with v2.2 file_name_misleading detection principle)

**Verified by**:
- `cat answer.md | grep "source_index_metadata_misleading"` returns ≥1 entry per mismatched case
- `source-index.md` rewrite proposal sent to manager after detection

**Reference**: Economics 0455 (2026-07-04 01:18) — source-index T1 = "Why choose?" / T2 = "Syllabus overview" (preface names) but PDF actual T1 = "The basic economic problem" / T2 = "The allocation of resources" (real content). Worker 实读 caught in Stage 2 answer; v2.4 surfaces it earlier in step[1] pre-flight.

---

## Scenario 18 — per-subject AO lookup table + AOs cross-subject 不能类比规则 (v2.4)

**Given** worker is about to answer Qs that probe AOs (Assessment Objectives)
**When** worker reads MVP questions or dispatches
**Then**
- §18a Worker MUST NOT assume AO count similarity across subjects. Specifically:
  - do NOT infer from Add Math 0606 (2 AOs) that CS 0478 also has 2 AOs
  - do NOT infer from Business 0450 2026 v2 (4 AOs) that History 0470 also has 4 AOs
  - do NOT infer from Chinese 0509 (2 AOs) that Economics 0455 also has 2 AOs
- §18b Worker MUST look up per-subject AO count from the table below BEFORE answering AOs Qs:

  | Subject | AO count | Typical distribution |
  |---|---|---|
  | Math 0580 | 3 | AO1 50% + AO2 30% + AO3 20% |
  | Physics 0625 | 3 | AO1 50% + AO2 30% + AO3 20% |
  | Chemistry 0620 | 3 | AO1 50% + AO2 30% + AO3 20% |
  | Biology 0610 | 3 | AO1 50% + AO2 30% + AO3 20% |
  | **Business 0450 (2026 v2)** | **4** | AO1+AO2+AO3+AO4 |
  | **Add Math 0606 (2028-2030)** | **2** | AO1 45-55% + AO2 45-55% |
  | CS 0478 | 3 | AO1 40% + AO2 40% + AO3 20% |
  | **Chinese 0509** | **2** | AO1+AO2 (language-heavy) |
  | History 0470 | 3 | AO1 30% + AO2 45% + AO3 25% |
  | **Economics 0455** | **3** | **AO1 40% + AO2 40% + AO3 20%** (P1 50/50/0, P2 35/35/30) |
  | Psychology 0266 | (TBD) | (TBD after REDO complete verification) |

- §18c If subject not in table → flag `⚠️ AO lookup miss: <subject>` and read PDF Assessment overview directly (typically p.7-10)
- §18d For new subjects not in 11-subject baseline (e.g. A-Level / IB / AP / DSE), Worker MUST NOT extend this table by analogy; each new board / level has its own AO structure that MUST be verified per-subject

**Verified by**:
- For 11 IGCSE subjects in the 2026-07-04 sprint, `verdict.md` AOs Qs cite PDF actual AO count verbatim
- `cat answer.md | grep "AOs cross-subject speculation"` returns 0 entries for 11 IGCSE sprint (no violations)

**Reference**: 11 学科 6 个独立 AO count 验证:
- 3 AOs (标准): Math / Physics / Chemistry / Biology / CS / History / Economics (7 学科)
- 4 AOs (新 syllabus): Business 0450 (2026 v2)
- 2 AOs: Add Math 0606 (2028-2030) + Chinese 0509 (language-heavy)
- TBD: Psychology 0266 (after REDO)

⚠️ **Worker 跨学科 AO assumption 红线**: 即使 Add Math / Chinese / Business 各自独立 AO count, 不能从任一推另两; 每个学科 PDF Assessment overview 是唯一 source of truth.

---

## Scenario 19 — A-Level cycle features (v2.4.1)

**Given** manager dispatches a new A-Level KQA sprint (Math 9709 / Economics 9708 / + more)
**When** review_course runs step[1] pre-flight
**Then**
- §19a Surface detection — scan PDF for 4 distinguishing A-Level signals:
  - Signal A: PDF contains BOTH "AS Level" AND "A2 Level" / "A Level" sections (e.g. Math 9709 p.8-11: "AS only" / "A Level Linear" / "A Level Staged")
  - Signal B: PDF has multi-paper structure (≥4 papers; e.g. Math 9709: 6 papers P1-P6)
  - Signal C: PDF references "formula booklet" / "MF19" (e.g. Math 9709 p.39-52 "Formulae that are not in the MF19 booklet will be provided")
  - Signal D: PDF contains BOTH "A*-E" AND "a-e" grade scales (e.g. Math 9709 p.9: "Grades A*, A, B, C, D, E, a, b, c, d, e")
- §19b If ≥2 signals detected → flag `alevel_cycle_features` pattern in step[1]
- §19c Worker MUST treat the A-Level cycle as structurally distinct from IGCSE:
  - Distinguish "AS Level only" (year 1) vs "A Level full" (AS + A2) question scopes
  - Treat each paper as distinct sub-content (Pure Math / Mechanics / P&S for Math)
  - Cite MF19 formula booklet explicitly for formulae (NOT recall from memory)
  - Use A*-E (A Level) / a-e (AS Level) grade scales correctly (NOT IGCSE A*-G)
- §19d A-Level vs IGCSE 5 重大差异表 (per Math 9709 lesson):
  | 差异 | IGCSE | A-Level |
  |---|---|---|
  | **学制** | 1 年制 end | 2 年制 (AS year 1 + A2 year 2) |
  | **Papers** | 2-4 papers (single tier) | 4-7 papers (multi-tier: Pure + Mech + P&S) |
  | **Routes** | single tier | 3 routes: AS only / A Level Linear / A Level Staged |
  | **AOs** | 3-4 AOs (Bio 3 / Chem 3 / Bus 4) | 2-3 AOs (Math 9709: 2 AOs only AO1+AO2) |
  | **Grade scale** | A*-G (8-level) | A*-E (A Level) + a-e (AS Level) (9-level) |
  | **Formula booklet** | 不 provided (需 memorize) | MF19 formula booklet provided |
  | **Calculator** | 部分 paper 不同 rules | All papers calculator allowed (Math 9709) |

**Verified by**:
- `cat verdict.md | grep "alevel_cycle_features"` returns ≥1 entry for any A-Level KQA sprint
- `cat answer.md | grep "MF19"` records formula booklet citation (Math 9709)
- `cat verdict.md | grep "A\*-E\|a-e"` records A-Level grade scale verbatim

**Reference**: Math 9709 (2026-07-04 11:00) — A-Level 第 1 闭环, 4 signals 全检测 (AS+A2 + 6 papers + MF19 + A*-E+a-e), 10 worker catches in Stage 1, ~50 min 2-stage 闭环.

---

## Scenario 20 — autopromote default for A-Level cycle (v2.4.1)

**Given** manager dispatches a new A-Level KQA sprint
**When** manager emits dispatch message
**Then**
- §20a Manager dispatch message MUST include `level: alevel` flag (for A-Level subjects) or `level: igcse` flag (for IGCSE subjects)
- §20b If `level: alevel` → workflow MUST default to 2-stage (Stage 1 PDF 实读 + Stage 2 answer), regardless of page_map completeness
  - Replaces v2.3 conditional trigger (which required 双 source 缺 to promote)
  - Reasoning: A-Level page-map extraction difficulty is much higher than IGCSE (Math 9709: -36 delta most severe ever)
- §20c If `level: igcse` → workflow follows v2.3 conditional trigger:
  - If `page_map_incomplete` AND `source_index` incomplete → autopromote 2-stage
  - If page_map looks complete → 1-stage answer
- §20d Stage 1 (PDF 实读) for A-Level: estimated time ≈ `pages × 0.5 min` (Math 9709: 59 pages × 0.5 = ~30 min, matches actual)
- §20e Stage 2 (Answer) for A-Level: estimated 20-30 min per subject (Math 9709: 20 min, matches actual)
- §20f Total A-Level budget: **45-60 min** (Math 9709 evidence: 50 min actual)

**Verified by**:
- Manager dispatch message contains `level: alevel` or `level: igcse` field
- For `level: alevel`: workflow skips conditional trigger check and proceeds directly to 2-stage
- `qa-batch/<subject>_<code>/pdf-structure-recovery.md` exists for all A-Level subjects (regardless of page_map appearance)
- Sprint time tracked separately: Stage 1 time + Stage 2 time = total (visible in `verdict.md`)

**Reference**: Math 9709 (2026-07-04 10:15-11:00, ~50 min = Stage 1 30 min + Stage 2 20 min) — first A-Level run under `autopromote_default_for_alevel` rule.

---

## Scenario 21 — A-Level Grade scale table + UMS mark scale (v2.4.1)

**Given** worker is about to answer Q-typed grade Qs (Q20-style "Grades" + Q-typed mark scale Qs)
**When** worker reads MVP questions or dispatches
**Then**
- §21a Worker MUST look up grade scale from this table before answering:

  | Level | Grade scale | UMS mark scale | Examples |
  |---|---|---|---|
  | **IGCSE** | **A*-G** (8-grade + ungraded) | 0-100 (varies per subject) | Math 0580 / Add Math 0606 / CS 0478 / etc. |
  | **AS Level** | **a-e** (5-grade + ungraded) | 0-100 (UMS = Uniform Mark Scale) | Math 9709 P1+P2 (AS-only path) |
  | **A Level** | **A*-E** (5-grade + ungraded) | 0-100 (UMS, A* requires ≥80% on A2 UMS) | Math 9709 P1-P6 (full A Level) |
  | **Business/Accounting (UMS)** | (n/a — IGCSE) | 0-100 (UMS) | Business 0450 / Accounting 0452 (future A-Level cycles) |

- §21b A*-E scale is TIGHTER than A*-G:
  - IGCSE A*-G: 8 grades + ungraded (A* ≥ 90% / A ≥ 80% / B ≥ 70% / C ≥ 60% / D ≥ 50% / E ≥ 40% / F ≥ 30% / G ≥ 20%)
  - A Level A*-E: 5 grades + ungraded (A* ≥ 80% on A2 UMS / A ≥ 70% / B ≥ 60% / C ≥ 50% / D ≥ 40% / E ≥ 30%)
  - AS a-e: 5 grades + ungraded (a ≥ 80% / b ≥ 70% / c ≥ 60% / d ≥ 50% / e ≥ 40%)
- §21c Worker MUST NOT confuse A-Level grade scale with IGCSE:
  - E (A Level) ≈ G (IGCSE) equivalent (both near minimum pass)
  - A* (A Level) requires ≥80% (vs IGCSE A* typically ≥90%)
  - AS small-letter scale (a-e) is A-Level's "AS only" sub-scale, NOT same as A Level capital-letter (A-E)
- §21d If subject not in table → flag `⚠️ Grade scale lookup miss: <subject>` and read PDF grade scale section directly (typically p.9 for Math 9709)

**Verified by**:
- For A-Level KQA sprints, `verdict.md` A*-E/a-e grade Qs cite PDF actual grade scale verbatim
- `cat answer.md | grep "A\*-E\|a-e\|UMS"` records A-Level grade scale citation
- `cat answer.md | grep "Grade scale cross-level confusion"` returns 0 entries (no violations)

**Reference**: Math 9709 (2026-07-04 10:55) — Q20a 1:1 cite PDF p.9: "Grades A*, A, B, C, D, E, a, b, c, d, e"; Q20b MF19 booklet 1:1 cite PDF p.39-52.

---

## Scenario 22 — t_gap_decode_recipe (v2.4.2, NEW)

**Given** worker_syllabus is dispatching a new subject (any level: IGCSE / A-Level) and finds page-map + source-index dual-source labeling a topic as missing (e.g. "T4 missing")
**When** worker reviews the apparent topic gap during step[1] pre-flight or Stage 1 实读
**Then**
- §22a Worker MUST NOT immediately conclude "content gap" when both sources agree on missing
- §22b Worker MUST run `t_gap_decode_recipe` (extraction artifact vs content gap):
  1. Check `page-map.json` for "T_X missing" / "T_X not found" / similar label
  2. Check `source-index.md` Topic Inventory for same missing label
  3. If BOTH sources agree on missing → Stage 1 实读 PDF actual content for that topic area
  4. Search PDF for "T_X" section content by approximate page (use other topics' page mapping as guide)
  5. **Output decision**:
     - **Extraction artifact** (PDF has T_X content but page-map/source-index extraction failed): continue with PDF actual content; flag `t_gap_decode: T_X = extraction artifact` in verdict.md
     - **Actual content gap** (PDF genuinely missing T_X): escalate to manager for syllabus review; cannot complete workflow
- §22c Worker MUST cite the actual PDF page + actual section title in answer.md (not the missing label)
- §22d Reviewer MUST verify the decode decision by re-opening PDF; if Stage 1 caught extraction artifact, mark as PASS

**Verified by**:
- `cat verdict.md | grep "t_gap_decode"` returns ≥1 entry per dual-source missing case
- `cat answer.md | grep "extraction artifact"` records the decode decision

**Reference**: Econ 9708 (2026-07-04 11:18-12:15, ~50 min) — T4 missing in both page-map and source-index, Stage 1 实读 verify T4 = "The macroeconomy" actually exists PDF p.18-19 with 6 sub-topics (4.1-4.6 National income / Circular flow / AD-AS / Economic growth / Unemployment / Price stability). Extraction artifact, NOT content gap. Worker caught in Stage 1 saved rework cost (vs late catch in Stage 2 answer).

---

## Scenario 23 — alevel_econ_vs_math_diff marker (v2.4.2)

**Given** worker dispatches a new A-Level KQA sprint (3rd A-Level subject after Math 9709 + Econ 9708)
**When** worker reviews MVP questions or PDF actual content for per-subject variation
**Then**
- §23a Worker MUST NOT assume A-Level uniformity across subjects. Each A-Level subject has its own paper structure + AO count + formula booklet rules:
  | Dim | Math 9709 (A-Level) | Econ 9708 (A-Level) | Per-subject Diff |
  |---|---|---|---|
  | Papers | 6 P1-P6 (Pure 1+2+3 + Mech + P&S 1+2) | 4 P1-P4 (AS+A2 MCQ+Data Resp) | Math 6 vs Econ 4 |
  | AOs | 2 (AO1 55/52% + AO2 45/48%, NO AO3) | 3 (AO1 35% + AO2 40% + AO3 25%) | Math 2 vs Econ 3 |
  | Formula booklet | YES MF19 (PDF p.39-52) | NO (自己写公式) | Math YES vs Econ NO |
  | Pages | 59 | 43 | varies |
  | Sub-topics | 6 Content Sections × 38 sub | 11 main + ~60 sub | varies |
  | 2-year structure | YES (AS+A2) | YES (AS+A2) | Same |
  | Grade scale | A*-E + a-e | A*-E + a-e | Same |
  | T4 anomaly | (N/A, page-map 2 entries only) | T4 missing = extraction artifact | varies |
- §23b Worker MUST verify per-subject PDF Assessment overview (typically p.7-12 for A-Level) for paper count + AO count + formula booklet rules BEFORE answering Qs
- §23c Worker MUST NOT use Math 9709 patterns (6 papers + 2 AOs + MF19) as a template for other A-Level subjects; per-subject PDF is source of truth
- §23d Future A-Level subjects (Physics 9702 / Chemistry 9701 / Biology 9700 / + more) likely each have own per-subject variations; Worker MUST NOT assume uniformity

**Verified by**:
- `cat verdict.md | grep "alevel_econ_vs_math_diff"` returns ≥1 entry per A-Level KQA sprint
- For each A-Level subject, `verdict.md` paper count + AO count + formula booklet status cited 1:1 from PDF
- `cat answer.md | grep "A-Level uniformity assumption"` returns 0 entries (no violations)

**Reference**: 2-run A-Level cycle evidence (Math 9709 + Econ 9708) — confirmed A-Level cycle has per-subject variation, not standardized structure.

---

## Scenario 24 — t_gap_decode_recipe confirm (v2.4.3, 3 A-Level runs evidence)

**Given** worker is dispatching a new A-Level KQA sprint (any subject beyond 3 A-Level runs)
**When** worker reviews page-map.json + source-index.md for dual-source missing labels
**Then**
- §24a Confirm `t_gap_decode_recipe` rule (per v2.4.2) — when page-map + source-index dual-source labels a topic as missing, Stage 1 实读 verify extraction artifact vs content gap
- §24b Default verdict per **occam's razor**: **extraction artifact until proven otherwise** (more likely listing bug than missing topics in new syllabus)
- §24c 3-run A-Level evidence (Math 9709 + Econ 9708 + Phys 9702) confirms this rule:
  | Subject | page_map delta | T gaps detected | T gaps verified as extraction artifact |
  |---|---|---|---|
  | Math 9709 | -36 (most severe) | (multiple, not enumerated) | ALL extraction artifacts |
  | Econ 9708 | -6 | T4 single gap | 1 extraction artifact (T4 = Macroeconomy) |
  | **Phys 9702** | **-15 + 11 T gaps** (T6/T8/T10/T11/T13/T14/T15/T18/T19/T21/T22) | **11 gaps** | **ALL 11 extraction artifacts** (default verdict held) |
- §24d Worker MUST NOT raise false alarm to manager about "content gap" without Stage 1 实读 verifying
- §24e If Stage 1 实读 finds actual content gap (extraction artifact hypothesis falsified), THEN escalate to manager; otherwise continue with PDF actual content

**Verified by**:
- `cat verdict.md | grep "t_gap_decode"` returns ≥1 entry per dual-source missing case (across all 14 学科)
- `cat answer.md | grep "extraction artifact"` records the decode decision

**Reference**: 3-run A-Level cycle (Math 9709 + Econ 9708 + Phys 9702, 2026-07-04) — t_gap_decode_recipe verified across all 3 A-Level subjects, default verdict "extraction artifact" held in 100% of cases observed.

---

## Scenario 25 — alevel_phys_practical_focus marker (v2.4.3)

**Given** worker dispatches a new A-Level Physics KQA sprint (or any future A-Level subject with practical papers)
**When** worker reviews PDF for practical skills section + AO3 distribution
**Then**
- §25a Surface detection — scan PDF for 3 unique A-Level Physics signals:
  - Signal A: PDF contains "Practical Skills" or "Planning and Analysis" section headers (e.g. Phys 9702 P3 + P5)
  - Signal B: PDF mentions "experimental evaluation" / "data processing" / "lab work" in assessment sections
  - Signal C: PDF contains AO3 distribution table where AO3 100% on specific practical papers
- §25b If all 3 signals detected → flag `aleval_phys_practical_focus` pattern in step[1]
- §25c Worker MUST treat practical papers (P3 + P5 for Phys 9702) as structurally distinct:
  - P3 = Advanced Practical Skills 1 (2h, AO3 100%, 40 marks)
  - P5 = Planning/Analysis (1h15m, AO3 100%, 30 marks)
  - Both require experimental evaluation (NOT knowledge recall)
- §25d Worker MUST cite Data booklet ONLY for non-practical papers (Phys 9702: P1 + P2 + P4 only, NOT P3/P5 practical)
- §25e Cross-A-Level comparison (3-run evidence):
  | Subject | Papers | Practical papers? |
  |---|---|---|
  | Math 9709 | 6 P1-P6 (Pure/Mech/P&S) | NO |
  | Econ 9708 | 4 P1-P4 (AS+A2 MCQ+Data Resp) | NO |
  | **Phys 9702** | **5 P1-P5** | **YES (P3 + P5, AO3 100%)** |
  Worker MUST NOT assume other A-Level subjects have practical papers; per-subject verify.

**Verified by**:
- `cat verdict.md | grep "aleval_phys_practical_focus"` returns ≥1 entry per A-Level Physics KQA sprint
- For Phys 9702, `answer.md` Q12-19 (Q18-Q19 especially) cite AO3 100% on P3+P5 verbatim
- `cat answer.md | grep "Practical Skills"` records the practical paper structure

**Reference**: Phys 9702 (2026-07-04 12:18-13:25, ~60 min, 3 scientific 第 1 个) — A-Level cycle 第 3 run; 5 papers 含 2 practical (P3+P5 AO3 100%) confirmed unique vs Math 9709 (6 pure) + Econ 9708 (4 pure).

---

## Scenario 26 — Data booklet per-paper verify (v2.4.3)

**Given** worker is about to answer Q-typed formula/equation Qs in A-Level KQA sprint
**When** worker reads PDF for formula booklet presence + per-paper distribution
**Then**
- §26a Worker MUST look up formula booklet status from this table BEFORE answering:
  | Subject | Booklet | Which papers |
  |---|---|---|
  | **Math 9709** | MF19 | All 6 papers (P1-P6) |
  | **Econ 9708** | NO booklet | (自己写公式, all 4 papers) |
  | **Phys 9702** | Data and formulae booklet | P1 + P2 + P4 only (NOT P3/P5 practical) |
- §26b Worker MUST cite formula booklet ONLY for papers that include it:
  - Math 9709: cite MF19 for ALL 6 papers
  - Econ 9708: NO booklet cite (always recall from memory or standard formula)
  - Phys 9702: cite Data booklet for P1+P2+P4 only; for P3/P5 practical, student does NOT use booklet
- §26c Worker MUST NOT infer formula booklet presence from IGCSE sibling (e.g. IGCSE Math 0580 has NO booklet, but A-Level Math 9709 has MF19 — opposite)
- §26d Worker MUST NOT assume uniform booklet presence across all papers within same A-Level subject (Phys 9702: booklet for P1+P2+P4 but NOT P3+P5)
- §26e Violation → flag `⚠️ Booklet per-paper speculation` in answer.md, retry with per-paper verify

**Verified by**:
- For each A-Level subject, `answer.md` formula cites include explicit booklet reference (e.g. "MF19 p.5" / "Data booklet p.2")
- `cat answer.md | grep "Booklet per-paper speculation"` returns 0 entries (no violations)
- For Phys 9702 P3+P5 Qs, `answer.md` correctly excludes Data booklet citation (since booklet NOT for practical)

**Reference**: 3-run A-Level cycle evidence (Math 9709 + Econ 9708 + Phys 9702) — booklet presence varies per subject AND per paper within same subject (Phys 9702 booklet for P1+P2+P4 only, not P3/P5 practical).