from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_governance_document_set_exists() -> None:
    required = {
        "docs/architecture/TRUST_MODEL.md",
        "docs/operations/CONTROL_PLANE_SLO.md",
        "docs/operations/HUMAN_TAKEOVER_RUNBOOK.md",
        "docs/governance/OWNERSHIP.md",
        "docs/governance/DECISION_AND_EXCEPTION_PROCESS.md",
        "docs/governance/COMPATIBILITY_DEBT.md",
    }
    assert all((ROOT / path).is_file() for path in required)


def test_trust_model_has_complete_authority_matrix_and_separation_of_duties() -> None:
    text = _read("docs/architecture/TRUST_MODEL.md")
    roles = (
        "member", "operator", "admin", "manager", "worker", "reviewer",
        "builder", "runtime_operator", "recorder",
    )
    dimensions = ("Tools", "Credentials", "Files", "External systems")
    for role in roles:
        assert f"| `{role}` |" in text
        row = next(line for line in text.splitlines() if line.startswith(f"| `{role}` |"))
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        assert len(cells) == 5
        assert all(cells), f"authority matrix contains a blank cell for {role}"
    for dimension in dimensions:
        assert dimension in text
    assert "operator cannot clear or runtime-switch" in text
    assert "admin" in text and "runtime_operator" in text and "structured actor" in text
    assert "unknown identity" in text and "fail closed" in text
    assert "Prompt injection" in text and "maximum damage" in text
    assert "two-role confirmation" in text
    assert "two distinct provisioned actors" in text
    assert "same human" in text and "cannot self-confirm" in text
    assert "missing second actor" in text and "fail closed" in text


def test_ownership_and_exception_contracts_are_complete() -> None:
    ownership = _read("docs/governance/OWNERSHIP.md")
    for owner in (
        "control-plane owner", "security owner", "workflow definition maintainer",
        "Skill registry maintainer", "schema/migration owner", "runtime operator",
    ):
        assert owner in ownership
    assert "REVIEW | `worker_review`" in ownership
    assert "CLOSEOUT | `manager`" in ownership
    assert "manager is dispatch-only" in ownership
    for document in (
        _read("docs/architecture/TRUST_MODEL.md"),
        _read("docs/operations/CONTROL_PLANE_SLO.md"),
        ownership,
    ):
        assert "owner approved; independent REVIEW pending" in document
        assert "runtime_operator" in document and "provisioned" in document
        assert "issuecomment-4953662798" in document

    process = _read("docs/governance/DECISION_AND_EXCEPTION_PROCESS.md")
    for field in ("owner", "reason", "scope", "expiry", "removal_test"):
        assert f"`{field}`" in process
    assert "Unbounded exceptions are prohibited" in process


def test_slo_and_takeover_transitions_are_explicit() -> None:
    slo = _read("docs/operations/CONTROL_PLANE_SLO.md")
    approved = (
        "high_priority_durable_persist",
        "retryable_delivery_terminal_result",
        "runtime_switch_terminal_result",
        "workflow_handoff_ack",
        "orphan_detection",
        "unauthorized_control_action_rejection",
    )
    for slo_id in approved:
        assert f"| `{slo_id}` |" in slo
    for threshold in (
        "runtime_switch", "message_retry", "loop_failure", "workflow_repair",
    ):
        assert f"| `{threshold}` |" in slo
    assert "inactive -> active -> recovering -> inactive" in slo
    assert "stop before side effects" in slo
    assert "consecutive failed automatic recovery attempts" in slo
    assert "successful proved automatic recovery resets" in slo
    assert "manual authorized override does not increment or reset" in slo
    assert "durable switch event" in slo
    for objective in ("99.9%", "10 seconds", "5 minutes", "3 minutes", "2 inspection cycles", "100%"):
        assert objective in slo


