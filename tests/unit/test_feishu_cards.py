"""Tests for feishu/cards.py — pure card-schema builders."""
from __future__ import annotations

from eduflow.feishu.cards import (
    beijing_stamp, fenced_block, simple_card,
)


def test_simple_card_emits_v2_schema_shape():
    """R159: card v2 schema — `schema:"2.0"`, `body.elements` list with a
    single `tag:"markdown"` element. v1's `config.wide_screen_mode` and
    nested `text.tag:"lark_md"` are gone; v2's markdown element renders
    fenced code blocks + nested lists which v1 silently dropped."""
    card = simple_card("Hello", "**bold** body")
    assert card["schema"] == "2.0"
    assert card["header"]["title"]["content"] == "Hello"
    assert card["header"]["title"]["tag"] == "plain_text"
    assert card["header"]["template"] == "blue"  # default
    elements = card["body"]["elements"]
    assert len(elements) == 1
    assert elements[0]["tag"] == "markdown"
    assert elements[0]["content"] == "**bold** body"


def test_simple_card_accepts_color_override():
    assert simple_card("X", "y", color="red")["header"]["template"] == "red"
    assert simple_card("X", "y", color="green")["header"]["template"] == "green"


def test_simple_card_falls_back_to_blue_on_unknown_color():
    """Defensive — a typo or future palette change shouldn't bork rendering.

    R166 expanded the palette to include `purple` / `orange` / `turquoise`
    (used by /health server-load card), so use a genuinely-invalid name
    here to keep this test honest."""
    assert simple_card("X", "y", color="magenta")["header"]["template"] == "blue"
    assert simple_card("X", "y", color="")["header"]["template"] == "blue"


def test_simple_card_empty_body_becomes_space():
    """Feishu rejects elements with empty content; coerce to a single space
    so the card schema still validates instead of failing the send."""
    card = simple_card("Title", "")
    assert card["body"]["elements"][0]["content"] == " "


# ── beijing_stamp helper (R117 / R136-relocated) ─────────────────


def test_beijing_stamp_renders_canonical_format():
    """The trailing-stamp helper produces the literal "<YYYY-MM-DD HH:MM>
    北京时间" string used by every card-bearing slash handler."""
    import datetime
    fixed = datetime.datetime(2026, 5, 4, 10, 30)
    assert beijing_stamp(now=lambda: fixed) == "2026-05-04 10:30 北京时间"


def test_beijing_stamp_default_now_is_datetime_now():
    """When no `now` callable is passed, helper uses datetime.now and
    produces a literal-shape string with current local time."""
    s = beijing_stamp()
    assert "北京时间" in s
    # Format `YYYY-MM-DD HH:MM ` shape — verify the dash + colon positions
    assert s[4] == "-" and s[7] == "-"
    assert s[10] == " " and s[13] == ":"


# ── fenced_block helper (R118 / R136-relocated) ──────────────────


def test_fenced_block_wraps_text_in_triple_backticks():
    """Helper for /health, /usage, /tmux body fencing. R159: card v2's
    `markdown` element renders the standard GFM fenced block (triple
    backticks) as a real code block — pre-R159 cards used `lark_md`
    which silently dropped the fence to literal backtick text. Output
    shape is unchanged; just the surrounding card schema swapped."""
    assert fenced_block("alpha\nbeta") == "```\nalpha\nbeta\n```"
    # Empty string still produces a valid fence (Feishu rejects empty
    # element content; an empty fence renders as a 1-line empty code
    # block, harmless)
    assert fenced_block("") == "```\n\n```"


# ── R166: rich card primitives (column_set + colored fonts) ─────


def test_col_cell_wraps_content_in_weighted_column():
    from eduflow.feishu.cards import col_cell
    cell = col_cell("**hi**", weight=2)
    assert cell["tag"] == "column"
    assert cell["width"] == "weighted"
    assert cell["weight"] == 2
    assert cell["elements"][0]["tag"] == "markdown"
    assert cell["elements"][0]["content"] == "**hi**"


def test_column_set_3_joins_cells_with_paragraph_breaks():
    """R172.b: column_set rendering is broken in current Feishu (both
    v1 and v2 collapse it to stacked paragraphs anyway), so column_set_3
    now returns a single markdown element with cells separated by `\\n\\n`
    paragraph breaks. Empty/blank cells are dropped."""
    from eduflow.feishu.cards import column_set_3
    row = column_set_3(["**CPU**\n0%", "", "**Disk**\n10%"])
    assert row["tag"] == "markdown"
    assert "**CPU**" in row["content"]
    assert "**Disk**" in row["content"]
    # Empty cell didn't leak as a stray separator
    assert row["content"].count("\n\n") == 1


