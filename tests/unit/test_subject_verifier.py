"""Tests for store/subject_verifier.py — artifact verifier / subject closeout gate.

Package 6: machine-verifiable checks replacing worker self-audit.
"""
from __future__ import annotations

from pathlib import Path
from helpers import isolated_env
from eduflow.store import tasks, subject_verifier


def _make_subject_dir(content_dir: Path, slug: str, *,
                       topics: list[str] | None = None,
                       qa_files: list[str] | None = None,
                       qql_files: list[str] | None = None,
                       items_files: list[str] | None = None,
                       manifest_rows: list[dict] | None = None,
                       legacy_fragments: list[str] | None = None,
                       orphan_files: list[str] | None = None):
    """Scaffold a minimal subject content directory for verification.

    File spec: "name|Qcount" strings for content files.
      e.g. qa_files=["topic-1.1.md|5"] creates qa/topic-1.1.md with 5 Question entities.
    """
    subj_dir = content_dir / slug
    subj_dir.mkdir(parents=True, exist_ok=True)

    if topics is not None:
        topic_lines = "| ID | Name | Level |\n|---|---|---|\n"
        for t in topics:
            parts = t.split("|")
            tid = parts[0].strip()
            tname = parts[1].strip() if len(parts) > 1 else tid
            tlevel = parts[2].strip() if len(parts) > 2 else "Core"
            topic_lines += f"| {tid} | {tname} | {tlevel} |\n"
        (subj_dir / "topic-outline.md").write_text(topic_lines, encoding="utf-8")

    for layer, files in [("qa", qa_files), ("qa-question-level", qql_files), ("items", items_files)]:
        if files is None:
            continue
        layer_dir = subj_dir / layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        for fname in files:
            parts = fname.split("|", 1)
            name = parts[0].strip()
            q_count = int(parts[1]) if len(parts) > 1 else 0
            content = ""
            for i in range(q_count):
                content += (
                    f"### Question Q-T{i+1}.{i+1}-{i+1}\n"
                    f"**Difficulty**: Standard\n"
                    f"**Question**: Test question {i+1}\n"
                    f"**Answer**: Test answer {i+1}\n"
                    f"**Explanation**: Test explanation {i+1}\n"
                    f"**Tags**: test\n\n"
                )
            (layer_dir / name).write_text(content, encoding="utf-8")

    if manifest_rows is not None:
        import csv
        with open(subj_dir / "qa-manifest.csv", "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["qa_file", "question_count"])
            writer.writeheader()
            for row in manifest_rows:
                writer.writerow(row)

    if legacy_fragments is not None:
        items_dir = subj_dir / "items"
        items_dir.mkdir(parents=True, exist_ok=True)
        for frag_name in legacy_fragments:
            (items_dir / frag_name).write_text(
                "### Question Q-1-1\n**Difficulty**: Standard\n**Question**: x\n**Answer**: y\n**Explanation**: z\n**Tags**: t\n",
                encoding="utf-8",
            )

    if orphan_files is not None:
        items_dir = subj_dir / "items"
        items_dir.mkdir(parents=True, exist_ok=True)
        for idx, fname in enumerate(orphan_files):
            (items_dir / fname).write_text(
                f"### Question Q-ORPHAN-{idx+1}\n**Difficulty**: Standard\n**Question**: x\n**Answer**: y\n**Explanation**: z\n**Tags**: t\n",
                encoding="utf-8",
            )


def _make_approved_task(title="IGCSE Physics 0625 300 QA 正式完成",
                         evidence=None,
                         verdict_target: str = "full_subject"):
    """Create an approved+delivered curriculum task, return tid.

    Package 3 invariant: the review verdict must declare a
    verdict_target that derives to `full_subject` (via
    `derive_verdict_scope_from_target`), otherwise
    `subject_closeout_status` will report
    `closeout_blocked_review_not_approved` and the test that
    exercises `manager_closeout_subject` will never reach the
    verifier gate.
    """
    tid = tasks.create_flow(
        "worker_course", title,
        stage="curriculum", owner="worker_course", creator="manager",
    )
    tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
    tasks.transition_flow(tid, to_status="assigned", actor="manager")
    tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
    tasks.submit_for_review(tid, actor="worker_course")
    tasks.review_flow(tid, outcome="approve", actor="review_course",
                      verdict_target=verdict_target,
                      evidence_packet=evidence or {
                          "qa_count": 300, "item_count": 300,
                          "files_sampled": ["f.md"], "q_ids_checked": ["Q-1"],
                          "calculation_or_concept_checks": ["checked"],
                          "items_mapping_count": 300,
                      })
    return tid


# ── Basic verifier outputs ─────────────────────────────────────────


def test_verifier_reports_topic_count():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core", "1.2 | Forces | Core", "3.1 | Waves | Extended"],
                          qa_files=["topic-1.1.md|5"])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert result["topic_count"] == 3


def test_verifier_reports_qa_qql_items_count():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-chemistry-0620",
                          topics=["1.1 | Particles | Core"],
                          qa_files=["topic-1.md|5"],
                          qql_files=["qql-1.md|3"],
                          items_files=["items-1.md|8"])
        result = subject_verifier.verify_subject(content_dir, "igcse-chemistry-0620")
        assert result["qa_count"] == 5
        assert result["qql_count"] == 3
        assert result["items_count"] == 8
        assert result["total_questions"] == 16


def test_verifier_reports_manifest_path():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core"],
                          manifest_rows=[{"qa_file": "topic-1.1.md", "question_count": "5"}])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert result["has_manifest"] is True
        assert "qa-manifest.csv" in str(result.get("manifest_path", ""))


def test_verifier_reports_difficulty_distribution():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-biology-0610",
                          topics=["1.1 | Cells | Core"],
                          qa_files=["topic-1.md|3"])
        result = subject_verifier.verify_subject(content_dir, "igcse-biology-0610")
        assert "difficulty_distribution" in result
        diff_dist = result["difficulty_distribution"]
        assert isinstance(diff_dist, dict)


def test_verifier_reports_missing_layers():
    """Empty or missing content layers should be reported."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["topic-1.1.md|5"],
                          manifest_rows=[{"qa_file": "qa/topic-1.1.md", "question_count": "5"}])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert "missing_layers" in result
        # qql and items are absent → reported as missing
        assert len(result["missing_layers"]) >= 1


def test_verifier_supports_hash_question_headings():
    """`# Question` (qql convention) is parsed same as `### Question`."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        subj_dir = content_dir / "igcse-physics-0625"
        subj_dir.mkdir(parents=True, exist_ok=True)
        (subj_dir / "topic-outline.md").write_text(
            "| ID | Name | Level |\n|---|---|---|\n| 1.1 | Motion | Core |\n", encoding="utf-8")
        qql_dir = subj_dir / "qa-question-level"
        qql_dir.mkdir(parents=True, exist_ok=True)
        (qql_dir / "q1.md").write_text(
            "# Question Q-1.1-01\ntest\n\n"
            "# Question Q-1.1-02\ntest2\n",
            encoding="utf-8")
        (subj_dir / "qa-manifest.csv").write_text(
            "qa_file,question_count\nqa-question-level/q1.md,2\n", encoding="utf-8")
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert result["qql_count"] == 2


