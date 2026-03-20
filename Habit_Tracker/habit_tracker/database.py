"""SQLite database layer for habit persistence."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from .models import Habit, Periodicity, ensure_utc


class DatabaseLayer:
    """Persistence adapter around SQLite."""

    def __init__(self, db_path="habit_tracker.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        # Enforce referential integrity so orphan completions are not possible.
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self.initialize()

    def initialize(self):
        """Create tables if they do not exist."""
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS habits (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    periodicity TEXT NOT NULL CHECK (periodicity IN ('DAILY', 'WEEKLY')),
                    creation_date TEXT NOT NULL
                );
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS completions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    FOREIGN KEY (habit_id) REFERENCES habits (id) ON DELETE CASCADE
                );
                """
            )

    def save_habit(self, habit):
        """Insert or update a habit record."""
        with self.connection:
            # Upsert keeps writes idempotent when seeding or re-saving existing habits.
            self.connection.execute(
                """
                INSERT INTO habits (id, name, periodicity, creation_date)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    periodicity = excluded.periodicity,
                    creation_date = excluded.creation_date;
                """,
                (
                    habit.id,
                    habit.name,
                    habit.periodicity.value,
                    ensure_utc(habit.creation_date).isoformat(),
                ),
            )

    def delete_habit(self, habit_id):
        """Delete a habit and related completions."""
        with self.connection:
            self.connection.execute("DELETE FROM habits WHERE id = ?;", (habit_id,))

    def save_completion(self, habit_id, completed_at):
        """Insert a completion event."""
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO completions (habit_id, completed_at)
                VALUES (?, ?);
                """,
                (habit_id, ensure_utc(completed_at).isoformat()),
            )

    def load_habits(self):
        """Load all habits with completion history."""
        habits_cursor = self.connection.execute(
            """
            SELECT id, name, periodicity, creation_date
            FROM habits
            ORDER BY creation_date ASC;
            """
        )
        rows = habits_cursor.fetchall()

        # Build habit objects first, then attach completion rows in a second pass.
        habits = {
            row["id"]: Habit(
                id=row["id"],
                name=row["name"],
                periodicity=Periodicity.from_value(row["periodicity"]),
                creation_date=_parse_datetime(row["creation_date"]),
            )
            for row in rows
        }

        completions_cursor = self.connection.execute(
            """
            SELECT habit_id, completed_at
            FROM completions
            ORDER BY completed_at ASC;
            """
        )
        for row in completions_cursor.fetchall():
            habit = habits.get(row["habit_id"])
            if habit is None:
                continue
            habit.completion_dates.append(_parse_datetime(row["completed_at"]))

        for habit in habits.values():
            habit.completion_dates.sort()

        return list(habits.values())

    def load_habit(self, habit_id):
        """Load a single habit by id."""
        habits = {habit.id: habit for habit in self.load_habits()}
        return habits.get(habit_id)

    def load_completions(self, habit_id):
        """Load completion timestamps for one habit."""
        cursor = self.connection.execute(
            """
            SELECT completed_at
            FROM completions
            WHERE habit_id = ?
            ORDER BY completed_at ASC;
            """,
            (habit_id,),
        )
        return [_parse_datetime(row["completed_at"]) for row in cursor.fetchall()]

    def close(self):
        self.connection.close()


def _parse_datetime(value):
    """Parse stored ISO datetime and normalize it to UTC."""
    return ensure_utc(datetime.fromisoformat(value))
