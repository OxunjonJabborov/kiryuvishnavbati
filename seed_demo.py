"""Namoyish uchun demo ma'lumotlar: python seed_demo.py (bazani to'ldiradi)."""
from datetime import datetime, timedelta

from kirnavbat.app import create_app, tashkent_now

STUDENTS = [("ali", "Aliyev Ali", "312"), ("vali", "Valiyev Vali", "215"),
            ("dilnoza", "Karimova Dilnoza", "408"), ("sardor", "Rahimov Sardor", "117"),
            ("madina", "Yusupova Madina", "406"), ("jasur", "Tursunov Jasur", "221")]

app = create_app()
s = app.extensions["kirnavbat"]
for username, name, room in STUDENTS:
    if s["users"].by_username(username) is None:
        s["auth"].register(username, name, room, "parol123")

now = tashkent_now().replace(minute=0, second=0, microsecond=0)
today, tomorrow = now.date(), now.date() + timedelta(days=1)
plan = [("vali", 1, today, 16), ("dilnoza", 1, today, 18), ("sardor", 2, today, 17),
        ("madina", 3, today, 20), ("jasur", 2, tomorrow, 9), ("dilnoza", 3, tomorrow, 12),
        ("sardor", 4, tomorrow, 10), ("ali", 1, today, 19)]
for username, machine, day, hour in plan:
    try:
        s["booking"].book(s["users"].by_username(username), machine, day, hour,
                          now - timedelta(hours=10))
    except Exception as e:  # demo: band bo'lsa o'tkazib yuboramiz
        print("o'tkazildi:", username, e)
admin = s["users"].by_username("admin")
s["booking"].set_machine_status(admin, 4, "buzilgan", now)
print("Demo ma'lumotlar tayyor.")