# ── Package vs subject scope ───────────────────────────────────────


def test_verifier_distinguishes_package_scope():
    """Verifier identifies batch/package scope independently of task status."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["topic-1.1.md|5"])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert result["scope"] == "subject"


def test_verifier_does_not_confuse_package_pass_for_subject_pass():
    """A small package PASS on a task must not propagate to subject PASS."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["topic-1.1.md|50"])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert result["status"] != "pass"
        assert any("manifest" in r.lower() for r in result.get("blocking_reasons", []))


def test_subject_closeout_gate_rejects_package_scope():
    """Package-scope verifier results must never close out a subject."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625-batch1",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["t1.md|5"])
        pkg_result = subject_verifier.verify_package(content_dir, "igcse-physics-0625-batch1")
        assert pkg_result["scope"] == "package"
        tid = _make_approved_task()
        gate_result = subject_verifier.subject_closeout_gate(
            task=tasks.get(tid),
            verifier_result=pkg_result,
            content_dir=str(content_dir),
        )
        assert gate_result["closeout_allowed"] is False
        assert "verifier_scope_is_package_not_subject" in gate_result["blocking_reasons"]


# ── Subject closeout gate integration ───────────────────────────────


def test_verifier_default_status_when_missing_content():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert result["status"] == "fail"
        assert len(result["blocking_reasons"]) > 0


def test_verifier_pass_requires_all_layers_topics_manifest_and_questions():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        # Real IGCSE shape: manifest enumerates the QQL set (one row per
        # QQL file with question_count=questions in that file). items/ is
        # a derived layer; qa/ is informational.
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core", "1.2 | Forces | Core"],
                          qa_files=["topic-1.1.md|5", "topic-1.2.md|3"],
                          qql_files=["topic-1.1.md|5", "topic-1.2.md|3"],
                          items_files=["topic-1.1.md|5", "topic-1.2.md|3"],
                          manifest_rows=[
                              {"qa_file": "qa-question-level/topic-1.1.md", "question_count": "5"},
                              {"qa_file": "qa-question-level/topic-1.2.md", "question_count": "3"},
                          ])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert result["status"] == "pass"
        assert result["blocking_reasons"] == []
        assert result["missing_layers"] == []
        assert result["consistency"]["blocking_drift_count"] == 0


def test_verifier_pass_fails_on_legacy_fragment_even_with_aligned_counts():
    """Legacy -s2 fragment must still produce warn/fail even when counts align."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        # Use a separate dir for legacy fragments so they don't inflate items_count.
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core", "1.2 | Forces | Core"],
                          qa_files=["topic-1.1.md|5", "topic-1.2.md|3"],
                          qql_files=["topic-1.1.md|5", "topic-1.2.md|3"],
                          items_files=["topic-1.1.md|5", "topic-1.2.md|3"],
                          manifest_rows=[
                              {"qa_file": "qa-question-level/topic-1.1.md", "question_count": "5"},
                              {"qa_file": "qa-question-level/topic-1.2.md", "question_count": "3"},
                          ])
        # Add legacy fragment manually under a non-counted subdir.
        legacy_dir = content_dir / "igcse-physics-0625" / "_legacy"
        legacy_dir.mkdir(exist_ok=True)
        (legacy_dir / "1-1-s2-items.md").write_text(
            "### Question Q-1.1-99\n**Difficulty**: Standard\n**Question**: legacy\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8",
        )
        # But the legacy detector scans _KNOWN_CONTENT_LAYERS = (qa, qql, items) only,
        # so this won't be detected. To trigger the legacy path, put it in items/.
        # Use a different filename suffix that doesn't match `-s2-` so it doesn't
        # inflate items_count via the parsing pipeline.
        # Simpler: the test verifies that even with blocking_drift_count=0,
        # a legacy -s2 file in items/ causes warn. We accept the items_count
        # inflation here (it IS a real signal that legacy fragments are mixed
        # into the items layer).
        (content_dir / "igcse-physics-0625" / "items" / "1-1-s2-items.md").write_text(
            "### Question Q-1.1-99\n**Difficulty**: Standard\n**Question**: legacy\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8",
        )
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        # The legacy fragment is detected (warn level)
        assert result["status"] in ("warn", "fail")
        assert result["legacy_fragment_present"] is True
        # Note: blocking_drift_count may be 1 here because the legacy fragment
        # inflates items_count past qql_count. That's an honest signal of the
        # real failure mode.


# ── Orphan quarantine ──────────────────────────────────────────────


def test_verifier_reports_orphan_candidates_as_quarantine():
    """Orphan files are reported as quarantine recommendation, NOT auto-deleted."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["topic-1.1.md|5"],
                          qql_files=["q1.md|2"],
                          items_files=["i1.md|3"],
                          manifest_rows=[{"qa_file": "qa/topic-1.1.md", "question_count": "5"}],
                          orphan_files=["unknown-topic-99.md"])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert "orphan_candidates" in result
        assert len(result["orphan_candidates"]) >= 1
        orphan = result["orphan_candidates"][0]
        assert orphan["recommendation"] == "quarantine_review"
        assert orphan["auto_delete"] is False


def test_verifier_orphan_includes_evidence():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["topic-1.1.md|5"],
                          qql_files=["q1.md|2"],
                          items_files=["i1.md|3"],
                          manifest_rows=[{"qa_file": "qa/topic-1.1.md", "question_count": "5"}],
                          orphan_files=["random-file.md", "extra-content.md"])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        orphans = result["orphan_candidates"]
        # orphan_files + unmanifested qql/items with unique Q-IDs
        assert len(orphans) >= 2
        orphan_names = {o["file"] for o in orphans}
        assert "items/random-file.md" in orphan_names
        assert "items/extra-content.md" in orphan_names
        for o in orphans:
            assert "file" in o
            assert "reason" in o
            assert "evidence" in o
            assert o.get("auto_delete") is False


def test_verifier_many_orphans_downgrades_to_warn():
    """>10 orphan candidates should produce warn even with manifest."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        orphan_names = [f"orphan-{i}.md" for i in range(20)]
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core", "1.2 | Forces | Core"],
                          qa_files=["t1.md|5", "t2.md|3"],
                          qql_files=["q1.md|2"],
                          items_files=["i1.md|4"],
                          manifest_rows=[
                              {"qa_file": "qa/t1.md", "question_count": "5"},
                              {"qa_file": "qa/t2.md", "question_count": "3"},
                          ],
                          orphan_files=orphan_names)
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        # All orphan files + unmanifested layer files → >10 orphans
        assert len(result["orphan_candidates"]) > 10
        assert result["status"] in ("warn", "fail")


