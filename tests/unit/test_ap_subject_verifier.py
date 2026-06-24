"""Unit tests for src/eduflow/store/ap_subject_verifier.py."""
from __future__ import annotations

import csv
import tempfile
from pathlib import Path

from eduflow.store.ap_subject_verifier import compact_summary, verify_ap_subject


def _write_item(path: Path, **overrides: str) -> None:
    defaults = {
        "id": path.stem,
        "difficulty": path.stem.split("-")[-1],
        "type": "MCQ",
        "calculator": "Not Allowed",
        "subject": "AP Computer Science A",
        "unit": "1",
        "topic": "1.1",
        "subtopic": "1.1.1",
        "learning_objective": "Test objective",
        "knowledge_point": "Test point",
        "core_concept": "Test concept",
        "exam_pattern": "MCQ-计算",
        "question_type": "MCQ",
        "common_mistake": "Test mistake",
        "explanation_context": "Test context",
    }
    defaults.update(overrides)
    fm_lines = ["---"]
    for k, v in defaults.items():
        fm_lines.append(f"{k}: {v}")
    fm_lines.append("---")
    body = (
        "\nSample question?\n\n"
        "## Options\n\nA. x\nB. y\nC. z\nD. w\n\n"
        "## Answer\n\nB\n\n"
        "## Explanation\n\nBecause.\n"
    )
    path.write_text("\n".join(fm_lines) + body, encoding="utf-8")


def _write_manifest(unit_dir: Path, item_ids: list[str]) -> None:
    manifest_path = unit_dir / "qa-manifest.csv"
    with open(manifest_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["unit", "topic", "subtopic", "item_id", "difficulty", "type", "calculator", "status", "notes"],
        )
        writer.writeheader()
        for iid in item_ids:
            parts = iid.split("-")
            writer.writerow({
                "unit": "1",
                "topic": "1.1",
                "subtopic": "1.1.1",
                "item_id": iid,
                "difficulty": parts[-1],
                "type": "MCQ",
                "calculator": "Not Allowed",
                "status": "passed",
                "notes": "",
            })


def _write_qa(unit_dir: Path) -> None:
    (unit_dir / "QA-自检.md").write_text(
        "# QA\n\n| 项 | 通过 |\n|---|---|\n| 1 | ✅ |\n\n## 状态判定\n\n本 Unit 状态：**完成**\n",
        encoding="utf-8",
    )


def test_verify_ap_subject_pass():
    with tempfile.TemporaryDirectory() as tmp:
        subject = Path(tmp) / "AP Computer Science A"
        unit_dir = subject / "02-题库" / "items" / "Unit 1"
        unit_dir.mkdir(parents=True)
        item_ids = ["U1.1.1-F", "U1.1.1-S", "U1.1.1-C"]
        for iid in item_ids:
            _write_item(unit_dir / f"{iid}.md")
        _write_manifest(unit_dir, item_ids)
        _write_qa(unit_dir)

        result = verify_ap_subject(subject)
        assert result["status"] == "pass"
        assert result["item_count"] == 3
        assert result["manifest_item_rows"] == 3
        assert result["qa_passed"] is True
        assert result["blocking_reasons"] == []
        summary = compact_summary(result)
        assert summary["status"] == "pass"


def test_missing_frontmatter_key():
    with tempfile.TemporaryDirectory() as tmp:
        subject = Path(tmp) / "AP CSA"
        unit_dir = subject / "02-题库" / "items" / "Unit 1"
        unit_dir.mkdir(parents=True)
        _write_item(unit_dir / "U1.1.1-F.md", core_concept="")
        _write_manifest(unit_dir, ["U1.1.1-F"])
        _write_qa(unit_dir)

        result = verify_ap_subject(subject)
        assert result["status"] == "fail"
        assert any("missing_frontmatter" in r for r in result["blocking_reasons"])


def test_missing_heading():
    with tempfile.TemporaryDirectory() as tmp:
        subject = Path(tmp) / "AP CSA"
        unit_dir = subject / "02-题库" / "items" / "Unit 1"
        unit_dir.mkdir(parents=True)
        path = unit_dir / "U1.1.1-F.md"
        _write_item(path)
        text = path.read_text(encoding="utf-8").replace("## Answer", "## Ans")
        path.write_text(text, encoding="utf-8")
        _write_manifest(unit_dir, ["U1.1.1-F"])
        _write_qa(unit_dir)

        result = verify_ap_subject(subject)
        assert result["status"] == "fail"
        assert any("missing_heading" in r for r in result["blocking_reasons"])


def test_manifest_count_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        subject = Path(tmp) / "AP CSA"
        unit_dir = subject / "02-题库" / "items" / "Unit 1"
        unit_dir.mkdir(parents=True)
        _write_item(unit_dir / "U1.1.1-F.md")
        _write_manifest(unit_dir, ["U1.1.1-F", "U1.1.1-S"])
        _write_qa(unit_dir)

        result = verify_ap_subject(subject)
        assert result["status"] == "fail"
        assert any("manifest_item_count_mismatch" in r for r in result["blocking_reasons"])


def test_qa_not_complete():
    with tempfile.TemporaryDirectory() as tmp:
        subject = Path(tmp) / "AP CSA"
        unit_dir = subject / "02-题库" / "items" / "Unit 1"
        unit_dir.mkdir(parents=True)
        _write_item(unit_dir / "U1.1.1-F.md")
        _write_manifest(unit_dir, ["U1.1.1-F"])
        (unit_dir / "QA-自检.md").write_text("本 Unit 状态：**需返工**", encoding="utf-8")

        result = verify_ap_subject(subject)
        assert result["status"] == "fail"
        assert any("qa_self_check" in r for r in result["blocking_reasons"])


def test_no_items_directory():
    with tempfile.TemporaryDirectory() as tmp:
        subject = Path(tmp) / "AP CSA"
        subject.mkdir()
        result = verify_ap_subject(subject)
        assert result["status"] == "fail"
        assert any("items_directory_not_found" in r for r in result["blocking_reasons"])


def test_invalid_difficulty():
    with tempfile.TemporaryDirectory() as tmp:
        subject = Path(tmp) / "AP CSA"
        unit_dir = subject / "02-题库" / "items" / "Unit 1"
        unit_dir.mkdir(parents=True)
        _write_item(unit_dir / "U1.1.1-F.md", difficulty="X")
        _write_manifest(unit_dir, ["U1.1.1-F"])
        _write_qa(unit_dir)

        result = verify_ap_subject(subject)
        assert result["status"] == "fail"
        assert any("invalid_difficulty" in r for r in result["blocking_reasons"])
