import os
import sqlite3
from typing import Iterable

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def column_names(cur, table: str) -> set[str]:
    rows = cur.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def add_column(cur, table: str, column: str, definition: str):
    cols = column_names(cur, table)
    if column not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS servers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ip TEXT NOT NULL,
        country TEXT DEFAULT 'KR',
        mode TEXT DEFAULT 'PvP',
        discord TEXT,
        description TEXT,
        loot_rate TEXT,
        zombie_rate TEXT,
        vehicle_rate TEXT,
        max_players TEXT,
        diagnosis TEXT DEFAULT '설정파일 없음',
        likes INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT DEFAULT 'free',
        title TEXT NOT NULL,
        author TEXT DEFAULT 'Anonymous',
        content TEXT NOT NULL,
        likes INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        author TEXT DEFAULT 'Anonymous',
        content TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )
    """)

    # Safe migrations for older Render SQLite files.
    server_columns = {
        "country": "country TEXT DEFAULT 'KR'",
        "mode": "mode TEXT DEFAULT 'PvP'",
        "discord": "discord TEXT",
        "description": "description TEXT",
        "loot_rate": "loot_rate TEXT",
        "zombie_rate": "zombie_rate TEXT",
        "vehicle_rate": "vehicle_rate TEXT",
        "max_players": "max_players TEXT",
        "diagnosis": "diagnosis TEXT DEFAULT '설정파일 없음'",
        "likes": "likes INTEGER DEFAULT 0",
        "views": "views INTEGER DEFAULT 0",
        "created_at": "created_at TEXT DEFAULT CURRENT_TIMESTAMP",
    }
    for col, definition in server_columns.items():
        add_column(cur, "servers", col, definition)

    post_columns = {
        "category": "category TEXT DEFAULT 'free'",
        "author": "author TEXT DEFAULT 'Anonymous'",
        "likes": "likes INTEGER DEFAULT 0",
        "views": "views INTEGER DEFAULT 0",
        "created_at": "created_at TEXT DEFAULT CURRENT_TIMESTAMP",
    }
    for col, definition in post_columns.items():
        add_column(cur, "posts", col, definition)

    comment_columns = {
        "author": "author TEXT DEFAULT 'Anonymous'",
        "created_at": "created_at TEXT DEFAULT CURRENT_TIMESTAMP",
    }
    for col, definition in comment_columns.items():
        add_column(cur, "comments", col, definition)

    conn.commit()
    conn.close()


def rows_to_dicts(rows: Iterable[sqlite3.Row]):
    return [dict(row) for row in rows]
