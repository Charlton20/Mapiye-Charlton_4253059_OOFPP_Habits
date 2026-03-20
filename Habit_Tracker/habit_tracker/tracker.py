"""Core HabitTracker orchestration class."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from . import analytics
from .fixtures import build_predefined_habits
from .models import Habit, Periodicity, ensure_utc


class HabitTracker:
    """High-level API used by CLI and tests."""

    def __init__(self, database):
        self.database = database
        self.habits = []
        self._by_id = {}
        self.refresh()

    def refresh(self):
        """Reload habits from storage."""
        self.habits = self.database.load_habits()
        # Keep an index for fast id lookups during CLI operations.
        self._by_id = {habit.id: habit for habit in self.habits}

    def add_habit(
        self,
        habit=None,
        name=None,
        periodicity=None,
        creation_date=None,
        habit_id=None,
    ):
        """Create or save a habit."""
        if habit is None:
            if name is None or periodicity is None:
                raise ValueError("name and periodicity are required when habit is not provided")
            periodicity_value = (
                periodicity if isinstance(periodicity, Periodicity) else Periodicity.from_value(periodicity)
            )
            habit = Habit(
                id=habit_id or str(uuid4()),
                name=name,
                periodicity=periodicity_value,
                creation_date=ensure_utc(creation_date or datetime.now(timezone.utc)),
            )
        else:
            # Normalize imported habits to UTC before persisting.
            habit.creation_date = ensure_utc(habit.creation_date)
            habit.completion_dates = [ensure_utc(ts) for ts in habit.completion_dates]

        self.database.save_habit(habit)
        self.refresh()
        return self._by_id[habit.id]

    def delete_habit(self, habit_id):
        self.database.delete_habit(habit_id)
        self.refresh()

    def list_habits(self):
        # Kept as a functional call to satisfy analytics-module requirements.
        return analytics.all_habits(self.habits)

    def get_habits_by_periodicity(self, periodicity):
        periodicity_value = (
            periodicity if isinstance(periodicity, Periodicity) else Periodicity.from_value(periodicity)
        )
        return analytics.habits_by_periodicity(self.habits, periodicity_value)

    def mark_completed(self, habit_id, completed_at=None):
        habit = self._by_id.get(habit_id)
        if habit is None:
            raise KeyError("Habit not found: {0}".format(habit_id))

        timestamp = ensure_utc(completed_at or datetime.now(timezone.utc))
        self.database.save_completion(habit_id, timestamp)
        # Update in-memory state immediately; refresh keeps storage and memory aligned.
        habit.complete_task(timestamp)
        self.refresh()
        return timestamp

    def get_longest_streak(self, habit_id=None):
        if habit_id:
            habit = self._by_id.get(habit_id)
            if habit is None:
                raise KeyError("Habit not found: {0}".format(habit_id))
            return analytics.longest_streak_for_habit(habit)

        return analytics.longest_streak_all_habits(self.habits)

    def get_all_longest_streaks(self):
        return analytics.all_longest_streaks(self.habits)

    def get_consistency_trends(self, start, end, limit=5):
        return analytics.least_consistent_habits(self.habits, start=start, end=end, limit=limit)

    def get_habit(self, habit_id):
        return self._by_id.get(habit_id)

    def seed_predefined_data(self, replace_existing=False):
        """
        Seed 5 predefined habits with 4 weeks of example data.

        Returns number of habits inserted.
        """
        if replace_existing:
            # Start clean when explicitly requested.
            for habit in list(self.habits):
                self.database.delete_habit(habit.id)
            self.refresh()

        existing_ids = {habit.id for habit in self.habits}
        inserted = 0

        for habit, completions in build_predefined_habits():
            if habit.id in existing_ids:
                continue
            self.database.save_habit(habit)
            for completion in completions:
                self.database.save_completion(habit.id, completion)
            inserted += 1

        self.refresh()
        return inserted
