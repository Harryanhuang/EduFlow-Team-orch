"""Feishu interactive card builders.

Slash handlers return a dict matching Feishu **card v2** schema and
`deliver._apply_slash` sends it via `chat.send_card`
(`--msg-type interactive`) instead of plain text.

Builders are pure: no I/O, no env reads. `simple_card` is the
one-section constructor; `column_set_2/3` + `rich_card` build
multi-section layouts (used by /health and /usage). `beijing_stamp`
and `fenced_block` produce the timestamp suffix and monospace fence
that titles / bodies share.

We're on card v2 (`schema: "2.0"`) because v1's `lark_md` element
silently dropped fenced code blocks and nested lists. v2's
`markdown` element renders the full GFM subset.
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable


# Lark template colors that Feishu's web/mobile app actually renders. These
# are the only ones tested; others (orange, turquoise, etc.) work but
# render varies across mobile/desktop versions.
_VALID_COLORS = ("blue", "green", "red", "yellow", "grey", "purple",
                 "orange", "turquoise", "pink")


def _normalised_color(color: str) -> str:
    """Fall back to blue on any unrecognised template color so a typo can't
    bork the whole reply."""
    return color if color in _VALID_COLORS else "blue"


_MD_ESCAPE_TRANS = str.maketrans({
    "*": "\\*",
    "_": "\\_",
    "`": "\\`",
    "[": "\\[",
    "]": "\\]",
    "<": "\\<",
    ">": "\\>",
})


def _escape_md(text: object) -> str:
    """Escape Lark markdown metacharacters in dynamic card content.

    Interpolating raw task titles, agent names, blocker text, workflow IDs,
    or recommended actions into card markdown can accidentally start bold /
    italic / code / link / HTML spans. Escaping keeps the rendered card
    faithful to the source value.
    """
    return str(text).translate(_MD_ESCAPE_TRANS)


def simple_card(title: str, body: str, *, color: str = "blue") -> dict:
    """Single-section card v2: header + one markdown body element.

    `body` is rendered through Feishu's card v2 `markdown` element, which
    supports a fuller GFM subset than v1's `lark_md` text tag — including
    **fenced code blocks** (triple backticks) and **nested lists**, both
    of which v1 silently degraded to literal text. Empty `body` becomes
    a single space so the element validates.
    """
    return {
        "schema": "2.0",
        "header": {
            "title": {"content": title, "tag": "plain_text"},
            "template": _normalised_color(color),
        },
        "body": {
            "elements": [{"tag": "markdown", "content": body or " "}],
        },
    }


def beijing_stamp(now: Callable[[], datetime] = datetime.now) -> str:
    """Format `now()` as `YYYY-MM-DD HH:MM 北京时间` — the trailing
    suffix every card title uses (manager identity rule that all
    timestamps shown to the boss are in Beijing time)."""
    return f"{now().strftime('%Y-%m-%d %H:%M')} 北京时间"


def fenced_block(text: str) -> str:
    """Wrap `text` in a triple-backtick fence so monospace / box-drawing
    / ANSI artefacts survive Feishu's markdown collapsing (which would
    otherwise eat indentation and merge consecutive spaces)."""
    return f"```\n{text}\n```"


# ── rich card primitives (column_set + colored fonts) ──────


def col_cell(content: str, weight: int = 1) -> dict:
    """Single column cell containing one markdown element.

    Kept for backwards-compat with any external callers; production
    rebuild code path no longer uses this directly — see column_set_2
    / column_set_3 below for the inlined-markdown-row replacement."""
    return {"tag": "column", "width": "weighted", "weight": weight,
            "elements": [{"tag": "markdown", "content": content}]}


def column_set_3(cells: list[str]) -> dict:
    """3-cell section rendered as one markdown element with each cell
    its own paragraph (cells separated by `\\n\\n`). Feishu's
    `tag:"column_set"` renders stacked anyway (no real horizontal
    grid), so we collapse to paragraphs and accept the layout. Empty
    cells dropped so the body doesn't end with a dangling blank."""
    parts = [c for c in cells if c.strip()]
    return {"tag": "markdown",
            "content": "\n\n".join(parts) if parts else " "}


def column_set_2(left: str, right: str, **_legacy_kwargs) -> dict:
    """2-cell row rendered as a single markdown line `<left>: <right>`.

    Same rationale as `column_set_3`: Feishu's `column_set` tag does
    not render side-by-side in current builds, so we collapse to one
    line. `**Bold**` left labels stay bold naturally; the right cell
    can carry `<font color='…'>` spans + monospace ` markers.
    """
    return {"tag": "markdown", "content": f"{left}：{right}"}


def load_color(pct: int) -> str:
    """Traffic-light color for a load percentage. red≥80, orange≥50,
    green<50. Used for CPU / memory / disk percentages."""
    if pct >= 80:
        return "red"
    if pct >= 50:
        return "orange"
    return "green"


