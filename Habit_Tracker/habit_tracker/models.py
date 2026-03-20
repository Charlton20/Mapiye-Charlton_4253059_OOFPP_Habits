"""Domain models for the habit tracker."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Iterable, List, Optional


class Periodicity(str, Enum):
    """Supported periodicity options for habits."""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"

    @classmethod
    def from_value(cls, value):
        # Accept a few friendly aliases from CLI input.
        normalized = value.strip().upper()
        if normalized == "DAY":
            normalized = "DAILY"
        if normalized == "WEEK":
            normalized = "WEEKLY"
        return cls(normalized)


@dataclass
class Habit:
    """Represents a habit and its completion history."""

    id: str
    name: str
    periodicity: Periodicity
    creation_date: datetime
    completion_dates: List[datetime] = field(default_factory=list)

    def complete_task(self, completed_at=None):
        """Record completion for this habit."""
        timestamp = ensure_utc(completed_at or datetime.now(timezone.utc))
        self.completion_dates.append(timestamp)
        # Keep dates sorted so streak calculations are deterministic.
        self.completion_dates.sort()
        return timestamp

    def get_streak(self):
        """Return the longest streak for this habit."""
        return longest_streak_for_dates(self.completion_dates, self.periodicity)


def longest_streak_for_dates(completion_dates, periodicity):
    """Compute longest consecutive-period streak from completion timestamps."""
    # Multiple check-offs in the same period still count as one period success.
    periods = sorted({_period_start(ts, periodicity) for ts in completion_dates})
    if not periods:
        return 0

    # Daily streaks advance by 1 day; weekly streaks advance by 7 days.
    step = timedelta(days=1 if periodicity == Periodicity.DAILY else 7)
    longest = 1
    current = 1

    for previous, current_period in zip(periods, periods[1:]):
        if current_period - previous == step:
            current += 1
        else:
            current = 1
        if current > longest:
            longest = current

    return longest


def _period_start(timestamp, periodicity):
    """Normalize a timestamp to its period boundary."""
    day = timestamp.date()
    if periodicity == Periodicity.DAILY:
        return day
    # Weekly periods are bucketed from Monday.
    return day - timedelta(days=day.weekday())


def ensure_utc(timestamp):
    """Normalize datetime as timezone-aware UTC."""
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)
