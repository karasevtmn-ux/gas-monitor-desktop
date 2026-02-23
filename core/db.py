import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional

APP_DIR = Path(os.environ.get("LOCALAPPDATA", ".")) / "GASMonitor"
DB_PATH = APP_DIR / "data.sqlite3"

SCHEMA = """
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL,
  plaintiff TEXT NOT NULL,
  defendant TEXT NOT NULL,
  court TEXT NOT NULL,
  case_number TEXT NOT NULL,
  comment TEXT NOT NULL,
  region TEXT NOT NULL,
  tz_override TEXT NULL,
  status TEXT NOT NULL DEFAULT 'active', -- active/error/problem
  last_ok_at TEXT NULL,
  last_check_at TEXT NULL,
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  link_id INTEGER NOT NULL REFERENCES links(id) ON DELETE CASCADE,
  started_at TEXT NOT NULL,
  finished_at TEXT NULL,
  ok INTEGER NOT NULL,
  error TEXT NULL
);

CREATE TABLE IF NOT EXISTS changes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  link_id INTEGER NOT NULL REFERENCES links(id) ON DELETE CASCADE,
  detected_at TEXT NOT NULL,
  change_type TEXT NOT NULL,
  summary TEXT NOT NULL,
  details TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
  link_id INTEGER PRIMARY KEY REFERENCES links(id) ON DELETE CASCADE,
  updated_at TEXT NOT NULL,
  snapshot_json TEXT NOT NULL
);
"""

class Database:
    def __init__(self):
        APP_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def init(self):
        self.executescript(SCHEMA)

    def executescript(self, script: str):
        self.conn.executescript(script)
        self.conn.commit()

    def execute(self, sql: str, params: Iterable[Any] = ()):
        cur = self.conn.execute(sql, tuple(params))
        self.conn.commit()
        return cur

    def query(self, sql: str, params: Iterable[Any] = ()):
        cur = self.conn.execute(sql, tuple(params))
        return cur.fetchall()

    def query_one(self, sql: str, params: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
        cur = self.conn.execute(sql, tuple(params))
        return cur.fetchone()
