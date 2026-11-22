"""SQLite event store (stdlib only)."""

import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    src_ip TEXT NOT NULL,
    user TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    doc TEXT NOT NULL
)
"""


class EventStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def add(self, doc: dict) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO events (ts, src_ip, user, risk_score, doc) VALUES (?, ?, ?, ?, ?)",
                (doc["@timestamp"], doc["source"]["ip"], doc["user"]["name"],
                 doc["risk_score"], json.dumps(doc)),
            )
            return int(cur.lastrowid)

    def search_by_user(self, user: str) -> list[dict]:
        query = f"SELECT doc FROM events WHERE user = '{user}' ORDER BY id"
        with self._connect() as conn:
            return [json.loads(row[0]) for row in conn.execute(query)]

    def all(self) -> list[dict]:
        with self._connect() as conn:
            return [json.loads(row[0]) for row in conn.execute("SELECT doc FROM events ORDER BY id")]
