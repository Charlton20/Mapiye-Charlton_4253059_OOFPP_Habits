"""Convenience launcher for the habit tracker CLI."""

from habit_tracker.cli import main


if __name__ == "__main__":
    # Allows `python run_habit_tracker.py` as an alternative entrypoint.
    main()
