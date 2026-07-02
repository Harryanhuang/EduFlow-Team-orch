#!/usr/bin/env python3
"""Extract text and metadata from DSE curriculum and assessment guide PDFs."""
import json
import hashlib
import subprocess
from pathlib import Path
import pdfplumber

PDFS = {
    "chemistry": "/Users/huanganan/Desktop/未命名文件夹/化学课程评估及指引.pdf",
    "mathematics": "/Users/huanganan/Desktop/未命名文件夹/数学课程评估及指引.pdf",
    "physics": "/Users/huanganan/Desktop/未命名文件夹/物理课程评估及指引.pdf",
    "biology": "/Users/huanganan/Desktop/未命名文件夹/生物课程评估及指引.pdf",
}

OUT_ROOT = Path("pilot-output/source-bundles")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def pdfinfo(path: str) -> dict:
    result = subprocess.run(
        ["pdfinfo", path],
        capture_output=True, text=True, check=False,
    )
    info = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            info[k.strip()] = v.strip()
    return info


def extract_subject(subject: str, pdf_path: str):
    bundle_dir = OUT_ROOT / f"dse-{subject}-ca-guide"
    text_dir = bundle_dir / "extracted-text"
    text_dir.mkdir(parents=True, exist_ok=True)

    checksum = sha256(pdf_path)
    info = pdfinfo(pdf_path)
    pages = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            txt = page.extract_text() or ""
            page_file = text_dir / f"page-{i:03d}.txt"
            page_file.write_text(txt, encoding="utf-8")
            pages.append({
                "physical_page": i,
                "printed_page": None,
                "chars": len(txt),
                "first_200": txt[:200].replace("\n", " "),
            })

    manifest = {
        "schema_version": "1",
        "subject": subject,
        "local_archive_ref": pdf_path,
        "file_checksum_sha256": checksum,
        "pdfinfo": info,
        "total_pages": len(pages),
        "pages": pages,
    }
    (bundle_dir / "extract-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Extracted {subject}: {len(pages)} pages -> {bundle_dir}")


if __name__ == "__main__":
    for subject, pdf_path in PDFS.items():
        extract_subject(subject, pdf_path)
