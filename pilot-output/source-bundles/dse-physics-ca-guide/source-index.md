# Source Index

> Source evidence bundle for DSE Physics Curriculum and Assessment Guide.

## Source Identity

- source_id: `dse-physics-ca-guide`
- title: 物理課程及評估指引 (中四至中六)
- assessment_identity:
  - assessment_type: `syllabus`
  - system: `DSE`
  - board_or_owner: `HKEAA/CDI`
  - subject: `Physics`
  - level: `Senior Secondary (S4-S6)`
  - assessment_code: `DSE-PHYS`
  - valid_from: `2007`
  - valid_to: `(updated 2015, ongoing)`
- source_document_type: `course_and_assessment_guide`
- source_layout_profile: `dse_curriculum_assessment_guide`
- source_format: `pdf`
- official_url: `https://www.hkeaa.edu.hk/tc/hkdse/assessment/assessment_framework/`
- local_archive_ref: `/Users/huanganan/Desktop/未命名文件夹/物理课程评估及指引.pdf`
- file_checksum_sha256: `613f053a4c10d7b8314b5c3d5083e8affccd39232c4589b74f98f88d486a2af0`
- document_version: `2007 (updated November 2015)`
- retrieved_at: `2026-06-30`
- extracted_at: `2026-06-30`
- extracted_by: `worker_syllabus`
- extraction_tool: `pdftotext`
- extraction_method: `structured_extract`
- total_pages: `150`

## PDF Identity Check

- pdfinfo_pages: `150`
- pdfinfo_title: `Microsoft Word - Phy C&A Guide_c_20151102_Clean.doc`
- pdf_creator: `PScript5.dll Version 5.2.2`
- pdf_creation_date: `2015-11-24`
- pdf_mod_date: `2015-11-24`
- pdf_encrypted: `no`
- pdf_copy_allowed: `yes`
- pdf_print_allowed: `yes`
- scan_or_ocr_status: `native_digital_text_with_font_encoding_issues`
- local_filename_year_check: `match`
- identity_conflicts: `none`

## Page Reference Convention

- human_page_refs: `printed_page`
- rendered_page_refs: `physical_page`
- known_offsets:
  - `printed_page = physical_page - 8` for numbered body pages
- example_mapping:
  - printed_page_ref: `p.17`
    physical_page: `25`
    rendered_file: `physical-page-025.png`
  - printed_page_ref: `p.74`
    physical_page: `82`
    rendered_file: `physical-page-082.png`
  - printed_page_ref: `p.103`
    physical_page: `111`
    rendered_file: `physical-page-111.png`

## Section Map

| section | page_refs | extracted | notes |
| --- | --- | --- | --- |
| Title page / copyright | physical 1 | admin | Source identity only |
| Table of contents | physical 3-5 | yes | Section outline verified |
| Foreword / preface | physical 6-7 (print i-ii) | admin | Programme rationale |
| Chapter 1: Overview | physical 14-20 (print 6-12) | admin | Background, rationale, progression |
| Chapter 2: Curriculum Framework | physical 21-78 (print 13-70) | yes | Aims, learning objectives, 9 topics |
| Topic I: Heat and Gases (compulsory) | physical 25-29 (print 17-21) | yes | 23 curriculum hours |
| Topic II: Force and Motion (compulsory) | physical 30-36 (print 22-28) | yes | 50 curriculum hours |
| Topic III: Wave Motion (compulsory) | physical 37-41 (print 29-33) | yes | 47 curriculum hours |
| Topic IV: Electricity and Magnetism (compulsory) | physical 42-47 (print 34-39) | yes | 48 curriculum hours |
| Topic V: Radioactivity and Nuclear Energy (compulsory) | physical 48-51 (print 40-43) | yes | 16 curriculum hours |
| Topic VI: Astronomy and Space Science (elective) | physical 52-58 (print 44-50) | yes | 25 curriculum hours |
| Topic VII: Atomic World (elective) | physical 59-64 (print 51-56) | yes | 25 curriculum hours |
| Topic VIII: Energy and Use of Energy (elective) | physical 65-71 (print 57-63) | yes | 25 curriculum hours |
| Topic IX: Medical Physics (elective) | physical 72-78 (print 64-70) | yes | 25 curriculum hours |
| Chapter 3: Assessment | physical 82-111 (print 74-103) | yes | Public exam design, SBA, grading |
| Chapter 4: Learning and Teaching | physical 112-128 (print 104-120) | admin | Pedagogy, not assessable scope |
| Chapter 5: Assessment Activities | physical 129-137 (print 121-129) | admin | SBA implementation guidance |
| Chapter 6: Appendices | physical 138-150 (print 130-142) | partial | References, resource lists |

## Extraction Notes

- Text extracted with `pdftotext -layout` from the provided extracted-text bundle.
- Source PDF uses embedded Chinese fonts with custom encoding; rendered glyphs are not mapped to standard Unicode, so most Chinese text appears as CID placeholders or tofu characters.
- Page numbers in body sections are explicit in the PDF footer; offset `physical - 8` verified against Chapter 1 start (physical 14 = printed 6) and assessment chapter (physical 82 = printed 74).
- Topic boundaries and curriculum-hour values were inferred from topic-heading pages where roman-numeral topic numbers and hour counts are readable as digits.
- Detailed learning outcomes and command-word lists could not be reliably transcribed from the garbled text; topic scope statements rely on publicly known DSE Physics curriculum structure and should be verified against a readable rendering.
- Assessment design table (Paper 1 / Paper 2 / SBA) is in Chapter 3 but exact numeric values are garbled; weightings and durations are filled from the well-known DSE Physics public-exam design and should be verified visually.

## Risks

- `medium` extraction_confidence because extractor and reviewer are the same agent.
- Native text extraction is severely degraded by custom font encoding; most Chinese content is unreadable in the extracted text.
- Topic scope statements and assessment numeric values are reconstructed from structure plus domain knowledge; independent visual review is strongly recommended.
- Printed/physical offset is consistent for body pages; roman-numbered front matter and blank pages are not used for scope refs.
- Rendered pages not produced in this run; visual review of high-impact tables pending.
- Exact paper item counts, question distribution, and formula-sheet policies require the annual HKEAA examination regulations for independent verification.

## Reuse Key

- `dse-physics-ca-guide + 2007 (updated November 2015) + 613f053a4c10d7b8314b5c3d5083e8affccd39232c4589b74f98f88d486a2af0`
