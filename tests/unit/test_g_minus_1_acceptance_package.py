from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "acceptance" / "G-1"
BASELINE_REVISION = "bde14c5ce94aacd99ef80f9c11b65092dcf25fc3"
SUBMISSION_REVISION = "58d926778dde76724467b2eab307e80b0a1c5ea3"
REVISION_LINEAGE = {
    "implementation": "cc95c5a488a8cd699dff515eadf431277669ffc6",
    "remediation": "d578691b8e1d3e0dc6f5221120c4a0d0e4ace6ab",
    "security ledger": "2296dc08c14eae9de34accdf43d4a11c6b8ba68f",
    "Ruff R4 scripts": "73e7b3f4cd47cbc48b985ccbf261266fe38b02d2",
    "runtime authority consolidation": "21d000e5eca28c1ad5a91ad3485c548f8ce1c389",
    "full-source mypy remediation": "175a7f31e0538ac646d9a6c523ba14638f662372",
    "published Flow Memory dependency": "ad149069f246abe9bda93f184fd68d0106a4305d",
    "topology classifier remediation / submission target": SUBMISSION_REVISION,
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
REQUIRED_SUPPORTING_FILES = {"owner-checkpoint.md"}

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


def test_flow_memory_is_a_pinned_runtime_dependency() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]

    assert "flow-memory==0.1.1" in project["dependencies"]


def test_g_minus_1_acceptance_package_has_exact_required_file_set() -> None:
    present = {path.name for path in PACKAGE.iterdir() if path.is_file()}
    assert REQUIRED_FILES <= present
    assert REQUIRED_SUPPORTING_FILES <= present


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


def test_owner_authority_checkpoint_is_durably_bound() -> None:
    combined = "\n".join(
        _read(name)
        for name in (
            "summary.md",
            "known-risks.md",
            "review-verdict.md",
            "owner-checkpoint-request.md",
            "owner-checkpoint.md",
        )
    )
    assert "runtime_operator" in combined
    assert "ou_557e95aadc346010e58dbc71090123f3" in combined
    assert "Kenny" in combined
    assert (
        "https://github.com/Harryanhuang/EduFlow-Team-orch/issues/7"
        "#issuecomment-4953662798"
    ) in combined
    assert "deny-all sentinel" in combined
    assert "author_association=OWNER" in combined
    assert "contact:user:search" in combined


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
        "AC-GLOBAL-04": "PASS",
        "AC-GLOBAL-05": "PASS",
        "AC-GLOBAL-06": "PASS",
        "AC-GLOBAL-07": "PASS",
        "AC-G-1-01": "PASS",
        "AC-G-1-02": "PASS",
        "AC-G-1-03": "PASS",
        "AC-G-1-04": "PASS",
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
        r"(?s)## Machine-verifiable candidate plus evidence-refresh paths.*?```text\n(.*?)\n```",
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


