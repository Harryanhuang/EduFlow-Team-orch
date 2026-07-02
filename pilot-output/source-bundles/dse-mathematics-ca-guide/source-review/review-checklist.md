# Source Review Checklist

## Reviewer instructions

- Compare `source-index.md` against the local PDF archive.
- Verify page references using the printed/physical offset `printed_page = physical_page - 6`.
- Confirm no large passages of official text are copied.
- Sign `review-verdict.json` after completing this checklist.

## Identity checks

- [ ] PDF title page matches source identity: 數學課程及評估指引（中四至中六）.
- [ ] Assessment code `DSE-MATH`, system `DSE`, board/owner `HKEAA/CDI` are correct.
- [ ] Valid years `2007 (updated December 2017)` match the title page/version statement.
- [ ] File checksum `4f587886cb2ed64d4917db5cfa72c0556fc18ad5a98847c17337406363ae086f` matches local archive.
- [ ] Total pages `140` match `pdfinfo` output.

## Coverage checks

- [ ] All three compulsory strands are mapped in `page-map.json`.
- [ ] All compulsory learning units (1-18) are mapped.
- [ ] Module 1 (Calculus and Statistics) learning units are mapped.
- [ ] Module 2 (Algebra and Calculus) learning units are mapped.
- [ ] Advanced learning units are not misclassified as standard public-exam content.
- [ ] Assessment framework (Compulsory Paper 1, Paper 2; Module 1 paper; Module 2 paper) is captured with correct weightings and durations.
- [ ] Question styles (MCQ, short questions, long questions) are recorded.
- [ ] Admin/marketing/copyright sections are excluded from topic scope.

## Traceability checks

- [ ] Printed/physical page offset is verified on at least 3 sample pages (e.g. p.12=physical 18, p.33=physical 39, p.93=physical 99).
- [ ] Every topic scope statement in `topics.json` can be traced to a `page-map.json` entry.
- [ ] Assessment model values in `assessment.json` trace back to `p.93`.

## Risk review

- [ ] Extraction confidence `medium` is appropriate (same agent as extractor).
- [ ] `dual_pass_checked=false` and `review_status=not_reviewed` are correct before review.
- [ ] Any rendered pages required for high-impact sections have been created or waived.
- [ ] Known risks in `extraction-report.json` are acceptable or escalated.

## Verdict

- [ ] Pass: no blocking risks; set `review_status=reviewed`, `dual_pass_checked=true`, update `reuse_status`.
- [ ] Fail: document blocking risks and return to extractor.
- [ ] Conditional pass (P2 only): record issues and allow `validated` but not `active`.
