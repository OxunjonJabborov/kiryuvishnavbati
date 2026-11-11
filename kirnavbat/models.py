"""Domen sinflari: Foydalanuvchi, Mashina, Navbat, Xabarnoma."""
from dataclasses import dataclass
from datetime import datetime

ROLE_STUDENT = "talaba"
ROLE_ADMIN = "admin"
ROLE_TECH = "texnik"

STATUS_WORKING = "ishlaydi"
STATUS_BROKEN = "buzilgan"


@dataclass
class User:
    """TTJ da yashovchi talaba, administrator yoki texnik usta."""
    id: int
    username: str
    full_name: str
    room: int
    role: str
    password_hash: str = ""

    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    def can_change_machine(self) -> bool:
        """Mashina holatini faqat admin yoki texnik o'zgartira oladi."""
        return self.role in (ROLE_ADMIN, ROLE_TECH)


@dataclass
class Machine:
    """Bitta kir yuvish mashinasi."""
    id: int
    name: str
    floor: int
    status: str = STATUS_WORKING

    def is_available(self) -> bool:
        return self.status == STATUS_WORKING


@dataclass
class Booking:
    """Bir soatlik navbat: qaysi talaba, qaysi mashina, qachon."""
    id: int
    user_id: int
    machine_id: int
    start: datetime
    status: str = "faol"          # faol | bekor

    def is_active(self) -> bool:
        return self.status == "faol"


@dataclass
class Notification:
    """Foydalanuvchiga ko'rsatiladigan xabar (Observer natijasi)."""
    id: int
    user_id: int
    text: str
    created_at: str
    is_read: int = 0