def test_verifier_cross_layer_qid_not_orphaned():
    """A file sharing Q-IDs with another layer should not be orphaned."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        subj_dir = content_dir / "igcse-physics-0625"
        subj_dir.mkdir(parents=True, exist_ok=True)
        (subj_dir / "topic-outline.md").write_text(
            "| ID | Name | Level |\n|---|---|---|\n| 1.1 | Motion | Core |\n", encoding="utf-8")
        (subj_dir / "qa-manifest.csv").write_text(
            "qa_file,question_count\nqa/t1.md,3\n", encoding="utf-8")
        # qa and items both have Q-1.1-1
        qa_dir = subj_dir / "qa"
        qa_dir.mkdir(parents=True, exist_ok=True)
        (qa_dir / "t1.md").write_text(
            "### Question Q-1.1-1\n**Difficulty**: Standard\n**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8")
        items_dir = subj_dir / "items"
        items_dir.mkdir(parents=True, exist_ok=True)
        (items_dir / "x1.md").write_text(
            "### Question Q-1.1-1\n**Difficulty**: Standard\n**Question**: q2\n**Answer**: a2\n**Explanation**: e2\n**Tags**: t\n",
            encoding="utf-8")
        qql_dir = subj_dir / "qa-question-level"
        qql_dir.mkdir(parents=True, exist_ok=True)
        (qql_dir / "q1.md").write_text(
            "### Question Q-UNIQUE-99\n**Difficulty**: Standard\n**Question**: u\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8")
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        # items/x1.md shares Q-1.1-1 with qa → not orphaned
        # qql/q1.md has unique Q-ID → orphaned
        assert any(o["file"] == "qa-question-level/q1.md" for o in result["orphan_candidates"])


# ── Legacy fragments (-s2 / -s3 and variants) ──────────────────────


def test_verifier_detects_legacy_fragments():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-chemistry-0620",
                          topics=["1.1 | Particles | Core"],
                          manifest_rows=[{"qa_file": "items/1-1-items.md", "question_count": "5"}],
                          legacy_fragments=["1-1-s2-items.md", "1-1-s3-items.md"])
        result = subject_verifier.verify_subject(content_dir, "igcse-chemistry-0620")
        assert result["legacy_fragment_present"] is True
        assert len(result.get("legacy_fragments", [])) == 2


def test_verifier_legacy_fragments_not_mixed_into_pass():
    """Legacy fragments produce warn-level status, not pass."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-chemistry-0620",
                          topics=["1.1 | Particles | Core"],
                          qa_files=["topic-1.md|5"],
                          qql_files=["q1.md|2"],
                          items_files=["i1.md|3"],
                          manifest_rows=[{"qa_file": "qa/topic-1.md", "question_count": "5"}],
                          legacy_fragments=["1-1-s2-items.md"])
        result = subject_verifier.verify_subject(content_dir, "igcse-chemistry-0620")
        assert result["status"] in ("warn", "fail")


def test_verifier_detects_round2_legacy_fragments():
    """Legacy regex also catches -round2-items.md variants."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-chemistry-0620",
                          topics=["1.1 | Particles | Core"],
                          qa_files=["topic-1.md|5"],
                          qql_files=["q1.md|2"],
                          items_files=["i1.md|3"],
                          manifest_rows=[{"qa_file": "qa/topic-1.md", "question_count": "5"}],
                          legacy_fragments=["1-1-round2-items.md"])
        result = subject_verifier.verify_subject(content_dir, "igcse-chemistry-0620")
        assert result["legacy_fragment_present"] is True
        assert len(result.get("legacy_fragments", [])) >= 1


def test_verifier_detects_uppercase_legacy_fragments():
    """Case-insensitive legacy fragment matching."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-chemistry-0620",
                          topics=["1.1 | Particles | Core"],
                          qa_files=["topic-1.md|5"],
                          qql_files=["q1.md|2"],
                          items_files=["i1.md|3"],
                          manifest_rows=[{"qa_file": "qa/topic-1.md", "question_count": "5"}],
                          legacy_fragments=["1-1-S2-items.md"])
        result = subject_verifier.verify_subject(content_dir, "igcse-chemistry-0620")
        assert result["legacy_fragment_present"] is True


def test_verifier_no_legacy_fragments_when_clean():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["topic-1.1.md|5"],
                          qql_files=["q1.md|2"],
                          items_files=["i1.md|3"],
                          manifest_rows=[{"qa_file": "qa/topic-1.1.md", "question_count": "5"}])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert result["legacy_fragment_present"] is False
        assert result.get("legacy_fragments") == []


# ── ID mapping summary ─────────────────────────────────────────────


def test_verifier_reports_question_id_bidirectional_mapping():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core", "2.1 | Energy | Core"],
                          qa_files=["topic-1.1.md|3"],
                          items_files=["items-2.1.md|2"])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert "id_mapping" in result
        id_map = result["id_mapping"]
        assert "total_unique_ids" in id_map
        assert "by_layer" in id_map


def test_verifier_cross_layer_id_mapping_correct():
    """Same Q-ID in qa + items should increment cross_layer_count."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        subj_dir = content_dir / "igcse-physics-0625"
        subj_dir.mkdir(parents=True, exist_ok=True)
        (subj_dir / "topic-outline.md").write_text(
            "| ID | Name | Level |\n|---|---|---|\n| 1.1 | Motion | Core |\n", encoding="utf-8")
        (subj_dir / "qa-manifest.csv").write_text(
            "qa_file,question_count\nqa/t1.md,1\nitems/i1.md,1\n", encoding="utf-8")
        qa_dir = subj_dir / "qa"
        qa_dir.mkdir(parents=True, exist_ok=True)
        (qa_dir / "t1.md").write_text(
            "### Question Q-1.1-1\n**Difficulty**: Standard\n**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8")
        items_dir = subj_dir / "items"
        items_dir.mkdir(parents=True, exist_ok=True)
        (items_dir / "i1.md").write_text(
            "### Question Q-1.1-1\n**Difficulty**: Challenge\n**Question**: q2\n**Answer**: a2\n**Explanation**: e2\n**Tags**: t\n",
            encoding="utf-8")
        qql_dir = subj_dir / "qa-question-level"
        qql_dir.mkdir(parents=True, exist_ok=True)
        (qql_dir / "q1.md").write_text(
            "### Question Q-UNIQUE-1\n**Difficulty**: Standard\n**Question**: u\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8")
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        id_map = result["id_mapping"]
        assert id_map["cross_layer_count"] == 1
        assert "Q-1.1-1" in id_map["cross_layer_ids"]
        assert len(id_map["cross_layer_ids"]) <= 1


# ── Negative cases ─────────────────────────────────────────────────


def test_verifier_fail_missing_manifest():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-biology-0610",
                          topics=["1.1 | Cells | Core"],
                          qa_files=["topic-1.1.md|5"])
        result = subject_verifier.verify_subject(content_dir, "igcse-biology-0610")
        assert result["status"] == "fail"
        assert any("manifest" in r.lower() for r in result["blocking_reasons"])


def test_verifier_fail_missing_topics():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-economics-0455",
                          qa_files=["topic-1.md|5"],
                          manifest_rows=[{"qa_file": "qa/topic-1.md", "question_count": "5"}])
        result = subject_verifier.verify_subject(content_dir, "igcse-economics-0455")
        assert result["status"] == "fail"


def test_verifier_fail_no_questions_with_manifest():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-accounting-0452",
                          topics=["1.1 | Basics | Core"],
                          manifest_rows=[{"qa_file": "qa/nonexistent.md", "question_count": "10"}])
        result = subject_verifier.verify_subject(content_dir, "igcse-accounting-0452")
        assert result["total_questions"] == 0


def test_verifier_missing_layers_are_fail():
    """Missing content layers should cause fail, not pass."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["t1.md|5"],
                          manifest_rows=[{"qa_file": "qa/t1.md", "question_count": "5"}])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        # qql and items layers missing → fail
        assert result["status"] == "fail"
        assert len(result["missing_layers"]) >= 1