def remaining_color(pct: float) -> str:
    """Inverse of `load_color` — for `<remaining>%` displays where low
    is bad. red≤20, orange≤50, green>50."""
    if pct <= 20:
        return "red"
    if pct <= 50:
        return "orange"
    return "green"


def rich_card(title: str, elements: list, *, color: str = "blue") -> dict:
    """Card v2 with a pre-built `body.elements` list — for handlers
    that need multi-section layouts (/usage, /health) that
    `simple_card`'s single-element body can't express. v2 gives us
    GFM features (fenced blocks, nested lists, `<font color>` HTML)
    that v1's `lark_md` silently degrades."""
    return {
        "schema": "2.0",
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": _normalised_color(color),
        },
        "body": {"elements": elements or [
            {"tag": "markdown", "content": "(无内容)"}]},
    }


# ── M3: employee / team snapshot cards ────────────────────────────
#
# These two functions predate cards_v2.py and build v2-schema cards
# directly via `simple_card()`.  M9 (Card Protocol v2) added an
# `OPS_SNAPSHOT` card type so `say --card OPS_SNAPSHOT` can route
# through `validate_card` + `render_to_card_dict` for snapshot-like
# content, but the two paths intentionally coexist:
#
#   - /employees, /employee <agent> → employee_snapshot_card /
#     team_snapshot_card (this file, legacy M3 path)
#   - say --card OPS_SNAPSHOT      → cards_v2.build_card(...)
#     → validate_card + render_to_card_dict (M9 v2 path)
#
# The legacy M3 path uses a display-verdict → color mapping
# (`_verdict_color`); the v2 path uses severity → color
# (`SEVERITY_COLOR_MAP`).  Field names also differ: M3 uses
# `状态` `驻留` `下一步` `建议动作`; M9 OPS_SNAPSHOT uses
# `看板类型` `当前状态` `顶行动` `证据引用` `常驻摘要`.  Both
# produce schema=2.0 markdown cards.  Slash commands keep using
# the M3 path; explicit `say --card` calls keep using the M9 path.
# A future M3.5 could rewrite the M3 helpers to delegate to
# cards_v2 once the field set stabilises.


def _verdict_color(verdict: str) -> str:
    """Traffic-light color for a display verdict."""
    if verdict in ("blocked", "stopped"):
        return "red"
    if verdict in ("stale_display", "waiting_inbox"):
        return "yellow"
    if verdict in ("active", "idle", "warm_idle"):
        return "green"
    return "blue"


def employee_snapshot_card(snapshot: dict, *, title_suffix: str = "") -> dict:
    """Feishu card v2 for a single employee snapshot.

    Displays the fields required by the M3 spec: agent,
    display_verdict, declared_status, current_task,
    workflow_id/gate/next_action, staleness_reason,
    recommended_next_action, and residency_label/mode.
    """
    agent = _escape_md(snapshot.get("agent") or "unknown")
    verdict = _escape_md(snapshot.get("display_verdict") or "unknown")

    title = f"👤 {agent}"
    if title_suffix:
        title = f"{title} {_escape_md(title_suffix)}"

    lines: list[str] = [f"**状态**: {verdict}"]

    residency_label = _escape_md(snapshot.get("residency_label") or "")
    residency_mode = _escape_md(snapshot.get("residency_mode") or "")
    if residency_label or residency_mode:
        mode_part = f" ({residency_mode})" if residency_mode else ""
        lines.append(f"**驻留**: {residency_label}{mode_part}")

    declared_status = _escape_md(snapshot.get("declared_status") or "")
    if declared_status:
        lines.append(f"**声明状态**: {declared_status}")

    current_task = _escape_md(snapshot.get("current_task_title") or "")
    if not current_task:
        current_task = _escape_md(snapshot.get("declared_task") or "")
    if current_task:
        lines.append(f"**当前任务**: {current_task}")

    workflow_id = _escape_md(snapshot.get("workflow_id") or "")
    if workflow_id:
        lines.append(f"**工作流**: `{workflow_id}`")
    workflow_gate = _escape_md(snapshot.get("workflow_gate") or "")
    workflow_gate_status = _escape_md(snapshot.get("workflow_gate_status") or "")
    if workflow_gate:
        lines.append(
            f"**关口**: {workflow_gate} / {workflow_gate_status or '-'}"
        )
    workflow_next_action = _escape_md(snapshot.get("workflow_next_action") or "")
    if workflow_next_action:
        lines.append(f"**下一步**: {workflow_next_action}")

    staleness_reason = _escape_md(snapshot.get("staleness_reason") or "")
    if staleness_reason:
        lines.append(f"**陈旧原因**: {staleness_reason}")

    recommended_next_action = _escape_md(snapshot.get("recommended_next_action") or "")
    if recommended_next_action:
        lines.append(f"**建议动作**: {recommended_next_action}")

    degraded = _escape_md(snapshot.get("degraded") or "")
    if degraded:
        lines.append(f"<font color='grey'>degraded: {degraded}</font>")

    return simple_card(title, "\n".join(lines), color=_verdict_color(verdict))


