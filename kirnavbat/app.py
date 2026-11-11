"""Ekran qatlami: Flask marshrutlari. SQL yo'q, faqat servislarni chaqiradi."""
import os
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import generate_password_hash

from . import validators as v
from .db import connect, init_db
from .models import ROLE_ADMIN, ROLE_TECH, STATUS_BROKEN, STATUS_WORKING
from .observer import AuditLogObserver, EventBus, NotificationObserver
from .repository import (BookingRepository, MachineRepository,
                         NotificationRepository, UserRepository)
from .services import AuthService, BookingService, ServiceError

WEEKDAYS = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=os.environ.get("KIRNAVBAT_SECRET", "dev-faqat-lokal-uchun"),
        DATABASE=os.path.join(app.instance_path, "kirnavbat.db"),
        NOW=datetime.now,            # testlarda vaqtni almashtirish uchun
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    conn = connect(app.config["DATABASE"])
    init_db(conn)
    users = UserRepository(conn)
    _seed_staff(users)
    events = EventBus()
    events.subscribe(NotificationObserver(NotificationRepository(conn)))
    audit = AuditLogObserver()
    events.subscribe(audit)

    app.extensions["kirnavbat"] = {
        "conn": conn, "users": users, "audit": audit,
        "auth": AuthService(users),
        "booking": BookingService(BookingRepository(conn),
                                  MachineRepository(conn), events),
        "machines": MachineRepository(conn),
        "bookings": BookingRepository(conn),
        "notes": NotificationRepository(conn),
    }
    _register_routes(app)
    return app


def _seed_staff(users: UserRepository) -> None:
    """Birinchi ishga tushishda administrator va texnik hisobini yaratadi."""
    if users.by_username("admin") is None:
        users.add("admin", "TTJ mudiri", 1, ROLE_ADMIN, generate_password_hash("admin123"))
    if users.by_username("usta") is None:
        users.add("usta", "Texnik usta", 1, ROLE_TECH, generate_password_hash("usta123"))


def _register_routes(app: Flask) -> None:
    def ctx():
        return app.extensions["kirnavbat"]

    def now() -> datetime:
        return app.config["NOW"]()

    @app.before_request
    def load_user():
        uid = session.get("user_id")
        g.user = ctx()["users"].by_id(uid) if uid else None

    @app.context_processor
    def inject():
        unread = ctx()["notes"].unread_count(g.user.id) if g.get("user") else 0
        return {"user": g.get("user"), "unread": unread}

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def staff_required(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not g.user.can_change_machine():
                abort(403)
            return view(*args, **kwargs)
        return wrapped

    @app.route("/")
    def index():
        return redirect(url_for("schedule"))

    @app.route("/kirish", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            try:
                user = ctx()["auth"].login(request.form.get("username", ""),
                                           request.form.get("password", ""), now())
                session.clear()
                session["user_id"] = user.id
                return redirect(url_for("schedule"))
            except ServiceError as e:
                flash(str(e), "error")
        return render_template("login.html")

    @app.route("/royxat", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            f = request.form
            try:
                ctx()["auth"].register(f.get("username", ""), f.get("full_name", ""),
                                       f.get("room", ""), f.get("password", ""))
                flash("Ro'yxatdan o'tdingiz. Endi kiring.", "ok")
                return redirect(url_for("login"))
            except ServiceError as e:
                flash(str(e), "error")
        return render_template("register.html")

    @app.route("/chiqish")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/jadval")
    @login_required
    def schedule():
        today = now().date()
        try:
            day = date.fromisoformat(request.args.get("kun", today.isoformat()))
        except ValueError:
            day = today
        if not v.is_valid_day(day, today):
            day = today
        days = [today + timedelta(days=i) for i in range(v.BOOK_DAYS_AHEAD + 1)]
        grid = ctx()["booking"].day_grid(day)
        rooms = {b.user_id: ctx()["users"].by_id(b.user_id).room for b in grid.values()}
        return render_template(
            "schedule.html", day=day, days=days, weekdays=WEEKDAYS,
            machines=ctx()["machines"].all(), grid=grid, rooms=rooms,
            hours=range(v.FIRST_HOUR, v.LAST_HOUR + 1), now=now())

    @app.post("/navbat")
    @login_required
    def book():
        f = request.form
        try:
            day = date.fromisoformat(f.get("day", ""))
            ctx()["booking"].book(g.user, int(f.get("machine_id", 0)), day,
                                  int(f.get("hour", 0)), now())
            flash(f"Navbat olindi: {day:%d.%m}, {int(f['hour']):02d}:00.", "ok")
        except (ValueError, ServiceError) as e:
            msg = str(e) if isinstance(e, ServiceError) else "Noto'g'ri ma'lumot."
            flash(msg, "error")
            day = None
        return redirect(url_for("schedule", kun=day.isoformat() if day else None))

    @app.route("/navbatlarim")
    @login_required
    def my_bookings():
        items = ctx()["bookings"].for_user(g.user.id)
        names = {m.id: m.name for m in ctx()["machines"].all()}
        return render_template("my_bookings.html", items=items, names=names, now=now())

    @app.post("/navbat/<int:booking_id>/bekor")
    @login_required
    def cancel(booking_id):
        try:
            ctx()["booking"].cancel(g.user, booking_id, now())
            flash("Navbat bekor qilindi.", "ok")
        except ServiceError as e:
            flash(str(e), "error")
        return redirect(request.referrer or url_for("my_bookings"))

    @app.route("/xabarlar")
    @login_required
    def notifications():
        items = ctx()["notes"].for_user(g.user.id)
        ctx()["notes"].mark_all_read(g.user.id)
        return render_template("notifications.html", items=items)

    @app.route("/boshqaruv")
    @staff_required
    def admin():
        today = now().date()
        grid = ctx()["booking"].day_grid(today)
        users = {b.user_id: ctx()["users"].by_id(b.user_id) for b in grid.values()}
        return render_template("admin.html", machines=ctx()["machines"].all(),
                               grid=grid, users=users, today=today,
                               log=ctx()["audit"].records[-8:][::-1])

    @app.post("/boshqaruv/mashina/<int:machine_id>")
    @staff_required
    def machine_status(machine_id):
        status = request.form.get("status", "")
        try:
            ctx()["booking"].set_machine_status(g.user, machine_id, status, now())
            flash("Mashina holati yangilandi.", "ok")
        except ServiceError as e:
            flash(str(e), "error")
        return redirect(url_for("admin"))
