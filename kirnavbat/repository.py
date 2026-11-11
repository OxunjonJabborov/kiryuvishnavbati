"""Ma'lumotlar qatlami: faqat SQL so'rovlar, biznes qoidasi yo'q.

Barcha so'rovlar parametrli (?) — SQL injection dan himoya (kod qoidasi №4).
"""
import sqlite3
from datetime import datetime
from typing import Optional

from .models import Booking, Machine, Notification, User

DT_FMT = "%Y-%m-%d %H:%M"


def _user(row) -> Optional[User]:
    if row is None:
        return None
    return User(row["id"], row["username"], row["full_name"], row["room"],
                row["role"], row["password_hash"])


def _booking(row) -> Booking:
    return Booking(row["id"], row["user_id"], row["machine_id"],
                   datetime.strptime(row["start"], DT_FMT), row["status"])


class UserRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, username, full_name, room, role, password_hash) -> int:
        cur = self.conn.execute(
            "INSERT INTO users(username, full_name, room, role, password_hash)"
            " VALUES (?, ?, ?, ?, ?)",
            (username, full_name, room, role, password_hash))
        self.conn.commit()
        return cur.lastrowid

    def by_username(self, username: str) -> Optional[User]:
        return _user(self.conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)).fetchone())

    def by_id(self, user_id: int) -> Optional[User]:
        return _user(self.conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())

    def lock_info(self, username: str):
        return self.conn.execute(
            "SELECT failed_logins, locked_until FROM users WHERE username = ?",
            (username,)).fetchone()

    def set_lock_info(self, username, failed, locked_until) -> None:
        self.conn.execute(
            "UPDATE users SET failed_logins = ?, locked_until = ?"
            " WHERE username = ?", (failed, locked_until, username))
        self.conn.commit()


class MachineRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def all(self) -> list[Machine]:
        rows = self.conn.execute("SELECT * FROM machines ORDER BY floor, id")
        return [Machine(r["id"], r["name"], r["floor"], r["status"]) for r in rows]

    def by_id(self, machine_id: int) -> Optional[Machine]:
        r = self.conn.execute("SELECT * FROM machines WHERE id = ?",
                              (machine_id,)).fetchone()
        return Machine(r["id"], r["name"], r["floor"], r["status"]) if r else None

    def set_status(self, machine_id: int, status: str) -> None:
        self.conn.execute("UPDATE machines SET status = ? WHERE id = ?",
                          (status, machine_id))
        self.conn.commit()


class BookingRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, user_id: int, machine_id: int, start: datetime) -> int:
        cur = self.conn.execute(
            "INSERT INTO bookings(user_id, machine_id, start) VALUES (?, ?, ?)",
            (user_id, machine_id, start.strftime(DT_FMT)))
        self.conn.commit()
        return cur.lastrowid

    def by_id(self, booking_id: int) -> Optional[Booking]:
        r = self.conn.execute("SELECT * FROM bookings WHERE id = ?",
                              (booking_id,)).fetchone()
        return _booking(r) if r else None

    def is_taken(self, machine_id: int, start: datetime) -> bool:
        r = self.conn.execute(
            "SELECT 1 FROM bookings WHERE machine_id = ? AND start = ?"
            " AND status = 'faol'", (machine_id, start.strftime(DT_FMT))).fetchone()
        return r is not None

    def count_future_active(self, user_id: int, now: datetime) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE user_id = ? AND status = 'faol'"
            " AND start >= ?", (user_id, now.strftime(DT_FMT))).fetchone()[0]

    def for_day(self, day_str: str) -> list[Booking]:
        rows = self.conn.execute(
            "SELECT * FROM bookings WHERE status = 'faol' AND start LIKE ?",
            (day_str + "%",))
        return [_booking(r) for r in rows]

    def for_user(self, user_id: int) -> list[Booking]:
        rows = self.conn.execute(
            "SELECT * FROM bookings WHERE user_id = ? ORDER BY start DESC",
            (user_id,))
        return [_booking(r) for r in rows]

    def future_for_machine(self, machine_id: int, now: datetime) -> list[Booking]:
        rows = self.conn.execute(
            "SELECT * FROM bookings WHERE machine_id = ? AND status = 'faol'"
            " AND start >= ?", (machine_id, now.strftime(DT_FMT)))
        return [_booking(r) for r in rows]

    def users_with_cancelled_future(self, machine_id: int, now: datetime) -> list[int]:
        rows = self.conn.execute(
            "SELECT DISTINCT user_id FROM bookings WHERE machine_id = ?"
            " AND status = 'bekor' AND start >= ?", (machine_id, now.strftime(DT_FMT)))
        return [r[0] for r in rows]

    def cancel(self, booking_id: int) -> None:
        self.conn.execute("UPDATE bookings SET status = 'bekor' WHERE id = ?",
                          (booking_id,))
        self.conn.commit()


class NotificationRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, user_id: int, text: str, created_at: datetime) -> None:
        self.conn.execute(
            "INSERT INTO notifications(user_id, text, created_at) VALUES (?, ?, ?)",
            (user_id, text, created_at.strftime(DT_FMT)))
        self.conn.commit()

    def for_user(self, user_id: int) -> list[Notification]:
        rows = self.conn.execute(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC",
            (user_id,))
        return [Notification(r["id"], r["user_id"], r["text"], r["created_at"],
                             r["is_read"]) for r in rows]

    def unread_count(self, user_id: int) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
            (user_id,)).fetchone()[0]

    def mark_all_read(self, user_id: int) -> None:
        self.conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?",
                          (user_id,))
        self.conn.commit()
