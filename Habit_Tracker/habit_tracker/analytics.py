"""Functional analytics module for habit calculations."""

from __future__ import annotations

from datetime import timedelta

from .models import Periodicity, longest_streak_for_dates


def all_habits(habits):
    """Return all tracked habits as a list."""
    return list(habits)


def habits_by_periodicity(habits, periodicity):
    """Return habits filtered by periodicity."""
    return [habit for habit in habits if habit.periodicity == periodicity]


def longest_streak_for_habit(habit):
    """Return longest streak for one habit."""
    return longest_streak_for_dates(habit.completion_dates, habit.periodicity)


def all_longest_streaks(habits):
    """Return longest streak per habit id."""
    return {habit.id: longest_streak_for_habit(habit) for habit in habits}


def overall_longest_streak(habits):
    """Return the habit with longest streak and streak value."""
    best_habit = None
    best_streak = 0

    # Single scan across all habits to find the maximum streak.
    for habit in habits:
        streak = longest_streak_for_habit(habit)
        if streak > best_streak:
            best_habit = habit
            best_streak = streak

    return best_habit, best_streak


def longest_streak_all_habits(habits):
    """Return only the longest streak value across all tracked habits."""
    _, streak = overall_longest_streak(habits)
    return streak


def least_consistent_habits(habits, start, end, limit=5):
    """Return habits ordered by lowest consistency ratio in the date range."""
    scored = []
    for habit in habits:
        ratio = consistency_ratio(habit, start=start, end=end)
        scored.append((habit, ratio))

    # Low consistency first, because these are the habits users struggle with most.
    scored.sort(key=lambda pair: pair[1])
    return scored[: max(limit, 0)]


def consistency_ratio(habit, start, end):
    """
    Consistency ratio in [0, 1]:
    completed periods divided by expected periods in the window.
    """
    if end < start:
        return 0.0

    expected = _expected_period_count(start, end, habit.periodicity)
    if expected <= 0:
        return 0.0

    # Count unique completed periods to avoid over-counting multiple check-offs.
    completed_periods = {
        _period_bucket(timestamp.date(), habit.periodicity)
        for timestamp in habit.completion_dates
        if start <= timestamp <= end
    }
    return min(1.0, float(len(completed_periods)) / float(expected))


def _expected_period_count(start, end, periodicity):
    """Calculate how many periods should exist in a date range."""
    if periodicity == Periodicity.DAILY:
        return (end.date() - start.date()).days + 1

    current = _period_bucket(start.date(), periodicity)
    last = _period_bucket(end.date(), periodicity)
    count = 0
    while current <= last:
        count += 1
        current = current + timedelta(days=7)
    return count


def _period_bucket(day, periodicity):
    """Map a calendar day to the period key used for analytics grouping."""
    if periodicity == Periodicity.DAILY:
        return day
    return day - timedelta(days=day.weekday())
