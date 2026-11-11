"""SQLite baza: sxema yaratish va ulanish."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    full_name     TEXT NOT NULL,
    room          INTEGER NOT NULL,
    role          TEXT NOT NULL DEFAULT 'talaba',
    password_hash TEXT NOT NULL,
    failed_logins INTEGER NOT NULL DEFAULT 0,
    locked_until  TEXT
);
CREATE TABLE IF NOT EXISTS machines (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT NOT NULL,
    floor  INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'ishlaydi'
);
CREATE TABLE IF NOT EXISTS bookings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    machine_id INTEGER NOT NULL REFERENCES machines(id),
    start      TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'faol'
);
-- Bitta mashinaga bitta vaqtda faqat bitta FAOL navbat bo'lishi mumkin
CREATE UNIQUE INDEX IF NOT EXISTS uniq_active_slot
    ON bookings(machine_id, start) WHERE status = 'faol';
CREATE TABLE IF NOT EXISTS notifications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    text       TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_read    INTEGER NOT NULL DEFAULT 0
);
"""

DEFAULT_MACHINES = [("1-qavat, 1-mashina", 1), ("1-qavat, 2-mashina", 1),
                    ("2-qavat, 1-mashina", 2), ("3-qavat, 1-mashina", 3)]


def connect(path: str) -> sqlite3.Connection:
    """Bazaga ulanadi; qatorlarni lug'at kabi o'qish uchun Row factory."""
    conn = sqlite3.connect(path, detect_types=0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Jadvallarni yaratadi va mashinalar bo'sh bo'lsa, ularni qo'shadi."""
    conn.executescript(SCHEMA)
    count = conn.execute("SELECT COUNT(*) FROM machines").fetchone()[0]
    if count == 0:
        conn.executemany("INSERT INTO machines(name, floor) VALUES (?, ?)",
                         DEFAULT_MACHINES)
    conn.commit()
