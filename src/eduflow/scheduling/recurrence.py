"""Pure recurrence kernel for D scheduled tasks.

Accepts display/parse input in the configured timezone (typically
Asia/Shanghai) and emits persisted UTC datetimes.  All core functions
receive an explicit `now` parameter and never call datetime.now().

Supported frequencies: once, daily, weekly.
Unsupported or ambiguous input returns a structured error dict instead
of raising, so callers (e.g. the manager skill) can decide whether to
ask the user for clarification.
"""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones


SUPPORTED_FREQUENCIES = frozenset({"once", "daily", "weekly"})

# Relative / ambiguous markers that the kernel refuses to resolve.
FUZZY_NATURAL_MARKERS = (
    "下周",
    "周末",
    "下午",
    "每隔",
    "明天",
    "后天",
    "昨晚",
    "今早",
)

_WEEKDAY_NAMES = {
    # English
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
    # Chinese
    "周一": 0,
    "星期二": 1,
    "周二": 1,
    "星期三": 2,
    "周三": 2,
    "星期四": 3,
    "周四": 3,
    "星期五": 4,
    "周五": 4,
    "星期六": 5,
    "周六": 5,
    "星期日": 6,
    "星期天": 6,
    "周日": 6,
}

_TIME_RE = re.compile(r"^([0-9]{1,2}):([0-9]{2})$")


def _error(error_code: str, message: str) -> dict:
    return {"ok": False, "error_code": error_code, "message": message}


def _ok(frequency: str, next_due_utc: datetime, timezone_name: str, local_time: datetime) -> dict:
    return {
        "ok": True,
        "frequency": frequency,
        "next_due_utc": next_due_utc.isoformat(),
        "display": {
            "timezone": timezone_name,
            "local": local_time.strftime("%Y-%m-%d %H:%M"),
        },
    }


def _detect_fuzzy(text: str) -> bool:
    return any(marker in text for marker in FUZZY_NATURAL_MARKERS)


def _parse_time(token: str) -> tuple[int, int] | None:
    match = _TIME_RE.match(token.strip())
    if match is None:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour, minute


def _parse_weekday(token: str) -> int | None:
    token = token.strip()
    # Numeric 1-7, where 1 = Monday and 7 = Sunday.
    if token.isdigit():
        value = int(token)
        if 1 <= value <= 7:
            return (value - 1) % 7
        return None
    return _WEEKDAY_NAMES.get(token.lower())


def _load_timezone(timezone_name: str) -> ZoneInfo | None:
    name = (timezone_name or "").strip()
    if not name or name not in available_timezones():
        return None
    return ZoneInfo(name)