# ── next_action field ──────────────────────────────────────────────


def test_verifier_pass_produces_expected_next_action():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | T1 | Core", "1.2 | T2 | Core"],
                          qa_files=["t1.md|5", "t2.md|3"],
                          qql_files=["q1.md|2"],
                          items_files=["i1.md|4"],
                          manifest_rows=[
                              {"qa_file": "qa/t1.md", "question_count": "5"},
                              {"qa_file": "qa/t2.md", "question_count": "3"},
                          ])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert "next_action" in result
        assert result["next_action"] not in ("", None)


def test_verifier_fail_produces_blocking_next_action():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-missing-0999")
        result = subject_verifier.verify_subject(content_dir, "igcse-missing-0999")
        assert result["status"] == "fail"
        assert "next_action" in result
        assert result["next_action"] != ""


# ── subject_closeout_gate (integration with tasks) ──────────────────


def test_subject_closeout_gate_queries_verifier():
    """manager_closeout_subject must check verifier status before allowing closeout."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["topic-1.1.md|5"],
                          qql_files=["q1.md|2"],
                          items_files=["i1.md|3"],
                          manifest_rows=[{"qa_file": "qa/topic-1.1.md", "question_count": "5"}])
        tid = _make_approved_task()
        vresult = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        gate_result = subject_verifier.subject_closeout_gate(
            task=tasks.get(tid),
            verifier_result=vresult,
            content_dir=str(content_dir),
        )
        assert "closeout_allowed" in gate_result
        assert "blocking_reasons" in gate_result
        if vresult["status"] == "pass":
            assert gate_result["closeout_allowed"] is True


def test_package_pass_not_upgraded_to_subject_pass():
    """Explicit test: package-level pass does NOT become subject-level pass."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["topic-1.1.md|20"],
                          manifest_rows=[{"qa_file": "qa/topic-1.1.md", "question_count": "20"}])
        vresult = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert vresult["scope"] == "subject"
        assert "package_pass_claimed" not in vresult.get("blocking_reasons", [])


def test_subject_closeout_gate_blocked_when_verifier_fails():
    """If verifier says fail, subject closeout gate must be blocked."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        tid = _make_approved_task()
        vresult = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert vresult["status"] == "fail"
        gate_result = subject_verifier.subject_closeout_gate(
            task=tasks.get(tid),
            verifier_result=vresult,
            content_dir=str(content_dir),
        )
        assert gate_result["closeout_allowed"] is False


def test_verifier_evidence_path_includes_sources():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["topic-1.1.md|5"],
                          qql_files=["qql-1.md|3"],
                          items_files=["items-1.md|8"],
                          manifest_rows=[{"qa_file": "qa/topic-1.1.md", "question_count": "5"}])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        assert "evidence" in result
        evidence = result["evidence"]
        assert "source_paths" in evidence or "content_dir" in evidence


# ── subject inventory integration ──────────────────────────────────


def test_verifier_produces_compact_summary_for_subject_inventory():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625",
                          topics=["1.1 | Motion | Core", "1.2 | Forces | Core"],
                          qa_files=["t1.md|5", "t2.md|3"],
                          qql_files=["q1.md|2"],
                          items_files=["i1.md|4"],
                          manifest_rows=[
                              {"qa_file": "qa/t1.md", "question_count": "5"},
                              {"qa_file": "qa/t2.md", "question_count": "3"},
                          ])
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        compact = subject_verifier.compact_summary(result)
        assert "subject_slug" in compact
        assert "status" in compact
        assert "topic_count" in compact
        assert "total_questions" in compact
        assert "evidence" not in compact


# ── Batch verifier stays separate ──────────────────────────────────


def test_batch_verifier_and_subject_verifier_are_separate():
    """The package/batch verifier should not be conflated with subject verifier."""
    assert hasattr(subject_verifier, "verify_subject")
    assert callable(subject_verifier.verify_subject)
    assert hasattr(subject_verifier, "verify_package")
    assert callable(subject_verifier.verify_package)


def test_package_verifier_scope_is_package():
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625-batch1",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["t1.md|5"])
        pkg_result = subject_verifier.verify_package(content_dir, "igcse-physics-0625-batch1")
        assert pkg_result["scope"] == "package"
        assert "blocking_reasons" in pkg_result


# ── Package 2: Artifact Consistency Verifier (yesterday's IGCSE 8h drift) ──


def _write_raw_items_file(path: Path, body: str) -> None:
    """Write a raw markdown body to a file in any layer dir."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _build_drift_subject(content_dir: Path, *,
                          slug: str,
                          qa_count: int,
                          qql_count: int,
                          items_count: int,
                          manifest_count: int,
                          topics: int = 1) -> None:
    """Build a subject directory with controlled items/QQL/manifest drift.

    Mimics the 0606 8h monitor situation: items/QQL/manifest numbers don't agree.
    """
    subj_dir = content_dir / slug
    subj_dir.mkdir(parents=True, exist_ok=True)

    topic_lines = "| ID | Name | Level |\n|---|---|---|\n"
    for i in range(1, topics + 1):
        topic_lines += f"| 1.{i} | Topic {i} | Core |\n"
    (subj_dir / "topic-outline.md").write_text(topic_lines, encoding="utf-8")

    # Distribute counts across a few files to look like real IGCSE layout
    qa_dir = subj_dir / "qa"
    qa_dir.mkdir(exist_ok=True)
    qa_file = qa_dir / "topic-1.1.md"
    body = ""
    for i in range(1, qa_count + 1):
        body += (
            f"### Question Q-1.1-{i:02d}\n"
            f"**Difficulty**: Standard\n"
            f"**Question**: q{i}\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
        )
    qa_file.write_text(body, encoding="utf-8")

    qql_dir = subj_dir / "qa-question-level"
    qql_dir.mkdir(exist_ok=True)
    qql_file = qql_dir / "q1.md"
    body = ""
    for i in range(1, qql_count + 1):
        body += (
            f"### Question Q-1.1-{i:02d}\n"
            f"**Difficulty**: Foundation\n"
            f"**Question**: q{i}\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
        )
    qql_file.write_text(body, encoding="utf-8")

    items_dir = subj_dir / "items"
    items_dir.mkdir(exist_ok=True)
    items_file = items_dir / "i1.md"
    body = ""
    for i in range(1, items_count + 1):
        body += (
            f"### Question Q-1.1-{i:02d}\n"
            f"**Difficulty**: Challenge\n"
            f"**Question**: q{i}\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
        )
    items_file.write_text(body, encoding="utf-8")

    # Manifest
    manifest = "qa_file,question_count\n"
    for i in range(1, manifest_count + 1):
        manifest += "qa/topic-1.1.md,1\n"
    (subj_dir / "qa-manifest.csv").write_text(manifest, encoding="utf-8")


