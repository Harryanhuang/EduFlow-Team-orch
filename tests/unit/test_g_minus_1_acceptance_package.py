from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "acceptance" / "G-1"
BASELINE_REVISION = "bde14c5ce94aacd99ef80f9c11b65092dcf25fc3"
SUBMISSION_REVISION = "2296dc08c14eae9de34accdf43d4a11c6b8ba68f"
REVISION_LINEAGE = {
    "implementation": "cc95c5a488a8cd699dff515eadf431277669ffc6",
    "remediation": "d578691b8e1d3e0dc6f5221120c4a0d0e4ace6ab",
    "security ledger": SUBMISSION_REVISION,
}

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


def test_summary_has_machine_recountable_twelve_criterion_ledger() -> None:
    summary = _read("summary.md")
    rows = re.findall(
        r"(?m)^\|\s*([^|]+?)\s*\|\s*(PASS|FAIL)\s*\|\s*([^|]+?)\s*\|$",
        summary,
    )
    assert len(rows) == 12
    assert len({criterion.strip() for criterion, _, _ in rows}) == 12
    actual_statuses = {
        criterion.strip().split(maxsplit=1)[0]: result
        for criterion, result, _ in rows
    }
    assert actual_statuses == {
        "AC-GLOBAL-01": "PASS",
        "AC-GLOBAL-02": "PASS",
        "AC-GLOBAL-03": "PASS",
        "AC-GLOBAL-04": "FAIL",
        "AC-GLOBAL-05": "FAIL",
        "AC-GLOBAL-06": "PASS",
        "AC-GLOBAL-07": "PASS",
        "AC-G-1-01": "PASS",
        "AC-G-1-02": "PASS",
        "AC-G-1-03": "PASS",
        "AC-G-1-04": "FAIL",
        "AC-G-1-05": "PASS",
    }
    declared = re.search(
        r"(?m)^Mandatory criteria passed/total:\s*(\d+)/(\d+)$", summary
    )
    assert declared
    assert (sum(result == "PASS" for _, result, _ in rows), len(rows)) == (
        int(declared.group(1)),
        int(declared.group(2)),
    )


def test_changed_files_machine_section_matches_submission_paths() -> None:
    changed_files = _read("changed-files.txt")
    match = re.search(
        r"(?s)## Machine-verifiable submission paths.*?```text\n(.*?)\n```",
        changed_files,
    )
    assert match, "missing machine-verifiable submission path section"
    recorded = [line for line in match.group(1).splitlines() if line]
    tracked = subprocess.run(
        ["git", "diff", "--name-only", BASELINE_REVISION, "--"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert recorded == sorted(set(tracked) | set(untracked))
    assert "uncommitted" not in changed_files.lower()


def test_changed_files_uses_commit_stable_candidate_inventory_language() -> None:
    changed_files = _read("changed-files.txt")
    normalized = " ".join(changed_files.lower().split())
    for unstable in (
        "current working-tree",
        "current working tree",
        "working-tree delta",
        "working-tree evidence refresh",
        "baseline-to-current-submission",
    ):
        assert unstable not in normalized
    assert "candidate/evidence-refresh path inventory" in normalized


def test_evidence_names_submission_target_and_complete_revision_lineage() -> None:
    summary = _read("summary.md")
    assert re.search(rf"(?m)^Revision:\s*{SUBMISSION_REVISION}$", summary)
    for label, revision in REVISION_LINEAGE.items():
        assert re.search(rf"(?mi)^-\s*{re.escape(label)}:\s*`?{revision}`?$", summary)

    for name in (
        "test-results.txt",
        "security-results.txt",
        "migration-results.txt",
        "rollback-proof.md",
        "review-verdict.md",
        "fault-injection-results.txt",
        "known-risks.md",
    ):
        assert SUBMISSION_REVISION in _read(name), f"stale submission scope: {name}"

    review = _read("review-verdict.md")
    assert "current uncommitted" not in review.lower()
    assert "uncommitted task" not in review.lower()


def test_fault_ledger_marks_actor_optional_claim_as_superseded() -> None:
    fault = _read("fault-injection-results.txt")
    lines = [line for line in fault.splitlines() if "actor-optional" in line]
    assert lines
    assert all("SUPERSEDED" in line for line in lines)
    assert "missing actor" in fault
    assert "rejected before" in fault


def test_summary_risk_tally_matches_known_risk_rows_and_deferrals_are_explicit() -> None:
    summary = _read("summary.md")
    risks = _read("known-risks.md")
    tally = re.search(
        r"(?m)^Open Critical/High/Medium/Low:\s*(\d+)/(\d+)/(\d+)/(\d+)$",
        summary,
    )
    assert tally
    counts = Counter(
        re.findall(r"(?m)^\|\s*(Critical|High|Medium|Low)\s*\|", risks)
    )
    assert tuple(map(int, tally.groups())) == tuple(
        counts[level] for level in ("Critical", "High", "Medium", "Low")
    )
    assert "## Deferred platform facts" in risks
    normalized = " ".join(risks.split())
    assert "not counted as additional open Gate risks" in normalized
    assert "UNKNOWN production compatibility metrics" in normalized
    assert "user_version=0" in risks


def test_formal_acceptance_ownership_is_a_process_gate_not_an_open_risk() -> None:
    review = _read("review-verdict.md")
    assert "**Process gate — formal acceptance ownership is incomplete.**" in review
    assert "Medium — formal acceptance ownership" not in review


def test_rollback_procedure_uses_private_tempdir_and_status_preserving_cleanup() -> None:
    rollback = _read("rollback-proof.md")
    match = re.search(r"(?s)## Reproducible procedure.*?```bash\n(.*?)\n```", rollback)
    assert match, "missing executable rollback procedure"
    script = match.group(1)
    assert "set -euo pipefail" in script
    assert "mktemp -d" in script
    assert "eduflow-g1-rollback.XXXXXX" in script
    assert 'TMP_ROOT="${TMP_ROOT%/}"' in script
    assert 'TMP_ROOT="$(cd "$TMP_ROOT" && pwd -P)"' in script
    assert re.search(r"cleanup\(\)\s*\{\s*rc=\$\?", script)
    assert "trap cleanup EXIT" in script
    assert 'WT="$TMP_DIR/worktree"' in script
    assert 'PATCH="$TMP_DIR/submission.patch"' in script
    assert "WT_REGISTERED=0" in script
    assert "WT_REGISTERED=1" in script
    assert "git worktree list --porcelain" in script
    assert 'worktree $WT' in script
    assert '"$TMP_DIR" == "$TMP_ROOT"/eduflow-g1-rollback.*' in script
    assert script.index('git worktree remove --force "$WT"') < script.index(
        'rm -rf -- "$TMP_DIR"'
    )
    assert not re.search(r"(?m)^(?:WT|PATCH)=/", script)


def test_feishu_bot_creator_lockfile_is_trackable_and_complete() -> None:
    package_dir = ROOT / "scripts" / "feishu_bot_creator"
    manifest = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    lock_path = package_dir / "package-lock.json"

    assert lock_path.is_file(), "Node package exists but its lockfile is missing"
    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", str(lock_path.relative_to(ROOT))],
        cwd=ROOT,
        check=False,
    )
    assert ignored.returncode == 1, "package-lock.json must be eligible for tracking"
    candidate_paths = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert str(lock_path.relative_to(ROOT)) in candidate_paths

    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    assert lock["lockfileVersion"] >= 3
    assert lock["packages"][""]["dependencies"] == manifest["dependencies"]
    for name, entry in lock["packages"].items():
        if not name:
            continue
        assert re.fullmatch(r"\d+\.\d+\.\d+", entry["version"])
        assert entry["resolved"].startswith("https://")
        assert entry["integrity"].startswith("sha512-")


def test_feishu_bot_creator_production_dependencies_are_exactly_pinned() -> None:
    package_dir = ROOT / "scripts" / "feishu_bot_creator"
    manifest = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))

    assert manifest["dependencies"]
    assert all(
        re.fullmatch(r"\d+\.\d+\.\d+", version)
        for version in manifest["dependencies"].values()
    ), "production dependencies must not float across clean installs"


