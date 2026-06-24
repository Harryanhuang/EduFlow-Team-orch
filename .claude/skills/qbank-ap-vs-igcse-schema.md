---
name: qbank-ap-vs-igcse-schema
description: AP vs IGCSE QBank schema divergence reference. Covers directory layout, file format, difficulty codes, validation rules, and common mistakes when adapting one system's patterns to the other. Use when working across both AP and IGCSE subjects.
metadata:
  type: reference
  generated_by: worker_qbank
  date: 2026-06-24
---

# AP vs IGCSE QBank Schema Reference

## Directory Layout

| Aspect | IGCSE | AP |
|--------|-------|----|
| Root | `igcse-{subject}-{code}/` | `AP {Subject Name}/` |
| Question storage | `qa/`, `qa-question-level/`, `items/` (3 layers) | `02-题库/items/Unit N/` (1 layer) |
| File naming | `N.M-*.md` (multi-question) | `Ux.y.z-{F\|S\|C}.md` (one question per file) |
| Manifest | `qa-manifest.csv` | `qa-manifest.csv` |
| Self-check | N/A | `QA-自检.md` |

## File Format

| Aspect | IGCSE | AP |
|--------|-------|----|
| Format | Markdown with heading delimiters | Markdown with YAML frontmatter |
| Questions per file | Multiple (### or # headings) | One per file |
| Q-ID location | In heading: `### Question Q-x.y-zz` | In frontmatter: `id: Ux.y.z-S` |
| Difficulty | Full word: `Foundation`/`Standard`/`Challenge` | Short code: `F`/`S`/`C` |
| Required fields | `Difficulty`, `Question`, `Answer` | 15 YAML frontmatter keys |

## Q-ID Format

| System | Regex | Examples |
|--------|-------|----------|
| IGCSE | `^Q-[A-Z]?\d+(?:\.\d+)?-\d+$` | `Q-3.2-05`, `Q-A1-01` |
| AP | `^U\d+\.\d+\.\d+-[FSC]$` | `U4.2.1-S`, `U1.3.2-F` |

**Critical**: do NOT mix ID formats. An AP subject verifier will reject IGCSE Q-IDs and vice versa.

## Difficulty Mapping

| Concept | IGCSE | AP |
|---------|-------|----|
| Easy/Foundation | `Foundation` | `F` |
| Medium/Standard | `Standard` | `S` |
| Hard/Challenge | `Challenge` | `C` |

## Validation Differences

| Check | IGCSE | AP |
|-------|-------|----|
| Schema validation | Per-entity heading parse | Per-file YAML frontmatter |
| Required heading/keys | Difficulty + Q + A in entity | 15 YAML keys + 3 markdown headings |
| Cross-layer consistency | qa vs qql vs items count match | items count vs manifest count |
| Legacy fragment detection | Yes (`-s2`, `-round2`) | No (AP uses single layer) |
| Orphan detection | Yes (Q-ID unique to 1 layer) | No (single layer, no cross-reference) |
| Self-check document | N/A | `QA-自检.md` must be marked complete |
| Dedup needed | Yes (cross-layer) | Rare (single layer) |

## Common Mistakes When Crossing Systems

1. **Using IGCSE dedup on AP**: AP has 1 layer, so cross-layer dedup doesn't apply. Don't run content-hash dedup on AP subjects.

2. **Using AP frontmatter validation on IGCSE**: IGCSE files don't have YAML frontmatter. Use heading-based entity parsing instead.

3. **Mixing difficulty codes**: Writing `Foundation` in an AP file (should be `F`) or `S` in an IGCSE file (should be `Standard`).

4. **Assuming 3 layers exist for AP**: AP only has `items/`. Don't scan for `qa/` or `qa-question-level/` in AP directories.

5. **Applying IGCSE Q-ID regex to AP**: `U4.2.1-S` won't match `^Q-[A-Z]?\d+...`. Use the AP-specific regex `^U\d+\.\d+\.\d+-[FSC]$`.

## Verifier Scripts

| System | Script | Store Module |
|--------|--------|-------------|
| IGCSE | `scripts/qbank_verify.py` | N/A (standalone) |
| AP | `scripts/ap_qbank_verify.py` | `src/eduflow/store/ap_subject_verifier.py` |

## Related

- [[igcse-qbank-verification]] — IGCSE full verification flow
- [[ap-qbank-verification]] — AP full verification flow
- [[qbank-dedup-content-hash]] — dedup patterns (IGCSE-specific)
