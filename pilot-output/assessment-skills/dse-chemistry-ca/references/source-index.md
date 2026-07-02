# Source Index

> Source evidence bundle for DSE Chemistry Curriculum and Assessment Guide.

## Source Identity

- source_id: `dse-chemistry-ca-guide`
- title: 化學課程及評估指引 (中四至中六)
- assessment_identity:
  - assessment_type: `syllabus`
  - system: `DSE`
  - board_or_owner: `HKEAA/CDI`
  - subject: `Chemistry`
  - level: `Senior Secondary (S4-S6)`
  - assessment_code: `DSE-CHEM`
  - valid_from: `2007`
  - valid_to: `(updated 2018, ongoing)`
- source_document_type: `course_and_assessment_guide`
- source_layout_profile: `dse_curriculum_assessment_guide`
- source_format: `pdf`
- official_url: `https://www.hkeaa.edu.hk/tc/hkdse/assessment/assessment_framework/`
- local_archive_ref: `/Users/huanganan/Desktop/未命名文件夹/化学课程评估及指引.pdf`
- file_checksum_sha256: `a26ede119879a91641224c049e6e9cd293517c0aba9151a47723ad409650e483`
- document_version: `2007 (updated June 2018)`
- retrieved_at: `2026-06-30`
- extracted_at: `2026-06-30`
- extracted_by: `worker_syllabus`
- extraction_tool: `pdftotext`
- extraction_method: `structured_extract`
- total_pages: `159`

## PDF Identity Check

- pdfinfo_pages: `159`
- pdfinfo_title: `(empty)`
- pdf_creator: `Microsoft® Word 2010`
- pdf_creation_date: `2018-08-29`
- pdf_mod_date: `2020-08-07`
- pdf_encrypted: `no`
- pdf_copy_allowed: `yes`
- pdf_print_allowed: `yes`
- scan_or_ocr_status: `native_digital_text`
- local_filename_year_check: `match`
- identity_conflicts: `none`

## Page Reference Convention

- human_page_refs: `printed_page`
- rendered_page_refs: `physical_page`
- known_offsets:
  - `printed_page = physical_page - 7` for numbered body pages
- example_mapping:
  - printed_page_ref: `p.115`
    physical_page: `122`
    rendered_file: `physical-page-122.png`
  - printed_page_ref: `p.121`
    physical_page: `128`
    rendered_file: `physical-page-128.png`

## Section Map

| section | page_refs | extracted | notes |
| --- | --- | --- | --- |
| Title page / copyright | physical 1 | admin | Source identity only |
| Table of contents | physical 2-4 | yes | Section outline verified |
| Introduction | physical 6-7 (print i-ii) | admin | Programme rationale |
| Chapter 1: Overview | physical 8-12 (print 1-5) | admin | Background, rationale, progression |
| Chapter 2: Curriculum Framework | physical 14-87 (print 7-80) | yes | Aims, learning objectives, 16 topics |
| Topic 1: Earth | physical 23-25 (print 16-18) | yes | Compulsory |
| Topic 2: Microscopic World I | physical 26-31 (print 19-24) | yes | Compulsory |
| Topic 3: Metals | physical 32-36 (print 25-29) | yes | Compulsory |
| Topic 4: Acids and Bases | physical 37-40 (print 30-33) | yes | Compulsory |
| Topic 5: Fossil Fuels and Carbon Compounds | physical 41-45 (print 34-38) | yes | Compulsory |
| Topic 6: Microscopic World II | physical 46-48 (print 39-41) | yes | Compulsory |
| Topic 7: Redox, Chemical Cells and Electrolysis | physical 49-53 (print 42-46) | yes | Compulsory |
| Topic 8: Chemical Reactions and Energy | physical 54-55 (print 47-48) | yes | Compulsory |
| Topic 9: Reaction Rate | physical 56-58 (print 49-51) | yes | Compulsory |
| Topic 10: Chemical Equilibrium | physical 59-61 (print 52-54) | yes | Compulsory |
| Topic 11: Chemistry of Carbon Compounds | physical 62-66 (print 55-59) | yes | Compulsory |
| Topic 12: Patterns in the Chemical World | physical 67-69 (print 60-62) | yes | Compulsory |
| Topic 13: Industrial Chemistry (elective) | physical 70-73 (print 63-66) | yes | Elective, choose 2 of 3 |
| Topic 14: Materials Chemistry (elective) | physical 74-78 (print 67-71) | yes | Elective, choose 2 of 3 |
| Topic 15: Analytical Chemistry (elective) | physical 79-84 (print 72-77) | yes | Elective, choose 2 of 3 |
| Topic 16: Investigative Study | physical 85-87 (print 78-80) | partial | SBA-related, not public-exam scope |
| Chapter 3: Curriculum Planning | physical 88-105 (print 81-98) | admin | Implementation guidance |
| Chapter 4: Learning and Teaching | physical 106-121 (print 99-114) | admin | Pedagogy, not assessable scope |
| Chapter 5: Assessment | physical 122-131 (print 115-124) | yes | Public exam design, SBA, grading |
| Chapter 6: Learning and Teaching Resources | physical 132-139 (print 125-132) | admin | Resource guidance |
| Appendix 1: Timetabling | physical 140-143 (print 133-136) | admin | School admin guidance |
| Appendix 2: Experimental Techniques | physical 144-145 (print 137-138) | yes | Skill links, not topic scope |
| Glossary | physical 146-149 (print 139-142) | admin | Definitions |
| References | physical 150-155 (print 143-148) | admin | Bibliography |
| Committee Lists | physical 156-159 (print 149-152) | admin | Not assessable |

## Extraction Notes

- Text extracted with `pdftotext -layout`.
- Source is a native digital PDF with selectable text; no OCR quality issues detected.
- Page numbers in body sections are explicit in the PDF footer; offset `physical - 7` verified against Chapter 1 start (physical 8 = printed 1).
- Assessment design table (Paper 1 / Paper 2 / SBA) captured from print p.121 (physical 128).
- Detailed exam rules (e.g. exact question distribution per paper, data booklet, formulae sheet) are not in this guide; refer to annual HKEAA `Examination Regulations and Assessment Framework`.
- Topic 16 (Investigative Study) is curriculum time but not a public-exam topic; it underpins SBA skills.

## Risks

- `medium` extraction_confidence because extractor and reviewer are the same agent.
- Some topic pages include tables with two-column layout; `pdftotext` may interleave lines, but key bullet content was readable.
- Printed/physical offset is consistent for body pages; roman-numbered front matter and blank pages are not used for scope refs.
- Rendered pages not produced in this run; visual review of high-impact tables pending.
- This guide states assessment design at a high level; exact paper item counts and tier/option rules require the annual exam specification for independent verification.

## Reuse Key

- `dse-chemistry-ca-guide + 2007 (updated June 2018) + a26ede119879a91641224c049e6e9cd293517c0aba9151a47723ad409650e483`
