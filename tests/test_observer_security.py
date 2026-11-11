"""Observer pattern va xavfsizlik choralari."""
from datetime import date

import pytest

from kirnavbat.services import ServiceError
from tests.conftest import FIXED_NOW

DAY = date(2026, 11, 17)


def test_broken_machine_cancels_bookings_and_notifies(svc, ali, admin):
    svc["booking"].book(ali, 2, DAY, 9, FIXED_NOW)
    svc["booking"].set_machine_status(admin, 2, "buzilgan", FIXED_NOW)
    notes = svc["notes"].for_user(ali.id)
    assert len(notes) == 1 and "buzildi" in notes[0].text
    assert svc["bookings"].count_future_active(ali.id, FIXED_NOW) == 0
    with pytest.raises(ServiceError, match="buzilgan"):
        svc["booking"].book(ali, 2, DAY, 10, FIXED_NOW)


def test_fixed_machine_notifies_affected_users(svc, ali, admin):
    svc["booking"].book(ali, 2, DAY, 9, FIXED_NOW)
    svc["booking"].set_machine_status(admin, 2, "buzilgan", FIXED_NOW)
    svc["booking"].set_machine_status(admin, 2, "ishlaydi", FIXED_NOW)
    assert "yana ishlayapti" in svc["notes"].for_user(ali.id)[0].text


def test_student_cannot_change_machine_status(svc, ali):
    with pytest.raises(ServiceError, match="Faqat administrator"):
        svc["booking"].set_machine_status(ali, 1, "buzilgan", FIXED_NOW)


def test_password_is_not_stored_in_plain_text(svc, ali):
    stored = svc["users"].by_username("ali").password_hash
    assert "parol123" not in stored and stored.startswith(("pbkdf2:", "scrypt:"))


def test_account_locked_after_five_wrong_passwords(svc, ali):
    for _ in range(5):
        with pytest.raises(ServiceError):
            svc["auth"].login("ali", "xato-parol", FIXED_NOW)
    with pytest.raises(ServiceError, match="bloklangan"):
        svc["auth"].login("ali", "parol123", FIXED_NOW)       # to'g'ri parol ham rad


def test_sql_injection_in_login_does_not_work(svc, ali):
    with pytest.raises(ServiceError):
        svc["auth"].login("ali' OR '1'='1", "x", FIXED_NOW)
