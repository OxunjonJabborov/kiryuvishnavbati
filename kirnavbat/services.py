"""Mantiq qatlami: navbat qoidalari va autentifikatsiya."""
import sqlite3
from datetime import date, datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash

from . import validators as v
from .models import (ROLE_STUDENT, STATUS_BROKEN, STATUS_WORKING, Booking,
                     User)
from .observer import (BOOKING_CANCELLED, MACHINE_BROKEN, MACHINE_FIXED,
                       EventBus)


class ServiceError(Exception):
    """Foydalanuvchiga ko'rsatiladigan tushunarli xato."""


class AuthService:
    def __init__(self, users):
        self.users = users

    def register(self, username: str, full_name: str, room: str,
                 password: str) -> User:
        username = username.strip().lower()
        if not username or not full_name.strip():
            raise ServiceError("Login va F.I.Sh. bo'sh bo'lmasin.")
        if not room.isdigit() or not v.is_valid_room(int(room)):
            raise ServiceError(f"Xona raqami {v.MIN_ROOM}..{v.MAX_ROOM} oralig'ida bo'lsin.")
        if not v.is_valid_password(password):
            raise ServiceError(f"Parol kamida {v.MIN_PASSWORD_LEN} belgi bo'lsin.")
        if self.users.by_username(username):
            raise ServiceError("Bu login band.")
        # Himoya №1: parol ochiq emas, tuzli xesh (pbkdf2) ko'rinishida saqlanadi
        user_id = self.users.add(username, full_name.strip(), int(room),
                                 ROLE_STUDENT, generate_password_hash(password))
        return self.users.by_id(user_id)

    def login(self, username: str, password: str, now: datetime) -> User:
        username = username.strip().lower()
        info = self.users.lock_info(username)
        if info is None:
            raise ServiceError("Login yoki parol noto'g'ri.")
        failed, locked_until = info["failed_logins"], info["locked_until"]
        # Himoya №3: parolni tanlab topishga (brute force) qarshi bloklash
        if locked_until and now < datetime.fromisoformat(locked_until):
            raise ServiceError("Hisob vaqtincha bloklangan. Birozdan keyin urinib ko'ring.")
        user = self.users.by_username(username)
        if not check_password_hash(user.password_hash, password):
            failed += 1
            lock = None
            if failed >= v.MAX_LOGIN_ATTEMPTS:
                lock = (now + timedelta(minutes=v.LOCK_MINUTES)).isoformat()
                failed = 0
            self.users.set_lock_info(username, failed, lock)
            raise ServiceError("Login yoki parol noto'g'ri.")
        self.users.set_lock_info(username, 0, None)
        return user


def can_cancel(booking: Booking, user: User, now: datetime) -> bool:
    """Navbatni kim bekor qila oladi (Halstead va V(G) hisobi uchun tanlangan)."""
    if user.is_admin():
        return True
    if booking.user_id != user.id:
        return False
    return booking.start > now


class BookingService:
    def __init__(self, bookings, machines, events: EventBus):
        self.bookings = bookings
        self.machines = machines
        self.events = events

    def day_grid(self, day: date) -> dict:
        """Kun jadvali: {(machine_id, soat): Booking}."""
        taken = self.bookings.for_day(day.isoformat())
        return {(b.machine_id, b.start.hour): b for b in taken}

    def book(self, user: User, machine_id: int, day: date, hour: int,
             now: datetime) -> int:
        if not v.is_valid_hour(hour):
            raise ServiceError(f"Navbat soati {v.FIRST_HOUR}:00 dan {v.LAST_HOUR}:00 gacha.")
        if not v.is_valid_day(day, now.date()):
            raise ServiceError(f"Faqat bugundan {v.BOOK_DAYS_AHEAD} kun oldingacha yozilish mumkin.")
        start = datetime(day.year, day.month, day.day, hour)
        if start <= now:
            raise ServiceError("O'tib ketgan vaqtga yozilib bo'lmaydi.")
        machine = self.machines.by_id(machine_id)
        if machine is None:
            raise ServiceError("Bunday mashina yo'q.")
        if not machine.is_available():
            raise ServiceError("Bu mashina hozir buzilgan.")
        if self.bookings.is_taken(machine_id, start):
            raise ServiceError("Bu vaqt band.")
        if self.bookings.count_future_active(user.id, now) >= v.MAX_ACTIVE_BOOKINGS:
            raise ServiceError(f"Bir vaqtda ko'pi bilan {v.MAX_ACTIVE_BOOKINGS} ta faol navbat.")
        try:
            return self.bookings.add(user.id, machine_id, start)
        except sqlite3.IntegrityError:
            # Kod ko'rigida topilgan xato: ikki so'rov bir vaqtda kelsa,
            # is_taken ikkalasiga "bo'sh" deydi; baza indeksi ikkinchisini
            # to'xtatadi va endi 500 xato o'rniga tushunarli javob qaytadi.
            raise ServiceError("Bu vaqt band.") from None

    def cancel(self, user: User, booking_id: int, now: datetime) -> None:
        booking = self.bookings.by_id(booking_id)
        if booking is None or not booking.is_active():
            raise ServiceError("Navbat topilmadi.")
        # Himoya №2: bir talaba boshqasining navbatini o'chira olmaydi
        if not can_cancel(booking, user, now):
            raise ServiceError("Bu navbatni bekor qilishga huquqingiz yo'q.")
        self.bookings.cancel(booking_id)
        self.events.notify(BOOKING_CANCELLED, {
            "owner_id": booking.user_id, "start": f"{booking.start:%d.%m %H:%M}",
            "by_admin": booking.user_id != user.id, "now": now})

    def set_machine_status(self, user: User, machine_id: int, status: str,
                           now: datetime) -> None:
        if not user.can_change_machine():
            raise ServiceError("Faqat administrator yoki texnik o'zgartira oladi.")
        machine = self.machines.by_id(machine_id)
        if machine is None or status not in (STATUS_WORKING, STATUS_BROKEN):
            raise ServiceError("Noto'g'ri so'rov.")
        if machine.status == status:
            return
        self.machines.set_status(machine_id, status)
        if status == STATUS_BROKEN:
            affected = self.bookings.future_for_machine(machine_id, now)
            for b in affected:
                self.bookings.cancel(b.id)
            self.events.notify(MACHINE_BROKEN, {
                "machine": machine.name, "now": now,
                "affected": [(b.user_id, f"{b.start:%d.%m %H:%M}") for b in affected]})
        else:
            # Buzilish sababli navbati bekor bo'lganlarga «tuzatildi» xabari
            watchers = self.bookings.users_with_cancelled_future(machine_id, now)
            self.events.notify(MACHINE_FIXED, {"machine": machine.name,
                                               "watchers": watchers, "now": now})