def test_column_set_2_joins_label_value_with_colon():
    """R172.b: column_set_2 renders as one markdown line `<label>：<value>`
    (full-width colon) so the bold-label + colored-value pair stays
    on a single visual row."""
    from eduflow.feishu.cards import column_set_2
    row = column_set_2("**Total**", "<font color='blue'>**$1.23**</font>")
    assert row["tag"] == "markdown"
    assert "**Total**" in row["content"]
    assert "$1.23" in row["content"]
    assert "：" in row["content"]


def test_load_color_thresholds():
    from eduflow.feishu.cards import load_color
    # red ≥80, orange ≥50, green <50
    assert load_color(85) == "red"
    assert load_color(80) == "red"
    assert load_color(60) == "orange"
    assert load_color(50) == "orange"
    assert load_color(49) == "green"
    assert load_color(0) == "green"


def test_remaining_color_inverse_thresholds():
    from eduflow.feishu.cards import remaining_color
    # red ≤20, orange ≤50, green >50
    assert remaining_color(15) == "red"
    assert remaining_color(20) == "red"
    assert remaining_color(35) == "orange"
    assert remaining_color(50) == "orange"
    assert remaining_color(75) == "green"


def test_rich_card_emits_v2_schema_with_body_elements():
    """R172.b: rich_card stays on v2 (`schema:"2.0"` + `body.elements`).
    R172.a briefly flipped to v1 thinking column_set rendered side-by-
    side in v1 but not v2; reality is column_set is broken in BOTH
    schemas in current Feishu, so we dropped column_set entirely
    (cards.py column_set_2/3 now emit plain markdown rows) and kept
    v2 for its GFM features (fenced blocks, nested lists, font color
    HTML)."""
    from eduflow.feishu.cards import rich_card
    elements = [{"tag": "markdown", "content": "hi"}]
    card = rich_card("Title", elements, color="purple")
    assert card["schema"] == "2.0"
    assert card["header"]["template"] == "purple"
    assert card["header"]["title"]["content"] == "Title"
    assert card["body"]["elements"] == elements


def test_rich_card_falls_back_to_placeholder_when_elements_empty():
    from eduflow.feishu.cards import rich_card
    card = rich_card("Title", [], color="blue")
    assert card["body"]["elements"][0]["content"] == "(无内容)"


def test_simple_card_accepts_purple_after_R166():
    """R166 added purple to _VALID_COLORS for /health card. Sanity:
    simple_card propagates purple through _normalised_color."""
    from eduflow.feishu.cards import simple_card
    assert simple_card("X", "y", color="purple")["header"]["template"] == "purple"


# ── Package 8: colour palette validation ────────────────────────────
# Verify that turquoise (used by worker_qbank) is recognised as a valid
# card colour. The _VALID_COLORS set was expanded in R166; turquoise was
# already present but never explicitly tested.


def test_valid_colors_includes_turquoise():
    """worker_qbank uses turquoise — it must be a recognised colour so
    _normalised_color doesn't fall back to blue."""
    from eduflow.feishu.cards import _VALID_COLORS, _normalised_color
    assert "turquoise" in _VALID_COLORS
    assert _normalised_color("turquoise") == "turquoise"


def test_valid_colors_includes_package_8_agent_colors():
    """All Package 8 agent card colours must be valid."""
    from eduflow.feishu.cards import _normalised_color
    package_8_colors = ["blue", "purple", "green", "red", "orange",
                        "yellow", "turquoise"]
    for color in package_8_colors:
        assert _normalised_color(color) == color, \
            f"colour '{color}' must be recognised as valid"


def test_unknown_color_still_falls_back_to_blue():
    from eduflow.feishu.cards import _normalised_color
    assert _normalised_color("chartreuse") == "blue"
    assert _normalised_color("") == "blue"


# ── M3: employee / team snapshot cards ────────────────────────────


def test_employee_snapshot_card_emits_v2_schema_and_fields():
    """M3: employee card must use card v2 schema and surface agent,
    display_verdict, residency, current task, workflow gate/next_action,
    staleness_reason, and recommended_next_action."""
    from eduflow.feishu.cards import employee_snapshot_card
    snapshot = {
        "agent": "worker_course",
        "display_verdict": "active",
        "residency_label": "常驻",
        "residency_mode": "resident",
        "declared_status": "进行中",
        "declared_task": "Draft Unit 1",
        "current_task_title": "IGCSE Physics 0625",
        "workflow_id": "igcse-subject-launch",
        "workflow_gate": "review_handoff_gate",
        "workflow_gate_status": "waiting_worker_acceptance",
        "workflow_next_action": "worker submits for review",
        "staleness_reason": "",
        "recommended_next_action": "Continue current task.",
    }
    card = employee_snapshot_card(snapshot)
    assert card["schema"] == "2.0"
    assert "worker\\_course" in card["header"]["title"]["content"]
    assert card["header"]["template"] == "green"
    body = card["body"]["elements"][0]["content"]
    assert "active" in body
    assert "常驻" in body
    assert "resident" in body
    assert "IGCSE Physics 0625" in body
    assert "igcse-subject-launch" in body
    assert "review\\_handoff\\_gate" in body
    assert "worker submits for review" in body
    assert "Continue current task." in body