def test_security_ledger_records_current_node_and_ruff_results() -> None:
    security = _read("security-results.txt")
    risks = _read("known-risks.md")
    summary = _read("summary.md")
    review = _read("review-verdict.md")
    combined = "\n".join((security, risks, summary, review))
    security_normalized = " ".join(security.split())

    assert "ruff==0.15.10 check src tests scripts --statistics" in security
    assert "Ruff production source" in security
    assert "zero findings after R2f" in security
    assert "Found 131 errors" in security
    assert "all remaining findings are under tests/scripts" in security
    assert "baseline from 486 to 131" in security_normalized
    assert "npm audit --omit=dev --audit-level=high --offline" in security
    assert "0 vulnerabilities" in security
    assert "Node lockfile sub-check is closed" in review
    assert "offline audit freshness is not proven" in review
    assert "advisory snapshot provenance and freshness are unknown" in security_normalized
    assert "Node audit fails because no approved lockfile exists" not in combined
    assert "Node audit has no approved lockfile" not in combined
    assert "genuinely closed" not in combined


def test_ruff_affected_test_manifests_are_durable_and_machine_runnable() -> None:
    tracked = set(
        subprocess.run(
            ["git", "ls-files", "tests"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    )
    manifests = {
        "ruff_r2f_affected_unit_tests.txt": 77,
        "ruff_r3a_affected_tests.txt": 55,
        "ruff_r3b_f811_tests.txt": 3,
        "ruff_r3c_e741_tests.txt": 8,
    }
    for name, expected_count in manifests.items():
        manifest = ROOT / "tests" / name
        paths = manifest.read_text(encoding="utf-8").splitlines()
        assert len(paths) == expected_count
        assert paths == sorted(set(paths))
        assert all(path.startswith("tests/") and path.endswith(".py") for path in paths)
        assert all((ROOT / path).is_file() for path in paths)
        assert set(paths) <= tracked


def test_results_record_specification_correction_red_and_green() -> None:
    results = _read("test-results.txt")
    assert "Evidence criteria specification correction" in results
    assert "RED observed: 2 failed, 8 passed; exit code 1." in results
    assert "GREEN observed: 10 passed; exit code 0." in results