def test_changed_files_separately_binds_submission_and_refresh_inventories() -> None:
    changed_files = _read("changed-files.txt")
    submission = subprocess.run(
        ["git", "diff", "--name-only", BASELINE_REVISION, SUBMISSION_REVISION, "--"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    refresh_tracked = subprocess.run(
        ["git", "diff", "--name-only", SUBMISSION_REVISION, "--"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    refresh_untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()

    def digest(paths: list[str]) -> str:
        payload = "".join(f"{path}\n" for path in sorted(set(paths))).encode()
        return hashlib.sha256(payload).hexdigest()

    assert f"Immutable submission path count: {len(set(submission))}" in changed_files
    assert f"Immutable submission path SHA-256: `{digest(submission)}`" in changed_files
    refresh = sorted(set(refresh_tracked) | set(refresh_untracked))
    assert f"Evidence-refresh path count: {len(refresh)}" in changed_files
    assert f"Evidence-refresh path SHA-256: `{digest(refresh)}`" in changed_files
    for path in refresh:
        assert f"- `{path}`" in changed_files


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

    assert "ruff==0.15.10 check src tests scripts" in security
    assert "Ruff production source" in security
    assert "zero findings after R2f" in security
    assert "All checks passed" in security
    assert "repository baseline is reduced from 486 to zero" in security
    assert "baseline is reduced from 486 to zero" in security_normalized
    assert "npm audit --omit=dev --audit-level=high --registry=https://registry.npmjs.org" in security
    assert "0 vulnerabilities" in security
    assert "trufflehog 3.95.9" in security.lower()
    assert "9547" in security and "18196964" in security
    assert "verified_secrets=0" in security and "unverified_secrets=0" in security
    assert "pip-audit 2.10.1" in security
    assert "Python 3.10" in security
    assert "51" in security and "0 known vulnerabilities" in security
    assert "mypy 2.2.0" in security
    assert "flow-memory==0.1.1" in security
    assert "no-cache clean install" in security
    assert "owner approval" in combined
    assert "Node lockfile sub-check is closed" in review
    assert "scanner unavailable" not in security_normalized
    assert "remain unavailable" not in security_normalized
    assert "Node audit fails because no approved lockfile exists" not in combined
    assert "Node audit has no approved lockfile" not in combined
    assert "genuinely closed" not in combined


def test_owner_checkpoint_request_is_minimal_and_bound_to_submission() -> None:
    request = _read("owner-checkpoint-request.md")
    assert f"Submission target: `{SUBMISSION_REVISION}`" in request
    assert "Result: SATISFIED" in request
    assert "owner-checkpoint.md" in request
    assert "issuecomment-4953662798" in request
    assert "Do not include credential values" in request
    assert "these two checkpoints" in request
    assert "runtime_operator" in request
    assert "TRUST_MODEL.md" in request and "HUMAN_TAKEOVER_RUNBOOK.md" in request
    assert "mypy" not in request and "TruffleHog" not in request
    assert "pip-audit" not in request and "Trusted Publisher" not in request


def test_owner_checkpoint_binds_approved_revision_blobs_and_runtime_actor() -> None:
    receipt = _read("owner-checkpoint.md")
    assert "Result: SATISFIED" in receipt
    assert f"Applicable implementation revision: `{SUBMISSION_REVISION}`" in receipt
    assert "author_association=OWNER" in receipt
    assert "ou_557e95aadc346010e58dbc71090123f3" in receipt
    assert "contact:user:search" in receipt
    expected = {
        "docs/architecture/TRUST_MODEL.md":
            "dd514998fc3ba548d2501b41387f941181ff9581b6ed91946d9c5a6c893ba0f0",
        "docs/governance/OWNERSHIP.md":
            "c451c4e2e86a39e31552738570faf0b16ffdb662b82d82e6d7c2350303fd5a10",
        "docs/operations/CONTROL_PLANE_SLO.md":
            "4eab6b1445db4a060a580b40399917dff5cb784a4a408c162db3079a76f4f41f",
        "docs/operations/HUMAN_TAKEOVER_RUNBOOK.md":
            "cd3e7666fdc154f3677b8bf99e78d1697e1fb13f4136829c449456fd621f5859",
    }
    for path, digest in expected.items():
        blob = subprocess.run(
            ["git", "show", f"{SUBMISSION_REVISION}:{path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        assert hashlib.sha256(blob).hexdigest() == digest
        assert f"| `{path}` | `{digest}` |" in receipt


def test_refresh_artifacts_bind_scans_and_topology_to_exact_provenance() -> None:
    scans = json.loads(_read("scanner-refresh.json"))
    topology = json.loads(_read("production-topology-refresh.json"))

    assert scans["submission_revision"] == SUBMISSION_REVISION
    assert scans["scanned_revision"] == "2680a0b4cd1392275ce9382a5b88815e9b533a12"
    assert scans["timezone"] == "Asia/Shanghai"
    assert {run["name"] for run in scans["runs"]} == {
        "trufflehog_git", "npm_audit", "pip_audit_base_py310",
        "pip_audit_vector_py310", "mypy_full_source", "ruff_full",
        "pypi_install_py310",
    }
    for run in scans["runs"]:
        assert run["command"] and run["cwd"]
        assert run["timestamp_local"].endswith("+08:00")
        assert run["timestamp_utc"].endswith("Z")
        assert run["exit_code"] == 0
        assert re.fullmatch(r"[0-9a-f]{64}", run["output_sha256"])
        assert run["summary"]
        local = datetime.fromisoformat(run["timestamp_local"])
        utc = datetime.fromisoformat(run["timestamp_utc"].replace("Z", "+00:00"))
        assert local == utc

    vector = next(run for run in scans["runs"] if run["name"] == "pip_audit_vector_py310")
    assert vector["input"] == ["lancedb>=0.4", "sentence-transformers>=2.2"]
    assert vector["index_url"] == "https://pypi.org/simple"
    vector_input = "".join(f"{item}\n" for item in vector["input"]).encode()
    assert hashlib.sha256(vector_input).hexdigest() == vector["input_sha256"]

    assert topology["submission_revision"] == SUBMISSION_REVISION
    assert topology["production_revision"] == "bde14c5ce94aacd99ef80f9c11b65092dcf25fc3"
    assert topology["config_generation"] == "edc3a3ac9b8f328e"
    assert topology["exit_code"] == 0 and topology["ok"] is True
    assert topology["errors"] == [] and topology["suspect_count"] == 0
    assert topology["daemon_count"] == 3
    assert topology["pane_count"] == topology["agent_process_count"] == 11
    raw = (json.dumps(topology["raw"], ensure_ascii=False, indent=2) + "\n").encode()
    assert len(raw) == topology["raw_output_bytes"]
    assert hashlib.sha256(raw).hexdigest() == topology["raw_output_sha256"]
    assert topology["daemon_count"] == len(topology["raw"]["daemons"])
    assert topology["pane_count"] == len(topology["raw"]["panes"])
    assert topology["agent_process_count"] == len(topology["raw"]["agent_processes"])
    assert topology["suspect_count"] == len(topology["raw"]["suspect_processes"])
    local = datetime.fromisoformat(topology["timestamp_local"])
    utc = datetime.fromisoformat(topology["timestamp_utc"].replace("Z", "+00:00"))
    assert local == utc


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
        "ruff_r3d_e731_tests.txt": 4,
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
