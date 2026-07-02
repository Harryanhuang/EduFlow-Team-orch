#!/usr/bin/env python3
"""Run review_strict_v2 on a list of packages and emit summary."""
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from review_strict_v2 import review

# 16 high-risk packages (boss-specified)
HIGH_RISK = [
    "caie-alevel-biology-9700",
    "caie-alevel-physics-9702",
    "caie-alevel-mathematics-9709",
    "caie-igcse-biology-0610",
    "caie-igcse-physics-0625",
    "edexcel-ial-biology",
    "edexcel-ial-physics",
    "edexcel-ial-mathematics",
    "aqa-ial-biology-7402",
    "aqa-ial-physics-7408",
    "dse-biology",
    "dse-physics",
    "dse-mathematics",
    "dse-chemistry",
    "dse-biology-ca",
    "dse-physics-ca",
]

if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("pilot-output/assessment-skills")
    pkgs = sys.argv[2:] if len(sys.argv) > 2 else HIGH_RISK
    out = []
    for name in pkgs:
        p = root / name
        if not p.exists():
            print(f"⚠ {name}: package not found")
            continue
        r = review(p)
        out.append(r)
        a_short = r["axes"]["A_pdf_identity"]["notes"][:40]
        b_short = r["axes"]["B_topic_match"]["notes"][:60]
        c_short = r["axes"]["C_ek_truth"]["notes"][:60]
        print(f"{'✓' if r['overall']=='pass' else '⚠' if r['overall']=='warn' else '✗'} {name:<45} {r['overall']:<5}")
        if r['axes']['A_pdf_identity']['verdict'] != 'pass':
            print(f"   A: {a_short}")
        if r['axes']['B_topic_match']['verdict'] != 'pass':
            print(f"   B: {b_short}")
        if r['axes']['C_ek_truth']['verdict'] != 'pass':
            print(f"   C: {c_short}")
    # summary
    print()
    print(f"=== SUMMARY: {len(out)} packages ===")
    fail = sum(1 for r in out if r["overall"]=="fail")
    warn = sum(1 for r in out if r["overall"]=="warn")
    pas = sum(1 for r in out if r["overall"]=="pass")
    print(f"  pass: {pas}  warn: {warn}  fail: {fail}")
    p0_axis_a = sum(1 for r in out if r["axes"]["A_pdf_identity"]["verdict"]=="fail")
    p0_axis_b = sum(1 for r in out if r["axes"]["B_topic_match"]["verdict"]=="fail")
    p0_axis_c = sum(1 for r in out if r["axes"]["C_ek_truth"]["verdict"]=="fail")
    p0_axis_d = sum(1 for r in out if r["axes"]["D_assessment"]["verdict"]=="fail")
    print(f"  A(PDF身份) fail: {p0_axis_a}")
    print(f"  B(topic匹配) fail: {p0_axis_b}")
    print(f"  C(EK真实性) fail: {p0_axis_c}")
    print(f"  D(assessment) fail: {p0_axis_d}")
    # Save JSON
    summary_path = Path("strict-review-summary.json")
    summary_path.write_text(json.dumps({"results": out, "summary": {
        "total": len(out), "pass": pas, "warn": warn, "fail": fail,
        "axis_A_pdf_identity_fail": p0_axis_a,
        "axis_B_topic_match_fail": p0_axis_b,
        "axis_C_ek_truth_fail": p0_axis_c,
        "axis_D_assessment_fail": p0_axis_d,
    }}, indent=2, ensure_ascii=False))
    print(f"\nWritten: {summary_path}")