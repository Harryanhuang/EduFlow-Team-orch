# PyMuPDF PDF Extract Verification

Tool: PyMuPDF (fitz) 1.27.2.3
Samples: 5

| Season | Pages | Chars | Q-N found | Mojibake ratio | Unicode escapes | ASCII letters | Readable? |
|---|---:|---:|---:|---:|---:|---:|:---:|
| 2021 | 16 | 14158 | 17 | 0.0000 | 0 | 10043 | ✅ |
| 2022 | 20 | 29975 | 37 | 0.0000 | 0 | 6243 | ✅ |
| 2023 | 16 | 29930 | 25 | 0.0000 | 0 | 5756 | ✅ |
| 2024 | 16 | 29824 | 23 | 0.0000 | 0 | 5944 | ✅ |
| 2025 | 20 | 16540 | 30 | 0.0000 | 0 | 7371 | ✅ |

## Per-sample first 200 chars

**2021** — `0610_w21_qp_22.pdf`

```
  ⏎   ⏎ This document has 16 pages.  ⏎ IB21 11_0610_22/4RP  ⏎   ⏎ © UCLES 2021  ⏎   ⏎ [Turn over ⏎   ⏎ *9188095747* ⏎ Cambridge IGCSE™  ⏎   ⏎   ⏎   ⏎ BIOLOGY  ⏎ 0610/22  ⏎   ⏎ Paper 2 Multiple Choice (Extended)  ⏎  October/November 2021
```

**2022** — `0460_s22_qp_22.pdf`

```
This document has 20 pages. Any blank pages are indicated. ⏎   ⏎ [Turn over ⏎ Cambridge IGCSE™ ⏎ DC (PQ/SG) 304190/4 ⏎ © UCLES 2022 ⏎ * 8 8 0 2 6 3 3 7 5 2 * ⏎ GEOGRAPHY  ⏎ 0460/22 ⏎ Paper 2 Geographical Skills  ⏎ May/Ju
```

**2023** — `0460_w23_qp_22.pdf`

```
This document has 16 pages. ⏎   ⏎ [Turn over ⏎ Cambridge IGCSE™ ⏎ * 7 4 7 1 8 0 2 4 5 0 * ⏎ GEOGRAPHY  ⏎ 0460/22 ⏎ Paper 2 Geographical Skills  ⏎ October/November 2023 ⏎   ⏎ 1 hour 30 minutes ⏎ You must answer on the quest
```

**2024** — `0460_m24_qp_22.pdf`

```
This document has 16 pages. ⏎   ⏎ [Turn over ⏎ Cambridge IGCSE™ ⏎ GEOGRAPHY  ⏎ 0460/22 ⏎ Paper 2 Geographical Skills  ⏎ February/March 2024 ⏎   ⏎ 1 hour 30 minutes ⏎ You must answer on the question paper. ⏎ You will need: 
```

**2025** — `0580_m25_qp_22.pdf`

```
This document has 20 pages. ⏎   ⏎ [Turn over ⏎ Cambridge IGCSE™ ⏎ * 6 8 3 3 7 8 8 8 7 2 * ⏎ MATHEMATICS  ⏎ 0580/22 ⏎ Paper 2 Non-calculator (Extended)  ⏎ February/March 2025 ⏎   ⏎ 2 hours ⏎ You must answer on the question 
```

## Verdict

**PASS** — All 5 PDFs readable via PyMuPDF: mojibake_ratio < 0.05 AND Q-N count > 0 per file. CID-encoded CAIE PDFs are extracted cleanly. PyMuPDF is fit for the worker_qbank PDF extraction pipeline.