def test_consistency_items_qql_manifest_drift_fails_closeout():
    """Yesterday's real bug: items=378 / QQL=324 / manifest=324 must NOT pass.

    Drift between items and qql/manifest is a hard fail — it means the
    item-level content is not derivable from the canonical QA set.
    """
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _build_drift_subject(
            content_dir, slug="igcse-additional-mathematics-0606",
            qa_count=324, qql_count=324, items_count=378, manifest_count=324,
        )
        result = subject_verifier.verify_subject(
            content_dir, "igcse-additional-mathematics-0606",
        )
        assert "consistency" in result
        cons = result["consistency"]
        # items (378) must not match qql (324)
        assert any(
            d.get("kind") == "items_vs_qql_drift" for d in cons["drifts"]
        ), f"Expected items_vs_qql_drift in {cons['drifts']}"
        # status must be fail (or warn at best, never pass)
        assert result["status"] in ("fail", "warn")
        assert result["status"] != "pass"
        # Drift must surface in blocking_reasons so closeout gate sees it
        assert any(
            "drift" in r.lower() or "items" in r.lower()
            for r in result["blocking_reasons"]
        ), f"Expected drift reason in {result['blocking_reasons']}"
        # The closeout gate must block
        vgate = subject_verifier.subject_closeout_gate(
            task={"verdict": "approved", "status": "delivered"},
            verifier_result=result, content_dir=str(content_dir),
        )
        assert vgate["closeout_allowed"] is False


def test_consistency_scoped_pass_189_marks_scoped_not_target():
    """items=189/QQL=189/manifest=189 only passes as a scoped batch, not as
    the originally stated 300-400 expansion target. compact_summary must
    reflect that the current scope is 189, not 300+."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _build_drift_subject(
            content_dir, slug="igcse-additional-mathematics-0606",
            qa_count=189, qql_count=189, items_count=189, manifest_count=189,
        )
        result = subject_verifier.verify_subject(
            content_dir, "igcse-additional-mathematics-0606",
        )
        assert "consistency" in result
        cons = result["consistency"]
        # No drift between the three counts → no drift entries
        assert all(
            d.get("kind") not in ("items_vs_qql_drift", "items_vs_manifest_drift")
            for d in cons["drifts"]
        ), f"189/189/189 should not produce drift entries; got {cons['drifts']}"
        # The scoped total is recorded so caller knows this is 189, not 300+
        assert "scoped_total" in cons
        assert cons["scoped_total"] == 189
        # compact_summary surfaces the scoped total
        compact = subject_verifier.compact_summary(result)
        assert "consistency" in compact
        assert compact["consistency"]["scoped_total"] == 189


def test_consistency_detects_unclosed_question_block():
    """`**Item 10 [F]` (an unclosed `### Question` block) is a format error
    that the verifier must surface — not silently pass."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        subj_dir = content_dir / "igcse-physics-0625"
        subj_dir.mkdir(parents=True, exist_ok=True)
        (subj_dir / "topic-outline.md").write_text(
            "| ID | Name | Level |\n|---|---|---|\n| 1.1 | Motion | Core |\n",
            encoding="utf-8",
        )
        # 5 valid + 1 unclosed (no `\n` after the header line)
        items_dir = subj_dir / "items"
        items_dir.mkdir(exist_ok=True)
        broken_body = (
            "### Question Q-1.1-01\n**Difficulty**: Standard\n**Question**: q\n"
            "**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            "### Question Q-1.1-02\n**Difficulty**: Standard\n**Question**: q\n"
            "**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            "### Question Q-1.1-03\n**Difficulty**: Standard\n**Question**: q\n"
            "**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            "### Question Q-1.1-04\n**Difficulty**: Standard\n**Question**: q\n"
            "**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            "### Question Q-1.1-05\n**Difficulty**: Standard\n**Question**: q\n"
            "**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            "**Item 10 [F]\n"  # unclosed block: opens with **Item, no ### Question
        )
        (items_dir / "i1.md").write_text(broken_body, encoding="utf-8")
        # Provide a clean QQL + QA so the only failure is format
        qa_dir = subj_dir / "qa"
        qa_dir.mkdir(exist_ok=True)
        qa_body = "".join(
            f"### Question Q-1.1-{i:02d}\n**Difficulty**: Standard\n"
            f"**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            for i in range(1, 6)
        )
        (qa_dir / "topic-1.1.md").write_text(qa_body, encoding="utf-8")
        qql_dir = subj_dir / "qa-question-level"
        qql_dir.mkdir(exist_ok=True)
        qql_body = "".join(
            f"### Question Q-1.1-{i:02d}\n**Difficulty**: Standard\n"
            f"**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            for i in range(1, 6)
        )
        (qql_dir / "q1.md").write_text(qql_body, encoding="utf-8")
        (subj_dir / "qa-manifest.csv").write_text(
            "qa_file,question_count\nqa/topic-1.1.md,5\n", encoding="utf-8",
        )

        result = subject_verifier.verify_subject(
            content_dir, "igcse-physics-0625",
        )
        cons = result["consistency"]
        # Unclosed block must show as a format error, not silently passed
        assert len(cons["format_errors"]) >= 1
        # The error entry must mention the file and the kind of breakage
        fe = cons["format_errors"][0]
        assert "file" in fe
        assert "kind" in fe
        assert fe["kind"] in ("unclosed_question_block", "orphan_marker", "malformed_block")


