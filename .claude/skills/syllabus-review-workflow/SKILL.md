---
name: syllabus-review-workflow
description: "Run an end-to-end CAIE IGCSE Knowledge-level QA (KQA) sprint against an official syllabus PDF, with mandatory MVP pre-flight (version/page-map verify), review↔syllabus Q&A loop, PDF-gap handling, page-map offset correction (Chemistry -2 / Biology +2 patterns), Feishu doc append (4-section structure), 5-min cadence, and Psychology-type version mismatch protection. Use when manager dispatches a new IGCSE subject KQA (e.g. CS 0478, Add Math 0606, Chinese 0509, History 0470, Economics 0455), or when a KQA sprint needs to be re-run after syllabus version mismatch."
---

# syllabus-review-workflow (v2.4.3)

End-to-end KQA workflow for any **CAIE IGCSE / A-Level syllabus** (`pilot-output/assessment-skills/caie-{igcse,alevel}-<subject>-<code>/`), distilled from the 2026-07-03 to 2026-07-04 **14-subject sprint** (11 IGCSE: Math 0580 / Physics 0625 / Chemistry 0620 / Biology 0610 / Business 0450 / Psychology 0266 REDO / Add Math 0606 / CS 0478 / Chinese 0509 / History 0470 / Economics 0455 + 3 A-Level: Math 9709 / Econ 9708 / Phys 9702). **All 14 subjects closed-loop PASS, Feishu doc 272,698 chars.**

