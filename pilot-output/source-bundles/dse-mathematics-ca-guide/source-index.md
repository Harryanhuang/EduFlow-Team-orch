# Source Index

> Source evidence bundle for DSE Mathematics Curriculum and Assessment Guide.

## Source Identity

- source_id: `dse-mathematics-ca-guide`
- title: 數學課程及評估指引（中四至中六）
- assessment_identity:
  - assessment_type: `syllabus`
  - system: `DSE`
  - board_or_owner: `HKEAA/CDI`
  - subject: `Mathematics`
  - level: `Senior Secondary (S4-S6)`
  - assessment_code: `DSE-MATH`
  - valid_from: `2007`
  - valid_to: `(updated 2017, ongoing)`
- source_document_type: `course_and_assessment_guide`
- source_layout_profile: `dse_curriculum_assessment_guide`
- source_format: `pdf`
- official_url: `https://www.hkeaa.edu.hk/tc/hkdse/assessment/assessment_framework/`
- local_archive_ref: `/Users/huanganan/Desktop/未命名文件夹/数学课程评估及指引.pdf`
- file_checksum_sha256: `4f587886cb2ed64d4917db5cfa72c0556fc18ad5a98847c17337406363ae086f`
- document_version: `2007 (updated December 2017)`
- retrieved_at: `2026-06-30`
- extracted_at: `2026-06-30`
- extracted_by: `worker_syllabus`
- extraction_tool: `pdftotext`
- extraction_method: `structured_extract`
- total_pages: `140`

## PDF Identity Check

- pdfinfo_pages: `140`
- pdfinfo_title: `數學教育學習領域`
- pdf_creator: `Microsoft® Word 2013`
- pdf_creation_date: `2018-01-25`
- pdf_mod_date: `2018-02-02`
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
  - `printed_page = physical_page - 6` for numbered body pages (Chapter 1 onwards)
  - Front matter: physical 5 = printed i, physical 6 = printed ii
- example_mapping:
  - printed_page_ref: `p.12`
    physical_page: `18`
    rendered_file: `physical-page-018.png`
  - printed_page_ref: `p.33`
    physical_page: `39`
    rendered_file: `physical-page-039.png`
  - printed_page_ref: `p.93`
    physical_page: `99`
    rendered_file: `physical-page-099.png`

## Section Map

| section | page_refs | extracted | notes |
| --- | --- | --- | --- |
| Title page / copyright | physical 1 | admin | Source identity only |
| Table of contents | physical 3-4 | yes | Section outline verified |
| Introduction | physical 5-6 (print i-ii) | admin | Programme rationale |
| Chapter 1: Overview | physical 7-9 (print 1-3) | admin | Background, rationale, progression |
| Chapter 2: Curriculum Framework | physical 11-67 (print 5-61) | yes | Aims, learning objectives, compulsory and extended modules |
| 2.5 Compulsory part | physical 18-38 (print 12-32) | yes | Three strands plus advanced learning unit |
| 2.6 Extended part (Module 1 / Module 2) | physical 39-67 (print 33-61) | yes | Two optional modules |
| Chapter 3: Curriculum Planning | physical 69-80 (print 63-74) | admin | Implementation guidance |
| Chapter 4: Learning and Teaching | physical 81-92 (print 75-86) | admin | Pedagogy, not assessable scope |
| Chapter 5: Assessment | physical 93-100 (print 87-94) | yes | Public exam design and grading |
| Chapter 6: Learning and Teaching Resources | physical 101-106 (print 95-100) | admin | Resource guidance |
| Appendix 1: Bibliography | physical 107-122 (print 101-116) | admin | References |
| Appendix 2: Useful websites | physical 116-122 (print 110-116) | admin | References |
| Glossary | physical 123-126 (print 117-120) | admin | Definitions |
| References | physical 127-130 (print 121-124) | admin | Bibliography |
| Committee lists | physical 131-140 (print 125-134) | admin | Not assessable |

## Extraction Notes

- Text extracted with `pdftotext -layout`.
- Source is a native digital PDF with selectable text; no OCR quality issues detected.
- Page numbers in body sections are explicit in the PDF footer; offset `physical - 6` verified against Chapter 1 start (physical 7 = printed 1) and assessment table (physical 99 = printed 93).
- Assessment design table (Paper 1 / Paper 2 / Module 1 / Module 2) captured from print p.93 (physical 99).
- Detailed exam rules (e.g. exact question distribution per paper, calculator policy details) are not in this guide; refer to annual HKEAA `Examination Regulations and Assessment Framework`.
- Advanced learning units (`進階應用`, `探索與研究`) are curriculum components but are not standard public-exam content topics; included as nodes but flagged accordingly.

## Risks

- `medium` extraction_confidence because extractor and reviewer are the same agent.
- Some content pages include tables with formula notation; `pdftotext` renders mathematical symbols as Unicode or placeholders, but learning-point text was readable.
- Printed/physical offset is consistent for body pages; roman-numbered front matter and blank pages are not used for scope refs.
- Rendered pages not produced in this run; visual review of high-impact tables pending.
- This guide states assessment design at a high level; exact paper item counts and detailed rules require the annual exam specification for independent verification.

## Reuse Key

- `dse-mathematics-ca-guide + 2007 (updated December 2017) + 4f587886cb2ed64d4917db5cfa72c0556fc18ad5a98847c17337406363ae086f`
