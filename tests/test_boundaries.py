"""Chegaraviy testlar: xatolar ko'pincha chegarada bo'ladi."""
from datetime import date, timedelta

import pytest

from kirnavbat import validators as v

TODAY = date(2026, 11, 16)


@pytest.mark.parametrize("hour, expected", [(7, False), (8, True), (21, True), (22, False)])
def test_hour_boundaries(hour, expected):
    assert v.is_valid_hour(hour) is expected


@pytest.mark.parametrize("delta, expected", [(-1, False), (0, True), (6, True), (7, False)])
def test_day_boundaries(delta, expected):
    assert v.is_valid_day(TODAY + timedelta(days=delta), TODAY) is expected


@pytest.mark.parametrize("room, expected", [(0, False), (1, True), (999, True), (1000, False)])
def test_room_boundaries(room, expected):
    assert v.is_valid_room(room) is expected


@pytest.mark.parametrize("pwd, expected", [("12345", False), ("123456", True)])
def test_password_length_boundary(pwd, expected):
    assert v.is_valid_password(pwd) is expected
