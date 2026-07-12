"""E2E test: simulate a real IGCSE task through the full workflow.

Goal: exercise M6-M10 changes end-to-end and confirm the pieces
hold together when composed. We mock feishu_chat.send_card /
send_text so no real Feishu traffic happens, but every other
layer (state machine, evidence account, asset registry, workspace
metadata, recommend scoring, cards_v2 validator) runs against
isolated_env state.

Sequence:
  1. Manager dispatches an IGCSE Accounting 0452 task with
     workspace_mode=worktree.
  2. Worker (simulated via tasks.transition_flow) moves it through
     assigned -> in_progress -> submitted_for_review, with
     evidence_packet carrying items_count=320 / qql_count=320 /
     manifest_evidence={'rows': 320}.
  3. Manager invokes `task evidence-explain` to inspect readiness.
     Expected: PASS verdict, qbank_ready skill suggestion.
  4. Reviewer approves.
  5. Manager invokes `task manager-action-apply
     manager_formal_closeout --confirm`.
  6. Verify final task state: status=delivered, verdict=approved,
     closeout_status=closeout_completed, evidence_packet preserved.
  7. Verify workspace fields survived every transition.
  8. Verify `asset drift-check` reports clean (no regressions).
  9. Verify `workflow recommend` for the same task's drift class
     points at the right workflow.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as a bare script (`python tests/integration/...`) — under
# pytest the root conftest already puts src/ and tests/ on sys.path, so
# these inserts are idempotent no-ops there.
_ROOT = Path(__file__).resolve().parents[2]
for _p in (_ROOT / "src", _ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from helpers import attr_patch, env_patch, isolated_env, run_cli  # noqa: E402
from eduflow.feishu import chat as feishu_chat  # noqa: E402
from eduflow.store import (  # noqa: E402
    asset_registry, tasks,
)


def _fake_send_card(chat_id, card, **kw):
    return {"message_id": "om_test_card"}


def _fake_send_text(chat_id, text, **kw):
    return {"message_id": "om_test_text"}


def _step(label: str) -> None:
    print(f"\n── {label} ──", flush=True)


def main() -> int:
    failures: list[str] = []

    with isolated_env(
        team={
            "agents": {
                "manager": {
                    "role": "团队主管", "emoji": "🎯", "color": "blue",
                },
                "worker_course": {
                    "role": "课程研发", "color": "purple",
                },
                "review_course": {
                    "role": "复核", "color": "green",
                },
                "auto_ops": {
                    "role": "ops", "color": "red",
                },
            }
        },
        runtime_config={"chat_id": "oc_test_e2e", "lark_profile": ""},
    ):
        with attr_patch(feishu_chat, send_card=_fake_send_card), \
             attr_patch(feishu_chat, send_text=_fake_send_text):

            # ── Step 1: Manager dispatches a task with workspace metadata.
            _step("1. Manager dispatches IGCSE Accounting 0452 task")
            rc, out, err = run_cli([
                "task", "dispatch",
                "worker_course", "IGCSE Accounting 0452 全学科正式完成",
                "--stage", "curriculum",
                "--owner", "worker_course",
                "--by", "manager",
                "--workflow", "igcse-subject-launch",
                "--workspace-mode", "worktree",
                "--workspace-path", "/tmp/eduflow-e2e/worktree",
                "--workspace-branch", "feat/accounting-0452",
                "--workspace-base-commit", "abc1234",
            ])
            assert rc == 0, f"dispatch failed: {err}"
            tid = next(w for w in out.split() if w.startswith("T-") and w.endswith(":"))
            tid = tid.rstrip(":")
            print(f"  created {tid}")

            # ── Step 2: Worker moves through state machine.
            _step("2. Worker moves through state machine")
            tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")

            # Worker provides a complete evidence packet.
            data = tasks._load()
            for row in data.get("tasks", []):
                if row.get("id") == tid:
                    row["evidence_packet"] = {
                        "workflow_id": "igcse-subject-launch",
                        "task_id": tid,
                        "batch_range": "full_subject",
                        "items_count": 320,
                        # _subject_counts reads item_count from
                        # evidence_packet["items_count"] and
                        # evidence_packet["item_count"]; qa_count from
                        # evidence_packet["qa_count"].  Both are
                        # required for the strict-account gate
                        # (_qa_standard_status) to return
                        # "qa_standard_met".  Missing either causes
                        # "qa_standard_missing_counts" →
                        # "evidence_account_incomplete".
                        "item_count": 320,
                        "qql_count": 320,
                        "qa_count": 320,
                        # The manifest_evidence dict is the canonical
                        # format.  task_evidence_account reads
                        # manifest_rows from the dict keys (rows,
                        # manifest_rows, count, items_count).  Top-
                        # level manifest_rows is NOT preserved by
                        # _normalize_evidence_packet (it only copies
                        # _REQUIRED_EVIDENCE_PACKET_FIELDS and
                        # REVIEW_EVIDENCE_FIELDS), so we MUST put the
                        # row count inside the manifest_evidence dict.
                        "manifest_evidence": {"rows": 320},
                        "files_sampled": ["Q-1.md", "Q-50.md"],
                        "q_ids_checked": ["Q-1", "Q-50", "Q-100"],
                        "calculation_or_concept_checks": ["ok"],
                        "path_naming_result": "pass",
                    }
                    row["qbank"] = {"lifecycle_state": "qbank_ready"}
                    row["verifier_result"] = {
                        "scope": "subject",
                        "status": "pass",
                        "items_count": 320,
                        "qql_count": 320,
                        "manifest_rows": 320,
                        "blocking_reasons": [],
                        "consistency": {"drifts": [], "drift_count": 0},
                    }
            tasks._save(data)

            tasks.submit_for_review(tid, actor="worker_course")
            row = tasks.get(tid)
            assert row["status"] == "submitted_for_review"
            assert row["workspace_mode"] == "worktree"
            assert row["workspace_branch"] == "feat/accounting-0452"
            assert row["workspace_path"] == "/tmp/eduflow-e2e/worktree"
            assert row["workspace_base_commit"] == "abc1234"
            print("  state=in_progress -> submitted_for_review, workspace fields preserved")

            # ── Step 3: Manager inspects evidence BEFORE review approval (M6).
            # Expected: NEEDS_FIX / OBSERVE — the explainer must REFUSE to
            # say PASS until there is an authoritative review verdict. This
            # is the M6 safety property: worker-submitted evidence alone is
            # never enough for a PASS.
            _step("3. Manager inspects evidence BEFORE review (M6 must NOT say PASS)")
            rc, out, err = run_cli(["task", "evidence-explain", tid, "--json"])
            assert rc == 0, f"evidence-explain failed: {err}"
            packet = json.loads(out)["evidence_explain"]
            print(f"  pre-review verdict={packet['verdict']} "
                  f"(must not be PASS without an authoritative review)")
            if packet["verdict"] == "PASS":
                failures.append(
                    "pre-review verdict is PASS — M6 must not promote "
                    "worker evidence to PASS without a reviewer verdict"
                )
            if packet["manager_action_allowed"]:
                failures.append(
                    "pre-review manager_action_allowed is True — must be "
                    "False until the reviewer approves"
                )

            # ── Step 4: Reviewer approves.
            # CRITICAL: `review_flow` takes a `verdict_target` parameter
            # that the reviewer uses to declare the scope they reviewed
            # (e.g. "full_subject" / "QQL + items" / "Unit 1"). The
            # closeout gate later checks that the derived `verdict_scope`
            # covers the closeout target. A `verdict_target` of "全学科"
            # or "full_subject" makes the approval authoritative for
            # full-subject closeout. Without it, the gate says
            # "closeout_blocked_review_not_approved" because it cannot
            # verify the reviewer covered the full scope.
            _step("4. Reviewer approves with full evidence")
            tasks.review_flow(
                tid, outcome="approve", actor="review_course",
                review_reason="approved_for_delivery",
                latest_turn_summary="all 320 QA items verified",
                verdict_target="IGCSE Accounting 0452 全学科正式完成",
            )
            row = tasks.get(tid)
            assert row["verdict"] == "approved"
            assert row["workspace_mode"] == "worktree"  # preserved through review
            print("  verdict=approved, workspace_mode still worktree")

            # ── Step 4b: Manager inspects evidence AFTER review approval (M6).
            # Now the authoritative review verdict exists → PASS.
            _step("4b. Manager inspects evidence AFTER review (M6 should say PASS)")
            rc, out, err = run_cli(["task", "evidence-explain", tid, "--json"])
            assert rc == 0, f"evidence-explain failed: {err}"
            packet = json.loads(out)["evidence_explain"]
            print(f"  post-review verdict={packet['verdict']} confidence={packet['confidence']}")
            print(f"  required_next_owner={packet['required_next_owner']}")
            print(f"  manager_action_allowed={packet['manager_action_allowed']}")
            print(f"  safe_next_action={packet['safe_next_action']}")
            for f in packet["missing_evidence"]:
                failures.append(f"post-review missing_evidence: {f}")
            for f in packet["conflicting_evidence"]:
                failures.append(f"post-review conflicting_evidence: {f}")
            if packet["verdict"] != "PASS":
                failures.append(f"post-review verdict={packet['verdict']} (expected PASS)")
            if not packet["manager_action_allowed"]:
                failures.append("post-review manager_action_allowed should be True for PASS")
            if packet["required_next_owner"] != "manager":
                failures.append(
                    f"post-review required_next_owner={packet['required_next_owner']} "
                    f"(expected manager)"
                )
            if not packet["latest_authoritative_review"]["reviewer"]:
                failures.append("post-review latest_authoritative_review missing reviewer")

            # ── Step 5: Manager closes out.
            # The E2E has no real content directory, so the subject
            # verifier cannot re-check artifacts. We use --skip-verifier
            # under EDUFLOW_VERIFIER_BYPASS_ALLOWED=1 (the documented
            # test-only escape hatch) so the closeout can complete from
            # the evidence packet. In production a real content dir makes
            # this unnecessary.
            #
            # CRITICAL: the CLI returns rc=0 whether the apply succeeded
            # or was blocked by a precondition. We must NOT trust rc alone
            # — we assert on the `applied=` / `apply_reason=` fields in the
            # output. This is the exact blind spot that a naive
            # `assert rc == 0` would miss.
            _step("5. Manager invokes manager-action-apply manager_formal_closeout")
            with env_patch(EDUFLOW_VERIFIER_BYPASS_ALLOWED="1"):
                rc, out, err = run_cli([
                    "task", "manager-action-apply",
                    "manager_formal_closeout",
                    "--subject-id", tid,
                    "--confirm",
                    "--skip-verifier",
                ])
            print(f"  closeout rc={rc}")
            print(f"  {out.splitlines()[0] if out else '(no output)'}")
            # rc alone is not enough — the apply is only real when
            # applied=true.  A blocked apply also returns rc=0.
            if "applied=true" not in out:
                failures.append(
                    "closeout apply did not report applied=true — the "
                    f"apply was blocked or failed:\n{out}"
                )

            # ── Step 6: Verify final state.
            _step("6. Verify final task state")
            row = tasks.get(tid)
            print(f"  status={row['status']} verdict={row['verdict']}")
            print(f"  closeout_status={row.get('closeout_status')}")
            print(f"  workspace_mode={row['workspace_mode']}")
            print(f"  workspace_path={row['workspace_path']}")
            if row["status"] != "delivered":
                failures.append(f"status={row['status']} (expected delivered)")
            if row["verdict"] != "approved":
                failures.append(f"verdict={row['verdict']} (expected approved)")
            # Now that the apply actually completed, closeout_status must
            # be stamped.  This is the assertion that was MISSING in the
            # first E2E draft — it green-lit a silent closeout failure.
            if row.get("closeout_status") != "closeout_completed":
                failures.append(
                    f"closeout_status={row.get('closeout_status')!r} "
                    "(expected closeout_completed)"
                )
            if row["workspace_mode"] != "worktree":
                failures.append(
                    f"workspace_mode={row['workspace_mode']} (expected worktree)"
                )

            # ── Step 7: Re-run evidence-explain on closed task to confirm
            # the verdict still says PASS (no regression after closeout).
            _step("7. Post-closeout evidence-explain re-check")
            rc, out, _ = run_cli(["task", "evidence-explain", tid, "--json"])
            assert rc == 0
            packet = json.loads(out)["evidence_explain"]
            print(f"  post-closeout verdict={packet['verdict']}")
            if packet["verdict"] not in {"PASS", "OBSERVE"}:
                # Closed tasks are in terminal state; OBSERVE is acceptable
                # when latest review verdict is approved but closeout has
                # already happened.  PASS is the ideal.
                failures.append(
                    f"post-closeout verdict={packet['verdict']} "
                    f"(expected PASS or OBSERVE)"
                )

            # ── Step 8: Verify asset drift-check still works (M7).
            _step("8. asset drift-check on the running session")
            report = asset_registry.drift_check()
            print(f"  drift-check ok={report['ok']} errors={report['summary']['errors']} "
                  f"warnings={report['summary']['warnings']} "
                  f"info={report['summary']['info']}")
            if report["summary"]["errors"] > 0:
                failures.append(
                    f"drift-check reported {report['summary']['errors']} errors"
                )

    # ── Final summary.
    print()
    if failures:
        print(f"❌ E2E FAILED with {len(failures)} issues:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("✅ E2E PASSED: all 8 steps completed; M6-M10 changes hold together.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ── pytest entry point ──────────────────────────────────────────
#
# The same simulation, wrapped so it runs as part of the regression
# suite (`pytest tests/integration/test_e2e_full_workflow.py`).


def test_e2e_full_workflow():
    """E2E regression: a full IGCSE task lifecycle exercising M6-M10.

    Fails the test if `main()` reports any issue.
    """
    rc = main()
    assert rc == 0, "E2E workflow simulation reported failures (see stdout)"
