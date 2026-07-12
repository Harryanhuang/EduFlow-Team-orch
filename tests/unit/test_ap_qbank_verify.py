"""Unit tests for scripts/ap_qbank_verify.py."""
from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import scripts.ap_qbank_verify as ap_qbank_verify


def _write_item(path: Path) -> None:
    path.write_text(
        "---\n"
        "id: U1.1.1-F\n"
        "difficulty: F\n"
        "type: MCQ\n"
        "calculator: Not Allowed\n"
        "subject: AP CSA\n"
        "unit: 1\n"
        "topic: 1.1\n"
        "subtopic: 1.1.1\n"
        "learning_objective: obj\n"
        "knowledge_point: kp\n"
        "core_concept: cc\n"
        "exam_pattern: MCQ-计算\n"
        "question_type: MCQ\n"
        "common_mistake: cm\n"
        "explanation_context: ec\n"
        "---\n\nQ?\n\n## Options\n\nA. a\n\n## Answer\n\nA\n\n## Explanation\n\nBecause.\n",
        encoding="utf-8",
    )


def _write_manifest(unit_dir: Path) -> None:
    with open(unit_dir / "qa-manifest.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["unit", "topic", "subtopic", "item_id", "difficulty", "type", "calculator", "status", "notes"],
        )
        writer.writeheader()
        writer.writerow({
            "unit": "1", "topic": "1.1", "subtopic": "1.1.1",
            "item_id": "U1.1.1-F", "difficulty": "F", "type": "MCQ",
            "calculator": "Not Allowed", "status": "passed", "notes": "",
        })


def _write_qa(unit_dir: Path) -> None:
    (unit_dir / "QA-自检.md").write_text(
        "本 Unit 状态：**完成**", encoding="utf-8"
    )


def test_cli_pass():
    with tempfile.TemporaryDirectory() as tmp:
        subject = Path(tmp) / "AP CSA"
        unit_dir = subject / "02-题库" / "items" / "Unit 1"
        unit_dir.mkdir(parents=True)
        _write_item(unit_dir / "U1.1.1-F.md")
        _write_manifest(unit_dir)
        _write_qa(unit_dir)

        rc = ap_qbank_verify.main(["--subject-dir", str(subject)])
        assert rc == 0


def test_cli_fail():
    with tempfile.TemporaryDirectory() as tmp:
        subject = Path(tmp) / "AP CSA"
        subject.mkdir()
        rc = ap_qbank_verify.main(["--subject-dir", str(subject)])
        assert rc == 1


def test_cli_json():
    with tempfile.TemporaryDirectory() as tmp:
        subject = Path(tmp) / "AP CSA"
        unit_dir = subject / "02-题库" / "items" / "Unit 1"
        unit_dir.mkdir(parents=True)
        _write_item(unit_dir / "U1.1.1-F.md")
        _write_manifest(unit_dir)
        _write_qa(unit_dir)

        rc = ap_qbank_verify.main(["--subject-dir", str(subject), "--json"])
        assert rc == 0
        # No stdout capture here; function writes to stdout. We rely on rc.


def test_cli_json_parsable():
    with tempfile.TemporaryDirectory() as tmp:
        subject = Path(tmp) / "AP CSA"
        unit_dir = subject / "02-题库" / "items" / "Unit 1"
        unit_dir.mkdir(parents=True)
        _write_item(unit_dir / "U1.1.1-F.md")
        _write_manifest(unit_dir)
        _write_qa(unit_dir)

        import io
        import contextlib
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = ap_qbank_verify.main(["--subject-dir", str(subject), "--json"])
        assert rc == 0
        data = json.loads(out.getvalue())
        assert data["status"] == "pass"
        assert data["item_count"] == 1
