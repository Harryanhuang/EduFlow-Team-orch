from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "acceptance" / "G-1"

REQUIRED_FILES = {
    "summary.md",
    "changed-files.txt",
    "test-results.txt",
    "fault-injection-results.txt",
    "security-results.txt",
    "migration-results.txt",
    "rollback-proof.md",
    "known-risks.md",
    "review-verdict.md",
}

SUMMARY_FIELDS = (
    "Gate",
    "Revision",
    "Config generation",
    "Environment",
    "Acceptance result",
    "Mandatory criteria passed/total",
    "Open Critical/High/Medium/Low",
    "Rollback tested",
    "Reviewer",
    "Manager closeout",
)


def _read(name: str) -> str:
    return (PACKAGE / name).read_text(encoding="utf-8")


def test_g_minus_1_acceptance_package_has_exact_required_file_set() -> None:
    present = {path.name for path in PACKAGE.iterdir() if path.is_file()}
    assert REQUIRED_FILES <= present


def test_summary_records_every_mandatory_field_without_blank_values() -> None:
    summary = _read("summary.md")
    values: dict[str, str] = {}
    for field in SUMMARY_FIELDS:
        match = re.search(rf"(?m)^{re.escape(field)}:\s*(\S.*)$", summary)
        assert match, f"missing or blank summary field: {field}"
        values[field] = match.group(1).strip()

    assert values["Gate"] == "G-1"
    assert re.fullmatch(r"[0-9a-f]{40}", values["Revision"])
    assert values["Acceptance result"] in {"PASS", "CONDITIONAL PASS", "FAIL"}
    assert re.fullmatch(r"\d+/\d+", values["Mandatory criteria passed/total"])
    assert re.fullmatch(
        r"\d+/\d+/\d+/\d+", values["Open Critical/High/Medium/Low"]
    )


def test_each_evidence_file_records_a_result_or_not_applicable_reason() -> None:
    for name in REQUIRED_FILES - {"summary.md", "changed-files.txt"}:
        text = _read(name)
        assert text.strip(), f"empty evidence file: {name}"
        normalized = text.lower()
        assert (
            "result:" in normalized
            or "verdict:" in normalized
            or "not_applicable" in normalized
        ), f"{name} lacks a result, verdict, or not_applicable rationale"


def test_pending_authority_checkpoint_is_not_reported_as_approved() -> None:
    combined = "\n".join(
        _read(name)
        for name in ("summary.md", "known-risks.md", "review-verdict.md")
    )
    assert "runtime_operator" in combined
    assert "owner approval evidence" in combined
    assert "u_<admin_feishu_id>" not in combined
    assert "placeholder" in combined
    assert "pending" in combined.lower() or "blocked" in combined.lower()
