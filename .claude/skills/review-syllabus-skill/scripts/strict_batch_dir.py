#!/usr/bin/env python3
"""Run review_strict_v2 on ALL packages in a directory (or specified list)."""
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from review_strict_v2 import review

if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("pilot-output/assessment-skills")
    out = []
    pkgs = sorted([p for p in root.iterdir() if p.is_dir() and (p / "metadata.json").exists()])
    print(f"Scanning {len(pkgs)} packages...")
    for p in pkgs:
        try:
            r = review(p)
            out.append(r)
        except Exception as e:
            print(f"⚠ {p.name}: error {e}")
            continue
    fail = sum(1 for r in out if r["overall"]=="fail")
    warn = sum(1 for r in out if r["overall"]=="warn")
    pas = sum(1 for r in out if r["overall"]=="pass")
    p0_a = [r["package"] for r in out if r["axes"]["A_pdf_identity"]["verdict"]=="fail"]
    p0_b = [r["package"] for r in out if r["axes"]["B_topic_match"]["verdict"]=="fail"]
    p0_c = [r["package"] for r in out if r["axes"]["C_ek_truth"]["verdict"]=="fail"]
    p0_d = [r["package"] for r in out if r["axes"]["D_assessment"]["verdict"]=="fail"]
    p1_warn = [r["package"] for r in out if r["overall"]=="warn"]
    print()
    print(f"=== SUMMARY: {len(out)} packages ===")
    print(f"  pass: {pas}  warn: {warn}  fail: {fail}")
    print(f"  A(PDF身份) fail: {len(p0_a)} → {p0_a[:10]}")
    print(f"  B(topic匹配) fail: {len(p0_b)} → {p0_b[:10]}")
    print(f"  C(EK真实性) fail: {len(p0_c)} → {p0_c[:10]}")
    print(f"  D(assessment) fail: {len(p0_d)} → {p0_d[:10]}")
    print(f"  P1-only (warn): {len(p1_warn)}")

    # Top 10 worst
    worst = sorted(out, key=lambda r: (
        {"fail":3,"warn":2,"pass":1}[r["overall"]],
        -len(r["deviations"])
    ), reverse=True)[:10]
    print(f"\n=== TOP 10 WORST ===")
    for r in worst:
        print(f"  {r['overall']:<5} {r['package']:<45} deviations={len(r['deviations'])}")
        for d in r["deviations"][:2]:
            print(f"    [{d['severity']}] {d['field']}: {d['issue'][:80]}")

    summary_path = Path("strict-review-summary.json")
    summary_path.write_text(json.dumps({
        "results": out,
        "summary": {
            "total": len(out), "pass": pas, "warn": warn, "fail": fail,
            "axis_A_pdf_identity_fail": len(p0_a),
            "axis_B_topic_match_fail": len(p0_b),
            "axis_C_ek_truth_fail": len(p0_c),
            "axis_D_assessment_fail": len(p0_d),
            "p1_only_warn_count": len(p1_warn),
            "p0_pdf_identity_packages": p0_a,
            "p0_topic_match_packages": p0_b,
            "p0_ek_truth_packages": p0_c,
            "p0_assessment_packages": p0_d,
            "top10_worst": [{"pkg": r["package"], "overall": r["overall"],
                            "deviations": len(r["deviations"])} for r in worst],
        }
    }, indent=2, ensure_ascii=False))
    print(f"\nWritten: {summary_path}")