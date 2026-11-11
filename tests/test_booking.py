"""Navbat olish va bekor qilish qoidalari."""
from datetime import date

import pytest

from kirnavbat.services import ServiceError, can_cancel
from tests.conftest import FIXED_NOW

DAY = date(2026, 11, 16)


def test_book_free_slot(svc, ali):
    booking_id = svc["booking"].book(ali, 1, DAY, 14, FIXED_NOW)
    assert svc["bookings"].by_id(booking_id).user_id == ali.id


def test_same_slot_cannot_be_booked_twice(svc, ali, vali):
    svc["booking"].book(ali, 1, DAY, 14, FIXED_NOW)
    with pytest.raises(ServiceError, match="band"):
        svc["booking"].book(vali, 1, DAY, 14, FIXED_NOW)


def test_max_two_active_bookings(svc, ali):
    svc["booking"].book(ali, 1, DAY, 12, FIXED_NOW)
    svc["booking"].book(ali, 1, DAY, 13, FIXED_NOW)          # 2-navbat — chegarada, ruxsat
    with pytest.raises(ServiceError, match="ko'pi bilan 2"):
        svc["booking"].book(ali, 1, DAY, 14, FIXED_NOW)       # 3-navbat — rad etiladi


def test_past_slot_rejected(svc, ali):
    with pytest.raises(ServiceError, match="O'tib ketgan"):
        svc["booking"].book(ali, 1, DAY, 10, FIXED_NOW)       # 10:00 < 10:30


def test_student_cannot_cancel_others_booking(svc, ali, vali):
    bid = svc["booking"].book(ali, 1, DAY, 15, FIXED_NOW)
    with pytest.raises(ServiceError, match="huquqingiz yo'q"):
        svc["booking"].cancel(vali, bid, FIXED_NOW)
    assert svc["bookings"].by_id(bid).is_active()


def test_owner_cancels_and_slot_becomes_free(svc, ali, vali):
    bid = svc["booking"].book(ali, 1, DAY, 15, FIXED_NOW)
    svc["booking"].cancel(ali, bid, FIXED_NOW)
    assert svc["booking"].book(vali, 1, DAY, 15, FIXED_NOW)   # endi Vali ola oladi


def test_can_cancel_all_paths(svc, ali, vali, admin):
    """V(G)=3 bo'lgani uchun can_cancel ning 3 ta yo'li ham tekshiriladi."""
    bid = svc["booking"].book(ali, 1, DAY, 16, FIXED_NOW)
    b = svc["bookings"].by_id(bid)
    assert can_cancel(b, admin, FIXED_NOW) is True            # 1-yo'l: admin
    assert can_cancel(b, vali, FIXED_NOW) is False            # 2-yo'l: begona
    assert can_cancel(b, ali, FIXED_NOW) is True              # 3-yo'l: egasi, kelajakda


def test_race_two_students_same_slot(svc, ali, vali, monkeypatch):
    """Ikki talaba bir soniyada bosdi: is_taken ikkalasiga ham 'bo'sh' dedi."""
    svc["booking"].book(ali, 3, DAY, 19, FIXED_NOW)
    monkeypatch.setattr(svc["booking"].bookings, "is_taken", lambda *a: False)
    with pytest.raises(ServiceError, match="band"):
        svc["booking"].book(vali, 3, DAY, 19, FIXED_NOW)
