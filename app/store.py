"""SQLite conversation history, keyed by anonymous session id."""
import os
import sqlite3
import threading
from pathlib import Path

_lock = threading.Lock()


def _path() -> str:
    return os.getenv("CHAT_DB_PATH", str(Path(__file__).resolve().parent.parent / "chat.db"))


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_path())
    c.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, role TEXT NOT NULL,
        content TEXT NOT NULL, mode TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id, id)")
    return c


def add(session_id: str, role: str, content: str, mode: str | None = None) -> None:
    with _lock:
        c = _conn()
        with c:
            c.execute("INSERT INTO messages(session_id, role, content, mode) VALUES (?,?,?,?)",
                      (session_id, role, content, mode))
        c.close()


def history(session_id: str, limit: int = 50) -> list[dict]:
    with _lock:
        c = _conn()
        rows = c.execute("SELECT role, content, mode FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
                         (session_id, limit)).fetchall()
        c.close()
    return [{"role": r, "content": t, "mode": m} for r, t, m in reversed(rows)]


def clear(session_id: str) -> int:
    with _lock:
        c = _conn()
        with c:
            n = c.execute("DELETE FROM messages WHERE session_id=?", (session_id,)).rowcount
        c.close()
    return n
