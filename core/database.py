"""
database.py — OneTask
All SQLite logic. Single source of truth for all data.
Fixes: streak midnight bug, skip recovery, session date lock, memory safety.
"""

import sqlite3
import os
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'onetask.db')


def _connect():
    """Always use this to get a connection — never raw sqlite3.connect()."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name, not index
    conn.execute("PRAGMA journal_mode=WAL")  # Safe concurrent access
    return conn


def init_db():
    """Create all tables. Safe to call multiple times."""
    conn = _connect()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            priority    INTEGER DEFAULT 0,
            status      TEXT    DEFAULT 'pending',
            date        TEXT    NOT NULL,
            skip_count  INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS streaks (
            id                  INTEGER PRIMARY KEY,
            current_streak      INTEGER DEFAULT 0,
            longest_streak      INTEGER DEFAULT 0,
            last_completed_date TEXT    DEFAULT ''
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY,
            session_date TEXT   NOT NULL
        )
    ''')

    # Seed default rows safely
    c.execute("INSERT OR IGNORE INTO streaks (id) VALUES (1)")
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────
# SESSION DATE — Fix wrong system clock issues
# ─────────────────────────────────────────────────

def get_session_date():
    """
    Return today's date as a string.
    We lock it at first open so midnight edge cases don't corrupt data.
    If the app was last opened on a previous day, refresh the session.
    """
    today = str(date.today())
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT session_date FROM sessions WHERE id=1")
    row = c.fetchone()

    if row is None:
        # First ever launch
        c.execute("INSERT INTO sessions (id, session_date) VALUES (1, ?)", (today,))
        conn.commit()
        conn.close()
        return today

    stored = row['session_date']

    # If stored date is in the past, update it (new day)
    if stored < today:
        c.execute("UPDATE sessions SET session_date=? WHERE id=1", (today,))
        conn.commit()
        conn.close()
        return today

    conn.close()
    return stored


# ─────────────────────────────────────────────────
# TASKS
# ─────────────────────────────────────────────────

def get_today_tasks(session_date):
    conn = _connect()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM tasks WHERE date=? ORDER BY priority ASC",
        (session_date,)
    )
    tasks = [dict(row) for row in c.fetchall()]
    conn.close()
    return tasks


def add_task(title, priority, session_date):
    """
    Add a task. Returns (True, '') on success.
    Returns (False, reason) on failure.
    Hard limit: 3 tasks per day. No adding after 9pm for today.
    """
    now = datetime.now()

    # Block adding today's tasks after 9pm — force planning for tomorrow
    if now.hour >= 21 and session_date == str(date.today()):
        return False, "It's after 9pm! Plan tomorrow's tasks in the morning."

    conn = _connect()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as cnt FROM tasks WHERE date=?", (session_date,))
    count = c.fetchone()['cnt']

    if count >= 3:
        conn.close()
        return False, "Maximum 3 tasks per day. Focus!"

    if not title.strip():
        conn.close()
        return False, "Task cannot be empty."

    c.execute(
        "INSERT INTO tasks (title, priority, date) VALUES (?, ?, ?)",
        (title.strip(), priority, session_date)
    )
    conn.commit()
    conn.close()
    return True, ''


def complete_task(task_id):
    conn = _connect()
    c = conn.cursor()
    c.execute(
        "UPDATE tasks SET status='done' WHERE id=?",
        (task_id,)
    )
    conn.commit()
    conn.close()


def skip_task(task_id):
    """
    Skip moves task to bottom of priority order.
    After 2 skips it becomes 'rescued' — shown in summary as unfinished.
    Never silently deleted.
    """
    conn = _connect()
    c = conn.cursor()

    c.execute("SELECT skip_count, priority FROM tasks WHERE id=?", (task_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return

    new_skip = row['skip_count'] + 1
    new_priority = row['priority'] + 10  # Push to bottom

    if new_skip >= 2:
        # Mark as rescued — shown in end-of-day summary
        c.execute(
            "UPDATE tasks SET status='rescued', skip_count=?, priority=? WHERE id=?",
            (new_skip, new_priority, task_id)
        )
    else:
        c.execute(
            "UPDATE tasks SET skip_count=?, priority=? WHERE id=?",
            (new_skip, new_priority, task_id)
        )

    conn.commit()
    conn.close()


def get_current_task(session_date):
    """Get the next pending task ordered by priority."""
    conn = _connect()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM tasks WHERE date=? AND status='pending' ORDER BY priority ASC LIMIT 1",
        (session_date,)
    )
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_day_summary(session_date):
    """Returns (done, skipped, rescued, total)."""
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT status FROM tasks WHERE date=?", (session_date,))
    tasks = c.fetchall()
    conn.close()

    done = sum(1 for t in tasks if t['status'] == 'done')
    skipped = sum(1 for t in tasks if t['status'] == 'skipped')
    rescued = sum(1 for t in tasks if t['status'] == 'rescued')
    total = len(tasks)
    return done, skipped, rescued, total


# ─────────────────────────────────────────────────
# STREAKS — Midnight-safe logic
# ─────────────────────────────────────────────────

def get_streak():
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT current_streak, longest_streak FROM streaks WHERE id=1")
    row = c.fetchone()
    conn.close()
    if row:
        return row['current_streak'], row['longest_streak']
    return 0, 0


def try_update_streak(session_date):
    """
    Call after completing a task.
    Only updates once per day. Handles missed days correctly.
    Returns new streak count.
    """
    conn = _connect()
    c = conn.cursor()
    c.execute(
        "SELECT current_streak, longest_streak, last_completed_date FROM streaks WHERE id=1"
    )
    row = c.fetchone()
    streak = row['current_streak']
    longest = row['longest_streak']
    last_date = row['last_completed_date']

    # Already updated today
    if last_date == session_date:
        conn.close()
        return streak

    # Check if yesterday was the last completed day (continuity check)
    yesterday = str(date.today() - timedelta(days=1))
    if last_date == yesterday or last_date == '':
        streak += 1
    else:
        # Missed a day — reset streak
        streak = 1

    longest = max(longest, streak)

    c.execute(
        "UPDATE streaks SET current_streak=?, longest_streak=?, last_completed_date=? WHERE id=1",
        (streak, longest, session_date)
    )
    conn.commit()
    conn.close()
    return streak


def reset_streak_if_missed():
    """
    Call on app open. If user missed yesterday entirely, reset streak.
    """
    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT current_streak, last_completed_date FROM streaks WHERE id=1")
    row = c.fetchone()
    if not row:
        conn.close()
        return

    last_date = row['last_completed_date']
    if not last_date:
        conn.close()
        return

    yesterday = str(date.today() - timedelta(days=1))
    two_days_ago = str(date.today() - timedelta(days=2))

    # If last completed was before yesterday, reset
    if last_date <= two_days_ago:
        c.execute("UPDATE streaks SET current_streak=0 WHERE id=1")
        conn.commit()

    conn.close()
