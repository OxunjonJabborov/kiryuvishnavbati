"""Observer (kuzatuvchi) pattern.

Mashina buzilsa yoki navbat bekor qilinsa, `EventBus` (Subject) barcha
obuna bo'lgan kuzatuvchilarga avtomatik xabar beradi. Shunda mantiq
qatlami kimga va qanday xabar yuborilishini bilmaydi — yangi kuzatuvchi
(masalan, Telegram) qo'shish uchun mavjud kod o'zgarmaydi.
"""
from abc import ABC, abstractmethod
from datetime import datetime

MACHINE_BROKEN = "machine_broken"
MACHINE_FIXED = "machine_fixed"
BOOKING_CANCELLED = "booking_cancelled"


class Observer(ABC):
    @abstractmethod
    def update(self, event: str, data: dict) -> None:
        """Hodisa sodir bo'lganda chaqiriladi."""


class EventBus:
    """Subject: kuzatuvchilar ro'yxatini saqlaydi va ularga xabar beradi."""

    def __init__(self):
        self._observers: list[Observer] = []

    def subscribe(self, observer: Observer) -> None:
        self._observers.append(observer)

    def unsubscribe(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self, event: str, data: dict) -> None:
        for observer in self._observers:
            observer.update(event, data)


class NotificationObserver(Observer):
    """Hodisani foydalanuvchilar uchun ichki xabarnomaga aylantiradi."""

    def __init__(self, notification_repo):
        self.repo = notification_repo

    def update(self, event: str, data: dict) -> None:
        now = data.get("now", datetime.now())
        if event == MACHINE_BROKEN:
            for user_id, start in data["affected"]:
                self.repo.add(user_id,
                              f"«{data['machine']}» buzildi. {start} dagi "
                              "navbatingiz bekor qilindi, boshqa mashinani tanlang.",
                              now)
        elif event == MACHINE_FIXED:
            for user_id in data["watchers"]:
                self.repo.add(user_id, f"«{data['machine']}» yana ishlayapti.", now)
        elif event == BOOKING_CANCELLED and data.get("by_admin"):
            self.repo.add(data["owner_id"],
                          f"{data['start']} dagi navbatingizni administrator "
                          "bekor qildi.", now)


class AuditLogObserver(Observer):
    """Har bir hodisani audit jurnaliga yozadi (kim, nima, qachon)."""

    def __init__(self):
        self.records: list[str] = []

    def update(self, event: str, data: dict) -> None:
        safe = {k: v for k, v in data.items() if k != "now"}
        self.records.append(f"{datetime.now():%Y-%m-%d %H:%M:%S} {event} {safe}")
