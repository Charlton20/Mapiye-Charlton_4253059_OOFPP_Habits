# Habit Tracking Application (Python Backend)

This project implements a habit tracker backend according to the portfolio acceptance criteria.

## Acceptance-Criteria Alignment
- Python 3.7+ compatible codebase (standard library only).
- Habit modeled as an OOP class: `habit_tracker.models.Habit`.
- Supports two required periodicities: `DAILY` and `WEEKLY`.
- Includes 5 predefined habits with 4 weeks of sample tracking data.
- Tracks habit creation timestamp and completion timestamps.
- Persists data across sessions with SQLite.
- Functional analytics module with required outputs:
  - list all currently tracked habits,
  - list habits by periodicity,
  - longest streak across all habits,
  - longest streak for a given habit.
- Clean CLI API for create, delete, track, and analyze operations.
- Unit test suite included.

## Project Structure
- `habit_tracker/models.py`: domain model (`Habit`, `Periodicity`, streak logic).
- `habit_tracker/database.py`: SQLite persistence layer (`habits`, `completions` tables).
- `habit_tracker/tracker.py`: application service class (`HabitTracker`).
- `habit_tracker/analytics.py`: functional analytics module.
- `habit_tracker/fixtures.py`: predefined 5 habits and 4-week dataset.
- `habit_tracker/cli.py`: CLI command definitions and command dispatcher.
- `run_habit_tracker.py`: convenient launcher.
- `main.py`: root entrypoint (also launches the CLI).
- `tests/test_habit_tracker.py`: unit tests.

## Installation
1. Ensure Python 3.7+ is available:
```bash
python3 --version
```

2. Go to project folder:
```bash
cd /home/charlton/Documents/Projects/Habit_Tracker
```

3. No external package installation is required.

## Run The Application
You can use either launcher:
```bash
python3 run_habit_tracker.py --help
# or
python3 main.py --help
# or
python3 -m habit_tracker --help
```

## First-Time Setup
1. Initialize database:
```bash
python3 run_habit_tracker.py --db habit_tracker.db init-db
```

2. Load predefined 4-week fixture data:
```bash
python3 run_habit_tracker.py --db habit_tracker.db seed-demo --replace
```

3. List all tracked habits:
```bash
python3 run_habit_tracker.py --db habit_tracker.db list-habits
```

## How To Create New Habits
Create a daily habit:
```bash
python3 run_habit_tracker.py --db habit_tracker.db add-habit --name "Stretching" --periodicity daily
```

Create a weekly habit:
```bash
python3 run_habit_tracker.py --db habit_tracker.db add-habit --name "Weekly Planning" --periodicity weekly
```

## How To Complete A Habit Task Within A Period
Mark completion now:
```bash
python3 run_habit_tracker.py --db habit_tracker.db complete --id <habit_id>
```

Mark completion at a specific timestamp:
```bash
python3 run_habit_tracker.py --db habit_tracker.db complete --id <habit_id> --date "2026-03-04T09:30:00+00:00"
```

## Habit Inspection And Analytics
List habits by periodicity:
```bash
python3 run_habit_tracker.py --db habit_tracker.db list-habits --periodicity daily
python3 run_habit_tracker.py --db habit_tracker.db list-habits --periodicity weekly
```

Show completion history for one habit:
```bash
python3 run_habit_tracker.py --db habit_tracker.db history --id <habit_id>
```

Longest streak for one habit:
```bash
python3 run_habit_tracker.py --db habit_tracker.db longest-streak --id <habit_id>
```

Longest streak across all habits:
```bash
python3 run_habit_tracker.py --db habit_tracker.db longest-streak
```

Consistency trend analysis (extra analytics):
```bash
python3 run_habit_tracker.py --db habit_tracker.db consistency-trends --days 28 --limit 5
```

Delete a habit:
```bash
python3 run_habit_tracker.py --db habit_tracker.db delete-habit --id <habit_id>
```

## Run Unit Tests
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## SQLite Troubleshooting (If Needed)
If you get `ModuleNotFoundError: No module named '_sqlite3'`, your Python build lacks SQLite support.
Use a Python interpreter that includes sqlite3 (for example `/usr/bin/python3`) or rebuild your `pyenv` Python with SQLite dev libraries installed.