def test_consistency_detects_numeric_difficulty():
    """`**Difficulty**: 1` (or 2, 3) instead of F/S/C is invalid and must fail."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        subj_dir = content_dir / "igcse-biology-0610"
        subj_dir.mkdir(parents=True, exist_ok=True)
        (subj_dir / "topic-outline.md").write_text(
            "| ID | Name | Level |\n|---|---|---|\n| 1.1 | Cells | Core |\n",
            encoding="utf-8",
        )
        items_dir = subj_dir / "items"
        items_dir.mkdir(exist_ok=True)
        # Numeric difficulties (1, 2, 3) instead of F/S/C
        body = ""
        for i in range(1, 4):
            body += (
                f"### Question Q-1.1-{i:02d}\n"
                f"**Difficulty**: {i}\n"  # 1, 2, 3 — invalid
                f"**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            )
        (items_dir / "i1.md").write_text(body, encoding="utf-8")

        # Clean qa/qql to isolate the format issue
        qa_dir = subj_dir / "qa"
        qa_dir.mkdir(exist_ok=True)
        qa_body = "".join(
            f"### Question Q-1.1-{i:02d}\n**Difficulty**: Standard\n"
            f"**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            for i in range(1, 4)
        )
        (qa_dir / "topic-1.1.md").write_text(qa_body, encoding="utf-8")
        qql_dir = subj_dir / "qa-question-level"
        qql_dir.mkdir(exist_ok=True)
        qql_body = "".join(
            f"### Question Q-1.1-{i:02d}\n**Difficulty**: Standard\n"
            f"**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            for i in range(1, 4)
        )
        (qql_dir / "q1.md").write_text(qql_body, encoding="utf-8")
        (subj_dir / "qa-manifest.csv").write_text(
            "qa_file,question_count\nqa/topic-1.1.md,3\n", encoding="utf-8",
        )

        result = subject_verifier.verify_subject(
            content_dir, "igcse-biology-0610",
        )
        cons = result["consistency"]
        # Invalid difficulty entries should be surfaced
        assert len(cons["invalid_difficulty_files"]) >= 1
        entry = cons["invalid_difficulty_files"][0]
        assert "file" in entry
        assert "samples" in entry or "invalid_count" in entry


def test_consistency_manifest_only_no_qql_does_not_pass():
    """If manifest has rows but QQL is empty, manifest is not sufficient
    evidence. Status must be fail, not pass."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        subj_dir = content_dir / "igcse-combined-science-0653"
        subj_dir.mkdir(parents=True, exist_ok=True)
        (subj_dir / "topic-outline.md").write_text(
            "| ID | Name | Level |\n|---|---|---|\n| 1.1 | Biology | Core |\n",
            encoding="utf-8",
        )
        # Only items + manifest, no QA/QQL
        items_dir = subj_dir / "items"
        items_dir.mkdir(exist_ok=True)
        body = "".join(
            f"### Question Q-1.1-{i:02d}\n**Difficulty**: Standard\n"
            f"**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            for i in range(1, 9)
        )
        (items_dir / "i1.md").write_text(body, encoding="utf-8")
        (subj_dir / "qa-manifest.csv").write_text(
            "qa_file,question_count\nitems/i1.md,8\n", encoding="utf-8",
        )
        result = subject_verifier.verify_subject(
            content_dir, "igcse-combined-science-0653",
        )
        # qa and qql layers missing
        assert "qa" in result["missing_layers"]
        assert "qa-question-level" in result["missing_layers"]
        assert result["status"] == "fail"
        # And the consistency summary must reflect the missing layers
        assert result["consistency"]["has_qa"] is False
        assert result["consistency"]["has_qql"] is False


def test_consistency_package_pass_not_upgraded_to_subject():
    """A package-level verifier result must not be mistaken for a subject
    pass. compact_summary must show scope='package' and the closeout gate
    must hard-block with `verifier_scope_is_package_not_subject`."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _make_subject_dir(content_dir, "igcse-physics-0625-batch2",
                          topics=["1.1 | Motion | Core"],
                          qa_files=["t1.md|50"],
                          manifest_rows=[{"qa_file": "qa/t1.md", "question_count": "50"}])
        pkg = subject_verifier.verify_package(
            content_dir, "igcse-physics-0625-batch2",
        )
        assert pkg["scope"] == "package"
        assert pkg["status"] == "pass"
        # But feeding it to a subject closeout gate must block
        gate = subject_verifier.subject_closeout_gate(
            task={"verdict": "approved", "status": "delivered"},
            verifier_result=pkg, content_dir=str(content_dir),
        )
        assert gate["closeout_allowed"] is False
        assert "verifier_scope_is_package_not_subject" in gate["blocking_reasons"]
        # And compact_summary must surface the package scope to the manager
        compact = subject_verifier.compact_summary(pkg)
        assert compact["scope"] == "package"


def test_consistency_drift_blocks_manager_closeout_via_task_integration():
    """End-to-end: a task in closeout_ready state with items/QQL drift must
    be rejected by manager_closeout_subject with a clear blocking reason
    that surfaces the drift."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _build_drift_subject(
            content_dir, slug="igcse-additional-mathematics-0606",
            qa_count=300, qql_count=300, items_count=378, manifest_count=300,
        )
        # Build a task that has reached delivered/approved via canonical flow
        tid = _make_approved_task(
            title="IGCSE Additional Mathematics 0606 300 QA 正式完成",
            evidence={
                "qa_count": 300, "item_count": 378,
                "files_sampled": ["qa/topic-1.1.md"], "q_ids_checked": ["Q-1.1-01"],
                "calculation_or_concept_checks": ["checked"],
                "items_mapping_count": 378,
            },
        )
        # Now try to close out — must fail because of drift
        vresult = subject_verifier.verify_subject(
            content_dir, "igcse-additional-mathematics-0606",
        )
        try:
            tasks.manager_closeout_subject(
                tid, actor="manager",
                verifier_result=vresult, content_dir=str(content_dir),
            )
        except ValueError as exc:
            # The error must mention drift, not just generic "verifier failed"
            msg = str(exc)
            assert "drift" in msg.lower() or "items" in msg.lower(), (
                f"Expected drift-specific blocker, got: {msg}"
            )
        else:
            raise AssertionError(
                "manager_closeout_subject should have raised on drift"
            )


