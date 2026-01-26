import json
import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

APP_NAME = "Taskmenedger"
DB_FILENAME = "planner.db"
CURRENT_SCHEMA_VERSION = 1

logger = logging.getLogger(__name__)


def get_data_dir() -> Path:
    portable_flag = Path(__file__).resolve().parent.parent / "portable.flag"
    if os.getenv("TASKMENEDGER_PORTABLE") == "1" or portable_flag.exists():
        data_dir = Path(__file__).resolve().parent.parent / "data"
    else:
        appdata = os.getenv("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        data_dir = Path(appdata) / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    return get_data_dir() / DB_FILENAME


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect_db() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        _ensure_schema(conn)


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
    )
    row = conn.execute("SELECT version FROM schema_version").fetchone()
    if row is None:
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (0,))
        conn.commit()
    version = conn.execute("SELECT version FROM schema_version").fetchone()["version"]
    if version < CURRENT_SCHEMA_VERSION:
        _migrate(conn, version, CURRENT_SCHEMA_VERSION)


def _migrate(conn: sqlite3.Connection, from_version: int, to_version: int) -> None:
    logger.info("Migrating schema from %s to %s", from_version, to_version)
    if from_version < 1 <= to_version:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS note_entries (
                date TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'undone'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                duration INTEGER NOT NULL,
                break_duration INTEGER NOT NULL,
                linked_type TEXT NOT NULL,
                linked_id TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_task_items_date ON task_items(date)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_pomodoro_start_time ON pomodoro_sessions(start_time)"
        )
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS note_fts
            USING fts5(date, content, content='note_entries', content_rowid='rowid')
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS note_entries_ai
            AFTER INSERT ON note_entries BEGIN
                INSERT INTO note_fts(rowid, date, content)
                VALUES (new.rowid, new.date, new.content);
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS note_entries_ad
            AFTER DELETE ON note_entries BEGIN
                INSERT INTO note_fts(note_fts, rowid, date, content)
                VALUES('delete', old.rowid, old.date, old.content);
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS note_entries_au
            AFTER UPDATE ON note_entries BEGIN
                INSERT INTO note_fts(note_fts, rowid, date, content)
                VALUES('delete', old.rowid, old.date, old.content);
                INSERT INTO note_fts(rowid, date, content)
                VALUES (new.rowid, new.date, new.content);
            END;
            """
        )
        conn.execute("UPDATE schema_version SET version = 1")
    conn.commit()


@dataclass
class NoteEntry:
    date: str
    content: str
    updated_at: str


@dataclass
class TaskItem:
    id: int
    date: str
    text: str
    status: str


def upsert_note(date: str, content: str) -> None:
    updated_at = datetime.utcnow().isoformat()
    with connect_db() as conn:
        conn.execute(
            """
            INSERT INTO note_entries(date, content, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET content = excluded.content, updated_at = excluded.updated_at
            """,
            (date, content, updated_at),
        )
        conn.commit()


def fetch_note(date: str) -> NoteEntry | None:
    with connect_db() as conn:
        row = conn.execute(
            "SELECT date, content, updated_at FROM note_entries WHERE date = ?",
            (date,),
        ).fetchone()
    if not row:
        return None
    return NoteEntry(**row)


def search_notes(query: str) -> list[NoteEntry]:
    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT note_entries.date, note_entries.content, note_entries.updated_at
            FROM note_fts
            JOIN note_entries ON note_entries.rowid = note_fts.rowid
            WHERE note_fts MATCH ?
            ORDER BY note_entries.date DESC
            """,
            (query,),
        ).fetchall()
    return [NoteEntry(**row) for row in rows]


def list_notes(start_date: str | None = None, end_date: str | None = None) -> list[NoteEntry]:
    query = "SELECT date, content, updated_at FROM note_entries"
    params: list[str] = []
    if start_date and end_date:
        query += " WHERE date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    query += " ORDER BY date DESC"
    with connect_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [NoteEntry(**row) for row in rows]


def replace_tasks_for_date(date: str, tasks: list[tuple[str, str]]) -> None:
    with connect_db() as conn:
        conn.execute("DELETE FROM task_items WHERE date = ?", (date,))
        for text, status in tasks:
            conn.execute(
                "INSERT INTO task_items(date, text, status) VALUES (?, ?, ?)",
                (date, text, status),
            )
        conn.commit()


def list_tasks_for_date(date: str) -> list[TaskItem]:
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT id, date, text, status FROM task_items WHERE date = ?",
            (date,),
        ).fetchall()
    return [TaskItem(**row) for row in rows]


def add_pomodoro_session(
    start_time: str,
    duration: int,
    break_duration: int,
    linked_type: str,
    linked_id: str | None,
) -> None:
    with connect_db() as conn:
        conn.execute(
            """
            INSERT INTO pomodoro_sessions(start_time, duration, break_duration, linked_type, linked_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (start_time, duration, break_duration, linked_type, linked_id),
        )
        conn.commit()


def list_pomodoro_sessions(limit: int = 100) -> list[sqlite3.Row]:
    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT id, start_time, duration, break_duration, linked_type, linked_id
            FROM pomodoro_sessions
            ORDER BY start_time DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return rows


def set_setting(key: str, value: dict) -> None:
    payload = json.dumps(value, ensure_ascii=False)
    with connect_db() as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, payload),
        )
        conn.commit()


def get_setting(key: str, default: dict) -> dict:
    with connect_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row["value"])
    except json.JSONDecodeError:
        return default


def backup_database() -> Path:
    data_dir = get_data_dir()
    backup_dir = data_dir / "Backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"planner_{timestamp}.db"
    with connect_db() as conn:
        conn.backup(sqlite3.connect(backup_path))
    return backup_path
