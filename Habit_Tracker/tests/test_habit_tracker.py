"""Unit tests for critical habit tracking and analytics behavior."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from habit_tracker import analytics
from habit_tracker.database import DatabaseLayer
from habit_tracker.models import Periodicity
from habit_tracker.tracker import HabitTracker


class HabitTrackerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_habits.db"
        self.database = DatabaseLayer(str(self.db_path))
        self.tracker = HabitTracker(self.database)

    def tearDown(self):
        self.database.close()
        self.temp_dir.cleanup()

    def test_add_and_list_habits(self):
        self.tracker.add_habit(name="Drink Water", periodicity=Periodicity.DAILY)
        habits = self.tracker.list_habits()
        self.assertEqual(1, len(habits))
        self.assertEqual("Drink Water", habits[0].name)

    def test_filter_habits_by_periodicity(self):
        self.tracker.add_habit(name="Workout", periodicity=Periodicity.DAILY)
        self.tracker.add_habit(name="Meal Prep", periodicity=Periodicity.WEEKLY)

        daily = self.tracker.get_habits_by_periodicity(Periodicity.DAILY)
        weekly = self.tracker.get_habits_by_periodicity(Periodicity.WEEKLY)

        self.assertEqual(1, len(daily))
        self.assertEqual(1, len(weekly))
        self.assertEqual("Workout", daily[0].name)
        self.assertEqual("Meal Prep", weekly[0].name)

    def test_daily_longest_streak(self):
        habit = self.tracker.add_habit(name="Read", periodicity=Periodicity.DAILY)
        base = datetime(2026, 1, 1, 7, 0, 0)
        for offset in [0, 1, 2, 4]:
            self.tracker.mark_completed(habit.id, base + timedelta(days=offset))

        self.assertEqual(3, self.tracker.get_longest_streak(habit.id))

    def test_weekly_longest_streak(self):
        habit = self.tracker.add_habit(name="Budget", periodicity=Periodicity.WEEKLY)
        base = datetime(2026, 1, 5, 9, 0, 0)  # Monday
        for day_offset in [0, 7, 14, 28]:
            self.tracker.mark_completed(habit.id, base + timedelta(days=day_offset))

        self.assertEqual(3, self.tracker.get_longest_streak(habit.id))

    def test_analytics_required_outputs(self):
        first = self.tracker.add_habit(name="Study", periodicity=Periodicity.DAILY)
        second = self.tracker.add_habit(name="Plan Week", periodicity=Periodicity.WEEKLY)
        base = datetime(2026, 2, 2, 8, 0, 0)

        for offset in [0, 1, 2, 3]:
            self.tracker.mark_completed(first.id, base + timedelta(days=offset))
        for offset in [0, 7]:
            self.tracker.mark_completed(second.id, base + timedelta(days=offset))

        all_habits = analytics.all_habits(self.tracker.list_habits())
        self.assertEqual(2, len(all_habits))

        daily_only = analytics.habits_by_periodicity(all_habits, Periodicity.DAILY)
        self.assertEqual(1, len(daily_only))

        first_current = self.tracker.get_habit(first.id)
        self.assertEqual(4, analytics.longest_streak_for_habit(first_current))
        self.assertEqual(4, analytics.longest_streak_all_habits(all_habits))

    def test_seed_predefined_data(self):
        inserted = self.tracker.seed_predefined_data()
        habits = self.tracker.list_habits()

        self.assertEqual(5, inserted)
        self.assertEqual(5, len(habits))
        periodicities = {habit.periodicity for habit in habits}
        self.assertIn(Periodicity.DAILY, periodicities)
        self.assertIn(Periodicity.WEEKLY, periodicities)

    def test_persistence_between_sessions(self):
        created = self.tracker.add_habit(name="Journal", periodicity=Periodicity.DAILY)
        self.tracker.mark_completed(created.id, datetime(2026, 3, 1, 9, 0, 0))

        self.database.close()
        reopened_db = DatabaseLayer(str(self.db_path))
        reopened_tracker = HabitTracker(reopened_db)
        try:
            loaded = reopened_tracker.get_habit(created.id)
            self.assertIsNotNone(loaded)
            self.assertEqual("Journal", loaded.name)
            self.assertEqual(1, len(loaded.completion_dates))
        finally:
            reopened_db.close()


if __name__ == "__main__":
    unittest.main()
