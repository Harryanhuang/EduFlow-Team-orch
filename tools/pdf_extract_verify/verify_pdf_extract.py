#!/usr/bin/env python3
"""T-68: verify PyMuPDF can extract CID-encoded CAIE QP PDFs across seasons.

Picks 5 representative CAIE QP PDFs (2021-2025), extracts text via fitz,
and reports (pages, chars, Q-N count, mojibake ratio). Worker_qbank T-67
reported pdftotext produces mojibake on 2020-2023 + 2025 season PDFs;
this script proves PyMuPDF (fitz) sidesteps that.

Pure stdlib + PyMuPDF. Stdout format is markdown-friendly for piping
into verify_pdf_extract_report.md.

Usage:
  python3 verify_pdf_extract.py [--pdf <path> ...]

With no args, uses the 5 sample PDFs hard-coded below (sourced from
the Findclass / CAIE missing_pair mirror).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.stderr.write(
        "FATAL: PyMuPDF (fitz) not importable. Run: pip install PyMuPDF\n"
    )
    sys.exit(2)


# Sample set: CAIE QP PDFs across seasons. All are paper 2 (qp_22) for
# apples-to-apples comparison. 2024 is included as the "known-good"
# control (worker_qbank T-67 extracted these successfully with pdftotext).
DEFAULT_SAMPLES: list[tuple[str, str]] = [
    (
        "2021",
        "/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-Findclass 小程序/"
        "04-Findclass导入与原始卷资源/findclass_importer/replenishment_downloads/"
        "missing_pair_caie/0610_w21_qp_22.pdf",
    ),
    (
        "2022",
        "/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-Findclass 小程序/"
        "04-Findclass导入与原始卷资源/findclass_importer/replenishment_downloads/"
        "missing_pair_caie/0460_s22_qp_22.pdf",
    ),
    (
        "2023",
        "/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-Findclass 小程序/"
        "04-Findclass导入与原始卷资源/findclass_importer/replenishment_downloads/"
        "missing_pair_caie/0460_w23_qp_22.pdf",
    ),
    (
        "2024",
        "/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-Findclass 小程序/"
        "04-Findclass导入与原始卷资源/findclass_importer/replenishment_downloads/"
        "missing_pair_caie/0460_m24_qp_22.pdf",
    ),
    (
        "2025",
        "/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-Findclass 小程序/"
        "04-Findclass导入与原始卷资源/findclass_importer/replenishment_downloads/"
        "missing_pair_caie/0580_m25_qp_22.pdf",
    ),
]


# Heuristics for "mojibake / CID dump".
# A real PDF text dump should:
#   - have very few Unicode escape sequences (\uXXXX) — those are JSON-encoded
#     garbage that pdftotext emits when CID fonts aren't mapped.
#   - have plenty of printable ASCII letters (a-zA-Z).
#   - have plenty of whitespace (PDFs have lots of layout).
_RE_UNICODE_ESCAPE = re.compile(r"\\u[0-9a-fA-F]{4}")


def _count_questions(text: str) -> int:
    """Count distinct question markers at line starts.

    CAIE QPs use two main formats:
      - Paper 1 / MCQ: lines like ``Q1``, ``Q2`` ... possibly with spaces
        (``Q 1``). Match ``(?m)^\\s*Q\\s*\\d{1,2}\\b``.
      - Paper 2 / structured: lines like ``1``, ``2`` ... on their own
        line, followed by the question body. Match
        ``(?m)^\\s*\\d{1,2}\\s*$`` (digit-only line).

    We return the union of distinct markers from both patterns, deduped
    by the digit value when possible.
    """
    q_pat = re.compile(r"(?m)^\s*Q\s*(\d{1,2})\b")
    digit_pat = re.compile(r"(?m)^\s*(\d{1,2})\s*$")
    digits: set[int] = set()
    for pat in (q_pat, digit_pat):
        for m in pat.finditer(text):
            digits.add(int(m.group(1)))
    return len(digits)


def _mojibake_score(text: str) -> tuple[float, int, int]:
    """Return (escape_ratio, ascii_letters, total_alpha).

    escape_ratio = count(\\uXXXX) / max(1, ascii_letters).
    Below 0.05 = readable. Above 0.20 = clearly CID-broken.
    """
    escapes = len(_RE_UNICODE_ESCAPE.findall(text))
    ascii_letters = sum(1 for c in text if c.isascii() and c.isalpha())
    ratio = escapes / max(1, ascii_letters)
    return ratio, escapes, ascii_letters


def extract_one(path: Path) -> dict:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "error": "file not found",
        }
    try:
        doc = fitz.open(str(path))
    except Exception as exc:  # pragma: no cover - surface any fitz error
        return {"path": str(path), "exists": True, "error": f"open: {exc}"}

    try:
        page_texts: list[str] = []
        for page in doc:
            page_texts.append(page.get_text("text"))
        full = "\n".join(page_texts)

        ratio, escapes, ascii_letters = _mojibake_score(full)
        q_count = _count_questions(full)

        return {
            "path": str(path),
            "exists": True,
            "pages": len(doc),
            "chars": len(full),
            "q_count": q_count,
            "mojibake_ratio": round(ratio, 4),
            "unicode_escapes": escapes,
            "ascii_letters": ascii_letters,
            "readable": ratio < 0.05 and q_count > 0,
            "first_200_chars": full[:200].replace("\n", " ⏎ "),
        }
    finally:
        doc.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--pdf",
        action="append",
        default=None,
        help="Override a season's PDF: --pdf SEASON=PATH (repeatable).",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of markdown.",
    )
    args = ap.parse_args(argv)

    samples = list(DEFAULT_SAMPLES)
    if args.pdf:
        for spec in args.pdf:
            if "=" not in spec:
                sys.stderr.write(f"--pdf expects SEASON=PATH, got {spec!r}\n")
                return 2
            season, path = spec.split("=", 1)
            samples.append((season, path))

    results = [(season, extract_one(Path(p))) for season, p in samples]

    if args.json:
        print(json.dumps([{"season": s, **r} for s, r in results], indent=2))
        return 0

    # Markdown report.
    print("# PyMuPDF PDF Extract Verification\n")
    print("Tool: PyMuPDF (fitz) " + fitz.__version__)
    print(f"Samples: {len(results)}\n")
    print(
        "| Season | Pages | Chars | Q-N found | Mojibake ratio "
        "| Unicode escapes | ASCII letters | Readable? |"
    )
    print(
        "|---|---:|---:|---:|---:|---:|---:|:---:|"
    )
    all_readable = True
    for season, r in results:
        if not r.get("exists"):
            print(f"| {season} | – | – | – | – | – | – | ❌ missing |")
            all_readable = False
            continue
        if "error" in r:
            print(f"| {season} | – | – | – | – | – | – | ❌ {r['error']} |")
            all_readable = False
            continue
        ok = r["readable"]
        if not ok:
            all_readable = False
        print(
            f"| {season} | {r['pages']} | {r['chars']} | {r['q_count']} "
            f"| {r['mojibake_ratio']:.4f} | {r['unicode_escapes']} "
            f"| {r['ascii_letters']} | {'✅' if ok else '❌'} |"
        )

    print("\n## Per-sample first 200 chars\n")
    for season, r in results:
        if "first_200_chars" in r:
            print(f"**{season}** — `{Path(r['path']).name}`")
            print()
            print("```")
            print(r["first_200_chars"])
            print("```")
            print()

    print("## Verdict\n")
    if all_readable:
        print(
            "**PASS** — All 5 PDFs readable via PyMuPDF: "
            "mojibake_ratio < 0.05 AND Q-N count > 0 per file. "
            "CID-encoded CAIE PDFs are extracted cleanly. "
            "PyMuPDF is fit for the worker_qbank PDF extraction pipeline."
        )
        return 0
    print(
        "**FAIL** — At least one sample unreadable. See table above. "
        "Investigate before adopting PyMuPDF."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())