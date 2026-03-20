"""Command line interface for the habit tracker backend."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from .database import DatabaseLayer
from .models import Periodicity
from .tracker import HabitTracker


def build_parser():
    """Configure all CLI commands and options."""
    parser = argparse.ArgumentParser(description="Habit tracking application (CLI)")
    parser.add_argument(
        "--db",
        default="habit_tracker.db",
        help="Path to SQLite database file (default: habit_tracker.db).",
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    subparsers.add_parser("init-db", help="Initialize database schema.")

    seed_parser = subparsers.add_parser("seed-demo", help="Load predefined 4-week sample data.")
    seed_parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing habits before seeding demo data.",
    )

    add_parser = subparsers.add_parser("add-habit", help="Create a new habit.")
    add_parser.add_argument("--name", required=True, help="Habit name.")
    add_parser.add_argument(
        "--periodicity",
        required=True,
        choices=["daily", "weekly", "DAILY", "WEEKLY"],
        help="Habit periodicity.",
    )

    delete_parser = subparsers.add_parser("delete-habit", help="Delete habit by id.")
    delete_parser.add_argument("--id", required=True, help="Habit id.")

    complete_parser = subparsers.add_parser("complete", help="Mark habit as completed.")
    complete_parser.add_argument("--id", required=True, help="Habit id.")
    complete_parser.add_argument(
        "--date",
        help="Completion datetime in ISO 8601 format. Default is now (UTC).",
    )

    list_parser = subparsers.add_parser("list-habits", help="List tracked habits.")
    list_parser.add_argument(
        "--periodicity",
        choices=["daily", "weekly", "DAILY", "WEEKLY"],
        help="Filter habits by periodicity.",
    )

    history_parser = subparsers.add_parser("history", help="Show completion history for a habit.")
    history_parser.add_argument("--id", required=True, help="Habit id.")

    streak_parser = subparsers.add_parser("longest-streak", help="Get longest streak.")
    streak_parser.add_argument(
        "--id",
        help="Habit id. If omitted, returns overall longest streak across all habits.",
    )

    trends_parser = subparsers.add_parser(
        "consistency-trends",
        help="Show lowest consistency habits in a time window.",
    )
    trends_parser.add_argument(
        "--days",
        type=int,
        default=28,
        help="How many days back from now to analyze (default: 28).",
    )
    trends_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="How many habits to return (default: 5).",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # One DB/tracker instance per CLI invocation keeps lifecycle simple.
    database = DatabaseLayer(args.db)
    tracker = HabitTracker(database)

    try:
        # Command dispatch section.
        if args.command == "init-db":
            print("Database initialized at: {0}".format(args.db))
            return

        if args.command == "seed-demo":
            inserted = tracker.seed_predefined_data(replace_existing=args.replace)
            print("Seed complete. Added {0} habit(s).".format(inserted))
            return

        if args.command == "add-habit":
            periodicity = Periodicity.from_value(args.periodicity)
            habit = tracker.add_habit(name=args.name, periodicity=periodicity)
            print(
                "Habit created: id={0} | name={1} | periodicity={2}".format(
                    habit.id, habit.name, habit.periodicity.value
                )
            )
            return

        if args.command == "delete-habit":
            tracker.delete_habit(args.id)
            print("Habit deleted: {0}".format(args.id))
            return

        if args.command == "complete":
            timestamp = datetime.fromisoformat(args.date) if args.date else None
            completed = tracker.mark_completed(args.id, completed_at=timestamp)
            print("Completion saved for {0} at {1}".format(args.id, completed.isoformat()))
            return

        if args.command == "list-habits":
            habits = tracker.list_habits()
            if args.periodicity:
                habits = tracker.get_habits_by_periodicity(args.periodicity)
            _print_habits(habits)
            return

        if args.command == "history":
            habit = tracker.get_habit(args.id)
            if habit is None:
                raise KeyError("Habit not found: {0}".format(args.id))
            print(
                "{0} ({1}) completions: {2}".format(
                    habit.name, habit.periodicity.value, len(habit.completion_dates)
                )
            )
            for timestamp in habit.completion_dates:
                print("- {0}".format(timestamp.isoformat()))
            return

        if args.command == "longest-streak":
            if args.id:
                streak = tracker.get_longest_streak(args.id)
                habit = tracker.get_habit(args.id)
                name = habit.name if habit else args.id
                print("Longest streak for {0}: {1}".format(name, streak))
            else:
                streak = tracker.get_longest_streak()
                print("Overall longest streak: {0}".format(streak))
            return

        if args.command == "consistency-trends":
            # Analyze a rolling time window ending now.
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=max(args.days, 1))
            trends = tracker.get_consistency_trends(start=start, end=end, limit=args.limit)
            if not trends:
                print("No habits available for trend analysis.")
                return

            print("Consistency trends for last {0} day(s):".format(args.days))
            for habit, ratio in trends:
                print("- {0} ({1}): {2:.2%}".format(habit.name, habit.periodicity.value, ratio))
            return

        parser.error("Unknown command")
    finally:
        # Always close DB connection, even if command raises.
        database.close()


def _print_habits(habits):
    """Render habit summaries in a compact readable format."""
    if not habits:
        print("No habits found.")
        return

    print("Tracked habits:")
    for habit in habits:
        print(
            "- id={0} | name={1} | periodicity={2} | created={3} | completions={4} | longest_streak={5}".format(
                habit.id,
                habit.name,
                habit.periodicity.value,
                habit.creation_date.date().isoformat(),
                len(habit.completion_dates),
                habit.get_streak(),
            )
        )


if __name__ == "__main__":
    main()
