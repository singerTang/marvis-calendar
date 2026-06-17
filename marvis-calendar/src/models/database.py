"""Marvis Calendar — 数据库层

- 同步 sqlite3（三张小表，没必要异步）
- WAL 模式 + UUID 主键 + created_at/updated_at
- Schema 版本号（PRAGMA user_version）+ 简单迁移
"""

import sqlite3
import uuid
import datetime
import threading
from pathlib import Path
from typing import Optional

SCHEMA_VERSION = 1


class Database:
    def __init__(self, db_path: Path):
        self._path = db_path
        self._local = threading.local()

    @property
    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self._path), check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def initialize(self):
        cur = self._conn.execute("PRAGMA user_version")
        version = cur.fetchone()[0]

        if version < 1:
            self._create_tables()
            self._conn.execute("PRAGMA user_version = 1")
            self._conn.commit()

    def _create_tables(self):
        self._conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            start_time  TEXT NOT NULL,
            end_time    TEXT,
            all_day     INTEGER DEFAULT 0,
            repeat_rule TEXT,
            reminder_minutes INTEGER,
            notes       TEXT,
            color       TEXT DEFAULT '#5e8cf0',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS todos (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            completed   INTEGER DEFAULT 0,
            priority    INTEGER DEFAULT 0,
            due_date    TEXT,
            notes       TEXT,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key         TEXT PRIMARY KEY,
            value       TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );
        """)

    # ─── Events ─────────────────────────────────────────────────────────

    def add_event(self, title, start_time, end_time=None, all_day=0,
                  repeat_rule=None, reminder_minutes=None, notes=None,
                  color="#5e8cf0") -> dict:
        now = datetime.datetime.now().isoformat()
        eid = str(uuid.uuid4())
        self._conn.execute(
            """INSERT INTO events (id,title,start_time,end_time,all_day,
               repeat_rule,reminder_minutes,notes,color,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (eid, title, start_time, end_time, all_day,
             repeat_rule, reminder_minutes, notes, color, now, now))
        self._conn.commit()
        return self.get_event(eid)

    def get_event(self, eid: str) -> Optional[dict]:
        row = self._conn.execute("SELECT * FROM events WHERE id=?", (eid,)).fetchone()
        return dict(row) if row else None

    def get_events_by_date(self, date_str: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM events WHERE date(start_time)=? ORDER BY start_time",
            (date_str,)).fetchall()
        return [dict(r) for r in rows]

    def get_events_by_range(self, start: str, end: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM events WHERE start_time>=? AND start_time<? ORDER BY start_time",
            (start, end)).fetchall()
        return [dict(r) for r in rows]

    def update_event(self, eid: str, **kwargs) -> Optional[dict]:
        if not kwargs:
            return self.get_event(eid)
        kwargs["updated_at"] = datetime.datetime.now().isoformat()
        sets = ", ".join(f"{k}=?" for k in kwargs)
        vals = list(kwargs.values()) + [eid]
        self._conn.execute(f"UPDATE events SET {sets} WHERE id=?", vals)
        self._conn.commit()
        return self.get_event(eid)

    def delete_event(self, eid: str):
        self._conn.execute("DELETE FROM events WHERE id=?", (eid,))
        self._conn.commit()

    # ─── Todos ──────────────────────────────────────────────────────────

    def add_todo(self, title, due_date=None, priority=0, notes=None) -> dict:
        now = datetime.datetime.now().isoformat()
        tid = str(uuid.uuid4())
        self._conn.execute(
            """INSERT INTO todos (id,title,completed,priority,due_date,notes,created_at,updated_at)
               VALUES (?,?,0,?,?,?,?,?)""",
            (tid, title, priority, due_date, notes, now, now))
        self._conn.commit()
        return self.get_todo(tid)

    def get_todo(self, tid: str) -> Optional[dict]:
        row = self._conn.execute("SELECT * FROM todos WHERE id=?", (tid,)).fetchone()
        return dict(row) if row else None

    def get_all_todos(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM todos ORDER BY completed ASC, priority DESC, due_date ASC").fetchall()
        return [dict(r) for r in rows]

    def update_todo(self, tid: str, **kwargs) -> Optional[dict]:
        if not kwargs:
            return self.get_todo(tid)
        kwargs["updated_at"] = datetime.datetime.now().isoformat()
        sets = ", ".join(f"{k}=?" for k in kwargs)
        vals = list(kwargs.values()) + [tid]
        self._conn.execute(f"UPDATE todos SET {sets} WHERE id=?", vals)
        self._conn.commit()
        return self.get_todo(tid)

    def delete_todo(self, tid: str):
        self._conn.execute("DELETE FROM todos WHERE id=?", (tid,))
        self._conn.commit()

    # ─── Settings ───────────────────────────────────────────────────────

    def get_setting(self, key: str, default=None) -> Optional[str]:
        row = self._conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        now = datetime.datetime.now().isoformat()
        self._conn.execute(
            "INSERT OR REPLACE INTO settings (key,value,updated_at) VALUES (?,?,?)",
            (key, value, now))
        self._conn.commit()