def test_employee_snapshot_card_escapes_markdown_metacharacters():
    """Dynamic values containing markdown metacharacters must be escaped so
    they render literally rather than accidentally starting bold / italic /
    code / link / HTML spans."""
    from eduflow.feishu.cards import employee_snapshot_card
    card = employee_snapshot_card({
        "agent": "agent_*bold`_test",
        "display_verdict": "blocked",
        "declared_status": "status _italic_",
        "current_task_title": "task [link](x) <html>",
        "recommended_next_action": "retry `cmd` now",
    })
    body = card["body"]["elements"][0]["content"]
    assert "agent\\_\\*bold\\`\\_test" in card["header"]["title"]["content"]
    assert "task \\[link\\](x) \\<html\\>" in body
    assert "status \\_italic\\_" in body
    assert "retry \\`cmd\\` now" in body


def test_employee_snapshot_card_red_for_blocked():
    from eduflow.feishu.cards import employee_snapshot_card
    card = employee_snapshot_card({
        "agent": "worker_cc",
        "display_verdict": "blocked",
        "residency_label": "温备",
        "residency_mode": "warm",
        "declared_status": "受阻",
        "blocker": "API key missing",
        "recommended_next_action": "Resolve blocker: API key missing",
    })
    assert card["header"]["template"] == "red"
    body = card["body"]["elements"][0]["content"]
    assert "受阻" in body
    assert "API key missing" in body


def test_team_snapshot_card_emits_v2_schema_and_sections():
    """M3: team card must use v2 schema and show summary counts,
    residency counts, top actions, flagged agents, and degrade gracefully
    when degraded sources are empty."""
    from eduflow.feishu.cards import team_snapshot_card
    dashboard = {
        "summary": {
            "agents_total": 3,
            "active": 1,
            "stale_display": 1,
            "waiting_inbox": 0,
            "blocked": 1,
            "warm_idle": 0,
            "idle": 1,
            "unknown": 0,
        },
        "residency": {
            "resident": 1,
            "warm": 1,
            "cold": 0,
            "wake_failed": 0,
            "sleep_candidates": 0,
        },
        "top_actions": [
            {
                "priority": 2,
                "agent": "worker_cc",
                "reason": "API key missing",
                "recommended_next_action": "Resolve blocker: API key missing",
            },
            {
                "priority": 3,
                "agent": "worker_course",
                "reason": "status stale",
                "recommended_next_action": "Refresh status surface.",
            },
        ],
        "employees": [
            {
                "agent": "worker_cc",
                "display_verdict": "blocked",
                "current_task_title": "Repair router",
            },
            {
                "agent": "worker_course",
                "display_verdict": "stale_display",
                "current_task_title": "Draft Unit 1",
            },
            {
                "agent": "manager",
                "display_verdict": "idle",
                "current_task_title": "",
            },
        ],
        "degraded": [],
    }
    card = team_snapshot_card(dashboard)
    assert card["schema"] == "2.0"
    body = "\n".join(
        e.get("content", "")
        for e in card["body"]["elements"]
        if e.get("tag") == "markdown"
    )
    assert "3 agents" in body
    assert "常驻 1" in body
    assert "温备 1" in body
    assert "API key missing" in body
    assert "worker\\_cc" in body
    assert "worker\\_course" in body
    assert "blocked" in body
    assert "stale\\_display" in body


def test_team_snapshot_card_renders_degraded_sources():
    """M3: team card must render non-empty degraded sources."""
    from eduflow.feishu.cards import team_snapshot_card
    dashboard = {
        "summary": {"agents_total": 0},
        "residency": {},
        "top_actions": [],
        "employees": [],
        "degraded": [{
            "source": "employee_read_model.build_team_snapshot",
            "error_type": "RuntimeError",
            "message": "status store unreachable",
        }],
    }
    card = team_snapshot_card(dashboard)
    body = "\n".join(
        e.get("content", "")
        for e in card["body"]["elements"]
        if e.get("tag") == "markdown"
    )
    assert "降级来源" in body
    assert "employee\\_read\\_model.build\\_team\\_snapshot" in body
    assert "status store unreachable" in body


def test_team_snapshot_card_yellow_when_stale_or_degraded():
    from eduflow.feishu.cards import team_snapshot_card
    card = team_snapshot_card({
        "summary": {"agents_total": 1, "stale_display": 1},
        "employees": [{"agent": "x", "display_verdict": "stale_display"}],
    })
    assert card["header"]["template"] == "yellow"


def test_team_snapshot_card_red_when_blocked_or_waiting_inbox():
    from eduflow.feishu.cards import team_snapshot_card
    card = team_snapshot_card({
        "summary": {"agents_total": 1, "blocked": 1},
        "employees": [{"agent": "x", "display_verdict": "blocked"}],
    })
    assert card["header"]["template"] == "red"
