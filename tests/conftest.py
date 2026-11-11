"""Umumiy test sozlamalari: har bir test toza vaqtinchalik bazada ishlaydi."""
import os
from datetime import datetime

import pytest

from kirnavbat.app import create_app

# Belgilangan "hozir": 2026-yil 16-noyabr, dushanba, 10:30
FIXED_NOW = datetime(2026, 11, 16, 10, 30)


@pytest.fixture
def app(tmp_path):
    return create_app({"DATABASE": os.path.join(tmp_path, "test.db"),
                       "TESTING": True, "CSRF_DISABLED": True,
                       "NOW": lambda: FIXED_NOW})


@pytest.fixture
def svc(app):
    return app.extensions["kirnavbat"]


@pytest.fixture
def ali(svc):
    return svc["auth"].register("ali", "Aliyev Ali", "312", "parol123")


@pytest.fixture
def vali(svc):
    return svc["auth"].register("vali", "Valiyev Vali", "215", "parol456")


@pytest.fixture
def admin(svc):
    return svc["users"].by_username("admin")
