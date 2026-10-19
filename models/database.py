import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DATABASE_PATH", "data/gym.db")

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL CHECK(age BETWEEN 12 AND 100),
            gender TEXT NOT NULL,
            weight REAL NOT NULL CHECK(weight > 0),
            fitness_goal TEXT NOT NULL,
            join_date TEXT NOT NULL,
            plan TEXT NOT NULL CHECK(plan IN ('monthly','quarterly','yearly')),
            membership_start TEXT NOT NULL,
            membership_end TEXT NOT NULL,
            membership_status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
            attended_at TEXT NOT NULL,
            notes TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
            exercise_name TEXT NOT NULL,
            sets INTEGER NOT NULL CHECK(sets > 0),
            repetitions INTEGER NOT NULL CHECK(repetitions > 0),
            duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
            trainer_notes TEXT DEFAULT '',
            assigned_date TEXT NOT NULL,
            trainer_name TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS workout_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER NOT NULL REFERENCES workouts(id) ON DELETE CASCADE,
            completed_sets INTEGER NOT NULL,
            completed_repetitions INTEGER NOT NULL,
            completed_minutes INTEGER NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            notes TEXT DEFAULT '',
            logged_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
            plan TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount >= 0),
            paid_on TEXT NOT NULL,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL
        );
        """)
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
