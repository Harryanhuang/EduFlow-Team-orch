#!/usr/bin/env python3
"""review-syllabus-skill: batch reviewer across all packages in a directory.

Usage:
  python3 review_batch.py <root_dir>     # default: --json
  python3 review_batch.py <root_dir> --emit-verdict
  python3 review_batch.py <root_dir> --filter ap-   # only packages starting with ap-
"""
import argparse
import json
import sys
from pathlib import Path

# Make sibling importable
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from review_one import review

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--filter", default="")
    ap.add_argument("--emit-verdict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)
    if not root.exists():
        sys.exit(f"root not found: {root}")
    pkgs = sorted([p for p in root.iterdir() if p.is_dir() and (p / "metadata.json").exists()])
    if args.filter:
        pkgs = [p for p in pkgs if p.name.startswith(args.filter)]

    results = []
    for pkg in pkgs:
        r = review(pkg)
        results.append(r)
        if args.emit_verdict:
            from review_one import review as _r
            verdict_doc = {
                "schema_version": "1",
                "skill_id": r.get("skill_id"),
                "reviewer": "review-syllabus-skill",
                "reviewed_at": __import__("datetime").date.today().isoformat(),
                "verdict": r["verdict"],
                "findings": r["findings"],
                "summary": r["summary"],
            }
            (pkg / "review-verdict.json").write_text(json.dumps(verdict_doc, indent=2, ensure_ascii=False))
            (pkg / "review-checklist.json").write_text(json.dumps(r["findings"], indent=2, ensure_ascii=False))
        if not args.quiet:
            v = r["verdict"]
            tag = {"pass": "✓", "pass_with_risks": "△", "fail": "✗"}.get(v, "?")
            print(f"{tag} {pkg.name:<50} {v:<18} P0={r['summary']['P0']} P1={r['summary']['P1']} P2={r['summary']['P2']}")

    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r["verdict"] == "pass"),
        "pass_with_risks": sum(1 for r in results if r["verdict"] == "pass_with_risks"),
        "fail": sum(1 for r in results if r["verdict"] == "fail"),
        "p0_total": sum(r["summary"]["P0"] for r in results),
        "p1_total": sum(r["summary"]["P1"] for r in results),
        "p2_total": sum(r["summary"]["P2"] for r in results),
        "results": [
            {"package": r["package"], "skill_id": r.get("skill_id"), "verdict": r["verdict"], "summary": r["summary"]}
            for r in results
        ],
    }
    print()
    print(f"=== BATCH SUMMARY ===")
    print(f"  total: {summary['total']}  pass: {summary['pass']}  risks: {summary['pass_with_risks']}  fail: {summary['fail']}")
    print(f"  totals: P0={summary['p0_total']}  P1={summary['p1_total']}  P2={summary['p2_total']}")

    summary_path = root / "review-batch-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nWritten: {summary_path}")

if __name__ == "__main__":
    main()