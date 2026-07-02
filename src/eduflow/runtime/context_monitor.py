"""Context-window usage parsing shared by health and manager guards."""
from __future__ import annotations

import re
from dataclasses import dataclass


WARN_THRESHOLD_PCT = 80.0
COMPACT_THRESHOLD_PCT = 90.0

_HARD_EXHAUSTION_MARKERS = (
    "context window exceeds limit",
    "100% context used",
    "context used 100%",
    "interrupted prompt",
)

_PCT_PATTERNS = (
    re.compile(r"\bcontext\s*:\s*(\d+(?:\.\d+)?)\s*%", re.IGNORECASE),
    re.compile(r"\b(\d+(?:\.\d+)?)\s*%\s+context(?:\s+used)?\b", re.IGNORECASE),
    re.compile(r"\bcontext\s+used\s+(\d+(?:\.\d+)?)\s*%", re.IGNORECASE),
    re.compile(
        r"\bcontext\s+(?:at|is|was|reached)\s+"
        r"(?:~|about\s+|around\s+)?(\d+(?:\.\d+)?)\s*%",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class ContextUsageSignal:
    percent: float | None
    level: str
    marker: str

    @property
    def exhausted(self) -> bool:
        return self.level == "exhausted"

    @property
    def compact_recommended(self) -> bool:
        return self.level == "compact_recommended"

    @property
    def warning(self) -> bool:
        return self.level == "warning"


def detect_context_usage(text: str) -> ContextUsageSignal | None:
    """Return the strongest context-window signal found in ``text``.

    The monitor intentionally warns before failure and leaves execution policy
    to callers: 80-89% is visibility-only, 90-99% recommends compact/reidentify,
    and 100% or explicit context-limit markers are exhausted.
    """
    value = str(text or "")
    lowered = value.lower()
    for marker in _HARD_EXHAUSTION_MARKERS:
        if marker in lowered:
            return ContextUsageSignal(100.0, "exhausted", marker)

    pct_values: list[float] = []
    for pattern in _PCT_PATTERNS:
        for match in pattern.finditer(value):
            try:
                pct_values.append(float(match.group(1)))
            except ValueError:
                continue
    if not pct_values:
        return None

    percent = max(pct_values)
    marker = f"context_usage={percent:g}%"
    if percent >= 100.0:
        return ContextUsageSignal(percent, "exhausted", marker)
    if percent >= COMPACT_THRESHOLD_PCT:
        return ContextUsageSignal(percent, "compact_recommended", marker)
    if percent >= WARN_THRESHOLD_PCT:
        return ContextUsageSignal(percent, "warning", marker)
    return None
