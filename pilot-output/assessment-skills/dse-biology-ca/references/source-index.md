# Source Index

> Source evidence bundle for the DSE Biology Curriculum and Assessment Guide.

## Source Identity

- source_id: `primary_syllabus`
- title: 生物課程及評估指引 (中四至中六)
- assessment_identity:
  - assessment_type: `syllabus`
  - system: `DSE`
  - board_or_owner: `HKEAA/CDI`
  - subject: `Biology`
  - level: `Senior Secondary (S4-S6)`
  - assessment_code: `DSE-BIO`
  - valid_from: `2007`
  - valid_to: `(updated November 2015, ongoing)`
- source_document_type: `course_and_assessment_guide`
- source_layout_profile: `dse_curriculum_assessment_guide`
- source_format: `pdf`
- official_url: `https://www.hkeaa.edu.hk/tc/hkdse/assessment/assessment_framework/`
- local_archive_ref: `/Users/huanganan/Desktop/未命名文件夾/生物課程評估及指引.pdf`
- file_checksum_sha256: `c87a62cecaeb07ff599615bd46972b76c480b3778d981bd4d77527cdb64712d1`
- document_version: `2007 (updated November 2015)`
- retrieved_at: `2026-06-30`
- extracted_at: `2026-06-30`
- extracted_by: `worker_syllabus`
- extraction_tool: `pdftotext`
- extraction_method: `structured_extract`
- total_pages: 113

## PDF Identity Check

- pdfinfo_pages: 113
- pdfinfo_title: `Microsoft Word - Bio CA Guide_c_20151102_edit`
- pdf_encrypted: no
- pdf_copy_allowed: yes
- pdf_print_allowed: yes
- scan_or_ocr_status: native digital PDF (PScript5.dll / Acrobat Distiller)
- local_filename_year_check: `not_applicable` (filename does not include a year)
- identity_conflicts: none

## Page Reference Convention

- human_page_refs: `printed_page`
- rendered_page_refs: `physical_page`
- known_offsets:
  - Front matter uses Roman numerals; body pages use Arabic numerals.
  - Body pages: `printed_page = physical_page - 8` (physical page 9 = printed page 1).
  - Printed page `i` is physical page 7; printed page `ii` is physical page 8.
- example_mapping:
  - printed_page_ref: `p.1`
    physical_page: 9
    rendered_file: `source-review/rendered-pages/physical-page-009.png`
  - printed_page_ref: `p.8`
    physical_page: 16
    rendered_file: `source-review/rendered-pages/physical-page-016.png`
  - printed_page_ref: `p.80`
    physical_page: 88
    rendered_file: `source-review/rendered-pages/physical-page-088.png`

## Section Map

| section | page_refs | extracted | notes |
| --- | --- | --- | --- |
| Title page | physical 1 | no | Identity only |
| Contents | physical 3-5 | no | TOC verification |
| Chapter 1 Introduction | p.1-4 (physical 9-12) | no | Rationale and aims; not assessable content |
| Chapter 2 Curriculum Framework | p.5-35 (physical 13-43) | yes | Compulsory and elective topics, learning outcomes |
| 2.1 Design principles | p.5-7 (physical 13-15) | no | Pedagogical background |
| 2.2 Learning objectives | p.6-7 (physical 14-15) | partial | Used for AO mapping only |
| 2.3 Structure and organisation | p.7-35 (physical 15-43) | yes | Topic list, hours, topic detail tables |
| Scientific inquiry emphasis | p.12 (physical 20) | partial | Cross-cutting skill, not a topic |
| Compulsory Part I: Cells and Molecules | p.13-15 (physical 21-23) | yes | Subtopics a-e |
| Compulsory Part II: Heredity and Evolution | p.20-21 (physical 28-29) | yes | Subtopics a-c |
| Compulsory Part III: Organisms and Environment | p.25-30 (physical 33-38) | yes | Subtopics a-f |
| Compulsory Part IV: Health and Disease | p.33-34 (physical 41-42) | yes | Subtopics a-c |
| Elective Part V: Human Physiology: Regulation and Control | p.37-38 (physical 45-46) | yes | Subtopics a-d |
| Elective Part VI: Applied Ecology | p.42-43 (physical 50-51) | yes | Subtopics a-d |
| Elective Part VII: Microbes and Humans | p.47-48 (physical 55-56) | yes | Subtopics a-d |
| Elective Part VIII: Bioengineering | p.51 (physical 59) | yes | Subtopics a-c |
| Chapter 3 Curriculum Planning | p.53-62 (physical 61-70) | no | School planning guidance |
| Chapter 4 Learning and Teaching | p.63-78 (physical 71-86) | no | Pedagogy; not assessable scope |
| Chapter 5 Assessment | p.75-82 (physical 83-90) | yes | Assessment framework, public exam, SBA |
| 5.1-5.2 Role of assessment | p.75-76 (physical 83-84) | no | General assessment principles |
| 5.3 Assessment objectives | p.76-77 (physical 84-85) | yes | AO descriptions |
| 5.4 School-based assessment | p.77-78 (physical 85-87) | no | School-level guidance |
| 5.5 Public assessment | p.79-82 (physical 87-90) | yes | Paper 1, Paper 2, SBA, grading |
| Chapter 6 Learning and Teaching Resources | p.83-88 (physical 91-96) | no | Resources and references |
| Appendix 1 Timetabling | p.89-92 (physical 97-100) | no | Admin guidance |
| Appendix 2 EDB resources | p.93 (physical 101) | no | Resource list |
| Glossary | p.95-97 (physical 103-105) | no | General education terms |
| References / Committee lists | p.98-104 (physical 106-113) | no | Bibliography and membership |

## Extraction Notes

- Extracted topic structure and assessment framework from Chapter 2 and Chapter 5.
- Learning outcome tables were summarised as scope bullets; no full official text copied.
- Assessment design (Paper 1 / Paper 2 / SBA weightings and durations) taken from p.80.
- Front matter and administrative chapters excluded from assessable scope.
- Elective part requires students to answer 2 of the 4 elective topics in Paper 2.

## Risks

- `extraction_confidence` is `medium` because the same agent performed extraction and review.
- `dual_pass_checked=false`; independent reviewer still required before `active` status.
- Rendered high-impact pages not created in this run; visual review pending.
- Printed/footer page numbers are present in the digital PDF and align with offset +8 for body pages.
- The source was last updated in November 2015; users should cross-check current HKEAA assessment framework for any subsequent amendments.

## Reuse Key

- source_id + document_version + file_checksum_sha256
- `primary_syllabus` + `2007 (updated November 2015)` + `c87a62cecaeb07ff599615bd46972b76c480b3778d981bd4d77527cdb64712d1`
