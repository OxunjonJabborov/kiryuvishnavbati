"""Veb qatlam testlari (HTTP orqali)."""
import os

from kirnavbat.app import create_app
from tests.conftest import FIXED_NOW


def _login(client, username, password):
    return client.post("/kirish", data={"username": username, "password": password})


def test_schedule_requires_login(app):
    resp = app.test_client().get("/jadval")
    assert resp.status_code == 302 and "/kirish" in resp.headers["Location"]


def test_student_gets_403_on_admin_page(app, ali):
    c = app.test_client()
    _login(c, "ali", "parol123")
    assert c.get("/boshqaruv").status_code == 403


def test_full_booking_flow_over_http(app, ali):
    c = app.test_client()
    _login(c, "ali", "parol123")
    r = c.post("/navbat", data={"machine_id": 1, "day": "2026-11-16", "hour": 18},
               follow_redirects=True)
    assert "Navbat olindi" in r.text
    assert "18:00" in c.get("/navbatlarim").text


def test_post_without_csrf_token_is_rejected(tmp_path):
    app = create_app({"DATABASE": os.path.join(tmp_path, "c.db"), "TESTING": True,
                      "NOW": lambda: FIXED_NOW})
    resp = app.test_client().post("/kirish", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 400