def test_consistency_compact_summary_includes_drift_summary():
    """manager-panel / subject-inventory consumers must see the consistency
    summary via compact_summary, including drift kinds and format errors."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _build_drift_subject(
            content_dir, slug="igcse-chemistry-0620",
            qa_count=200, qql_count=200, items_count=200, manifest_count=200,
        )
        # Inject a format error into items
        items_file = content_dir / "igcse-chemistry-0620" / "items" / "i1.md"
        with items_file.open("a", encoding="utf-8") as fh:
            fh.write("**Item 99 [F]\n")  # unclosed
        result = subject_verifier.verify_subject(
            content_dir, "igcse-chemistry-0620",
        )
        compact = subject_verifier.compact_summary(result)
        assert "consistency" in compact
        cons = compact["consistency"]
        # Required keys for manager-panel rendering
        assert "drifts" in cons
        assert "format_errors" in cons
        assert "invalid_difficulty_files" in cons
        assert "scoped_total" in cons
        # The format error must be visible in the compact view
        assert len(cons["format_errors"]) >= 1


# ── Package 2: Defense-in-depth against forged verifier_result ──


def test_consistency_forged_pass_dict_does_not_bypass_closeout():
    """A forged verifier_result = {scope:'subject', status:'pass', blocking_reasons:[]}
    without a consistency payload must NOT pass the closeout gate.

    This blocks the attack pattern where a caller tries to fake a passing
    verifier by constructing an empty result dict. Even without a real
    consistency check, the gate must remain conservative.
    """
    forged = {"scope": "subject", "status": "pass",
              "blocking_reasons": [], "next_action": "ready"}
    gate = subject_verifier.subject_closeout_gate(
        task={"verdict": "approved", "status": "delivered"},
        verifier_result=forged, content_dir="",
    )
    assert gate["closeout_allowed"] is False
    assert "verifier_consistency_payload_missing" in gate["blocking_reasons"]


def test_consistency_forged_pass_with_consistency_but_blocking_drift_still_blocks():
    """Even with a consistency payload, a blocking drift must block closeout
    regardless of vstatus (catches a buggy caller that sets status='pass' but
    includes a severity=blocking drift)."""
    forged = {
        "scope": "subject", "status": "pass",
        "blocking_reasons": [],
        "consistency": {
            "drifts": [
                {"kind": "items_vs_qql_drift", "severity": "blocking",
                 "items": 378, "qql": 324, "delta": 54},
            ],
            "format_errors": [],
            "invalid_difficulty_files": [],
            "scoped_total": 324,
            "blocking_drift_count": 1,
        },
    }
    gate = subject_verifier.subject_closeout_gate(
        task={"verdict": "approved", "status": "delivered"},
        verifier_result=forged, content_dir="",
    )
    assert gate["closeout_allowed"] is False
    assert any("verifier_consistency_blocking_drift" in r
               for r in gate["blocking_reasons"])


def test_consistency_gate_combined_evidence_includes_consistency_payload():
    """When closeout is blocked by a forged verifier_result, the combined_evidence
    must include the consistency payload so managers can debug the rejection."""
    forged = {"scope": "subject", "status": "pass",
              "blocking_reasons": [], "consistency": {},
              "next_action": "ready"}
    gate = subject_verifier.subject_closeout_gate(
        task={"verdict": "approved", "status": "delivered"},
        verifier_result=forged, content_dir="/tmp/whatever",
    )
    assert "consistency" in gate["combined_evidence"]
    # The forged case has consistency={} → drift_count=0, but blocking_reasons
    # surfaces the missing-payload reason
    assert gate["combined_evidence"]["content_dir"] == "/tmp/whatever"
    assert "verifier_consistency_payload_missing" in gate["blocking_reasons"]


# ── Package 2: Codex Q9 — warn must also block closeout ──


def test_consistency_warn_status_blocks_closeout():
    """Codex Q9: workflow doc says "verify_subject returns status != 'pass'
    blocks closeout", but the implementation only blocked status='fail'.
    A status='warn' verifier result (e.g. legacy fragments, many orphans)
    must NOT silently close out.
    """
    forged = {
        "scope": "subject", "status": "warn",
        "blocking_reasons": [],
        "consistency": {
            "drifts": [],
            "format_errors": [],
            "invalid_difficulty_files": [],
            "scoped_total": 189,
            "blocking_drift_count": 0,
            "drift_count": 0,
            "format_error_count": 0,
            "invalid_difficulty_count": 0,
            "has_qa": True, "has_qql": True, "has_items": True,
            "has_manifest": True, "missing_layers": [],
        },
        "next_action": "review_warnings_before_closeout",
    }
    gate = subject_verifier.subject_closeout_gate(
        task={"verdict": "approved", "status": "delivered"},
        verifier_result=forged, content_dir="",
    )
    assert gate["closeout_allowed"] is False
    assert "subject_verifier_warn_blocks_closeout" in gate["blocking_reasons"]


def test_consistency_real_legacy_fragment_status_warn_blocks_closeout():
    """End-to-end: a real subject with a legacy fragment produces
    status='warn' (per _derive_status); this must block manager_closeout
    via the verifier gate, not silently pass.
    """
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        # Build a subject with a legacy -s2 fragment → status="warn"
        _make_subject_dir(content_dir, "igcse-chemistry-0620",
                          topics=["1.1 | Particles | Core", "1.2 | More | Core"],
                          qa_files=["topic-1.md|5", "topic-2.md|3"],
                          qql_files=["q1.md|2"],
                          items_files=["i1.md|4"],
                          manifest_rows=[
                              {"qa_file": "qa-question-level/q1.md", "question_count": "2"},
                          ])
        # Place a legacy -s2 fragment that will be detected but not counted
        (content_dir / "igcse-chemistry-0620" / "items" / "1-1-s2-items.md").write_text(
            "### Question Q-1.1-99\n**Difficulty**: Standard\n**Question**: l\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8",
        )
        result = subject_verifier.verify_subject(content_dir, "igcse-chemistry-0620")
        # Real verifier output: items=9 (8 + 1 legacy) > qql=2 → blocking_drift
        # So status will be "fail" (blocking_reasons non-empty), not just "warn".
        # Either way, the gate must block. The point of this test is to assert
        # the gate blocks status=warn OR status=fail, not that we land on warn.
        assert result["status"] in ("warn", "fail")
        gate = subject_verifier.subject_closeout_gate(
            task={"verdict": "approved", "status": "delivered"},
            verifier_result=result, content_dir=str(content_dir),
        )
        assert gate["closeout_allowed"] is False


# ── Package 2: Codex adversarial review — regression tests ──


def test_consistency_items_subset_of_qql_warns_not_passes():
    """Codex Q1: `items=180, qql=189, manifest=189` must NOT pass closeout.

    items < qql was previously `severity=info` and silently passed.
    Now it produces at least `status=warn`, which blocks closeout via
    the Codex Q9 warn-blocks-closeout invariant. Manager must see the
    delta before signing off.
    """
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        _build_drift_subject(
            content_dir, slug="igcse-additional-mathematics-0606",
            qa_count=189, qql_count=189, items_count=180, manifest_count=189,
        )
        result = subject_verifier.verify_subject(
            content_dir, "igcse-additional-mathematics-0606",
        )
        cons = result["consistency"]
        assert any(
            d.get("kind") == "items_subset_of_qql" for d in cons["drifts"]
        ), f"Expected items_subset_of_qql in {cons['drifts']}"
        # Status must be warn or fail — never pass — so closeout is blocked
        assert result["status"] in ("warn", "fail"), (
            f"items<qql must downgrade to warn/fail, got {result['status']}"
        )
        gate = subject_verifier.subject_closeout_gate(
            task={"verdict": "approved", "status": "delivered"},
            verifier_result=result, content_dir=str(content_dir),
        )
        assert gate["closeout_allowed"] is False


def test_consistency_detects_lowercase_orphan_marker():
    """Codex Q3: `**Item 10 [f]` (lowercase) must be caught the same way
    as `**Item 10 [F]`. The orphan marker regex was case-sensitive."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        subj_dir = content_dir / "igcse-physics-0625"
        subj_dir.mkdir(parents=True)
        (subj_dir / "topic-outline.md").write_text(
            "| ID | Name | Level |\n|---|---|---|\n| 1.1 | Motion | Core |\n",
            encoding="utf-8",
        )
        items_dir = subj_dir / "items"
        items_dir.mkdir(exist_ok=True)
        body = (
            "### Question Q-1.1-01\n**Difficulty**: Standard\n**Question**: q\n"
            "**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            "**Item 10 [f]\n"  # lowercase f — should be caught
        )
        (items_dir / "i1.md").write_text(body, encoding="utf-8")
        # Clean qa/qql layers
        qa_dir = subj_dir / "qa"
        qa_dir.mkdir(exist_ok=True)
        (qa_dir / "topic-1.1.md").write_text(
            "### Question Q-1.1-01\n**Difficulty**: Standard\n"
            "**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8",
        )
        qql_dir = subj_dir / "qa-question-level"
        qql_dir.mkdir(exist_ok=True)
        (qql_dir / "q1.md").write_text(
            "### Question Q-1.1-01\n**Difficulty**: Standard\n"
            "**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8",
        )
        (subj_dir / "qa-manifest.csv").write_text(
            "qa_file,question_count\nqa/topic-1.1.md,1\n", encoding="utf-8",
        )
        result = subject_verifier.verify_subject(content_dir, "igcse-physics-0625")
        cons = result["consistency"]
        assert len(cons["format_errors"]) >= 1, (
            f"Lowercase [f] orphan marker should be caught, got {cons['format_errors']}"
        )


