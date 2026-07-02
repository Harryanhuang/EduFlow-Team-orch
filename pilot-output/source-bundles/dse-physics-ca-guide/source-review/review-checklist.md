# Source Review Checklist

## Reviewer instructions

- Compare `source-index.md` against the local PDF archive.
- Verify page references using the printed/physical offset `printed_page = physical_page - 8`.
- Confirm no large passages of official text are copied.
- Sign `review-verdict.json` after completing this checklist.

## Identity checks

- [ ] PDF title page matches source identity: 物理課程及評估指引 (中四至中六).
- [ ] Assessment code `DSE-PHYS`, system `DSE`, board/owner `HKEAA/CDI` are correct.
- [ ] Valid years `2007 (updated November 2015)` match the title page/version statement.
- [ ] File checksum `613f053a4c10d7b8314b5c3d5083e8affccd39232c4589b74f98f88d486a2af0` matches local archive.
- [ ] Total pages `150` match `pdfinfo` output.

## Coverage checks

- [ ] All 5 compulsory topics (I-V) are mapped in `page-map.json`.
- [ ] All 4 elective topics (VI-IX) are mapped and marked "choose 2 of 4".
- [ ] Assessment framework (Paper 1, Paper 2, SBA) is captured with correct weightings and durations.
- [ ] Question styles (MCQ, short, structured, essay) are recorded.
- [ ] Admin/marketing/copyright sections are excluded from topic scope.

## Traceability checks

- [ ] Printed/physical page offset is verified on at least 3 sample pages (e.g. p.17=physical 25, p.74=physical 82, p.103=physical 111).
- [ ] Every topic scope statement in `topics.json` can be traced to a `page-map.json` entry.
- [ ] Assessment model values in `assessment.json` trace back to `p.74-78`.

## Risk review

- [ ] Extraction confidence `medium` is appropriate (same agent as extractor and font-encoding issues).
- [ ] `dual_pass_checked=false` and `review_status=not_reviewed` are correct before review.
- [ ] Any rendered pages required for high-impact sections have been created or waived.
- [ ] Known risks in `extraction-report.json` are acceptable or escalated.

## Verdict

- [ ] Pass: no blocking risks; set `review_status=reviewed`, `dual_pass_checked=true`, update `reuse_status`.
- [ ] Fail: document blocking risks and return to extractor.
- [ ] Conditional pass (P2 only): record issues and allow `validated` but not `active`.
