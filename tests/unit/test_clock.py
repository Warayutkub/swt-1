"""เทสต์นาฬิกาของระบบ

ไฟล์เล็ก ๆ แต่สำคัญ - ถ้าไม่มีเทสต์ตรงนี้เลย จะไม่มีใครรู้ว่า
นาฬิกาตัวจริงยังทำงานอยู่ เพราะเทสต์อื่นแทนที่มันด้วยของปลอมหมด
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from chatlog import clock

pytestmark = pytest.mark.unit


def test_now_คืนค่าเป็น_datetime() -> None:
    assert isinstance(clock.now(), datetime)


def test_today_คืนค่าเป็น_date() -> None:
    assert isinstance(clock.today(), date)


def test_today_ตรงกับวันที่ของ_now() -> None:
    assert clock.today() == clock.now().date()


def test_monkeypatch_แทนนาฬิกาได้จริง(frozen_clock) -> None:
    """พิสูจน์ว่า fixture frozen_clock ทำงาน - ถ้าข้อนี้พัง เทสต์เรื่องเวลาทั้งหมดเชื่อไม่ได้"""
    assert clock.today() == date(2026, 9, 15)


def test_นาฬิกาคืนสภาพเดิมหลังเลิกใช้ของปลอม() -> None:
    """กรณีที่น่ากลัวที่สุดของ monkeypatch คือ "ลืมคืนค่า"

    ถ้าคืนไม่สำเร็จ เทสต์ตัวถัดไปจะได้นาฬิกาปลอมติดไปด้วย
    แล้วจะพังแบบหาสาเหตุไม่เจอ เทสต์นี้พิสูจน์ว่าคืนจริง
    """
    real_today = clock.today()

    with pytest.MonkeyPatch.context() as patched:
        patched.setattr(clock, "today", lambda: date(1999, 1, 1))
        assert clock.today() == date(1999, 1, 1)

    assert clock.today() == real_today