def _ensure_local_now(now: datetime, tz: ZoneInfo) -> datetime:
    """Return `now` expressed in `tz`, treating naive datetimes as UTC."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(tz)


def _date_for_weekday(today: datetime, weekday: int) -> date:
    """Return the date of the target weekday within the current ISO week."""
    days_ahead = (weekday - today.weekday()) % 7
    return (today.date() + timedelta(days=days_ahead))


def compute_next_due_utc(
    frequency: str,
    local_time: datetime,
    now: datetime,
    tz: ZoneInfo,
) -> datetime:
    """Return the next due datetime in UTC for a supported frequency.

    `local_time` is the first candidate in `tz`.  It is rolled forward by
    one period (day or week) when it is not strictly after `now`.  For
    `once`, `local_time` is returned as-is in UTC.
    """
    if frequency not in SUPPORTED_FREQUENCIES:
        raise ValueError(f"unsupported frequency: {frequency}")
    if local_time.tzinfo is None:
        local_time = local_time.replace(tzinfo=tz)
    now_local = _ensure_local_now(now, tz)

    if frequency == "once":
        return local_time.astimezone(timezone.utc)

    if frequency == "daily":
        candidate = local_time
        if candidate <= now_local:
            candidate = candidate + timedelta(days=1)
        return candidate.astimezone(timezone.utc)

    # weekly
    candidate = local_time
    if candidate <= now_local:
        candidate = candidate + timedelta(weeks=1)
    return candidate.astimezone(timezone.utc)


def parse_schedule(text: str, timezone_name: str, now: datetime) -> dict:
    """Parse a structured schedule string and return the next due UTC.

    Input is displayed/parsed in `timezone_name`; persisted due time is
    returned as an ISO 8601 UTC string.

    Returns either::

        {"ok": True, "frequency": ..., "next_due_utc": ..., "display": {...}}

    or::

        {"ok": False, "error_code": ..., "message": ...}
    """
    if _detect_fuzzy(text):
        return _error(
            "fuzzy_natural_language",
            "Natural language relative times (e.g. 下周, 周末, 下午, 每隔一段时间) "
            "must be clarified before scheduling.",
        )

    tz = _load_timezone(timezone_name)
    if tz is None:
        return _error(
            "unknown_timezone",
            f"unknown or unsupported timezone: {timezone_name!r}",
        )

    now_local = _ensure_local_now(now, tz)
    tokens = text.strip().split()
    if not tokens:
        return _error("missing_frequency", "schedule text is empty")

    frequency = tokens[0].strip().lower()
    if frequency not in SUPPORTED_FREQUENCIES:
        return _error(
            "invalid_frequency",
            f"invalid frequency: {frequency!r} (valid: {sorted(SUPPORTED_FREQUENCIES)})",
        )

    rest = tokens[1:]

    if frequency == "once":
        if len(rest) < 2:
            return _error(
                "missing_time",
                "once schedule requires a date and time, e.g. 'once 2026-07-15 14:30'",
            )
        date_token, time_token = rest[0], rest[1]
        parsed_time = _parse_time(time_token)
        if parsed_time is None:
            return _error(
                "invalid_time_format",
                f"invalid time: {time_token!r} (expected HH:MM)",
            )
        try:
            date = datetime.strptime(date_token, "%Y-%m-%d").date()
        except ValueError:
            return _error(
                "invalid_date_format",
                f"invalid date: {date_token!r} (expected YYYY-MM-DD)",
            )
        local_time = datetime(
            date.year, date.month, date.day,
            parsed_time[0], parsed_time[1],
            tzinfo=tz,
        )
        if local_time <= now_local:
            return _error(
                "past_once_time",
                f"once schedule time {local_time.strftime('%Y-%m-%d %H:%M')} "
                f"is in the past (now {now_local.strftime('%Y-%m-%d %H:%M')}).",
            )
        due = compute_next_due_utc("once", local_time, now, tz)
        return _ok(frequency, due, timezone_name, local_time)

    # daily / weekly need a time token.
    if frequency == "daily":
        if not rest:
            return _error(
                "missing_time",
                "daily schedule requires a time, e.g. 'daily 09:00'",
            )
        time_token = rest[0]
        parsed_time = _parse_time(time_token)
        if parsed_time is None:
            return _error(
                "invalid_time_format",
                f"invalid time: {time_token!r} (expected HH:MM)",
            )
        local_time = datetime.combine(
            now_local.date(),
            time(parsed_time[0], parsed_time[1]),
        ).replace(tzinfo=tz)
        due = compute_next_due_utc("daily", local_time, now, tz)
        return _ok(frequency, due, timezone_name, due.astimezone(tz))

    # weekly
    if len(rest) < 1:
        return _error(
            "missing_weekday",
            "weekly schedule requires a weekday and time, e.g. 'weekly Monday 09:00'",
        )
    weekday_token = rest[0]
    if _parse_time(weekday_token) is not None:
        return _error(
            "missing_weekday",
            "weekly schedule requires a weekday before the time, e.g. 'weekly Monday 09:00'",
        )
    weekday = _parse_weekday(weekday_token)
    if weekday is None:
        return _error(
            "invalid_weekday",
            f"invalid weekday: {weekday_token!r}",
        )
    if len(rest) < 2:
        return _error(
            "missing_time",
            "weekly schedule requires a time after the weekday, e.g. 'weekly Monday 09:00'",
        )
    time_token = rest[1]
    parsed_time = _parse_time(time_token)
    if parsed_time is None:
        return _error(
            "invalid_time_format",
            f"invalid time: {time_token!r} (expected HH:MM)",
        )
    target_date = _date_for_weekday(now_local, weekday)
    local_time = datetime(
        target_date.year, target_date.month, target_date.day,
        parsed_time[0], parsed_time[1],
        tzinfo=tz,
    )
    due = compute_next_due_utc("weekly", local_time, now, tz)
    return _ok(frequency, due, timezone_name, due.astimezone(tz))