def test_consistency_accepts_short_form_difficulty_F_S_C():
    """Codex Q4: `**Difficulty**: F` (documented short form) must not be
    reported as invalid. The verifier should normalize F→Foundation, etc."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        subj_dir = content_dir / "igcse-biology-0610"
        subj_dir.mkdir(parents=True)
        (subj_dir / "topic-outline.md").write_text(
            "| ID | Name | Level |\n|---|---|---|\n| 1.1 | Cells | Core |\n",
            encoding="utf-8",
        )
        items_dir = subj_dir / "items"
        items_dir.mkdir(exist_ok=True)
        # Use short forms F/S/C — should be accepted
        body = "".join(
            f"### Question Q-1.1-{i:02d}\n**Difficulty**: {d}\n"
            f"**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n\n"
            for i, d in enumerate(["F", "S", "C"], start=1)
        )
        (items_dir / "i1.md").write_text(body, encoding="utf-8")
        qa_dir = subj_dir / "qa"
        qa_dir.mkdir(exist_ok=True)
        (qa_dir / "topic-1.1.md").write_text(
            "### Question Q-1.1-01\n**Difficulty**: Standard\n"
            "**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n"
            "### Question Q-1.1-02\n**Difficulty**: Standard\n"
            "**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n"
            "### Question Q-1.1-03\n**Difficulty**: Standard\n"
            "**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8",
        )
        qql_dir = subj_dir / "qa-question-level"
        qql_dir.mkdir(exist_ok=True)
        (qql_dir / "q1.md").write_text(
            "### Question Q-1.1-01\n**Difficulty**: Standard\n"
            "**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n"
            "### Question Q-1.1-02\n**Difficulty**: Standard\n"
            "**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n"
            "### Question Q-1.1-03\n**Difficulty**: Standard\n"
            "**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8",
        )
        (subj_dir / "qa-manifest.csv").write_text(
            "qa_file,question_count\nqa/topic-1.1.md,3\n", encoding="utf-8",
        )
        result = subject_verifier.verify_subject(content_dir, "igcse-biology-0610")
        cons = result["consistency"]
        # Short forms must NOT be flagged as invalid
        invalid_diffs = [
            ide for ide in cons["invalid_difficulty_files"]
            if ide["file"].startswith("items/")
        ]
        assert not invalid_diffs, (
            f"F/S/C short forms should not be invalid: {invalid_diffs}"
        )


def test_consistency_rejects_unknown_difficulty_short_form():
    """Codex Q4 negative: only F/S/C are accepted as short forms. `**Difficulty**: X`
    must still be flagged as invalid."""
    with isolated_env() as tmp:
        content_dir = tmp / "content"
        subj_dir = content_dir / "igcse-biology-0610"
        subj_dir.mkdir(parents=True)
        (subj_dir / "topic-outline.md").write_text(
            "| ID | Name | Level |\n|---|---|---|\n| 1.1 | Cells | Core |\n",
            encoding="utf-8",
        )
        items_dir = subj_dir / "items"
        items_dir.mkdir(exist_ok=True)
        (items_dir / "i1.md").write_text(
            "### Question Q-1.1-01\n**Difficulty**: X\n"
            "**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8",
        )
        qa_dir = subj_dir / "qa"
        qa_dir.mkdir(exist_ok=True)
        (qa_dir / "topic-1.1.md").write_text(
            "### Question Q-1.1-01\n**Difficulty**: Standard\n"
            "**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8",
        )
        qql_dir = subj_dir / "qa-question-level"
        qql_dir.mkdir(exist_ok=True)
        (qql_dir / "q1.md").write_text(
            "### Question Q-1.1-01\n**Difficulty**: Standard\n"
            "**Question**: q\n**Answer**: a\n**Explanation**: e\n**Tags**: t\n",
            encoding="utf-8",
        )
        (subj_dir / "qa-manifest.csv").write_text(
            "qa_file,question_count\nqa/topic-1.1.md,1\n", encoding="utf-8",
        )
        result = subject_verifier.verify_subject(content_dir, "igcse-biology-0610")
        cons = result["consistency"]
        # `X` is not a valid short form — must be flagged
        items_invalid = [
            ide for ide in cons["invalid_difficulty_files"]
            if ide["file"].startswith("items/")
        ]
        assert len(items_invalid) == 1, (
            f"Unknown difficulty 'X' should be flagged: {items_invalid}"
        )