def team_snapshot_card(dashboard: dict, *, title_suffix: str = "") -> dict:
    """Feishu card v2 for the team / ops dashboard snapshot.

    Displays summary counts, residency counts, top 3 actions,
    blocked/stale/waiting agents, and any degraded sources.
    """
    summary = dashboard.get("summary") or {}
    residency = dashboard.get("residency") or {}
    top_actions = dashboard.get("top_actions") or []
    employees = dashboard.get("employees") or []
    degraded = dashboard.get("degraded") or []

    title = "👥 团队状态快照"
    if title_suffix:
        title = f"{title} {_escape_md(title_suffix)}"

    elements: list = []

    summary_line = (
        f"**总计**: {summary.get('agents_total', 0)} agents · "
        f"活跃 {summary.get('active', 0)} · "
        f"外显陈旧 {summary.get('stale_display', 0)} · "
        f"高优未读 {summary.get('waiting_inbox', 0)} · "
        f"阻塞 {summary.get('blocked', 0)} · "
        f"温备空闲 {summary.get('warm_idle', 0)} · "
        f"空闲 {summary.get('idle', 0)} · "
        f"未知 {summary.get('unknown', 0)}"
    )
    elements.append({"tag": "markdown", "content": summary_line})

    residency_line = (
        f"**驻留**: 常驻 {residency.get('resident', 0)} · "
        f"温备 {residency.get('warm', 0)} · "
        f"冷备 {residency.get('cold', 0)} · "
        f"wake_failed {residency.get('wake_failed', 0)} · "
        f"sleep_candidates {residency.get('sleep_candidates', 0)}"
    )
    elements.append({"tag": "markdown", "content": residency_line})
    elements.append({"tag": "hr"})

    elements.append({"tag": "markdown", "content": "**🔥 Top 3 动作**"})
    if top_actions:
        for i, action in enumerate(top_actions[:3], 1):
            agent = _escape_md(action.get("agent") or "-")
            reason = _escape_md(action.get("reason") or "")
            recommended_next_action = _escape_md(
                action.get("recommended_next_action") or ""
            )
            elements.append({
                "tag": "markdown",
                "content": (
                    f"{i}. **{agent}**: {reason} → {recommended_next_action}"
                ),
            })
    else:
        elements.append({
            "tag": "markdown",
            "content": "<font color='grey'>暂无高优动作</font>",
        })

    elements.append({"tag": "hr"})

    flagged_verdicts = {"blocked", "stale_display", "waiting_inbox"}
    flagged = [
        emp for emp in employees
        if str(emp.get("display_verdict") or "") in flagged_verdicts
    ]
    elements.append({"tag": "markdown", "content": "**⚠️ 需关注员工**"})
    if flagged:
        emoji_map = {
            "blocked": "🔴",
            "stale_display": "🟡",
            "waiting_inbox": "📬",
        }
        for emp in flagged[:10]:
            verdict = _escape_md(emp.get("display_verdict") or "")
            emoji = emoji_map.get(str(emp.get("display_verdict") or ""), "⚠️")
            task = _escape_md(
                emp.get("current_task_title")
                or emp.get("declared_task")
                or "-"
            )
            elements.append({
                "tag": "markdown",
                "content": f"{emoji} **{_escape_md(emp.get('agent'))}** [{verdict}] {task}",
            })
    else:
        elements.append({
            "tag": "markdown",
            "content": "<font color='grey'>无阻塞/陈旧/未读员工</font>",
        })

    if degraded:
        elements.append({"tag": "hr"})
        elements.append({"tag": "markdown", "content": "**⚠️ 降级来源**"})
        for item in degraded:
            if isinstance(item, dict):
                elements.append({
                    "tag": "markdown",
                    "content": (
                        f"- `{_escape_md(item.get('source'))}`: "
                        f"{_escape_md(item.get('error_type'))}: {_escape_md(item.get('message'))}"
                    ),
                })
            else:
                elements.append({
                    "tag": "markdown",
                    "content": f"- {_escape_md(item)}",
                })

    # Header color: red if anyone is blocked or has high-priority unread,
    # yellow if stale or degraded sources exist, green otherwise.
    color = "green"
    if summary.get("blocked", 0) > 0 or summary.get("waiting_inbox", 0) > 0:
        color = "red"
    elif summary.get("stale_display", 0) > 0 or degraded:
        color = "yellow"

    return rich_card(title, elements, color=color)