def test_runbook_is_executable_and_records_provisioned_authorization() -> None:
    runbook = _read("docs/operations/HUMAN_TAKEOVER_RUNBOOK.md")
    for command in (
        "./scripts/eduflowteam human-takeover status --json",
        "./scripts/eduflowteam human-takeover enter",
        "./scripts/eduflowteam human-takeover recover",
    ):
        assert command in runbook
    assert "ou_557e95aadc346010e58dbc71090123f3" in runbook
    assert "Kenny" in runbook
    assert "`team.admins`, `team.runtime_operators`, and `team.runtime_operator`" in runbook
    assert "General `team.operators` have no enter/recover authority" in runbook
    assert "--actor" in runbook and "--reason" in runbook and "--generation" in runbook
    assert "issuecomment-4953662798" in runbook
    assert "does not machine-verify" in runbook
    assert "human checkpoint" in runbook
    assert "G1-Runtime-Authority" in runbook
    assert "test_human_takeover_recovery_requires_verified_probe_evidence" in runbook
    checkpoint = _read("acceptance/G-1/owner-checkpoint.md")
    assert "ou_557e95aadc346010e58dbc71090123f3" in checkpoint
    assert "runtime_operators" in checkpoint
    assert "deny-all sentinel" in checkpoint

    example = _read("eduflow.example.toml")
    assert 'chat_id = "oc_replace_me"' in example
    assert 'ANTHROPIC_AUTH_TOKEN = "${ANTHROPIC_AUTH_TOKEN}"' in example
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "eduflow.toml"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert tracked.returncode == 1


def test_compatibility_debt_ledger_has_bounded_entries() -> None:
    text = _read("docs/governance/COMPATIBILITY_DEBT.md")
    for field in (
        "compatibility_id", "old_contract", "new_contract", "why_still_needed",
        "owner", "usage_metric", "introduced_at", "expires_at", "removal_test",
    ):
        assert field in text
    assert "review_course" in text
    assert "No fail-open" in text
    rows = [line for line in text.splitlines() if line.startswith("| `COMPAT-")]
    assert len(rows) == 5
    for row in rows:
        assert len([cell for cell in row.strip("|").split("|")]) == 9
        assert "2026-07-12T" in row
        assert "438fa806" in row
        assert "baseline=" in row and "evidence=" in row
        assert ("pytest " in row or "rg " in row), "removal test must be runnable"
        assert "TBD" not in row


def test_compatibility_repository_baselines_are_reproducible_and_exclude_ledger() -> None:
    text = _read("docs/governance/COMPATIBILITY_DEBT.md")
    revision = "438fa806ab8112d415a4e159e03a9884e5983dbe"
    measurement_utc = "2026-07-12T08:21:43Z"
    assert f"Measurement completed at `{measurement_utc}`" in text
    cases = {
        "COMPAT-ROLE-001": (["review_course"], ["."]),
        "COMPAT-CARDS-001": (
            ["legacy.*card", "cards_legacy", "from eduflow.feishu.cards import", "import eduflow.feishu.cards"],
            ["src", "tests", "docs"],
        ),
        "COMPAT-STATE-001": (["dual.?write"], ["src", "tests", "docs"]),
        "COMPAT-WORKFLOW-001": (["alias", "aliases"], ["src", "tests", "docs"]),
        "COMPAT-MEMORY-001": (
            ["eduflow_memory", r"eduflow\.memory", "legacy.*memory", "memory import"],
            ["src", "tests", "docs"],
        ),
    }
    for compatibility_id, (patterns, roots) in cases.items():
        command = ["git", "grep", "-l", "-E"]
        for pattern in patterns:
            command.extend(["-e", pattern])
        command.extend([revision, "--", *roots])
        command.extend([":!docs/governance/COMPATIBILITY_DEBT.md"])
        command.extend([":!tests/unit/test_g_minus_1_governance_docs.py"])
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        assert result.returncode in {0, 1}, result.stderr
        count = len([line for line in result.stdout.splitlines() if line])
        row = next(line for line in text.splitlines() if line.startswith(f"| `{compatibility_id}` |"))
        assert f"baseline_repo_files={count}" in row
        assert f"measurement_revision=`{revision}`" in row
        assert f"measurement_utc=`{measurement_utc}`" in row
        assert "git grep -l -E" in row
        assert revision in row
        assert ":!docs/governance/COMPATIBILITY_DEBT.md" in row
        assert ":!tests/unit/test_g_minus_1_governance_docs.py" in row
    drift = subprocess.run(
        ["git", "diff", "--name-only", f"{revision}..HEAD", "--", "src", "tests", "docs"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert drift.returncode == 0, drift.stderr
    assert drift.stdout.splitlines(), "current committed drift must be detected separately"
    assert "does not rewrite or bless the recorded baseline" in text