> v2 changes (from v1, 2026-07-03 16:00): added §MVP 笔误 4 类典型 pattern (step[3]), answer.md 8 段模板 (step[3]), page-map 双路径检测 (step[1]), pause misjudgment 详细流程 (step[9]).
> **v2.1 changes (from v2, 2026-07-03 16:57)**: step[1] 加 `topic count delta` 字段 + `total_pages delta` 字段; step[1] 加 `depth_incomplete` pattern (数学科) + `formula_table_1to1` surface 检测; step[2] dispatch 加 Q20b-style structural refactor 检测 (e.g. 2 AOs vs 3 AOs).
> **v2.2 changes (from v2.1, 2026-07-03 17:34)**: step[2] 加 `do_not_speculate_rule` (page_map_incomplete 双 source 缺时不能 standard structure 推测) + `file_name_misleading` detection; step[3] 加 `redundancy_catch` (MVP 同答案题目 flag) + `per_subject_depth_budget`; step[8] cadence 加 `per_subject_type_budget` (Math 10 / CS 15-25 / Psychology 15 / Biology 30). Trigger words unchanged.
> **v2.3 changes (from v2.2, 2026-07-04 00:50)**: step[1] 加 `history_syllabus_3_components_complexity` pattern (History 唯一含 Component 3 Coursework + Paper 4 Alt 二选一, 3 components vs 2 papers 区分); step[1] 加 `autopromote_2_stage` 规则 (page_map_incomplete + source_index 不全 双 source 缺时自动 promote 1-stage → 2-stage workflow); step[8] cadence refined per-subject budget (Chinese 0509 25 min / History 0470 45 min / Economics 0455 15-20 min / Math 10 min / CS 15-25 min / Psychology 15 min / Biology 30 min). Trigger words unchanged.
> **v2.4 changes (from v2.3, 2026-07-04 01:42)**: step[1] 加 `topic_count_delta >= 3` autopromote trigger (Economics lesson, 即使 page-map 看似 complete 但 actual vs MVP topic delta ≥ 3 时自动 promote); step[1] 加 `source_index_metadata_misleading` detection (Economics lesson, source-index Topic Inventory labels may be inaccurate e.g. T1/T2 labelled "Why choose" 但 actual = real content); step[1] 加 per-subject AO lookup table (11 学科 6 个独立 AO count: Bio 3 / Chem 3 / Phys 3 / Math 3 / Bus 4 / Add Math 2 / CS 3 / Chinese 2 / History 3 / Economics 3); step[1] 加 AOs cross-subject 不能类比规则 (警告: 不要从 Add Math 2 AOs 推到 CS 3 AOs 等). Trigger words unchanged.
> **v2.4.1 changes (from v2.4, 2026-07-04 11:00)**: step[1] 加 `alevel_cycle_features` marker (Math 9709 lesson, 2-year AS+A2 / multi-paper 4-7 papers / MF19 formula booklet / A*-E+a-e grade scale); step[1] 加 `autopromote_default_for_alevel` (取代 v2.3 conditional trigger, A-Level cycle 默认 2-stage 因 page-map extraction 难度); step[1] 加 A-Level Grade scale table (A*-E A Level + a-e AS Level + UMS 0-100 mark scale for Business/Accounting); step[8] cadence per-level table (IGCSE 1-stage 10-15 / IGCSE standard 25-30 / **A-Level 2-stage 45-60 min** + per-subject Math 9709 evidence: 50 min). Trigger words unchanged.
> **v2.4.2 changes (from v2.4.1, 2026-07-04 12:20)**: step[1] 加 `t_gap_decode_recipe` (NEW, Econ 9708 lesson: 当 page-map + source-index 双 source 标 T_X 缺, worker 必须实读 verify 是 extraction artifact vs actual content gap; T4 missing verify = extraction artifact, NOT content gap, actual T4 = Macroeconomy PDF p.18-19); step[1] 加 `alevel_econ_vs_math_diff` marker (Econ NO formula booklet vs Math MF19; Econ 3 AOs vs Math 2 AOs; Econ 4 papers vs Math 6 papers — 同一 A-Level cycle 不同 paper structure / AO count / formula booklet rules); step[8] cadence confirmation 50 min avg per A-Level subject (Math 9709 50 min + Econ 9708 50 min, 2-run avg evidence); step[1] A-Level AOs cross-subject 不能类比规则更新 (Math 2 AOs vs Econ 3 AOs = 跨 2 A-Level 学科 verify 规则, 不预判). Trigger words unchanged.
> **v2.4.3 changes (from v2.4.2, 2026-07-04 13:35)**: step[1] `t_gap_decode_recipe` confirm (NEW v2.4.2 + 现 confirm 跨 3 A-Level runs: Math 9709 -36 / Econ 9708 -6 / Phys 9702 -13 page_map delta, 11 T gaps in Phys ALL extraction artifacts per occam's razor default verdict); step[1] §aleval_phys_practical_focus marker (A-Level Phys 5 papers 含 2 practical P3+P5, AO3 100% practical, A-Level 其他学科无 practical papers); step[1] Data booklet per-paper verify (A-Level Phys Data booklet for P1+P2+P4 only, NOT P3/P5 practical — vs Math MF19 all papers vs Econ NO booklet); step[1] AO3 100% on practical eval pattern (A-Level Phys 独有 evaluation pattern, IGCSE AO3 partial vs A-Level 学科-specific AO3 distribution); step[8] A-Level cycle cadence refined (Math 50 / Econ 50 / Phys 60, 3-run avg ~53 min, in 50-65 min budget). Trigger words unchanged.

## When to use this skill

- Manager dispatches a new IGCSE subject KQA (CS 0478 / Add Math 0606 / Chinese 0509 / History 0470 / Economics 0455 / + more).
- A previous KQA sprint needs re-validation after a syllabus version mismatch (e.g. Business 0450 2026 v2 vs MVP 2023 reprint).
- An operator wants to run a Given/When/Then regression sweep over the workflow.

Do **not** use this skill for:

- A-Level / AP / IB / DSE (out of scope; use sibling skills when available).
- Non-CAIE boards (Edexcel / AQA / OCR).
- Generating the syllabus skill package itself (use `assessment-skill-builder`).
- Validating the skill package structure (use `review-syllabus-skill`).

## Dispatch chain (4-role contract)

| Role | Agent | Responsibility |
|------|-------|----------------|
| Lead | `review_course` | Owns Q&A loop, MVP version verify, page-map correction, final verdict (`pass / warn / fail`) |
| Answerer | `worker_syllabus` | Answers N KQA questions from PDF, 1:1 citations, attaches skill path |
| Supplementer | `worker_course` | When worker_syllabus flags a PDF gap, writes `supplements.md` to fill it (Option A) |
| Publisher | `worker_builder` | Appends the 4-section Feishu doc section per subject, manages the single-doc archive |

The single source of truth for KQA results is the Feishu doc `ArZJd17OyoUlK3xsFmRcIK0EnAe` (one section per subject, 4-section structure).

## Workflow (10 steps)

### step[1] — MVP pre-flight (mandatory before any dispatch)

Run the 5-step pre-flight on every new subject, before writing `questions.md`. **Skipping this is the root cause of Psychology 14/20 + Business Q4b / Q12b / Q19 / + page-map drift failures.**

1. **Read `source-bundles/{bundle}-guide/source-index.md`** → extract `pdf_version` (year + version tag) + `total_pages`.
2. **Read `page-map.json`** → extract topic list (id, name, start_page, type) + `total_pages` from page-map.
3. **Compare to manager's expected version** (manager must declare year + total_pages in dispatch). If they don't match, escalate **before** writing questions.
   - **NEW (v2.1)**: Compute `total_pages_delta` = `pdf_actual_total - page_map_total`. If |delta| > 0, flag `page_map_incomplete` (page-map total ≠ PDF total, e.g. Add Math 0606: page-map=38, PDF actual=31, delta=-7).
   - **NEW (v2.1)**: Compute `topic_count_delta` = `pdf_topic_count - mvp_topic_count`. If != 0, flag `topic_count_mismatch` (e.g. Add Math 0606: PDF=14, MVP=12, delta=+2). Workflow should expect MVP questions referring to non-existent topics and PDF topics that MVP doesn't cover.
4. **Tag the pattern** so the rest of the workflow knows what to expect:
   - `chemistry_minus_2` — preface occupies t001/t002 (Chemistry 0620 observed)
   - `biology_plus_2` — preface + 2 short real topics occupy t001/t002 (Biology 0610 / Business 0450 observed)
   - `reprint_1_to_4_pages` — 2025-2026 reprint reshuffle (Chemistry 0620 / Business 0450 observed)
   - `version_mismatch` — MVP year/total_pages ≠ PDF year/total_pages (Business 0450 2026 v2 vs MVP 2023 reprint observed)
   - `topic_deletion` — major topics removed in new syllabus (Business 0450 PED removed, production types cut)
   - `page_map_incomplete` — page-map missing topics (CS 0478 / Chinese 0509 / History 0470 partial)
   - **NEW (v2.1) `depth_incomplete`** — MVP assumes deep coverage of topics, but PDF actual is shallow (Add Math 0606: MVP assumes dot product + 5 derivative rules + interpolation are core, PDF 2028-2030 T13 only add/sub/scalar mult, T14 only 6 standard functions). Mathematics-heavy subject pattern.
   - **NEW (v2.1) `formula_table_1to1`** — Mathematics subjects often have a "List of formulas" page (e.g. Add Math 0606 PDF p.22). Worker MUST cite formulas 1:1 from the formula table, not recall from memory. Surface marker: PDF contains "List of formulas" or "Formulae list" section.
   - **NEW (v2.3) `history_syllabus_3_components_complexity`** — History 0470 (and any future History / source-investigation-heavy subject) has a unique 3-components structure (Paper 1 essay + Paper 2 source-based + Component 3 Coursework OR Paper 4 Alt 二选一) that is structurally different from the 2-papers + 1-component pattern of all other 8 IGCSE subjects in the 2026-07-03 sprint. Surface markers: PDF contains "Component 3" + "Coursework" + "Alternative to Coursework" sections, OR multiple "prescribed topic changes per exam series" hints. Worker MUST treat each component as independent for sub-question mapping; cross-component AOs distribution (P1 33/67/0, P2 20/0/80, C3-P4 38/62/0) reflects question-type focus. **Do NOT speculate** which component a Q probes — read PDF Assessment overview (typically p.9) for component breakdown.
   - **NEW (v2.4) `topic_count_delta >= 3` autopromote trigger** (Economics 0455 lesson) — even if page-map.json appears complete (entries count matches source-index topic count), if `|topic_count_delta| >= 3` where delta = `pdf_topic_count - mvp_topic_count`, the workflow MUST autopromote to 2-stage + Stage 1 实读 verify. Surface detection: page-map topic count vs PDF actual topic count cross-check during step[1] pre-flight. **Economics case**: page-map 4 entries (T3-T6) matched source-index 6 entries labelled "T1/T2 = Why choose / Syllabus overview" — looked complete but actually skipped 2 real topics (basic economic problem + allocation of resources). Worker 实读 PDF 30 pages caught 7 MVP errors in 1-stage Stage 2 (cost: late catch). v2.4 trigger ensures Stage 1 实读 happens BEFORE questions.md write, catching these earlier.
   - **NEW (v2.4) `source_index_metadata_misleading` detection** (Economics 0455 lesson) — source-index.md Topic Inventory entries may have inaccurate labels even when entry count matches. Detection: Worker MUST cross-check `source_index Topic N title` against `PDF actual printed page Topic N title`. If they differ materially (e.g. source-index "T1 = Why choose?" but PDF actual "T1 = The basic economic problem"), flag `source_index_metadata_misleading: <entry> = <source_index title> ≠ <pdf_actual title>`. **Economics case**: source-index T1 = "Why choose?" / T2 = "Syllabus overview" (preface names) vs PDF actual T1 = "The basic economic problem" / T2 = "The allocation of resources" (real content). Worker 实读 caught this in Stage 2; v2.4 surfaces it earlier in step[1] pre-flight.
   - **NEW (v2.4) per-subject AO lookup table** — AOs cross-subject cannot be assumed similar. Worker MUST look up AO count from this table before answering Q-typed AOs Qs, NOT from "standard IGCSE" assumption:
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
   - **NEW (v2.4) AOs cross-subject 不能类比规则** — Worker MUST NOT assume AO count similarity across subjects. Specifically: do NOT infer from Add Math 2 AOs that CS 0478 also has 2 AOs; do NOT infer from Business 4 AOs that History 0470 also has 4 AOs. Each subject's AO structure is independent. Worker MUST verify per-subject PDF Assessment overview (typically p.7-10) before answering AOs Qs. Violation → flag `⚠️ AOs cross-subject speculation` in answer.md, retry with per-subject lookup.
   - **NEW (v2.4.1) `alevel_cycle_features`** (Math 9709 lesson) — A-Level cycle has 4 distinguishing features vs IGCSE that affect workflow structure:
     1. **2-year structure (AS + A2)** — AS Level = year 1 (P1+P2 for Math); A2 Level = year 2 (P3 for Math); A Level = AS + A2 combined. Worker MUST distinguish "AS Level only" vs "A Level full" question scopes.
     2. **Multi-paper structure (4-7 papers)** — A-Level typically has 4-7 papers vs IGCSE 2-4. Each paper has distinct sub-content (Pure Math / Mechanics / P&S for Math). Worker MUST NOT assume paper count similarity to IGCSE siblings.
     3. **MF19 formula booklet** (Math 9709 PDF p.39-52) — A-Level Math provides formula booklet; IGCSE Math does NOT. Worker MUST cite MF19 for formulae explicitly.
     4. **A*-E + a-e grade scale** — A Level uses A*-E (5-grade + ungraded); AS Level uses a-e (5-grade + ungraded). IGCSE uses A*-G (8-grade). Different grade scale = different pass threshold + different UMS mark scale.
     Surface detection: PDF contains "AS Level" AND "A2 Level" / "A Level" sections, OR has multi-paper structure (≥4 papers), OR references "formula booklet" / "MF19".
   - **NEW (v2.4.1) `autopromote_default_for_alevel`** (Math 9709 lesson) — For A-Level cycle subjects, autopromote_2_stage becomes the DEFAULT (replaces v2.3 conditional trigger). Reasoning: A-Level page-map extraction difficulty is much higher than IGCSE (Math 9709 page_map had only 2 entries vs actual 38 sub-topics = -36 delta, most severe ever). Manager dispatch MUST include `level: alevel` flag when dispatching A-Level subjects, so worker_syllabus knows to default to 2-stage. Conditional trigger (v2.3) still applies to IGCSE; default-promote (v2.4.1) applies to A-Level.
   - **NEW (v2.4.1) A-Level Grade scale table** — Worker MUST look up grade scale from this table before answering Q-typed grade Qs:
     | Level | Grade scale | UMS mark scale | Examples |
     |---|---|---|---|
     | **IGCSE** | **A*-G** (8-grade + ungraded) | 0-100 (varies per subject) | Math 0580 / Add Math 0606 / CS 0478 / etc. |
     | **AS Level** | **a-e** (5-grade + ungraded) | 0-100 (UMS = Uniform Mark Scale) | Math 9709 P1+P2; other A-Level AS components |
     | **A Level** | **A*-E** (5-grade + ungraded) | 0-100 (UMS, A* requires ≥80% on A2 UMS) | Math 9709 P1-P6; other A-Level full |
     | **Business/Accounting (UMS)** | (n/a — IGCSE) | 0-100 (UMS) | Business 0450 / Accounting 0452 (future A-Level cycles) |
     A*-E scale is TIGHTER than A*-G (E ≈ G-IGCSE equivalent; only 5 grades vs 8). AS small-letter scale (a-e) is A-Level's "AS only" sub-scale.
   - **NEW (v2.4.2) `t_gap_decode_recipe`** (Econ 9708 lesson) — when page-map + source-index dual-source labels a topic as missing (e.g. "T4 missing"), Worker MUST NOT assume content gap. Instead, run Stage 1 实读 verify recipe:
     1. Check page-map.json for "T_X missing" label
     2. Check source-index.md Topic Inventory for same missing label
     3. If BOTH sources agree on missing → do NOT conclude content gap yet. Worker MUST Stage 1 实读 PDF actual content for that topic area
     4. Cross-reference: search PDF for actual "T_X" section content by approximate page (use other topics' page mapping as guide)
     5. **Output decision**:
        - **Extraction artifact** (PDF has T_X content but page-map/source-index extraction failed): continue with PDF actual content; flag `t_gap_decode: T_X = extraction artifact` in verdict.md
        - **Actual content gap** (PDF genuinely missing T_X): escalate to manager for syllabus review; cannot complete workflow
     **Econ 9708 case**: T4 missing in both page-map and source-index, Stage 1 实读 verify T4 = "The macroeconomy" actually exists PDF p.18-19 with 6 sub-topics (4.1-4.6). Extraction artifact, NOT content gap. Worker caught in Stage 1 saved rework cost.
   - **NEW (v2.4.2) `alevel_econ_vs_math_diff` marker** — A-Level subjects vary significantly per-subject even within same cycle. Worker MUST NOT assume A-Level uniformity across subjects. Evidence from 2-run A-Level cycle:
     | Dim | Math 9709 (A-Level) | Econ 9708 (A-Level) | Diff implication |
     |---|---|---|---|
     | Papers | 6 P1-P6 (Pure 1+2+3 + Mech + P&S 1+2) | 4 P1-P4 (AS+A2 MCQ+Data Resp) | Per-subject paper count + split (Math 6 vs Econ 4) |
     | AOs | 2 (AO1 55/52% + AO2 45/48%, NO AO3) | 3 (AO1 35% + AO2 40% + AO3 25%) | Per-subject AO count (Math 2 vs Econ 3) |
     | Formula booklet | YES MF19 (PDF p.39-52) | NO (自己写公式) | Per-subject formula booklet presence (Math YES vs Econ NO) |
     | T4 anomaly | (N/A, page-map 2 entries only) | T4 missing = extraction artifact | Per-subject page-map severity |
     | Pages | 59 | 43 | Per-subject PDF length varies |
     | Sub-topics | 6 Content Sections × 38 sub | 11 main + ~60 sub | Per-subject topic structure varies |
   - **NEW (v2.4.2) A-Level AOs cross-subject 不能类比规则** (refined with 2 A-Level runs evidence) — Worker MUST NOT assume A-Level AO uniformity across A-Level subjects. Specifically:
     - do NOT infer from Math 9709 (2 AOs) that other A-Level subjects also have 2 AOs (Econ 9708 has 3 AOs, disproves)
     - do NOT infer from Econ 9708 (3 AOs) that all A-Level subjects have 3 AOs (Math 9709 has 2 AOs, disproves)
     - Per-subject PDF Assessment overview (typically p.8-12 for A-Level) is the ONLY source of truth for AO count.
   - **NEW (v2.4.3) `t_gap_decode_recipe` confirm (3 A-Level runs evidence)** — confirmed via Phys 9702 (3rd A-Level run). Workflow: when page-map + source-index 双 source labels topic_number gap (e.g. "T6 missing"), Worker MUST run t_gap_decode_recipe (Stage 1 实读 verify extraction artifact vs content gap). Default verdict per occam's razor: **extraction artifact until proven otherwise** (more likely listing bug than missing topics in new syllabus). Evidence:
     - Math 9709: page_map only 2 entries (most severe), all gaps extraction artifacts
     - Econ 9708: page_map T4 missing, verified extraction artifact (actual T4 = Macroeconomy PDF p.18-19)
     - Phys 9702: page_map 11 T gaps (T6/T8/T10/T11/T13/T14/T15/T18/T19/T21/T22), ALL verified as extraction artifacts (default verdict held)
   - **NEW (v2.4.3) `alevel_phys_practical_focus`** (Phys 9702 lesson) — A-Level Physics uniquely has 5 papers 含 2 practical papers (P3 + P5), both with AO3 100% weighting. This is structurally different from all other A-Level subjects in the 3-run cycle (Math 9709 6 papers pure + Econ 9708 4 papers pure). Surface detection: PDF contains "Practical Skills" or "Planning and Analysis" sections + AO3 % concentrated on practical papers. Worker MUST:
     - Treat P3 + P5 as practical skills papers with experimental focus
     - Cite Data booklet ONLY for P1+P2+P4 (NOT P3/P5 practical — students use lab equipment / experimental data, not provided formulae)
     - Recognize AO3 100% on practical means "experimental evaluation" is the dominant AO, NOT knowledge recall
   - **NEW (v2.4.3) Data booklet per-paper verify** — A-Level formula/booklet presence varies per subject AND per paper within same subject:
     | Subject | Booklet | Which papers |
     |---|---|---|
     | **Math 9709** | MF19 | All 6 papers (P1-P6) |
     | **Econ 9708** | NO booklet | (自己写公式, all 4 papers) |
     | **Phys 9702** | Data and formulae booklet | P1 + P2 + P4 only (NOT P3/P5 practical) |
     Worker MUST verify per-paper which papers include booklet — for Phys 9702, P3/P5 students do not use Data booklet (they do experiments). Violation → flag `⚠️ Booklet per-paper speculation` in answer.md.
   - **NEW (v2.4.3) AO3 100% on practical eval pattern** — A-Level Physics has unique evaluation pattern where AO3 (Evaluation) is 100% concentrated on practical papers (P3+P5), vs other A-Level subjects where AO3 may be spread across all papers. Cross-subject evidence:
     | Subject | AO3 % | Where concentrated |
     |---|---|---|
     | **Math 9709** | 0% | NO AO3 (only AO1+AO2) |
     | **Econ 9708** | 25% | Spread across P2 (10%) + P4 (20%) |
     | **Phys 9702** | 20% (but 100% on P3+P5) | **P3 (100% AO3) + P5 (100% AO3)** |
     Worker MUST NOT assume AO3 spread across all papers uniformly — per-subject verify AO3 concentration.
5. **Write `questions.md` with PDF actual page + actual topic**, NOT page-map numbers. Use this template per Q:

   ```markdown
   ## Qn (MVP Subject Topic N = PDF Topic N+2 if biology pattern, MVP p.M / PDF actual p.X, offset ±K)

   **QnX.** <question text>

   **源 PDF 证据** (p.X, Topic Y):
   预期答案: <expected answer or "see PDF">
   ```

### step[2] — review_course dispatches Q&A loop

- Read or generate 20 questions spanning the syllabus (Math style: 5 MVP + 15 expansion).
- For each Q, ensure sub-questions are well-scoped (avoid asking "5 scalars" when PDF lists 6 — see Chemistry Q1 lesson).
- **NEW (v2.1) Structural refactor detector** — before dispatch, verify against PDF actual Assessment overview:
  - **Papers count** (PDF may have changed 2 → 1 / 5 → 2 / etc.)
  - **AO count** (PDF may have changed 3 → 2 / 3 → 4, etc.) — **Add Math 0606 lesson**: PDF 2028-2030 only has 2 AOs (AO1 45-55% + AO2 45-55%); MVP was 3 AOs (50/30/20). Reviewer MUST flag in dispatch message so worker knows to catch Q20b-style "MV P wrong structure" Qs.
  - **Grade scale** (PDF may have changed A*-G → A*-E, etc.)
  - **Core/Extended tier** (PDF may have collapsed 5-paper Core/Extended → 2-paper single tier, etc.)
  - If any structural refactor detected, mark the question(s) that probe it with `⚠️ MVP structural refactor expected` flag.
- **NEW (v2.2) `do_not_speculate_rule`** — when `page_map_incomplete` AND topic inventory list is also incomplete (e.g. CS 0478 page-map missing T1/T2 + Inventory doesn't help), do NOT speculate topic content from standard syllabus structure. Instead:
  - Worker MUST `pdftotext -f <page>` to read actual PDF content before answering
  - If a Q asks about a topic that PDF doesn't have (e.g. CS 0478 Q8 Ethics — PDF has no Ethics topic), worker MUST flag `⚠️ MVP 推测错: PDF 无 [topic] topic, standard 知识补` rather than fabricate PDF content
  - **CS 0478 lesson**: review_course originally speculated Q7 = T006 Safety/Security and Q8 = T007 Ethics based on standard structure. Worker 实读 PDF found Q7 actual = T5.3 Cyber security (p.20), Q8 actual = no Ethics topic at all. Speculation caused both wrong topic mapping AND a wrong-Q8.
- **NEW (v2.3) `autopromote_2_stage`** — when **both** source signals are missing simultaneously (i.e. `page_map_incomplete` AND `source_index` topic inventory list also incomplete), the workflow MUST auto-promote from the default 1-stage loop (dispatch → answer → verify) to a 2-stage loop:
  - **Stage 1 (PDF 实读)**: Worker reads the full PDF (estimated time ≈ `pages × 0.5 min`), produces a `pdf-structure-recovery.md` report capturing all topics, components, AOs, page layout, and structural elements. This stage serves as a structural QA gate.
  - **Stage 2 (Answer)**: Reviewer uses Stage 1 report to **rewrite** `questions.md` from placeholder to PDF-actual content (e.g. CS 0478 Q8 from "Ethics" to a PDF-actual topic; History 0470 Q1-Q12 from "20+ topics" to "17 sub-units: Option A 6 + Option B 6 + 5 depth studies"). Worker then answers the rewritten Qs 1:1 cite against actual PDF.
  - **Trigger conditions (ALL must be true)**:
    1. `page_map_incomplete` flagged in step[1] pre-flight (page-map topic list does not match PDF topic count, |delta| >= 1)
    2. `source_index` topic inventory list also incomplete (e.g. lists only 5 of 17 topics, or stops at first depth study)
    3. `history_syllabus_3_components_complexity` pattern detected (cross-source missing is common in 3-component humanities)
  - **Cross-validation** (verified in CS 0478 + Add Math 0606 + Chinese 0509 + History 0470): Stage 1+Stage 2 catches 4+ MVP errors per subject that 1-stage misses (CS Q8 Ethics, Add Math 14 vs 12 topics, Chinese / History 17 sub-units vs MVP 20+). Total sprint time ~1.5× of 1-stage, but rework cost of 1-stage error is +20 min, so 2-stage ROI is positive.
  - **Manager dispatch message MUST include**: `autopromote_2_stage: true` flag when conditions are met, so worker_syllabus knows to expect Stage 1 + Stage 2 phases instead of single-shot answer.
- **NEW (v2.2) `file_name_misleading` detection** — source-index.md metadata `pdf_version` may not reflect PDF actual content. Worker MUST cross-check:
  - `pdfinfo <file>.pdf` → extract PDF internal version stamp
  - First page `Content overview` or `Preface` → look for explicit "Version X" or "Year YYYY-YYYY"
  - If source-index.md says "2025-2026 reprint" but PDF internal says "2023-2025 syllabus", trust PDF internal
  - **CS 0478 lesson**: source-index.md said "2025-2026 reprint of 2023-2025"; PDF filename was `CAIE_ComputerScience_0478_Syllabus_2025-2026.pdf`; but PDF Content overview + internal version stamp said "2023-2025 syllabus" — actual is 2023-2025 syllabus, filename is misleading.
- Push Q batch to `worker_syllabus` via `eduflow send worker_syllabus review_course "questions ready, MVP pre-flight pattern: <tag>, structural_refactors: <list>"`.

### step[3] — worker_syllabus answers with 1:1 PDF citations

- For each Q, cite **PDF actual page** (not page-map) with **PDF actual topic** (offset-aware).
- If PDF lacks content: write the gap as `PDF 未显式列 [thing], standard 知识补: [truth]`. Never fabricate.
- **NEW (v2.1) `formula_table_1to1` surface** — if pattern flagged in step[1], locate the PDF "List of formulas" page (e.g. Add Math 0606 p.22) and cite formulas 1:1 from the formula table. Do NOT recall from memory.
- **NEW (v2.1) `depth_incomplete` handling** — if pattern flagged, MVP may ask about topics that PDF only sketches. Worker answers PDF actual, marks `⚠️ MVP 假设超出 PDF 实际深度, standard 知识补`. Do NOT pretend PDF deep coverage.
- **NEW (v2.2) `per_subject_depth_budget`** — per-subject PDF depth differs wildly. Worker should know the budget per subject type:
  | Subject type | Depth budget | Known shallow areas |
  |---|---|---|
  | Math (0580, 0606) | Moderate; formulas strict | Add Math: dot product / 5 derivative rules / interpolation |
  | Science (Physics 0625, Chemistry 0620, Biology 0610) | Moderate; experiments explicit | PED formula not tested in Chem 0620 |
  | Computer Science (0478) | Shallow; only what PDF lists | SQL only 6 cmds / sort only bubble+linear / no Ethics topic |
  | Business (0450) | Moderate; new syllabus reduced | PED formula not tested |
  | Language (Chinese 0509) | TBD | TBD after first run |
  | Humanities (History 0470, Psychology 0266) | TBD | TBD after first run |
- **NEW (v2.2) `redundancy_catch`** — when 2+ questions reference the same PDF section and the answer is essentially the same content (e.g. CS 0478 Q7 + Q18 both ask about Cyber security threats and answer is "9 threats from PDF T5.3 p.20"), worker MUST flag in answer.md:
  ```
  ⚠️ Redundancy detected: Q7 + Q18 same answer (PDF T5.3 Cyber security threats)
  ```
  This signals to review_course that MVP has overlap and review should consolidate or differentiate.
- Save `answer.md` with all citations; include a `⚠️ PAGE-DISCREPANCY` + `⚠️ MVP structural refactor` + `⚠️ Redundancy detected` summary at top.
- Push to `review_course`.

### step[4] — review_course verifies and emits verdict

- Check 1:1 PDF citations (re-open PDF, locate citation, read).
- Check honest acknowledging (gaps marked, no fabrication).
- Check page-map offset pattern applied correctly.
- Emit `verdict.md` with:
  - `✅ PASS N/N` or `⚠️ WARN` or `✗ FAIL`
  - Per-question table (Q | Topic | status | notes)
  - **Worker 主动识别要点** section
  - **MVP vs PDF discrepancies** section if any
  - **page_discrepancy** table if any
  - **Lessons** section
- Send to `manager`.

### step[5] — manager dispatches Feishu doc append (worker_builder)

- On PASS / WARN verdict, manager dispatches `worker_builder` with:
  - verdict.md / answer.md / questions.md paths
  - Append position (subject N, after subject N-1)
  - Focus items (e.g. "5 PDF gaps + page_discrepancy table")

### step[6] — worker_builder appends 4-section Feishu section

- Re-format into 4 sections:
  1. **统计总览** — table: 题目数 / 子题数 / ✓ correct / ✗ / hallucination risk / PDF gaps / page_discrepancy
  2. **20 题逐项验证** — each Q with 题号 / 题目 / 答案 / 验证 ✓/✗ / 源 PDF 页码
  3. **Worker 表现评估** — table: 源对齐 / 缺口诚实 / 跨题引用 / MVP vs PDF 处置 / 综合评级
  4. **Review self-critique** — page-map offset summary / PDF gaps list / lessons
- Append via `lark-cli docs +update --doc ArZJd17OyoUlK3xsFmRcIK0EnAe --markdown @<section>.md --as bot --mode append`.
- Verify length grew by expected amount via `lark-cli docs +fetch --as bot`.

### step[7] — PDF gap supplementation (when worker_syllabus flags N gaps)

3 options (manager decides per gap):

| Option | Owner | Deliverable |
|--------|-------|-------------|
| A — Write `supplements.md` | `worker_course` | One supplements file per subject gap class; referenced in section as "see supplements.md §X" |
| B — Find alternative source | `worker_course` or `worker_builder` | Cross-check with prior syllabus version / textbook / CAIE FAQ |
| C — Mark known gap | `worker_syllabus` + `review_course` | Recorded in section's Review self-critique as known limitation |

Rule: never let a gap stall the workflow. If A or B is expensive, default to C and continue.

### step[8] — 5-min cadence (hard constraint, applies to ALL roles)

- Manager → boss: every 5 min, even with no new progress, send `5 min 无新进展` to chat (per boss's standing rule).
- worker_syllabus → review_course: every 5 min, send progress signal (`已答 N 题 / 待 review`).
- review_course → manager: every 5 min, send verdict-progress signal.
- worker_builder → manager + chat: every 5 min during Feishu append, send progress.

If a role misses 2 consecutive 5-min windows, the watchdog escalates. **Two KQA rounds missed cadence in the 2026-07-03 sprint — don't repeat.**

- **NEW (v2.4.1) `per_level_budget` (refined)** — total sprint time budget per **level × subject type** (the 5-min cadence is the inner heartbeat, this is the outer total). v2.4.1 adds the A-Level cycle budget based on Math 9709 evidence (~50 min actual):
  | Level × Type | Total budget | 2-stage? | Reasoning (refined v2.4.1 with A-Level Math 9709 evidence) |
  |---|---|---|---|
  | **IGCSE 1-stage clean** (Math 0580 / Physics 0625 / Economics 0455) | **10-15 min** | No | Formula strict 1:1 cite; minimal PDF-gap; page-map accurate. Math 0580 = 10 min (cleanest). Economics 0455 = 11 min (fastest of new subjects). |
  | **IGCSE standard** (Biology / Business / Psychology / Add Math / CS) | **25-30 min** | Optional | PDF-gap common; experiments explicit; topic cross-references needed. |
  | **IGCSE 2-stage** (Chinese 0509 / History 0470) | **25-45 min** | **Yes** | autopromote_2_stage triggered by 双 source 缺 or 严重 page_map_incomplete. Chinese = 25 min (Stage 1 10 + Stage 2 13). History = 45 min (Stage 1 25 + Stage 2 20). |
  | **A-Level 2-stage (default)** (Math 9709 / Econ 9708 / Phys 9702 / future) | **45-65 min** (3-run avg ~53 min) | **Yes (default)** | **autopromote_default_for_alevel** per v2.4.1. Page-map extraction difficulty (Math 9709: -36 delta most severe; Econ 9708: -6 delta + T4 GAP; Phys 9702: -15 + 11 T gaps all extraction artifacts per t_gap_decode). 3-run evidence: Math 9709 = 50 min (Stage 1 30 + Stage 2 20), Econ 9708 = 50 min (Stage 1 25 + Stage 2 25), Phys 9702 = 60 min (Stage 1 25 + Stage 2 30, LARGEST). Average = 53 min, range 50-65 min. |
  | **A-Level 1-stage (cleanest)** | ~15 min (predicted) | No | Reserved for subjects with well-structured PDF + page-map accurate (none observed in 2026-07-04 sprint, but possible). |
  If a sprint exceeds 1.5× the budget, manager should escalate to boss (`5 min cadence budget overrun` card) and decide whether to dispatch worker_builder help or accept overrun.

### step[9] — Pause / resume handling (Chemistry 0620 lesson)

When a worker pauses (review reads "QA 暂停" directive), the workflow must:

1. **Verify the pause scope explicitly** — read the boss directive in `manager` workspace; check if the current subject is in the suspension list.
2. **Common false-positive pattern**: review reads a global "暂停 KQA" as covering all subjects when it only covered the original 2 (Math 0580 / Physics 0625 in the 2026-07-03 case).
3. **If uncertain, dispatch worker_builder to do a runtime switch + reidentify** to flush the pause-misjudgment state, then resume.
4. **Always log the pause verification** to the audit log so the next sprint knows what to check.

### step[10] — Lessons distillation (closes the loop)

After every subject PASS:

- worker_builder appends to Feishu doc **§四 Review self-critique** with new lessons.
- worker_builder writes `eduflow remember worker_builder learning "repeat_work::igcse_kqa::<lesson>"` for high-value cross-subject lessons.
- luke_recorder captures cross-team lessons (manager misjudgment, worker dispatch patterns).

If 3+ subjects share the same lesson, **promote to a SKILL update** — edit this file or the sibling `review-syllabus-skill`.

## MVP validator pre-flight script (spec)

The future `scripts/mvp_validator.py` should accept a `bundle_path` and:

```python
def preflight(bundle_path):
    si = read(f"{bundle_path}/source-index.md")
    pm = read(f"{bundle_path}/page-map.json")
    pdf_year, pdf_pages = parse(si)
    topics = parse(pm)
    pattern = detect_pattern(pdf_year, pdf_pages, topics, manager_expected)
    return {
        "pdf_version": pdf_year,
        "pdf_pages": pdf_pages,
        "topic_count": len(topics),
        "pattern": pattern,
        "advice": advice_for(pattern)
    }
```

Patterns → advice map:

| Pattern | Advice |
|---------|--------|
| `chemistry_minus_2` | Real Subject Topic 1 = page-map t003. MVP N = PDF N+1. |
| `biology_plus_2` | Real Subject Topic 1-2 are short, occupy t001/t002. MVP N = PDF N+2. |
| `reprint_1_to_4_pages` | Verify every printed_page, do not trust page-map numbers. |
| `version_mismatch` | Halt. Notify manager. Worker answers PDF actual, not MVP. Mark `⚠️ MVP 错误` per affected Q. |
| `topic_deletion` | Check the question against PDF; mark `n/a` if the topic was removed. |
| `page_map_incomplete` | Read PDF directly to recover missing topics. |

## Cadence + escalation rules

| Event | Action | Owner |
|-------|--------|-------|
| 5 min no progress | Send "无新进展" line | each role |
| 10 min no progress + worker stuck | `send manager` BLOCKED signal | worker |
| Version mismatch detected | Halt questions.md write; escalate | review_course → manager |
| PDF gap can't be filled by A/B/C | Mark known gap, continue | review_course |
| worker pause misjudgment | Verify scope, runtime respawn if needed | worker_builder |
| Feishu doc append fails | Use `--api-version v2` flag; if still fails, write section.md to `pilot-output/assessment-skills/<bundle>/feishu-section.md` as fallback | worker_builder |

## Inputs

- `bundle_path` — path to `pilot-output/assessment-skills/caie-igcse-<subject>-<code>/`
- `manager_expected` — `{year: "2025-2026", pages: 60}` from dispatch message
- `qa_batch_dir` — `.eduflow-team-state/agents/review_course/qa-batch/T-IGCSE-KQA/<subject>_<code>/`

## Outputs

1. `questions.md` (after step[1] pre-flight)
2. `answer.md` (after step[3])
3. `verdict.md` (after step[4])
4. Feishu doc section appended (after step[6])
5. `supplements.md` (per gap, step[7] Option A only)
6. Lessons entries in `eduflow remember` (step[10])

## References (2026-07-03 to 2026-07-04 sprint — 11 学科 全闭环)

**2026-07-03 5-subject sprint (initial v2 baseline)**:
- Math 0580 — clean PASS, no known issues, 36/36 ✓ (10 min, fastest clean 1-stage)
- Physics 0625 — Topic 5/6 (Nuclear/Space) NOT covered (卷长); worker主动识别 review Q1 笔误 5/6→6/7; 39/39 ✓
- Chemistry 0620 — 6 PDF gaps (Q4a/Q2b/Q9b/Q14a/Q16b/Q17a) + page-map -2 (preface 占用 t001/t002); pause misjudgment root cause; 37/37 ✓
- Biology 0610 — 5 PDF gaps + page-map +2 (preface + 2 short topics); MVP 占位符全部 20 题替换为 PDF actual; 40/40 ✓ (30 min)
- Business 0450 — MAJOR version mismatch (PDF 2026 v2 32p vs MVP 2023 reprint 70p); 2 papers + 4 AOs vs MVP 5 + 3; PED 不考; 4 production types → 3; 40/40 ✓ (按 PDF actual, 30 min)

**2026-07-03 expansion (v2.1 / v2.2 trigger data)**:
- Psychology 0266 REDO — 16/20 strict PASS + 4/20 known issue (standard 知识补); 双重 pattern 验证 (biology_plus_2 + page_map_incomplete); workflow v2 试水; 15 min
- Add Math 0606 — 13/20 strict + 7/20 known issue + Q20b MVP catch (2 AOs vs 3); 3 pattern 验证 (chemistry_minus_2 + version_mismatch + page_map_incomplete); new pattern depth_incomplete (数学科) + formula_table_1to1; 14 topics vs MVP 12, A*-E vs MVP A*-G; 10 min
- CS 0478 — 13 strict + 6 known + 1 major MVP error Q8 Ethics; 9 worker catches 史上最高 (file name misleading + 10 topics vs 8 + Q7 实际位置 T5.3 + AOs 3 vs 2 + papers 1h45min vs 1h15min + SQL 6 cmd vs 5+ + sort 仅 bubble+linear); do_not_speculate_rule 救场; 18 min
- Chinese 0509 — 20/20 strict + 0 缺口 + 0 MVP error (cleanest sprint, 11 学科首 个 perfect); 2-stage workflow (Stage 1 10 min + Stage 2 13 min); autopromote_2_stage 第 1 activation; 25 min
- History 0470 — 20/20 strict + 0 缺口 + 0 MVP error (clean sprint 第 2 个); 2-stage workflow (Stage 1 25 min + Stage 2 20 min); autopromote_2_stage 第 2 activation; 11 学科最长 PDF 42p + 最长闭环 45 min; new pattern history_syllabus_3_components_complexity (3 components + 3 AOs + Paper 2 source investigation + Component 3 vs Paper 4 二选一); 4 worker catches (17 sub-units / 3 components / 3 AOs / A*-G)

**2026-07-04 final sprint (v2.3 闭环 + v2.4 consolidation trigger data)**:
- **Economics 0455** — 20/20 strict + 0 缺口 + 7 MVP errors caught (PDF version misleading 2025-2026 vs 2023-2025 + 6 topics not 4 + 2 papers not 5 + 3 AOs 40/40/20 + no Core/Extended + AO3 per component P1 0%/P2 30% + A*-G); 1-stage workflow; ~11 min **fastest of 11 学科**; trigger data for v2.4 (topic_count_delta >= 3 autopromote + source_index_metadata_misleading + per-subject AO lookup table + AOs cross-subject 不能类比)

**Feishu doc** `ArZJd17OyoUlK3xsFmRcIK0EnAe` — single source of truth, **14 subjects appended (11 IGCSE + 3 A-Level), 272,698 chars** (after Phys 9702 A-Level, 2026-07-04 13:35). lark-cli v2 API: `docs +update --doc <id> --command append --doc-format markdown --content @<file>.md --as bot`.

**14 学科 cadence final (IGCSE 11 + A-Level 3)**:
- Math 0580: 10 min (clean 1-stage)
- Add Math 0606: 10 min (math-skill heavy, 1-stage depth_incomplete)
- Economics 0455: ~11 min (1-stage topic_count_delta, fastest of new IGCSE subjects)
- Psychology 0266 REDO: 15 min (biology_plus_2 + page_map_incomplete)
- CS 0478: 18 min (page_map_incomplete 实读, do_not_speculate)
- Chinese 0509: 25 min (IGCSE 2-stage, autopromote 第 1 activation)
- Biology 0610 / Business 0450: 30 min (long content / MAJOR version mismatch)
- History 0470: 45 min (IGCSE 2-stage, autopromote 第 2 activation, IGCSE longest)
- Chemistry 0620 / Physics 0625: (早期, time 不精测)
- **Math 9709 (A-Level): ~50 min** (Stage 1 30 + Stage 2 20, page_map -36 most severe ever)
- **Econ 9708 (A-Level): ~50 min** (Stage 1 25 + Stage 2 25, T4 missing extraction artifact decode)
- **Phys 9702 (A-Level): ~60 min** (Stage 1 25 + Stage 2 30, t_gap_decode 11 gaps verified, LARGEST of 14 学科)

**v2.4.3 expansion candidates (Phys 9702 + 3 A-Level runs aggregate)**:
- `t_gap_decode_recipe` confirm (3 A-Level runs: Math 9709 -36 / Econ 9708 -6 / Phys 9702 -13, 11 T gaps ALL extraction artifacts per occam's razor)
- §aleval_phys_practical_focus marker (5 papers 含 2 practical P3+P5, AO3 100% practical)
- Data booklet per-paper verify (Math MF19 all / Econ NO / Phys P1+P2+P4 only, NOT P3/P5)
- AO3 100% on practical eval pattern (cross-subject AO3 distribution varies)
- A-Level cycle cadence refined (Math 50 / Econ 50 / Phys 60, 3-run avg ~53 min)

**v2.4.1 expansion candidates (Math 9709 A-Level cycle)**:
- `alevel_cycle_features` marker (2-year / multi-paper / MF19 / A*-E+a-e)
- `autopromote_default_for_alevel` (取代 v2.3 conditional trigger)
- A-Level Grade scale table (A*-E A Level + a-e AS Level + UMS 0-100)
- per-level budget table (IGCSE 1-stage 10-15 / IGCSE standard 25-30 / IGCSE 2-stage 25-45 / A-Level 2-stage 45-60 / A-Level 1-stage ~15 predicted)