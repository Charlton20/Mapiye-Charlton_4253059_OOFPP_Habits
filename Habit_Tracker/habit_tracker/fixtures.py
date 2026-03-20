"""Predefined habits and four-week sample tracking data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import Habit, Periodicity


def build_predefined_habits():
    """
    Return 5 predefined habits with 4 weeks of completion data.

    Includes at least one daily and one weekly habit.
    """
    # Monday baseline keeps weekly-period examples easy to reason about.
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=timezone.utc)

    def day_offsets(offsets, hour=8):
        """Build deterministic timestamps from day offsets."""
        return [start + timedelta(days=offset, hours=(hour - 8)) for offset in offsets]

    predefined = []

    # Daily habit: mostly consistent, with a few missed days.
    predefined.append(
        (
            Habit(
                id="habit-morning-run",
                name="Morning Run",
                periodicity=Periodicity.DAILY,
                creation_date=start - timedelta(days=3),
            ),
            day_offsets(
                [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    8,
                    9,
                    10,
                    11,
                    12,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                    27,
                ]
            ),
        )
    )

    # Daily habit: fully consistent for all 4 weeks.
    predefined.append(
        (
            Habit(
                id="habit-read-20",
                name="Read 20 Minutes",
                periodicity=Periodicity.DAILY,
                creation_date=start - timedelta(days=2),
            ),
            day_offsets(list(range(0, 28)), hour=21),
        )
    )

    # Daily habit: irregular pattern for trend analysis.
    predefined.append(
        (
            Habit(
                id="habit-meditation",
                name="Meditation",
                periodicity=Periodicity.DAILY,
                creation_date=start - timedelta(days=1),
            ),
            day_offsets(
                [
                    0,
                    2,
                    3,
                    4,
                    6,
                    7,
                    8,
                    10,
                    12,
                    13,
                    14,
                    15,
                    17,
                    18,
                    20,
                    21,
                    22,
                    24,
                    26,
                    27,
                ],
                hour=6,
            ),
        )
    )

    # Weekly habit: complete every week.
    predefined.append(
        (
            Habit(
                id="habit-meal-prep",
                name="Meal Prep",
                periodicity=Periodicity.WEEKLY,
                creation_date=start - timedelta(days=7),
            ),
            day_offsets([0, 7, 14, 21], hour=17),
        )
    )

    # Weekly habit: one missed week.
    predefined.append(
        (
            Habit(
                id="habit-budget-review",
                name="Budget Review",
                periodicity=Periodicity.WEEKLY,
                creation_date=start - timedelta(days=7),
            ),
            day_offsets([0, 7, 21], hour=19),
        )
    )

    return predefined
