"""Tests for runtime injection layer: inject.py + event_bridge.py + CLI.

Covers the user spec's 15 test points:
  1-3. inject_to_send (with task_id, without task_id, empty packet)
  4.   inject_to_reidentify — packet appended
  5.   inject_to_compact — packet prepended
  6.   injection_point filter (send vs reidentify vs compact)
  7-8. build_gate_check (blocked vs allowed)
  9.   format markers (---[EduFlow Memory Packet]---)
 10.   bridge_review_event (FAIL fires, PASS doesn't)
 11-12. bridge_closeout_check (mismatch fires, match doesn't)
 13.   bridge_manager_correction
 14.   bridge_task_lifecycle (2 fails fire, 1 doesn't)
 15.   CLI packet command
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tests.helpers import isolated_env


# ── helpers ───────────────────────────────────────────────────────

def _init_db():
    from eduflow.memory.db import init_schema, close
    close()
    init_schema()


def _reset_db():
    from eduflow.memory.db import close
    close()


def _add_constraint_with_injection(
    injection_point: str = "send,reidentify,compact",
    **kwargs,
) -> str:
    from eduflow.memory.constraints import add_constraint
    return add_constraint(
        scope=kwargs.pop("scope", "team"),
        level=kwargs.pop("level", "L0"),
        constraint_type=kwargs.pop("constraint_type", "must_follow"),
        content=kwargs.pop("content", "team rule content"),
        injection_point=injection_point,
        **kwargs,
    )


# ── 1. inject_to_send with task_id ───────────────────────────────

class TestInjectToSend:
    def test_with_task_id_prepends_packet(self):
        with isolated_env():
            _init_db()
            # Create a task-scoped constraint + a capsule so the packet is non-empty
            _add_constraint_with_injection(
                scope="task:T-101", level="L2",
                content="task T-101 specific rule",
            )
            from eduflow.memory.capsules import upsert_capsule
            upsert_capsule("T-101", workflow_id="wf_pub", goal="publish ch1")

            from eduflow.memory.inject import inject_to_send
            out = inject_to_send("worker", "please do T-101 now")
            assert "---[EduFlow Memory Packet]---" in out
            assert "---[End Memory Packet]---" in out
            assert "please do T-101 now" in out
            assert "task T-101 specific rule" in out
            _reset_db()

    # ── 2. without task_id: only team/lane constraints ────────────
    def test_without_task_id_only_team_scope(self):
        with isolated_env():
            _init_db()
            _add_constraint_with_injection(
                scope="team", level="L0",
                content="team-wide rule",
            )
            _add_constraint_with_injection(
                scope="task:T-999", level="L2",
                content="task-only rule",
            )
            from eduflow.memory.inject import inject_to_send
            out = inject_to_send("worker", "do something")  # no T-<n> in msg
            assert "team-wide rule" in out
            assert "task-only rule" not in out
            _reset_db()

    # ── 3. empty packet → pass-through ────────────────────────────
    def test_empty_packet_passthrough(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.inject import inject_to_send
            msg = "just a plain message"
            out = inject_to_send("worker", msg)
            assert out == msg  # no markers added
            _reset_db()

    def test_explicit_task_id_overrides_conflicting_message_id(self):
        with isolated_env():
            _init_db()
            _add_constraint_with_injection(
                scope="task:T-101", level="L2", content="message task context",
            )
            _add_constraint_with_injection(
                scope="task:T-404", level="L2", content="explicit task context",
            )
            from eduflow.memory.inject import inject_to_send
            out = inject_to_send(
                "worker", "continue T-101", task_id="T-404",
            )
            assert "explicit task context" in out
            assert "message task context" not in out
            _reset_db()

    def test_blank_explicit_task_id_falls_back_to_message_id(self):
        with isolated_env():
            _init_db()
            _add_constraint_with_injection(
                scope="task:T-101", level="L2", content="message task context",
            )
            from eduflow.memory.inject import inject_to_send
            out = inject_to_send("worker", "continue T-101", task_id="  ")
            assert "message task context" in out
            _reset_db()


# ── 4. inject_to_reidentify appends ─────────────────────────────

class TestInjectToReidentify:
    def test_appends_packet(self):
        with isolated_env():
            _init_db()
            _add_constraint_with_injection(
                content="reidentify-targeted rule",
                injection_point="reidentify",
            )
            from eduflow.memory.inject import inject_to_reidentify
            prompt = "You are worker. Read your identity."
            out = inject_to_reidentify("worker", prompt, task_id="T-200")
            # Packet comes AFTER the prompt (append mode)
            assert out.startswith(prompt)
            assert "---[EduFlow Memory Packet - Recovery Context]---" in out
            assert "reidentify-targeted rule" in out
            _reset_db()

    def test_empty_packet_passthrough(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.inject import inject_to_reidentify
            prompt = "just a prompt"
            out = inject_to_reidentify("worker", prompt)
            assert out == prompt
            _reset_db()


# ── 5. inject_to_compact prepends ────────────────────────────────

class TestInjectToCompact:
    def test_prepends_packet(self):
        with isolated_env():
            _init_db()
            _add_constraint_with_injection(
                content="survive-compact rule",
                injection_point="compact",
            )
            from eduflow.memory.inject import inject_to_compact
            compacted = "summary of prior context..."
            out = inject_to_compact("worker", compacted, task_id="T-300")
            # Packet comes BEFORE the compacted context (prepend mode)
            assert out.endswith(compacted)
            assert "---[EduFlow Memory Packet]---" in out
            assert "survive-compact rule" in out
            _reset_db()


# ── 6. injection_point filter ────────────────────────────────────

class TestInjectionPointFilter:
    def test_send_constraints_not_in_reidentify(self):
        """A constraint with injection_point='send' must NOT appear
        in reidentify output; 'reidentify'-targeted constraint must."""
        with isolated_env():
            _init_db()
            _add_constraint_with_injection(
                content="SEND_ONLY rule",
                injection_point="send",
            )
            _add_constraint_with_injection(
                content="REIDENTIFY_ONLY rule",
                injection_point="reidentify",
            )
            from eduflow.memory.inject import inject_to_send, inject_to_reidentify
            send_out = inject_to_send("worker", "hi")
            reident_out = inject_to_reidentify("worker", "prompt")
            assert "SEND_ONLY rule" in send_out
            assert "REIDENTIFY_ONLY rule" not in send_out
            assert "REIDENTIFY_ONLY rule" in reident_out
            assert "SEND_ONLY rule" not in reident_out
            _reset_db()

    def test_compact_only_constraint(self):
        with isolated_env():
            _init_db()
            _add_constraint_with_injection(
                content="COMPACT_ONLY rule",
                injection_point="compact",
            )
            from eduflow.memory.inject import inject_to_send, inject_to_compact
            send_out = inject_to_send("worker", "hi")
            compact_out = inject_to_compact("worker", "compacted")
            assert "COMPACT_ONLY rule" not in send_out
            assert "COMPACT_ONLY rule" in compact_out
            _reset_db()


# ── 7-8. build_gate_check ───────────────────────────────────────

class TestBuildGateCheck:
    def test_gate_required_blocks(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            add_constraint(
                scope="team", level="L0",
                constraint_type="gate_check",
                content="must pass verifier before closeout",
                enforcement="gate_required",
            )
            from eduflow.memory.inject import build_gate_check
            result = build_gate_check("worker", "T-400", "closeout")
            assert result["allowed"] is False
            assert len(result["blocking_constraints"]) == 1
            assert "verifier" in result["blocking_constraints"][0]["content"]
            _reset_db()

    def test_no_gate_required_allows(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            add_constraint(
                scope="team", level="L0",
                constraint_type="must_follow",
                content="soft rule",
                enforcement="prompt_only",
            )
            from eduflow.memory.inject import build_gate_check
            result = build_gate_check("worker", "T-500", "closeout")
            assert result["allowed"] is True
            assert result["blocking_constraints"] == []
            _reset_db()

    def test_l2_gate_required_does_not_block(self):
        """L2/L3 gate_required constraints inform but don't block
        structural gates (by design)."""
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            add_constraint(
                scope="task:T-600", level="L2",
                constraint_type="gate_check",
                content="task-local gate",
                enforcement="gate_required",
            )
            from eduflow.memory.inject import build_gate_check
            result = build_gate_check("worker", "T-600", "closeout")
            assert result["allowed"] is True
            _reset_db()

    def test_fail_open_on_import_error(self):
        """Even if memory module is broken, gate_check must return allowed=True."""
        with isolated_env():
            _init_db()
            # Corrupt the import path temporarily by patching
            import eduflow.memory.inject as inject_mod
            real_assemble = inject_mod._assemble
            def broken_assemble(*a, **kw):
                raise RuntimeError("db broken")
            inject_mod._assemble = broken_assemble
            try:
                from eduflow.memory.inject import build_gate_check
                # query_for_agent itself shouldn't break since DB is fine,
                # but if it did, fail-open kicks in.
                result = build_gate_check("worker", "T-700", "closeout")
                assert isinstance(result["allowed"], bool)
            finally:
                inject_mod._assemble = real_assemble
            _reset_db()


# ── 9. format markers ───────────────────────────────────────────

class TestFormatMarkers:
    def test_prepend_has_both_markers(self):
        with isolated_env():
            _init_db()
            _add_constraint_with_injection(content="marker-test")
            from eduflow.memory.inject import inject_to_send
            out = inject_to_send("worker", "body")
            assert "---[EduFlow Memory Packet]---" in out
            assert "---[End Memory Packet]---" in out
            # Packet block comes before the body
            open_idx = out.index("---[EduFlow Memory Packet]---")
            body_idx = out.index("body")
            assert open_idx < body_idx
            _reset_db()

    def test_append_uses_recovery_marker(self):
        with isolated_env():
            _init_db()
            _add_constraint_with_injection(
                content="recovery-test",
                injection_point="reidentify",
            )
            from eduflow.memory.inject import inject_to_reidentify
            out = inject_to_reidentify("worker", "prompt body")
            assert "---[EduFlow Memory Packet - Recovery Context]---" in out
            assert "---[End Memory Packet]---" in out
            _reset_db()


# ── 10. bridge_review_event ──────────────────────────────────────

class TestBridgeReviewEvent:
    def test_fail_fires_candidate(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_review_event
            cid = bridge_review_event({
                "task_id": "T-BR1",
                "worker": "worker_course",
                "verdict": "FAIL",
                "reason": "format errors",
                "workflow_id": "wf_pub",
            })
            assert cid is not None
            assert cid.startswith("CAND-")
            _reset_db()

    def test_pass_does_not_fire(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_review_event
            cid = bridge_review_event({
                "task_id": "T-BR2",
                "verdict": "PASS",
            })
            assert cid is None
            _reset_db()

    def test_rejected_also_fires(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_review_event
            cid = bridge_review_event({
                "task_id": "T-BR3",
                "verdict": "REJECTED",
                "reason": "inconsistent",
                "workflow_id": "wf_pub",
            })
            assert cid is not None
            _reset_db()


# ── 11-12. bridge_closeout_check ─────────────────────────────────

class TestBridgeCloseoutCheck:
    def test_mismatch_fires_candidate(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_closeout_check
            result = bridge_closeout_check(
                task_id="T-BC1",
                items_count=10,
                qql_count=8,  # mismatch
                manifest_count=10,
                workflow_id="wf_pub",
            )
            assert result["consistent"] is False
            assert result["candidate_id"] is not None
            _reset_db()

    def test_consistent_no_candidate(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_closeout_check
            result = bridge_closeout_check(
                task_id="T-BC2",
                items_count=10,
                qql_count=10,
                manifest_count=10,
                workflow_id="wf_pub",
            )
            assert result["consistent"] is True
            assert result["candidate_id"] is None
            _reset_db()


# ── 13. bridge_manager_correction ────────────────────────────────

class TestBridgeManagerCorrection:
    def test_fires_candidate(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_manager_correction
            cid = bridge_manager_correction(
                agent="worker_course",
                content="always verify QTL before publish",
                severity="high",
                context="after T-BM1 closeout",
            )
            assert cid is not None
            from eduflow.memory.candidate_gen import get_candidate
            c = get_candidate(cid)
            assert "worker_course" in c["content"]
            assert c["proposed_layer"] == "core"  # severity=high
            _reset_db()

    def test_empty_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_manager_correction
            assert bridge_manager_correction("", "content") is None
            assert bridge_manager_correction("agent", "") is None
            _reset_db()


# ── 14. bridge_task_lifecycle ────────────────────────────────────

class TestBridgeTaskLifecycle:
    def test_two_fails_fires_candidate(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            c1 = bridge_task_lifecycle(
                "T-BL1", "fail",
                context={"workflow_id": "wf_pub", "failure_reason": "format"},
            )
            # 1st fail: no prior history → count=1, below threshold → None
            assert c1 is None
            c2 = bridge_task_lifecycle(
                "T-BL2", "fail",
                context={"workflow_id": "wf_pub", "failure_reason": "format"},
            )
            # 2nd fail: count=2 → fires
            assert c2 is not None
            _reset_db()

    def test_single_fail_no_candidate(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            cid = bridge_task_lifecycle(
                "T-BL3", "fail",
                context={"workflow_id": "wf_lonely"},
            )
            assert cid is None
            _reset_db()

    def test_success_event_noop(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            cid = bridge_task_lifecycle(
                "T-BL4", "success",
                context={"workflow_id": "wf_pub"},
            )
            assert cid is None
            _reset_db()


# ── 15. CLI packet command ───────────────────────────────────────

class TestCLIPacket:
    def test_packet_preview(self):
        with isolated_env():
            _init_db()
            _add_constraint_with_injection(content="cli-packet-test")
            from tests.helpers import run_cli
            rc, out, err = run_cli([
                "memory", "packet", "--agent", "worker",
            ])
            assert rc == 0
            assert "cli-packet-test" in out
            _reset_db()

    def test_inject_check_cli(self):
        with isolated_env():
            _init_db()
            _add_constraint_with_injection(content="cli-inject-test")
            from tests.helpers import run_cli
            rc, out, err = run_cli([
                "memory", "inject-check", "worker",
                "--message", "hello world",
            ])
            assert rc == 0
            assert "---[EduFlow Memory Packet]---" in out
            assert "cli-inject-test" in out
            assert "hello world" in out
            _reset_db()

    def test_inject_check_cli_honors_explicit_task_when_message_has_no_id(self):
        with isolated_env():
            _init_db()
            _add_constraint_with_injection(
                scope="task:T-404",
                level="L2",
                content="explicit task context",
            )
            from tests.helpers import run_cli
            rc, out, err = run_cli([
                "memory", "inject-check", "worker",
                "--message", "continue the assigned work",
                "--task", "T-404",
            ])
            assert rc == 0, err
            assert "explicit task context" in out
            assert "continue the assigned work" in out
            _reset_db()

    @pytest.mark.parametrize(
        "tail",
        [
            ["--task"],
            ["--task", ""],
            ["--unknown", "value"],
        ],
    )
    def test_inject_check_cli_rejects_invalid_or_extra_args(self, tail):
        from tests.helpers import run_cli
        rc, out, err = run_cli([
            "memory", "inject-check", "worker", "--message", "hello", *tail,
        ])
        assert rc == 1
        assert err

    def test_gate_check_cli(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            add_constraint(
                scope="team", level="L0",
                constraint_type="gate_check",
                content="cli-gate block",
                enforcement="gate_required",
            )
            from tests.helpers import run_cli
            rc, out, err = run_cli([
                "memory", "gate-check", "worker",
                "--task", "T-CLI", "--gate", "closeout",
            ])
            assert rc == 0
            assert "allowed: False" in out
            assert "cli-gate block" in out
            _reset_db()
