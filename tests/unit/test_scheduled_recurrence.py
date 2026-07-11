"""P2: recurrence kernel for D scheduled tasks.

Tests parse_schedule and next-due computation:
- once/daily/weekly frequencies only
- Asia/Shanghai display, UTC persistence
- explicit `now` parameter drives all time decisions
- structured errors for past once, unknown timezone, malformed weekly,
  unsupported frequencies, and fuzzy natural language.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from eduflow.scheduling.recurrence import (
    compute_next_due_utc,
    parse_schedule,
)


# ── parse_schedule: once ─────────────────────────────────────────────


def test_once_future_returns_utc_due():
    now = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)  # 18:00 Shanghai
    result = parse_schedule("once 2026-07-15 14:30", "Asia/Shanghai", now)
    assert result["ok"] is True
    assert result["frequency"] == "once"
    assert result["next_due_utc"] == "2026-07-15T06:30:00+00:00"
    assert result["display"]["timezone"] == "Asia/Shanghai"
    assert result["display"]["local"] == "2026-07-15 14:30"


def test_once_past_returns_structured_error():
    now = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule("once 2026-07-10 14:30", "Asia/Shanghai", now)
    assert result["ok"] is False
    assert result["error_code"] == "past_once_time"
    assert "past" in result["message"].lower()


def test_once_missing_time_returns_error():
    now = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule("once 2026-07-15", "Asia/Shanghai", now)
    assert result["ok"] is False
    assert result["error_code"] == "missing_time"


# ── parse_schedule: daily ────────────────────────────────────────────


def test_daily_before_time_today_returns_today():
    now = datetime(2026, 7, 12, 6, 0, 0, tzinfo=timezone.utc)  # 14:00 Shanghai
    result = parse_schedule("daily 15:00", "Asia/Shanghai", now)
    assert result["ok"] is True
    assert result["frequency"] == "daily"
    assert result["next_due_utc"] == "2026-07-12T07:00:00+00:00"


def test_daily_after_time_today_returns_next_day():
    now = datetime(2026, 7, 12, 14, 0, 0, tzinfo=timezone.utc)  # 22:00 Shanghai
    result = parse_schedule("daily 15:00", "Asia/Shanghai", now)
    assert result["ok"] is True
    assert result["next_due_utc"] == "2026-07-13T07:00:00+00:00"


def test_daily_cross_day_boundary():
    # 22:00 UTC == 06:00+1 Shanghai; 05:00 Shanghai has already passed.
    now = datetime(2026, 7, 12, 22, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule("daily 05:00", "Asia/Shanghai", now)
    assert result["ok"] is True
    assert result["next_due_utc"] == "2026-07-13T21:00:00+00:00"


def test_daily_missing_time_returns_error():
    now = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule("daily", "Asia/Shanghai", now)
    assert result["ok"] is False
    assert result["error_code"] == "missing_time"


# ── parse_schedule: weekly ───────────────────────────────────────────


def test_weekly_this_week_when_time_not_yet_passed():
    # 2026-07-13 is Monday. 00:00 UTC == 08:00 Shanghai.
    now = datetime(2026, 7, 13, 0, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule("weekly Monday 10:00", "Asia/Shanghai", now)
    assert result["ok"] is True
    assert result["frequency"] == "weekly"
    assert result["next_due_utc"] == "2026-07-13T02:00:00+00:00"


def test_weekly_next_week_when_time_already_passed():
    now = datetime(2026, 7, 13, 6, 0, 0, tzinfo=timezone.utc)  # 14:00 Monday Shanghai
    result = parse_schedule("weekly Monday 10:00", "Asia/Shanghai", now)
    assert result["ok"] is True
    assert result["next_due_utc"] == "2026-07-20T02:00:00+00:00"


def test_weekly_chinese_weekday_supported():
    now = datetime(2026, 7, 13, 0, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule("weekly 周一 10:00", "Asia/Shanghai", now)
    assert result["ok"] is True
    assert result["next_due_utc"] == "2026-07-13T02:00:00+00:00"


def test_weekly_numeric_weekday_supported():
    now = datetime(2026, 7, 13, 0, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule("weekly 1 10:00", "Asia/Shanghai", now)
    assert result["ok"] is True
    assert result["next_due_utc"] == "2026-07-13T02:00:00+00:00"


def test_weekly_missing_weekday_returns_error():
    now = datetime(2026, 7, 13, 0, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule("weekly 10:00", "Asia/Shanghai", now)
    assert result["ok"] is False
    assert result["error_code"] == "missing_weekday"


def test_weekly_missing_time_returns_error():
    now = datetime(2026, 7, 13, 0, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule("weekly Monday", "Asia/Shanghai", now)
    assert result["ok"] is False
    assert result["error_code"] == "missing_time"


def test_weekly_unknown_weekday_returns_error():
    now = datetime(2026, 7, 13, 0, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule("weekly someday 10:00", "Asia/Shanghai", now)
    assert result["ok"] is False
    assert result["error_code"] == "invalid_weekday"


# ── invalid frequency / timezone / time format ───────────────────────


@pytest.mark.parametrize("freq", ["monthly", "cron", "interval"])
def test_unsupported_frequency_returns_error(freq):
    now = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule(f"{freq} 10:00", "Asia/Shanghai", now)
    assert result["ok"] is False
    assert result["error_code"] == "invalid_frequency"


def test_unknown_timezone_returns_error():
    now = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule("daily 10:00", "Mars/Valles", now)
    assert result["ok"] is False
    assert result["error_code"] == "unknown_timezone"


def test_invalid_time_format_returns_error():
    now = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule("daily 25:00", "Asia/Shanghai", now)
    assert result["ok"] is False
    assert result["error_code"] == "invalid_time_format"


# ── fuzzy natural language rejection ─────────────────────────────────


@pytest.mark.parametrize("phrase", ["下周", "周末", "下午", "每隔一段时间", "明天"])
def test_fuzzy_natural_language_returns_error(phrase):
    now = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)
    result = parse_schedule(f"daily 10:00 {phrase}", "Asia/Shanghai", now)
    assert result["ok"] is False
    assert result["error_code"] == "fuzzy_natural_language"


# ── compute_next_due_utc helper ──────────────────────────────────────


def test_compute_next_due_utc_daily():
    tz = ZoneInfo("Asia/Shanghai")
    now = datetime(2026, 7, 12, 14, 0, 0, tzinfo=timezone.utc)  # 22:00 Shanghai
    local_time = datetime(2026, 7, 12, 15, 0, tzinfo=tz)
    due = compute_next_due_utc("daily", local_time, now, tz)
    assert due.isoformat() == "2026-07-13T07:00:00+00:00"


def test_compute_next_due_utc_weekly_rolls_forward():
    tz = ZoneInfo("Asia/Shanghai")
    now = datetime(2026, 7, 13, 6, 0, 0, tzinfo=timezone.utc)  # Monday 14:00 Shanghai
    local_time = datetime(2026, 7, 13, 10, 0, tzinfo=tz)  # Monday 10:00 Shanghai
    due = compute_next_due_utc("weekly", local_time, now, tz)
    assert due.isoformat() == "2026-07-20T02:00:00+00:00"
