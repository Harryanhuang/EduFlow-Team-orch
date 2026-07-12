#!/usr/bin/env python3
"""AP qbank artifact verifier CLI.

Usage:
    python scripts/ap_qbank_verify.py --subject-dir "/path/to/AP Computer Science A"
    python scripts/ap_qbank_verify.py --subject-dir "/path/to/AP Computer Science A" --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow script to import from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eduflow.store.ap_subject_verifier import (  # noqa: E402
    compact_summary,
    verify_ap_subject,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify AP qbank artifacts")
    parser.add_argument(
        "--subject-dir", required=True, help="Path to AP subject directory"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON summary")
    args = parser.parse_args(argv)

    result = verify_ap_subject(args.subject_dir)
    summary = compact_summary(result)

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"AP subject: {summary['subject_name']}")
        print(f"status: {summary['status']}")
        print(f"units: {summary['unit_count']}")
        print(f"items: {summary['item_count']}")
        print(f"manifest_item_rows: {summary['manifest_item_rows']}")
        print(f"qa_passed: {summary['qa_passed']}")
        print(f"difficulty_distribution: {summary['difficulty_distribution']}")
        if summary["blocking_reasons"]:
            print("blocking_reasons:")
            for reason in summary["blocking_reasons"]:
                print(f"  - {reason}")

    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
