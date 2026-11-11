"""Kiritilgan qiymatlarni chegaralar bo'yicha tekshirish.

Barcha chegaralar shu yerda konstanta sifatida turadi (kod qoidasi №5).
"""
from datetime import date, timedelta

FIRST_HOUR = 8            # birinchi navbat 08:00 da boshlanadi
LAST_HOUR = 21            # oxirgi navbat 21:00 da (22:00 da tugaydi)
BOOK_DAYS_AHEAD = 6       # bugun + 6 kun (jami 7 kun) oldinga yozilish mumkin
MAX_ACTIVE_BOOKINGS = 2   # bir talabada bir vaqtda ko'pi bilan 2 faol navbat
MIN_ROOM, MAX_ROOM = 1, 999
MIN_PASSWORD_LEN = 6
MAX_LOGIN_ATTEMPTS = 5    # shuncha xato urinishdan keyin hisob bloklanadi
LOCK_MINUTES = 5


def is_valid_hour(hour: int) -> bool:
    """Soat 8..21 oralig'ida bo'lsa True."""
    return FIRST_HOUR <= hour <= LAST_HOUR


def is_valid_day(day: date, today: date) -> bool:
    """Kun bugundan BOOK_DAYS_AHEAD kungacha bo'lsa True."""
    return today <= day <= today + timedelta(days=BOOK_DAYS_AHEAD)


def is_valid_room(room: int) -> bool:
    return MIN_ROOM <= room <= MAX_ROOM


def is_valid_password(password: str) -> bool:
    return len(password) >= MIN_PASSWORD_LEN
