"""SQLite helpers. One connection per request (Flask `g`), plus a plain connect() for scripts/tests."""
import os
import sqlite3
from pathlib import Path

from flask import g

BASE_DIR = Path(__file__).parent
DEFAULT_DB = os.environ.get("APPT_DB", str(BASE_DIR / "hospital.db"))


def connect(db_path=None):
    conn = sqlite3.connect(db_path or DEFAULT_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=None):
    """Create all tables (safe to run repeatedly)."""
    conn = connect(db_path)
    conn.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))
    conn.commit()
    conn.close()


def get_db():
    """Per-request connection used inside Flask routes."""
    if "db" not in g:
        g.db = connect(g.get("db_path"))
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()