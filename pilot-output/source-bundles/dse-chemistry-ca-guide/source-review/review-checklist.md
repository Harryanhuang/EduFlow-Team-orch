# Source Review Checklist

## Reviewer instructions

- Compare `source-index.md` against the local PDF archive.
- Verify page references using the printed/physical offset `printed_page = physical_page - 7`.
- Confirm no large passages of official text are copied.
- Sign `review-verdict.json` after completing this checklist.

## Identity checks

- [ ] PDF title page matches source identity: 化學課程及評估指引 (中四至中六).
- [ ] Assessment code `DSE-CHEM`, system `DSE`, board/owner `HKEAA/CDI` are correct.
- [ ] Valid years `2007 (updated June 2018)` match the title page/version statement.
- [ ] File checksum `a26ede119879a91641224c049e6e9cd293517c0aba9151a47723ad409650e483` matches local archive.
- [ ] Total pages `159` match `pdfinfo` output.

## Coverage checks

- [ ] All 12 compulsory topics are mapped in `page-map.json`.
- [ ] All 3 elective topics are mapped and marked "choose 2 of 3".
- [ ] Topic 16 (Investigative Study) is not misclassified as public-exam content.
- [ ] Assessment framework (Paper 1, Paper 2, SBA) is captured with correct weightings and durations.
- [ ] Question styles (MCQ, short, structured, essay) are recorded.
- [ ] Admin/marketing/copyright sections are excluded from topic scope.

## Traceability checks

- [ ] Printed/physical page offset is verified on at least 3 sample pages (e.g. p.16=physical 23, p.63=physical 70, p.121=physical 128).
- [ ] Every topic scope statement in `topics.json` can be traced to a `page-map.json` entry.
- [ ] Assessment model values in `assessment.json` trace back to `p.121`.

## Risk review

- [ ] Extraction confidence `medium` is appropriate (same agent as extractor).
- [ ] `dual_pass_checked=false` and `review_status=not_reviewed` are correct before review.
- [ ] Any rendered pages required for high-impact sections have been created or waived.
- [ ] Known risks in `extraction-report.json` are acceptable or escalated.

## Verdict

- [ ] Pass: no blocking risks; set `review_status=reviewed`, `dual_pass_checked=true`, update `reuse_status`.
- [ ] Fail: document blocking risks and return to extractor.
- [ ] Conditional pass (P2 only): record issues and allow `validated` but not `active`.
